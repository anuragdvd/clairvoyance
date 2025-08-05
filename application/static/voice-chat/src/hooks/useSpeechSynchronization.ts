import { useState, useEffect, useRef, useCallback } from 'react';
import { LLMVisualizationResponse, HighlightAction } from '../components/visualizations/types';

interface UseSpeechSynchronizationProps {
  llmResponse?: LLMVisualizationResponse | null;
  isAudioPlaying: boolean;
}

interface SpeechSyncState {
  currentTime: number;
  isPlaying: boolean;
  duration: number;
  activeHighlights: Set<string>;
  speechProgress: number; // 0-100%
}

export const useSpeechSynchronization = ({ 
  llmResponse, 
  isAudioPlaying 
}: UseSpeechSynchronizationProps) => {
  const [syncState, setSyncState] = useState<SpeechSyncState>({
    currentTime: 0,
    isPlaying: false,
    duration: 0,
    activeHighlights: new Set(),
    speechProgress: 0
  });

  const timeRef = useRef<number>(0);
  const animationFrameRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(0);
  const highlightTimeoutsRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  // Calculate estimated speech duration based on text length and speech rate
  const estimateSpeechDuration = useCallback((text: string): number => {
    // Average speaking rate: 150-160 words per minute
    const wordsPerMinute = 155;
    const words = text.split(/\s+/).length;
    const minutes = words / wordsPerMinute;
    return minutes * 60; // Convert to seconds
  }, []);

  // Process all highlights and markers to create a timeline
  const createHighlightTimeline = useCallback((response: LLMVisualizationResponse) => {
    const timeline: { time: number; highlight: HighlightAction; vizIndex: number }[] = [];
    
    if (response.visualizations) {
      response.visualizations.forEach((viz, vizIndex) => {
        if (viz.highlights) {
          viz.highlights.forEach(highlight => {
            timeline.push({ time: highlight.timestamp, highlight, vizIndex });
          });
        }
      });
    }

    // Sort by timestamp
    return timeline.sort((a, b) => a.time - b.time);
  }, []);

  // Update time and trigger highlights
  const updateTime = useCallback(() => {
    if (!isAudioPlaying || !llmResponse) return;

    const currentTime = (Date.now() - startTimeRef.current) / 1000;
    timeRef.current = currentTime;

    const estimatedDuration = estimateSpeechDuration(llmResponse.speechText || '');
    const progress = Math.min((currentTime / estimatedDuration) * 100, 100);

    setSyncState(prev => ({
      ...prev,
      currentTime,
      speechProgress: progress,
      isPlaying: isAudioPlaying
    }));

    // Process highlights for current time
    const timeline = createHighlightTimeline(llmResponse);
    const currentHighlights = new Set<string>();

    timeline.forEach(({ time, highlight, vizIndex }) => {
      const timeDiff = Math.abs(currentTime - time);
      
      // Trigger highlight if we're within 100ms of the timestamp
      if (timeDiff < 0.1) {
        const highlightId = `${vizIndex}-${highlight.target}-${time}`;
        
        if (!highlightTimeoutsRef.current.has(highlightId)) {
          // Trigger the highlight
          currentHighlights.add(highlightId);
          
          // Set timeout to clear highlight
          const timeout = setTimeout(() => {
            setSyncState(prev => {
              const newActiveHighlights = new Set(prev.activeHighlights);
              newActiveHighlights.delete(highlightId);
              return {
                ...prev,
                activeHighlights: newActiveHighlights
              };
            });
            highlightTimeoutsRef.current.delete(highlightId);
          }, highlight.duration || 2000);
          
          highlightTimeoutsRef.current.set(highlightId, timeout);
        }
      }
    });

    // Update active highlights
    if (currentHighlights.size > 0) {
      setSyncState(prev => {
        const newActiveHighlights = new Set(prev.activeHighlights);
        currentHighlights.forEach(id => newActiveHighlights.add(id));
        return {
          ...prev,
          activeHighlights: newActiveHighlights
        };
      });
    }

    // Continue animation
    if (isAudioPlaying && progress < 100) {
      animationFrameRef.current = requestAnimationFrame(updateTime);
    }
  }, [isAudioPlaying, llmResponse, estimateSpeechDuration, createHighlightTimeline]);

  // Start synchronization when audio starts playing
  useEffect(() => {
    if (isAudioPlaying && llmResponse) {
      startTimeRef.current = Date.now();
      timeRef.current = 0;
      
      const duration = estimateSpeechDuration(llmResponse.speechText || '');
      setSyncState(prev => ({
        ...prev,
        isPlaying: true,
        duration,
        currentTime: 0,
        speechProgress: 0,
        activeHighlights: new Set()
      }));

      // Start the animation loop
      animationFrameRef.current = requestAnimationFrame(updateTime);
    } else {
      // Stop synchronization
      setSyncState(prev => ({
        ...prev,
        isPlaying: false
      }));

      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }

      // Clear all highlight timeouts
      highlightTimeoutsRef.current.forEach(timeout => clearTimeout(timeout));
      highlightTimeoutsRef.current.clear();
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      highlightTimeoutsRef.current.forEach(timeout => clearTimeout(timeout));
      highlightTimeoutsRef.current.clear();
    };
  }, [isAudioPlaying, llmResponse, updateTime, estimateSpeechDuration]);

  // Manual time seeking (for future implementation)
  const seekTo = useCallback((timeInSeconds: number) => {
    timeRef.current = timeInSeconds;
    startTimeRef.current = Date.now() - (timeInSeconds * 1000);
    
    if (llmResponse) {
      const duration = estimateSpeechDuration(llmResponse.speechText || '');
      const progress = Math.min((timeInSeconds / duration) * 100, 100);
      
      setSyncState(prev => ({
        ...prev,
        currentTime: timeInSeconds,
        speechProgress: progress
      }));
    }
  }, [llmResponse, estimateSpeechDuration]);

  // Get current highlights for a specific visualization
  const getActiveHighlightsForVisualization = useCallback((vizIndex: number): HighlightAction[] => {
    if (!llmResponse?.visualizations?.[vizIndex]) return [];

    const timeline = createHighlightTimeline(llmResponse);
    const currentTime = syncState.currentTime;
    
    return timeline
      .filter(({ time, vizIndex: vIndex }) => 
        vIndex === vizIndex && 
        Math.abs(currentTime - time) < 0.1
      )
      .map(({ highlight }) => highlight);
  }, [llmResponse, syncState.currentTime, createHighlightTimeline]);

  // Get speech markers for current time
  const getCurrentSpeechMarkers = useCallback((): string[] => {
    if (!llmResponse?.speechMarkers) return [];

    const currentTime = syncState.currentTime;
    return Object.entries(llmResponse.speechMarkers)
      .filter(([, timestamp]) => Math.abs(currentTime - timestamp) < 0.1)
      .map(([marker]) => marker);
  }, [llmResponse, syncState.currentTime]);

  return {
    syncState,
    seekTo,
    getActiveHighlightsForVisualization,
    getCurrentSpeechMarkers,
    
    // Helper methods
    formatTime: (seconds: number) => {
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    },
    
    // Debug info
    debug: {
      highlightTimeouts: highlightTimeoutsRef.current.size,
      timelineLength: llmResponse ? createHighlightTimeline(llmResponse).length : 0
    }
  };
};
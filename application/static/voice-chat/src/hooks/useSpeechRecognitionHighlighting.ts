import { useState, useEffect, useRef, useCallback } from 'react';
import { LLMVisualizationResponse } from '../components/visualizations/types';

// Declare global speech recognition interface
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

interface HighlightState {
  activeTarget: string | number | null;
  lastTriggered: number;
}

export const useSpeechRecognitionHighlighting = (
  llmResponse?: LLMVisualizationResponse | null,
  isAudioPlaying?: boolean
) => {
  const [highlightState, setHighlightState] = useState<HighlightState>({
    activeTarget: null,
    lastTriggered: 0
  });

  const recognitionRef = useRef<any>(null);
  const keywordMapRef = useRef<Map<string, { target: string | number; action: string }>>(new Map());
  const highlightTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Build keyword mapping from speech markers and highlights
  useEffect(() => {
    if (!llmResponse) {
      keywordMapRef.current.clear();
      return;
    }

    const keywordMap = new Map();
    
    // Extract keywords from speechMarkers
    if (llmResponse.speechMarkers) {
      Object.entries(llmResponse.speechMarkers).forEach(([keyword, timestamp]) => {
        // Find corresponding highlight action
        const visualization = llmResponse.visualizations?.[0];
        if (visualization?.highlights) {
          const highlight = visualization.highlights.find(h => 
            Math.abs(h.timestamp - timestamp) < 1.0 // Match within 1 second
          );
          
          if (highlight) {
            // Add the exact keyword and variations
            keywordMap.set(keyword.toLowerCase(), {
              target: highlight.target,
              action: highlight.action
            });
            
            // Add number variations for years
            if (/^\d{4}$/.test(keyword)) {
              keywordMap.set(keyword, { target: highlight.target, action: highlight.action });
            }
            
            // Add word variations
            const words = keyword.toLowerCase().split(' ');
            words.forEach(word => {
              if (word.length > 2) { // Only meaningful words
                keywordMap.set(word, { target: highlight.target, action: highlight.action });
              }
            });
          }
        }
      });
    }

    keywordMapRef.current = keywordMap;
    console.log('🎯 Built keyword map:', Array.from(keywordMap.entries()));
  }, [llmResponse]);

  // Trigger highlight
  const triggerHighlight = useCallback((target: string | number, duration: number = 2000) => {
    console.log('🎯 Triggering highlight for target:', target);
    
    setHighlightState({
      activeTarget: target,
      lastTriggered: Date.now()
    });

    // Clear previous timeout
    if (highlightTimeoutRef.current) {
      clearTimeout(highlightTimeoutRef.current);
    }

    // Auto-clear highlight after duration
    highlightTimeoutRef.current = setTimeout(() => {
      setHighlightState(prev => ({
        ...prev,
        activeTarget: null
      }));
    }, duration);
  }, []);

  // Speech recognition setup
  useEffect(() => {
    if (!isAudioPlaying || !llmResponse || keywordMapRef.current.size === 0) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
      return;
    }

    // Check if Speech Recognition is supported
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('Speech Recognition not supported in this browser');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((result: any) => result[0])
          .map((result) => result.transcript)
          .join('');

        console.log('🎤 Recognized speech:', transcript);

        // Check for keyword matches
        const lowerTranscript = transcript.toLowerCase();
        keywordMapRef.current.forEach((action, keyword) => {
          if (lowerTranscript.includes(keyword)) {
            console.log('🎯 Keyword detected:', keyword, '-> Target:', action.target);
            triggerHighlight(action.target);
            return; // Only trigger first match
          }
        });
      };

      recognition.onerror = (event: any) => {
        console.warn('Speech recognition error:', event.error);
      };

      recognition.start();
      recognitionRef.current = recognition;

      console.log('🎤 Started speech recognition for highlighting');
    } catch (error) {
      console.error('Failed to start speech recognition:', error);
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
    };
  }, [isAudioPlaying, llmResponse, triggerHighlight]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (highlightTimeoutRef.current) {
        clearTimeout(highlightTimeoutRef.current);
      }
    };
  }, []);

  return {
    activeTarget: highlightState.activeTarget,
    triggerHighlight
  };
};
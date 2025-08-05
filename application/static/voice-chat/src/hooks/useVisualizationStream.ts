import { useState, useEffect, useRef, useCallback } from 'react';
import { LLMVisualizationResponse } from '../components/visualizations/types';

interface UseVisualizationStreamProps {
  sessionId: string | undefined;
}

export const useVisualizationStream = ({ sessionId }: UseVisualizationStreamProps) => {
  const [currentVisualization, setCurrentVisualization] = useState<LLMVisualizationResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const visualizationWSRef = useRef<WebSocket | null>(null);

  const connectVisualizationWebSocket = useCallback((sessionId: string) => {
    if (visualizationWSRef.current) {
      visualizationWSRef.current.close();
    }

    const wsUrl = `ws://localhost:8000/ws/visualization/${sessionId}`;
    console.log('📊 Connecting to visualization WebSocket:', wsUrl);
    
    visualizationWSRef.current = new WebSocket(wsUrl);
    
    visualizationWSRef.current.onopen = () => {
      console.log('✅ Visualization WebSocket connected');
    };
    
    visualizationWSRef.current.onmessage = async (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('📊 Received visualization message:', message);
        
        if (message.type === 'visualization' && message.data) {
          setIsProcessing(true);
          setCurrentVisualization(message.data);
          console.log('🎨 Updated visualization state:', message.data);
        }
      } catch (error) {
        console.error('Error parsing visualization message:', error);
      } finally {
        setIsProcessing(false);
      }
    };
    
    visualizationWSRef.current.onclose = () => {
      console.log('🔌 Visualization WebSocket disconnected');
    };
    
    visualizationWSRef.current.onerror = (error) => {
      console.error('🔌 Visualization WebSocket error:', error);
    };
  }, []);

  // Parse JSON from transcript messages in real-time
  const parseVisualizationFromTranscript = useCallback((transcriptText: string) => {
    // Look for JSON blocks in transcript
    const jsonMatch = transcriptText.match(/```json\s*([\s\S]*?)\s*```/);
    if (jsonMatch) {
      try {
        const jsonData = JSON.parse(jsonMatch[1]);
        if (jsonData.visualizations && Array.isArray(jsonData.visualizations)) {
          console.log('🎯 Extracted visualization from transcript:', jsonData);
          setCurrentVisualization(jsonData);
          return true;
        }
      } catch (error) {
        console.log('Failed to parse JSON from transcript:', error);
      }
    }

    // Also look for direct JSON objects
    const directJsonMatch = transcriptText.match(/\{\s*"speechText"[\s\S]*?"visualizations"[\s\S]*?\}/);
    if (directJsonMatch) {
      try {
        const jsonData = JSON.parse(directJsonMatch[0]);
        if (jsonData.visualizations && Array.isArray(jsonData.visualizations)) {
          console.log('🎯 Extracted direct JSON from transcript:', jsonData);
          setCurrentVisualization(jsonData);
          return true;
        }
      } catch (error) {
        console.log('Failed to parse direct JSON from transcript:', error);
      }
    }

    return false;
  }, []);

  useEffect(() => {
    if (sessionId) {
      connectVisualizationWebSocket(sessionId);
    }

    return () => {
      if (visualizationWSRef.current) {
        visualizationWSRef.current.close();
        visualizationWSRef.current = null;
      }
    };
  }, [sessionId]); // Removed connectVisualizationWebSocket from dependencies

  const clearVisualization = useCallback(() => {
    setCurrentVisualization(null);
  }, []);

  const setMockVisualization = useCallback((mockData: LLMVisualizationResponse) => {
    setCurrentVisualization(mockData);
  }, []);

  return {
    currentVisualization,
    isProcessing,
    parseVisualizationFromTranscript,
    clearVisualization,
    setMockVisualization
  };
};
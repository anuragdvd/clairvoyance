import { useState, useEffect, useCallback, useRef } from 'react';
import { TranscriptMessage } from '../components/TranscriptDisplay';
import { useAudioManager } from './useAudioManager';

export const useWebSockets = (sessionId: string | undefined) => {
  const [transcript, setTranscript] = useState<TranscriptMessage[]>([]);
  const transcriptWSRef = useRef<WebSocket | null>(null);
  const audioWSRef = useRef<WebSocket | null>(null);
  const { playAudioData, resetAudio } = useAudioManager();

  const addToTranscript = useCallback((speaker: 'user' | 'assistant' | 'system', message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setTranscript(prev => [...prev, { timestamp, speaker, message }]);
  }, []);

  const connectTranscriptWebSocket = useCallback((sessionId: string) => {
    if (transcriptWSRef.current) {
      transcriptWSRef.current.close();
    }

    const wsUrl = `ws://localhost:8000/ws/transcript/${sessionId}`;
    transcriptWSRef.current = new WebSocket(wsUrl);

    transcriptWSRef.current.onopen = () => {
      console.log('📝 Transcript WebSocket connected');
      addToTranscript('system', 'Transcript stream connected');
    };

    transcriptWSRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('📝 Received transcript:', data);
        
        if (data.type === 'transcript' && data.speaker && data.message) {
          addToTranscript(data.speaker, data.message);
        }
      } catch (error) {
        console.error('Error parsing transcript message:', error);
      }
    };

    transcriptWSRef.current.onclose = () => {
      console.log('📝 Transcript WebSocket disconnected');
      addToTranscript('system', 'Transcript stream disconnected');
    };

    transcriptWSRef.current.onerror = (error) => {
      console.error('📝 Transcript WebSocket error:', error);
      addToTranscript('system', 'Transcript connection error');
    };
  }, [addToTranscript]);

  const connectAudioWebSocket = useCallback((sessionId: string) => {
    if (audioWSRef.current) {
      audioWSRef.current.close();
    }

    // Reset audio state for new session
    resetAudio();

    const wsUrl = `ws://localhost:8000/ws/audio/${sessionId}`;
    console.log('🔊 Connecting to audio WebSocket:', wsUrl);
    
    audioWSRef.current = new WebSocket(wsUrl);
    
    audioWSRef.current.onopen = () => {
      console.log('✅ Audio WebSocket connected');
    };
    
    audioWSRef.current.onmessage = async (event) => {
      if (event.data instanceof Blob) {
        // Received audio data
        const arrayBuffer = await event.data.arrayBuffer();
        const uint8Array = new Uint8Array(arrayBuffer);
        console.log('🎵 Received audio data:', uint8Array.length, 'bytes');
        
        // Convert PCM to AudioBuffer and play
        playAudioData(uint8Array);
      } else {
        // Text message (ping/pong)
        console.log('Audio WS message:', event.data);
      }
    };
    
    audioWSRef.current.onclose = () => {
      console.log('🔌 Audio WebSocket disconnected');
    };
    
    audioWSRef.current.onerror = (error) => {
      console.error('🔌 Audio WebSocket error:', error);
    };
  }, [playAudioData, resetAudio]);

  useEffect(() => {
    if (sessionId) {
      connectTranscriptWebSocket(sessionId);
      connectAudioWebSocket(sessionId);
    }

    return () => {
      if (transcriptWSRef.current) {
        transcriptWSRef.current.close();
        transcriptWSRef.current = null;
      }
      if (audioWSRef.current) {
        audioWSRef.current.close();
        audioWSRef.current = null;
      }
    };
  }, [sessionId, connectTranscriptWebSocket, connectAudioWebSocket]);

  return {
    transcript,
    addToTranscript
  };
};
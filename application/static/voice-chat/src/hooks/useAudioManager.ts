import { useCallback, useRef, useState } from 'react';

export const useAudioManager = () => {
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const [isPlaying, setIsPlaying] = useState(false);

  const setupAudio = useCallback(async () => {
    try {
      if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      
      if (audioContextRef.current.state === 'suspended') {
        await audioContextRef.current.resume();
      }
      
      console.log('🎵 Audio context created for WebSocket audio');
      return audioContextRef.current;
    } catch (error) {
      console.error('Failed to setup audio:', error);
      throw error;
    }
  }, []);

  const playAudioData = useCallback(async (uint8Array: Uint8Array) => {
    try {
      if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
        console.warn('Audio context not available');
        return;
      }
      
      // Convert bytes back to float32 samples (reverse of server PCM encoding)
      const samples = new Float32Array(uint8Array.length / 2);
      const view = new DataView(uint8Array.buffer);
      
      for (let i = 0; i < samples.length; i++) {
        const int16 = view.getInt16(i * 2, true); // little endian
        samples[i] = int16 / 32768.0; // Convert back to float
      }
      
      // Create AudioBuffer
      const audioBuffer = audioContextRef.current.createBuffer(1, samples.length, 16000);
      audioBuffer.getChannelData(0).set(samples);
      
      // Queue and play
      audioQueueRef.current.push(audioBuffer);
      if (!isPlayingRef.current) {
        isPlayingRef.current = true;
        setIsPlaying(true);
        playNextAudio();
      }
      
    } catch (error) {
      console.error('Error playing audio:', error);
    }
  }, []);

  const playNextAudio = useCallback(() => {
    if (audioQueueRef.current.length === 0 || !audioContextRef.current) {
      isPlayingRef.current = false;
      setIsPlaying(false);
      return;
    }
    
    const audioBuffer = audioQueueRef.current.shift()!;
    const source = audioContextRef.current.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContextRef.current.destination);
    
    source.onended = () => {
      console.log('🎵 Audio chunk finished');
      // Play next chunk immediately for seamless streaming
      if (audioQueueRef.current.length > 0) {
        playNextAudio(); // No delay for continuous streaming
      } else {
        isPlayingRef.current = false;
        setIsPlaying(false);
      }
    };
    
    source.start();
    console.log('🔊 Playing audio chunk');
  }, []);

  const resetAudio = useCallback(() => {
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    setIsPlaying(false);
  }, []);

  return {
    setupAudio,
    playAudioData,
    resetAudio,
    isPlaying
  };
};
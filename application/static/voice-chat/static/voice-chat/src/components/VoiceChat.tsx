import React, { useState, useCallback } from 'react';
import { useAudioManager } from '../hooks/useAudioManager';
import { useWebSockets } from '../hooks/useWebSockets';
import { useDailyCall } from '../hooks/useDailyCall';
import { TranscriptDisplay } from './TranscriptDisplay';
import { VoiceControls } from './VoiceControls';
import { SessionInfo } from './SessionInfo';

interface VoiceSession {
  session_id: string;
  room_url: string;
  room_token: string;
}

export const VoiceChat: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [sessionData, setSessionData] = useState<VoiceSession | null>(null);
  const [status, setStatus] = useState('Ready to start voice session');
  const [userName, setUserName] = useState('');
  const [voiceName, setVoiceName] = useState('');
  const [ttsProvider, setTtsProvider] = useState('google');

  const { transcript, addToTranscript } = useWebSockets(sessionData?.session_id);
  const { setupAudio } = useAudioManager();
  const { joinCall, leaveCall } = useDailyCall();

  const startVoiceSession = useCallback(async () => {
    try {
      setStatus('Starting voice session...');
      
      const response = await fetch('/voice/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_name: userName || null,
          tts_provider: ttsProvider,
          voice_name: voiceName || null,
          session_timeout: 1800
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: VoiceSession = await response.json();
      setSessionData(data);
      
      // Setup audio context
      await setupAudio();
      
      // Join Daily.co call
      await joinCall(data.room_url, data.room_token);
      
      setIsConnected(true);
      setStatus('Connected! You can now speak to the voice agent.');
      addToTranscript('system', 'Voice session started');
      
    } catch (error) {
      console.error('Error starting voice session:', error);
      setStatus(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [userName, ttsProvider, voiceName, setupAudio, joinCall, addToTranscript]);

  const stopVoiceSession = useCallback(async () => {
    try {
      setStatus('Stopping voice session...');
      
      await leaveCall();
      setIsConnected(false);
      setSessionData(null);
      setStatus('Voice session stopped');
      addToTranscript('system', 'Voice session ended');
      
    } catch (error) {
      console.error('Error stopping voice session:', error);
      setStatus(`Error stopping session: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [leaveCall, addToTranscript]);

  return (
    <div className="voice-chat">
      <div className="header">
        <h1>🎤 Voice AI Assistant</h1>
        <p className="subtitle">Powered by PipeCat + Daily.co + Azure OpenAI</p>
      </div>

      <div className="main-content">
        <div className="left-panel">
          <VoiceControls
            isConnected={isConnected}
            userName={userName}
            setUserName={setUserName}
            voiceName={voiceName}
            setVoiceName={setVoiceName}
            ttsProvider={ttsProvider}
            setTtsProvider={setTtsProvider}
            onStart={startVoiceSession}
            onStop={stopVoiceSession}
            status={status}
          />
          
          {sessionData && (
            <SessionInfo sessionData={sessionData} />
          )}
        </div>

        <div className="right-panel">
          <TranscriptDisplay 
            transcript={transcript}
            isConnected={isConnected}
          />
        </div>
      </div>
    </div>
  );
};
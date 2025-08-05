import React, { useState, useCallback } from 'react';
import { useAudioManager } from '../hooks/useAudioManager';
import { useWebSockets } from '../hooks/useWebSockets';
import { useDailyCall } from '../hooks/useDailyCall';
import { useSpeechSynchronization } from '../hooks/useSpeechSynchronization';
import { useSpeechRecognitionHighlighting } from '../hooks/useSpeechRecognitionHighlighting';
import { useVisualizationStream } from '../hooks/useVisualizationStream';
import { TranscriptDisplay } from './TranscriptDisplay';
import { VoiceControls } from './VoiceControls';
import { SessionInfo } from './SessionInfo';
import { VisualizationContainer } from './visualizations/VisualizationContainer';
import { LLMVisualizationResponse } from './visualizations/types';
import './VoiceChat.css';

interface VoiceSession {
  session_id: string;
  room_url: string;
  room_token: string;
}

export const VoiceChat: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [sessionData, setSessionData] = useState<VoiceSession | null>(null);
  const [status, setStatus] = useState('Ready to start voice session');
  const [currentView, setCurrentView] = useState<'start' | 'conversation'>('start');
  const [userName, setUserName] = useState('');
  const [voiceName, setVoiceName] = useState('');
  const [ttsProvider, setTtsProvider] = useState('google');
  const { setupAudio, playAudioData, resetAudio, isPlaying } = useAudioManager();

  const {
    currentVisualization,
    parseVisualizationFromTranscript,
    clearVisualization: clearLiveVisualization,
    setMockVisualization
  } = useVisualizationStream({
    sessionId: sessionData?.session_id
  });

  const { transcript, addToTranscript } = useWebSockets({
    sessionId: sessionData?.session_id,
    playAudioData,
    resetAudio,
    onVisualizationData: parseVisualizationFromTranscript
  });
  const { joinCall, leaveCall } = useDailyCall();

  const { syncState, getActiveHighlightsForVisualization } = useSpeechSynchronization({
    llmResponse: currentVisualization,
    isAudioPlaying: isPlaying
  });

  // New speech recognition highlighting
  const { activeTarget, triggerHighlight } = useSpeechRecognitionHighlighting(
    currentVisualization,
    isPlaying
  );

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
      setCurrentView('conversation');
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
      setCurrentView('start');
      setStatus('Voice session stopped');
      addToTranscript('system', 'Voice session ended');

    } catch (error) {
      console.error('Error stopping voice session:', error);
      setStatus(`Error stopping session: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [leaveCall, addToTranscript]);

  // Mock LLM visualization response for demo (remove when backend integration is complete)
  const mockVisualization: LLMVisualizationResponse = {
    speechText: "Let me show you our sales data for the past 7 days. On the first day we had 100 sales, which was a great start. The fourth day was particularly strong with 180 sales.",
    speechMarkers: {
      "first day": 4.5,
      "fourth day": 8.2
    },
    visualizations: [
      {
        type: 'bar',
        title: 'Weekly Sales Data',
        data: [
          { name: 'Day 1', value: 100 },
          { name: 'Day 2', value: 120 },
          { name: 'Day 3', value: 150 },
          { name: 'Day 4', value: 180 },
          { name: 'Day 5', value: 160 },
          { name: 'Day 6', value: 140 },
          { name: 'Day 7', value: 170 }
        ],
        highlights: [
          { timestamp: 4.5, target: 0, action: 'highlight', duration: 2000, color: '#ff6b6b' },
          { timestamp: 8.2, target: 3, action: 'pulse', duration: 3000, color: '#4ecdc4' }
        ],
        config: {
          xKey: 'name',
          yKey: 'value',
          colors: ['#667eea'],
          animated: true
        }
      }
    ],
    presentationMode: false
  };

  const handleVisualizationInteraction = useCallback((type: string, target: string | number) => {
    console.log('Visualization interaction:', { type, target });
  }, []);

  // Start Screen - Clean single button
  if (currentView === 'start') {
    return (
      <div className="voice-chat" style={{
        fontFamily: 'system-ui, -apple-system, sans-serif',
        height: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{
          textAlign: 'center',
          color: 'white',
          maxWidth: '400px',
          padding: '40px'
        }}>
          <div style={{ fontSize: '72px', marginBottom: '20px' }}>🎤</div>
          <h1 style={{ fontSize: '2.5rem', margin: '0 0 20px 0', fontWeight: '300' }}>
            Voice AI Assistant
          </h1>
          <p style={{ fontSize: '1.1rem', opacity: 0.9, marginBottom: '40px' }}>
            Click to start a voice conversation with AI
          </p>

          <button
            onClick={startVoiceSession}
            disabled={status.includes('Starting')}
            style={{
              fontSize: '1.2rem',
              padding: '20px 40px',
              background: 'rgba(255, 255, 255, 0.2)',
              color: 'white',
              border: '2px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '50px',
              cursor: 'pointer',
              backdropFilter: 'blur(10px)',
              transition: 'all 0.3s ease',
              fontWeight: '500'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.3)';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            {status.includes('Starting') ? 'Starting...' : 'Start Voice Session'}
          </button>

          {status.includes('Error') && (
            <p style={{
              color: '#ffcccb',
              marginTop: '20px',
              background: 'rgba(255, 0, 0, 0.1)',
              padding: '10px',
              borderRadius: '8px'
            }}>
              {status}
            </p>
          )}
        </div>
      </div>
    );
  }

  // Conversation Screen - Clean single column
  return (
    <div className="voice-chat" style={{
      fontFamily: '"Inter", "Segoe UI", system-ui, -apple-system, sans-serif',
      height: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
      display: 'flex',
      flexDirection: 'column',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Animated Background Elements */}
      <div className="floating-element" style={{
        position: 'absolute',
        top: '10%',
        left: '10%',
        width: '200px',
        height: '200px',
        borderRadius: '50%',
        background: 'rgba(255, 255, 255, 0.1)',
        filter: 'blur(40px)',
        zIndex: 0
      }} />
      <div className="floating-element-reverse" style={{
        position: 'absolute',
        top: '60%',
        right: '15%',
        width: '150px',
        height: '150px',
        borderRadius: '50%',
        background: 'rgba(255, 255, 255, 0.08)',
        filter: 'blur(30px)',
        zIndex: 0
      }} />

      {/* Glassmorphism Header */}
      <div className="glassmorphism" style={{
        background: 'rgba(255, 255, 255, 0.15)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.2)',
        color: 'white',
        padding: '20px 30px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
        position: 'relative',
        zIndex: 2
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ 
            fontSize: '32px',
            background: 'rgba(255, 255, 255, 0.2)',
            padding: '10px',
            borderRadius: '12px',
            backdropFilter: 'blur(10px)'
          }}>🎤</div>
          <div>
            <h1 style={{ 
              margin: 0, 
              fontSize: '1.6rem', 
              fontWeight: '600',
              background: 'linear-gradient(135deg, #fff, #e0e7ff)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>Voice AI Assistant</h1>
            <p style={{ 
              margin: 0, 
              fontSize: '0.9rem', 
              opacity: 0.8,
              fontWeight: '400'
            }}>Powered by Advanced AI Analytics</p>
          </div>
        </div>
        <button
          onClick={stopVoiceSession}
          style={{
            background: 'rgba(255, 255, 255, 0.2)',
            color: 'white',
            border: '2px solid rgba(255, 255, 255, 0.3)',
            borderRadius: '25px',
            padding: '12px 24px',
            cursor: 'pointer',
            fontSize: '0.95rem',
            fontWeight: '500',
            backdropFilter: 'blur(10px)',
            transition: 'all 0.3s ease',
            boxShadow: '0 4px 15px rgba(0, 0, 0, 0.1)'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.3)';
            e.currentTarget.style.transform = 'translateY(-2px)';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
            e.currentTarget.style.transform = 'translateY(0)';
          }}
        >
          End Session
        </button>
      </div>

      {/* Main Dashboard Area */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        padding: '30px',
        position: 'relative',
        zIndex: 1
      }}>
        {/* Status Card */}
        {/* <div className="status-connected" style={{
          background: isConnected 
            ? 'rgba(76, 175, 80, 0.15)' 
            : 'rgba(255, 193, 7, 0.15)',
          backdropFilter: 'blur(20px)',
          border: `2px solid ${isConnected ? 'rgba(76, 175, 80, 0.3)' : 'rgba(255, 193, 7, 0.3)'}`,
          borderRadius: '16px',
          padding: '16px 24px',
          marginBottom: '30px',
          textAlign: 'center',
          color: 'white',
          fontSize: '1rem',
          fontWeight: '500',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
        }}>
          {isConnected ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
              <div style={{ 
                width: '12px', 
                height: '12px', 
                borderRadius: '50%', 
                background: '#4CAF50',
                boxShadow: '0 0 0 3px rgba(76, 175, 80, 0.3)'
              }} className="floating-element" />
              Connected - You can speak now
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
              <div style={{ 
                width: '12px', 
                height: '12px', 
                borderRadius: '50%', 
                background: '#FFC107'
              }} className="floating-element" />
              Connecting to AI...
            </div>
          )}
        </div> */}

        {/* Main Analytics Dashboard */}
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative'
        }}>
          {currentVisualization ? (
            <div className="chart-container glassmorphism" style={{
              width: '100%',
              maxWidth: '1000px',
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(20px)',
              borderRadius: '20px',
              padding: '30px',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
              position: 'relative'
            }}>
              {/* Chart Header */}
              <div style={{
                position: 'absolute',
                top: '-10px',
                left: '30px',
                background: 'linear-gradient(135deg, #667eea, #764ba2)',
                color: 'white',
                padding: '8px 16px',
                borderRadius: '20px',
                fontSize: '0.85rem',
                fontWeight: '600',
                boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)'
              }}>
                📊 Live Analytics
              </div>
              
              <VisualizationContainer
                llmResponse={currentVisualization}
                isPlaying={isPlaying}
                currentTime={syncState.currentTime}
                activeTarget={activeTarget}
                onVisualizationInteraction={handleVisualizationInteraction}
              />
            </div>
          ) : (
            <div className="glassmorphism" style={{
              textAlign: 'center',
              color: 'white',
              fontSize: '1.2rem',
              background: 'rgba(255, 255, 255, 0.1)',
              backdropFilter: 'blur(20px)',
              borderRadius: '24px',
              padding: '60px 40px',
              border: '2px solid rgba(255, 255, 255, 0.2)',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
              maxWidth: '600px'
            }}>
              <div style={{ 
                fontSize: '5rem', 
                marginBottom: '30px',
                background: 'linear-gradient(135deg, #fff, #e0e7ff)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.1))'
              }}>📊</div>
              
              <h2 style={{
                margin: '0 0 20px 0',
                fontSize: '1.8rem',
                fontWeight: '600',
                background: 'linear-gradient(135deg, #fff, #e0e7ff)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}>AI Analytics Dashboard</h2>
              
              <p style={{ 
                fontSize: '1.1rem', 
                opacity: 0.9,
                lineHeight: '1.6',
                marginBottom: '25px'
              }}>
                Your interactive charts and data visualizations will appear here
              </p>
              
              <div style={{
                background: 'rgba(255, 255, 255, 0.1)',
                borderRadius: '16px',
                padding: '20px',
                border: '1px solid rgba(255, 255, 255, 0.2)'
              }}>
                <p style={{ 
                  fontSize: '1rem', 
                  opacity: 0.8,
                  margin: '0 0 10px 0',
                  fontWeight: '500'
                }}>🎤 Try saying:</p>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  fontSize: '0.95rem',
                  opacity: 0.7
                }}>
                  <div>"Show me sales data for this quarter"</div>
                  <div>"Create a revenue vs profit chart"</div>
                  <div>"Display customer growth metrics"</div>
                </div>
              </div>
            </div>
          )}
          
          {/* Modern Stop Button */}
          {isPlaying && (
            <button
              onClick={() => {
                resetAudio();
              }}
              className="glassmorphism"
              style={{
                position: 'fixed',
                bottom: '40px',
                left: '50%',
                transform: 'translateX(-50%)',
                width: '90px',
                height: '90px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #ff6b6b, #ee5a24)',
                border: '3px solid rgba(255, 255, 255, 0.3)',
                color: 'white',
                fontSize: '28px',
                cursor: 'pointer',
                boxShadow: '0 15px 35px rgba(255, 107, 107, 0.4), 0 5px 15px rgba(0, 0, 0, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.3s ease',
                fontWeight: 'bold',
                zIndex: 1000,
                backdropFilter: 'blur(10px)'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.transform = 'translateX(-50%) scale(1.1) translateY(-3px)';
                e.currentTarget.style.boxShadow = '0 20px 40px rgba(255, 107, 107, 0.6), 0 10px 25px rgba(0, 0, 0, 0.15)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = 'translateX(-50%) scale(1) translateY(0)';
                e.currentTarget.style.boxShadow = '0 15px 35px rgba(255, 107, 107, 0.4), 0 5px 15px rgba(0, 0, 0, 0.1)';
              }}
              title="Stop AI from speaking"
            >
              ⏹️
            </button>
          )}
        </div>

      </div>
    </div>
  );
};
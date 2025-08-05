import React from 'react';

interface VoiceControlsProps {
  isConnected: boolean;
  userName: string;
  setUserName: (name: string) => void;
  voiceName: string;
  setVoiceName: (name: string) => void;
  ttsProvider: string;
  setTtsProvider: (provider: string) => void;
  onStart: () => void;
  onStop: () => void;
  status: string;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({
  isConnected,
  userName,
  setUserName,
  voiceName,
  setVoiceName,
  ttsProvider,
  setTtsProvider,
  onStart,
  onStop,
  status
}) => {
  return (
    <div className="voice-controls">
      <div className="status-section">
        <div className={`status ${isConnected ? 'connected' : 'disconnected'}`}>
          {status}
        </div>
      </div>

      <div className="form-section">
        <h3>Session Settings</h3>
        
        <div className="form-group">
          <label htmlFor="userName">Your Name (optional):</label>
          <input
            type="text"
            id="userName"
            value={userName}
            onChange={(e) => setUserName(e.target.value)}
            placeholder="Enter your name"
            disabled={isConnected}
          />
        </div>

        <div className="form-group">
          <label htmlFor="ttsProvider">Voice Provider:</label>
          <select
            id="ttsProvider"
            value={ttsProvider}
            onChange={(e) => setTtsProvider(e.target.value)}
            disabled={isConnected}
          >
            <option value="google">Google TTS</option>
            <option value="azure">Azure TTS</option>
            <option value="openai">OpenAI TTS</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="voiceName">Voice Name (optional):</label>
          <input
            type="text"
            id="voiceName"
            value={voiceName}
            onChange={(e) => setVoiceName(e.target.value)}
            placeholder="e.g., en-US-Neural2-D"
            disabled={isConnected}
          />
        </div>

        <div className="button-group">
          {!isConnected ? (
            <button 
              className="start-btn"
              onClick={onStart}
            >
              🎤 Start Voice Session
            </button>
          ) : (
            <button 
              className="stop-btn"
              onClick={onStop}
            >
              🛑 Stop Voice Session
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
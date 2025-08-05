import React, { useEffect, useRef } from 'react';

export interface TranscriptMessage {
  timestamp: string;
  speaker: 'user' | 'assistant' | 'system';
  message: string;
}

interface TranscriptDisplayProps {
  transcript: TranscriptMessage[];
  isConnected: boolean;
}

export const TranscriptDisplay: React.FC<TranscriptDisplayProps> = ({
  transcript,
  isConnected
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcript]);

  const getSpeakerIcon = (speaker: string) => {
    switch (speaker) {
      case 'user': return '👤';
      case 'assistant': return '🤖';
      case 'system': return '⚙️';
      default: return '💬';
    }
  };

  const getSpeakerClass = (speaker: string) => {
    return `message ${speaker}`;
  };

  return (
    <div className="transcript-section">
      <div className="transcript-header">
        <h3>📝 Conversation Transcript</h3>
        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
        </div>
      </div>
      
      <div className="transcript-container" ref={scrollRef}>
        {transcript.length === 0 ? (
          <div className="empty-transcript">
            <p>Transcript will appear here when you start talking...</p>
          </div>
        ) : (
          transcript.map((msg, index) => (
            <div key={index} className={getSpeakerClass(msg.speaker)}>
              <div className="message-header">
                <span className="speaker-icon">{getSpeakerIcon(msg.speaker)}</span>
                <span className="speaker-name">{msg.speaker}</span>
                <span className="timestamp">{msg.timestamp}</span>
              </div>
              <div className="message-content">
                {msg.message}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
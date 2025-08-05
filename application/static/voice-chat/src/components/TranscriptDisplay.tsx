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

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {transcript.length === 0 ? (
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#6c757d',
          fontSize: '1.1rem',
          textAlign: 'center'
        }}>
          <div>
            <div style={{ fontSize: '3rem', marginBottom: '20px' }}>👋</div>
            <p>Start speaking to begin the conversation</p>
          </div>
        </div>
      ) : (
        <div ref={scrollRef} style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          padding: '10px 0'
        }}>
          {transcript.map((msg, index) => (
            <div key={index} style={{
              display: 'flex',
              justifyContent: msg.speaker === 'user' ? 'flex-end' : 'flex-start',
              alignItems: 'flex-end',
              gap: '8px'
            }}>
              {msg.speaker === 'assistant' && (
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #667eea, #764ba2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '16px',
                  flexShrink: 0,
                  marginBottom: '4px'
                }}>
                  🤖
                </div>
              )}
              
              <div style={{
                maxWidth: '75%',
                minWidth: '120px'
              }}>
                <div style={{
                  padding: '12px 16px',
                  borderRadius: msg.speaker === 'user' 
                    ? '18px 18px 4px 18px' 
                    : '18px 18px 18px 4px',
                  background: msg.speaker === 'user' 
                    ? '#007bff'
                    : '#ffffff',
                  color: msg.speaker === 'user' ? 'white' : '#333333',
                  fontSize: '15px',
                  lineHeight: '1.4',
                  boxShadow: msg.speaker === 'user' 
                    ? '0 2px 12px rgba(0, 123, 255, 0.25)'
                    : '0 2px 12px rgba(0, 0, 0, 0.08)',
                  border: msg.speaker === 'assistant' ? '1px solid #e1e5e9' : 'none',
                  wordWrap: 'break-word',
                  position: 'relative'
                }}>
                  {msg.message}
                </div>
                
                <div style={{
                  fontSize: '11px',
                  color: '#8e8e93',
                  marginTop: '4px',
                  textAlign: msg.speaker === 'user' ? 'right' : 'left',
                  paddingLeft: msg.speaker === 'user' ? '0' : '8px',
                  paddingRight: msg.speaker === 'user' ? '8px' : '0'
                }}>
                  {new Date(msg.timestamp).toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </div>
              </div>

              {msg.speaker === 'user' && (
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #007bff, #0056b3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '16px',
                  flexShrink: 0,
                  marginBottom: '4px'
                }}>
                  👤
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
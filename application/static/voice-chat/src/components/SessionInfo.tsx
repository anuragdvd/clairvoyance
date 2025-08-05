import React from 'react';

interface SessionData {
  session_id: string;
  room_url: string;
  room_token: string;
}

interface SessionInfoProps {
  sessionData: SessionData;
}

export const SessionInfo: React.FC<SessionInfoProps> = ({ sessionData }) => {
  return (
    <div className="session-info">
      <h3>📋 Session Information</h3>
      <div className="info-group">
        <div className="info-item">
          <label>Session ID:</label>
          <span className="session-id">{sessionData.session_id}</span>
        </div>
        <div className="info-item">
          <label>Room URL:</label>
          <span className="room-url">{sessionData.room_url}</span>
        </div>
      </div>
    </div>
  );
};
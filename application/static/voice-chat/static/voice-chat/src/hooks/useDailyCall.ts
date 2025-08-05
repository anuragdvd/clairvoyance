import { useCallback, useRef } from 'react';
import DailyIframe from '@daily-co/daily-js';

export const useDailyCall = () => {
  const callRef = useRef<any>(null);

  const joinCall = useCallback(async (roomUrl: string, roomToken: string) => {
    try {
      // Create Daily call object
      callRef.current = DailyIframe.createCallObject({
        audioSource: true,
        videoSource: false,
      });

      // Set up event listeners
      callRef.current
        .on('joined-meeting', () => {
          console.log('✅ Successfully joined Daily.co meeting');
        })
        .on('left-meeting', () => {
          console.log('👋 Left Daily.co meeting');
        })
        .on('error', (error: any) => {
          console.error('❌ Daily.co error:', error);
        })
        .on('participant-joined', (event: any) => {
          console.log('👥 Participant joined:', event.participant);
        })
        .on('participant-left', (event: any) => {
          console.log('👋 Participant left:', event.participant);
        });

      // Join the meeting
      await callRef.current.join({
        url: roomUrl,
        token: roomToken,
      });

      console.log('🎤 Daily.co call connected');
      
    } catch (error) {
      console.error('Failed to join Daily.co call:', error);
      throw error;
    }
  }, []);

  const leaveCall = useCallback(async () => {
    try {
      if (callRef.current) {
        await callRef.current.leave();
        await callRef.current.destroy();
        callRef.current = null;
        console.log('📞 Daily.co call ended');
      }
    } catch (error) {
      console.error('Error leaving call:', error);
      throw error;
    }
  }, []);

  const toggleMicrophone = useCallback(async () => {
    if (callRef.current) {
      const currentState = callRef.current.localAudio();
      await callRef.current.setLocalAudio(!currentState);
      return !currentState;
    }
    return false;
  }, []);

  return {
    joinCall,
    leaveCall,
    toggleMicrophone
  };
};
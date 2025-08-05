# Voice Agent Debugging Checklist

## 1. Browser Microphone Permissions
- Click the microphone icon in your browser's address bar
- Ensure microphone access is "Allow" for localhost:8001
- Try refreshing the page and allowing microphone access

## 2. Check Server Logs
Look for these in your terminal:
```
✅ Subprocess started with PID: [number]
✅ Voice agent started with session ID: [id]
✅ First participant joined
```

## 3. Audio Input Test
- In the Daily.co interface, look for:
  - Microphone button (should be unmuted)
  - Audio level indicators when you speak
  - Green/red microphone status

## 4. Common Issues

### Issue: No subprocess starts
- **Check:** Environment variables in .env
- **Fix:** Ensure DAILY_API_KEY, AZURE_OPENAI_API_KEY, etc. are set

### Issue: Microphone not working
- **Check:** Browser permissions
- **Fix:** Click microphone icon → Allow → Refresh

### Issue: Agent subprocess crashes
- **Check:** Google credentials file path
- **Fix:** Verify GOOGLE_CREDENTIALS_JSON path exists

### Issue: No voice response
- **Check:** TTS configuration
- **Fix:** Verify Google TTS credentials

## 5. Quick Tests

### Test 1: Check if subprocess is running
```bash
ps aux | grep "app.agents.voice.simple"
```

### Test 2: Check Daily.co room directly
Open the room URL in a new tab to test Daily.co connectivity

### Test 3: Test microphone in browser
Go to https://webrtc.github.io/samples/src/content/getusermedia/gum/

## 6. Environment Variables Check
```bash
source application/venv311/bin/activate
python -c "
import os
print('DAILY_API_KEY:', 'SET' if os.getenv('DAILY_API_KEY') else 'MISSING')
print('AZURE_OPENAI_API_KEY:', 'SET' if os.getenv('AZURE_OPENAI_API_KEY') else 'MISSING') 
print('GOOGLE_CREDENTIALS_JSON:', 'SET' if os.getenv('GOOGLE_CREDENTIALS_JSON') else 'MISSING')
"
```
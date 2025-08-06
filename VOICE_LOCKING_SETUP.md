# Voice Locking Setup Guide

## 🔑 **Required API Keys**

To enable voice locking functionality, you need to set up the following keys:

### **1. HuggingFace Hub Token (Required)**

The voice locking system uses pyannote.audio models hosted on HuggingFace Hub.

#### **Get Your Token:**
1. Go to [HuggingFace.co](https://huggingface.co)
2. Create an account or sign in
3. Go to [Settings > Access Tokens](https://huggingface.co/settings/tokens)
4. Create a new token with "Read" permissions
5. Copy the token (starts with `hf_...`)

#### **Set Environment Variable:**
```bash
export HUGGINGFACE_HUB_TOKEN="hf_your_token_here"
```

#### **Or add to your .env file:**
```bash
HUGGINGFACE_HUB_TOKEN=hf_your_token_here
```

### **2. Voice Locking Configuration**

Add these environment variables to enable and configure voice locking:

```bash
# Enable voice locking
ENABLE_VOICE_LOCKING=true

# HuggingFace token for model access
HUGGINGFACE_HUB_TOKEN=hf_your_token_here

# Speaker enrollment duration (seconds)
SPEAKER_ENROLLMENT_DURATION=5.0

# Speaker similarity threshold (0.0-1.0, higher = more strict)
SPEAKER_SIMILARITY_THRESHOLD=0.8

# Audio chunk size for processing (seconds)
DIARIZATION_CHUNK_SIZE=2.0

# Overall voice lock sensitivity (0.0-1.0)
VOICE_LOCK_SENSITIVITY=0.7

# Audio quality threshold for enrollment (0.0-1.0)
AUDIO_QUALITY_THRESHOLD=0.7
```

## 📦 **Installation Steps**

### **1. Install Voice Locking Dependencies**
```bash
pip install -r requirements-voice-locking.txt
```

### **2. Verify Installation**
```bash
python -c "
import torch
import torchaudio
from pyannote.audio import Pipeline
print('✅ All voice locking dependencies installed successfully')
"
```

### **3. Test HuggingFace Authentication**
```bash
python -c "
import os
from pyannote.audio import Pipeline
token = os.environ.get('HUGGINGFACE_HUB_TOKEN')
if token:
    print('✅ HuggingFace token found')
    # This will test if the token works
    try:
        pipeline = Pipeline.from_pretrained('pyannote/speaker-diarization', use_auth_token=token)
        print('✅ HuggingFace authentication successful')
    except Exception as e:
        print(f'❌ Authentication failed: {e}')
else:
    print('❌ HUGGINGFACE_HUB_TOKEN not set')
"
```

## 🚀 **Quick Start**

### **1. Update Your .env File**
```bash
# Add these lines to your .env file:
ENABLE_VOICE_LOCKING=true
HUGGINGFACE_HUB_TOKEN=hf_your_actual_token_here
SPEAKER_ENROLLMENT_DURATION=5.0
SPEAKER_SIMILARITY_THRESHOLD=0.8
```

### **2. Start the Server**
```bash
python app/main.py
```

### **3. Check Voice Locking Status**
```bash
curl http://localhost:8000/voice-locking/status
```

Expected response:
```json
{
  "enabled": true,
  "enrollment_duration": 5.0,
  "similarity_threshold": 0.8,
  "chunk_size": 2.0,
  "sensitivity": 0.7,
  "quality_threshold": 0.7
}
```

### **4. Test Voice Session with Voice Locking**
```bash
curl -X POST "http://localhost:8000/agent/voice/automatic" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "live",
    "userName": "test_user",
    "ttsService": {
      "ttsProvider": "google", 
      "voiceName": "bret"
    }
  }'
```

## 🔍 **Troubleshooting**

### **Common Issues:**

**1. "HTTP 401: Unauthorized" from HuggingFace**
- Check your token is correct and has "Read" permissions
- Verify the token is set in environment variable

**2. "ModuleNotFoundError: No module named 'pyannote'"**
- Install dependencies: `pip install -r requirements-voice-locking.txt`

**3. "RuntimeError: Detected that PyTorch and torchvision were compiled with different CUDA versions"**
- Reinstall PyTorch: `pip uninstall torch torchaudio && pip install torch torchaudio`

**4. High memory usage**
- Reduce `DIARIZATION_CHUNK_SIZE` to 1.0
- Consider running on a machine with more RAM (minimum 4GB recommended)

### **Log Monitoring:**
```bash
# Watch for voice locking initialization
tail -f logs/app.log | grep "voice locking\|speaker\|enrollment"

# Check for errors
tail -f logs/app.log | grep "ERROR\|❌"
```

## 🎯 **Expected Behavior**

When voice locking is enabled:

1. **First Voice Session**: System will prompt for 5-second enrollment
2. **Speaker Enrollment**: "🎙️ Starting speaker enrollment - please speak for 5 seconds"
3. **Voice Locking Active**: Only enrolled speaker's voice gets transcribed
4. **Multi-speaker Filtering**: Other voices automatically filtered out

### **Log Examples:**

**Successful Setup:**
```
Voice locking enabled: True
Speaker enrollment duration: 5.0s
Initializing voice locking components...
Speaker diarization service initialized
Voice locking components initialized successfully
```

**During Operation:**
```
🎙️ Starting speaker enrollment - please speak for 5 seconds
✅ Speaker enrollment completed successfully
✅ Allowing transcription: 'hello there' (reason: target_speaker_confidence_0.85)
🚫 Filtering transcription: 'background voice' (reason: non_target_speaker_confidence_0.42)
```

---

**🎤 Follow this guide to set up voice locking and enable sophisticated speaker isolation in your Clairvoyance voice agent!**
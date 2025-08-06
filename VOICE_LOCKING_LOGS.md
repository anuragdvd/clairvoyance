# Voice Locking System - Log Monitoring Guide

## 🎯 **Quick Start**

### **Run the Log Monitor**
```bash
# Auto-detect logs and monitor in real-time
python monitor_voice_locking.py

# Monitor specific log file  
python monitor_voice_locking.py logs/app.log
```

### **Manual Log Monitoring**
```bash
# Watch application logs for voice locking activity
tail -f logs/app.log | grep -E "(🔊|🎙️|✅|🚫|voice|speaker|enrollment)"

# Monitor just the key events
tail -f logs/app.log | grep -E "(VOICE LOCKING|ENROLLMENT|ALLOWING|FILTERING)"
```

## 📋 **Log Categories & What They Mean**

### **🔊 SYSTEM INITIALIZATION**
These logs show voice locking system startup:

```
🔊 ===== INITIALIZING VOICE LOCKING SYSTEM =====
🔊 Voice locking enabled with config:
🔊   - Similarity threshold: 0.8
🔊   - Enrollment duration: 5.0s
🔊   - Chunk size: 2.0s
🔊   - Sensitivity: 0.7
🔊 Loading pyannote speaker diarization pipeline...
✅ Speaker diarization pipeline loaded successfully
🔊 Loading speaker embedding model...
✅ Speaker embedding model loaded successfully
🎯 Speaker diarization service fully initialized and ready!
✅ ===== VOICE LOCKING SYSTEM READY =====
```

**What to check:**
- ✅ All components load successfully
- ❌ If errors occur, check HuggingFace token and dependencies

### **🎙️ SPEAKER ENROLLMENT**
These logs track the enrollment process:

```
🎤 User started speaking at 14:30:15.123
🎙️ No speaker enrolled yet - starting enrollment process
🎙️ ===== STARTING SPEAKER ENROLLMENT =====
🎙️ Please speak continuously for 5.0 seconds
🎙️ Enrollment started at 14:30:15.123

🎤 User stopped speaking after 5.2s
🎙️ Enrollment duration reached (5.2s >= 5.0s) - completing enrollment
🎙️ ===== COMPLETING SPEAKER ENROLLMENT =====
🎙️ Retrieving enrollment audio from buffer...
🎙️ Found enrollment audio: 83200 samples, 5.2s
🎙️ Enrolling speaker 'target' from 5.2s audio
🎙️ Audio data: 83200 samples at 16000Hz
✅ Speaker 'target' enrolled successfully!
🎙️ Speaker embedding shape: (192,)
✅ ===== SPEAKER ENROLLMENT COMPLETED SUCCESSFULLY =====
🎯 Voice locking is now ACTIVE - only target speaker will be processed
```

**What to check:**
- 🎙️ Enrollment starts when first user speaks
- ⏱️ Duration should reach target (5 seconds by default)
- ✅ Enrollment completes successfully
- 🎯 Voice locking activates after enrollment

### **🎵 AUDIO PROCESSING** 
These logs show audio buffer and processing activity:

```
🎵 Processing audio frame: 1024 bytes
🎵 Audio chunk ready: 32000 bytes accumulated
🎵 Audio chunk processed: 16000 samples, 2.0s duration
🎵 Buffer now contains 3 chunks
🎵 Calling speaker diarization for chunk at 1641234567.123
🔊 Identified 1 speaker segments in 2.0s audio
🔊 Segment: speaker=SPEAKER_00, time=0.00-2.00s
🎵 Speaker diarization completed for chunk
```

**What to check:**
- 🎵 Audio frames are being processed
- 🎵 Chunks are created at regular intervals
- 🔊 Speaker segments are identified
- No errors in diarization processing

### **✅ TRANSCRIPTION ALLOWING**
These logs show when transcriptions are allowed through:

```
🎯 Speaker similarity check: 0.856, is_target: true
✅ TARGET SPEAKER DETECTED (confidence: 0.856)
✅ ALLOWING transcription: 'hello there how are you' (reason: target_speaker_confidence_0.86, confidence: 0.86)
```

**What to check:**
- 🎯 Similarity scores are above threshold (default 0.8)
- ✅ Target speaker is consistently detected
- ✅ Transcriptions are allowed with good confidence

### **🚫 TRANSCRIPTION FILTERING**
These logs show when transcriptions are filtered out:

```
🎯 Speaker similarity check: 0.432, is_target: false
🚫 Non-target speaker detected (confidence: 0.432)
🚫 FILTERING transcription: 'background conversation' (reason: non_target_speaker_confidence_0.43, confidence: 0.43)
```

**What to check:**
- 🚫 Non-target speakers are correctly identified
- 🎯 Similarity scores are below threshold
- 🚫 Unwanted transcriptions are filtered out

### **❌ ERROR CONDITIONS**
These logs indicate problems:

```
❌ Failed to initialize speaker diarization: HTTP 401: Unauthorized
⚠️  Continuing WITHOUT voice locking
❌ Error in diarization callback: RuntimeError: Model not found
❌ Speaker enrollment failed
❌ No audio available for speaker enrollment
```

**What to check:**
- 🔑 HuggingFace token is valid and set
- 📦 Dependencies are properly installed
- 🎵 Audio is being captured correctly
- 💾 Sufficient memory and resources

## 🔍 **Monitoring Commands**

### **Real-time Monitoring**
```bash
# Use the provided monitoring script (recommended)
python monitor_voice_locking.py

# Manual monitoring with grep
tail -f logs/app.log | grep -E "(🔊|🎙️|✅|🚫|🎯|❌)"

# Focus on key events only
tail -f logs/app.log | grep -E "(VOICE LOCKING|ENROLLMENT|ALLOWING|FILTERING)"

# Monitor errors only
tail -f logs/app.log | grep -E "(❌|Error|Failed)"
```

### **Historical Analysis**
```bash
# Count successful enrollments
grep "Speaker enrollment completed" logs/app.log | wc -l

# Count allowed vs filtered transcriptions
echo "Allowed: $(grep 'ALLOWING transcription' logs/app.log | wc -l)"
echo "Filtered: $(grep 'FILTERING transcription' logs/app.log | wc -l)"

# Find initialization times
grep "VOICE LOCKING SYSTEM READY" logs/app.log

# Check for errors
grep -E "(❌|Error|Failed)" logs/app.log | tail -10
```

### **Performance Analysis**
```bash
# Check speaker detection confidence scores
grep "Speaker similarity check" logs/app.log | tail -10

# Monitor audio processing timing
grep "Audio chunk processed" logs/app.log | tail -5

# Check enrollment timing
grep -A5 -B5 "ENROLLMENT" logs/app.log
```

## 📊 **Expected Log Flow**

### **Successful Session with Voice Locking**

1. **System Startup** (30-60 seconds)
```
🔊 INITIALIZING VOICE LOCKING SYSTEM
✅ VOICE LOCKING SYSTEM READY
```

2. **First User Speech** (immediate)
```
🎤 User started speaking
🎙️ STARTING SPEAKER ENROLLMENT
```

3. **Enrollment Complete** (after 5 seconds)
```
🎙️ COMPLETING SPEAKER ENROLLMENT
✅ Speaker enrollment completed
🎯 Voice locking is now ACTIVE
```

4. **Ongoing Operation** (continuous)
```
🎵 Audio chunk processed
🎯 Speaker similarity check: 0.85, is_target: true
✅ ALLOWING transcription: 'user speech'
🎯 Speaker similarity check: 0.42, is_target: false  
🚫 FILTERING transcription: 'background noise'
```

## 🚨 **Troubleshooting by Logs**

### **No Voice Locking Logs at All**
```bash
# Check if voice locking is enabled
grep "Voice locking enabled" logs/app.log
```
**Solution:** Set `ENABLE_VOICE_LOCKING=true`

### **Initialization Fails**
```bash
# Check for authentication errors
grep "401\|Unauthorized\|token" logs/app.log
```
**Solution:** Set valid `HUGGINGFACE_HUB_TOKEN`

### **No Enrollment Happening**
```bash
# Check if user speech is detected
grep "User started speaking" logs/app.log
```
**Solution:** Check audio input and VAD settings

### **All Transcriptions Filtered**
```bash
# Check similarity scores
grep "Speaker similarity check" logs/app.log | tail -5
```
**Solution:** Lower `SPEAKER_SIMILARITY_THRESHOLD`

### **No Filtering Happening**
```bash
# Check if enrollment completed
grep "Voice locking is now ACTIVE" logs/app.log
```
**Solution:** Ensure enrollment process completes

## 🎯 **Success Indicators**

**✅ Voice Locking Working Correctly:**
- System initializes without errors
- Speaker enrollment completes successfully
- Target speaker transcriptions are allowed
- Non-target speaker transcriptions are filtered
- Similarity scores make sense (>0.8 for target, <0.8 for others)

**❌ Voice Locking Not Working:**
- Initialization errors or warnings
- Enrollment never completes or fails
- All transcriptions allowed (no filtering)
- All transcriptions filtered (too strict)
- Consistent low similarity scores

---

**🎤 Use these logs to monitor and troubleshoot your voice locking system in real-time!**
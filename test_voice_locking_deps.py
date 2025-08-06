#!/usr/bin/env python3
"""
Test script to verify voice locking dependencies are properly installed.
"""

import sys

def test_imports():
    """Test all required imports for voice locking"""
    
    tests = [
        ("torch", "PyTorch"),
        ("torchaudio", "TorchAudio"), 
        ("numpy", "NumPy"),
        ("scipy", "SciPy"),
        ("sklearn", "Scikit-learn"),
        ("librosa", "Librosa"),
        ("soundfile", "SoundFile"),
    ]
    
    print("🔍 Testing basic dependencies...")
    
    for module, name in tests:
        try:
            __import__(module)
            print(f"✅ {name}: OK")
        except ImportError as e:
            print(f"❌ {name}: FAILED - {e}")
            return False
    
    print("\n🔍 Testing pyannote.audio...")
    try:
        from pyannote.audio import Pipeline
        from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding
        print("✅ pyannote.audio: OK")
    except ImportError as e:
        print(f"❌ pyannote.audio: FAILED - {e}")
        return False
    
    print("\n🔍 Testing PyTorch functionality...")
    try:
        import torch
        x = torch.randn(10)
        print(f"✅ PyTorch tensor operations: OK")
        print(f"🔧 PyTorch version: {torch.__version__}")
        print(f"🔧 CUDA available: {torch.cuda.is_available()}")
    except Exception as e:
        print(f"❌ PyTorch functionality: FAILED - {e}")
        return False
    
    print("\n🔍 Testing audio processing...")
    try:
        import librosa
        import numpy as np
        
        # Create dummy audio data
        dummy_audio = np.random.randn(16000)  # 1 second at 16kHz
        
        # Test MFCC extraction
        mfccs = librosa.feature.mfcc(y=dummy_audio, sr=16000, n_mfcc=13)
        print(f"✅ Audio feature extraction: OK")
        print(f"🔧 MFCC shape: {mfccs.shape}")
        
    except Exception as e:
        print(f"❌ Audio processing: FAILED - {e}")
        return False
    
    return True

def test_huggingface_connection():
    """Test HuggingFace connection (optional)"""
    print("\n🔍 Testing HuggingFace connection...")
    
    import os
    token = os.environ.get('HUGGINGFACE_HUB_TOKEN')
    
    if not token:
        print("⚠️  HUGGINGFACE_HUB_TOKEN not set - skipping connection test")
        return True
    
    try:
        from pyannote.audio import Pipeline
        
        print("🔄 Attempting to load speaker diarization pipeline...")
        # This will test both network connection and authentication
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization", 
            use_auth_token=token
        )
        print("✅ HuggingFace connection and authentication: OK")
        return True
        
    except Exception as e:
        print(f"❌ HuggingFace connection: FAILED - {e}")
        print("💡 Check your HUGGINGFACE_HUB_TOKEN and internet connection")
        return False

def main():
    print("🎤 Voice Locking Dependencies Test")
    print("=" * 50)
    
    # Test basic imports
    if not test_imports():
        print("\n❌ Basic dependency test FAILED")
        print("💡 Run the installation commands above and try again")
        sys.exit(1)
    
    # Test HuggingFace (optional)
    test_huggingface_connection()
    
    print("\n" + "=" * 50)
    print("🎯 All core dependencies are working!")
    print("\n📋 Next steps:")
    print("1. Set HUGGINGFACE_HUB_TOKEN environment variable")
    print("2. Set ENABLE_VOICE_LOCKING=true in your .env file") 
    print("3. Start your voice application")
    print("4. Monitor logs with: python monitor_voice_locking.py")

if __name__ == "__main__":
    main()
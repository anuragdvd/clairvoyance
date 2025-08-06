#!/bin/bash
"""
Voice Locking Dependencies Installation Script
Automatically installs all required dependencies for voice locking functionality.
"""

set -e  # Exit on any error

echo "🎤 Voice Locking Dependencies Installer"
echo "======================================"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    echo "🍎 Detected macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo "🐧 Detected Linux"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install system dependencies
echo ""
echo "📦 Installing system dependencies..."

if [[ "$OS" == "macos" ]]; then
    # Check for Homebrew
    if ! command_exists brew; then
        echo "🍺 Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install system packages
    echo "🔧 Installing system packages via Homebrew..."
    brew update
    brew install cmake pkg-config protobuf portaudio sox libsndfile
    
elif [[ "$OS" == "linux" ]]; then
    # Ubuntu/Debian
    if command_exists apt-get; then
        sudo apt-get update
        sudo apt-get install -y cmake pkg-config protobuf-compiler libprotobuf-dev
        sudo apt-get install -y portaudio19-dev sox libsox-dev libsndfile1-dev
        sudo apt-get install -y build-essential python3-dev
    # CentOS/RHEL
    elif command_exists yum; then
        sudo yum install -y cmake pkgconfig protobuf-devel
        sudo yum install -y portaudio-devel sox-devel libsndfile-devel
        sudo yum groupinstall -y "Development Tools"
    else
        echo "❌ Unsupported Linux distribution"
        exit 1
    fi
fi

echo "✅ System dependencies installed"

# Install Python dependencies
echo ""
echo "🐍 Installing Python dependencies..."

# Upgrade pip first
python -m pip install --upgrade pip setuptools wheel

# Install PyTorch (CPU version for compatibility)
echo "🔥 Installing PyTorch..."
python -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install core scientific libraries
echo "🔬 Installing scientific libraries..."
python -m pip install numpy scipy scikit-learn

# Install audio processing libraries
echo "🎵 Installing audio libraries..."
python -m pip install librosa soundfile

# Install pyannote.audio
echo "🔊 Installing pyannote.audio..."
python -m pip install pyannote.audio

# Install optional libraries
echo "🎯 Installing optional speaker libraries..."
python -m pip install speechbrain resemblyzer || echo "⚠️  Optional libraries failed to install (continuing...)"

echo ""
echo "✅ Python dependencies installation completed!"

# Test installation
echo ""
echo "🧪 Testing installation..."
python test_voice_locking_deps.py

echo ""
echo "🎯 Installation Summary:"
echo "========================"
echo "✅ System dependencies installed"
echo "✅ Python dependencies installed"  
echo "✅ Installation test passed"
echo ""
echo "📋 Next Steps:"
echo "1. Get HuggingFace token from https://huggingface.co/settings/tokens"
echo "2. Set HUGGINGFACE_HUB_TOKEN environment variable"
echo "3. Set ENABLE_VOICE_LOCKING=true in your .env file"
echo "4. Start your application and check logs"
echo ""
echo "📚 Documentation:"
echo "- Setup guide: VOICE_LOCKING_SETUP.md"
echo "- Log monitoring: VOICE_LOCKING_LOGS.md"
echo "- Monitor logs: python monitor_voice_locking.py"
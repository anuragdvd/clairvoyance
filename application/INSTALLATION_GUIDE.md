# Installation Guide for Simple Voice Agent

## Current Status: Basic Server Working ✅

Your basic FastAPI server is now running successfully! Here's what works and what needs to be done for full voice functionality.

## What's Working Now

✅ **Basic FastAPI Server** - Running on http://localhost:8000  
✅ **Environment Configuration** - Your .env is set up  
✅ **Web Interface** - Basic HTML client available  
✅ **Health Check** - API endpoints working  

## Test Your Current Setup

1. **Start the basic server:**
   ```bash
   source application/venv/bin/activate
   python run_simple.py
   ```

2. **Open browser:** http://localhost:8000
3. **Test endpoints:**
   - Health: http://localhost:8000/health
   - Version: http://localhost:8000/version

## Full Voice Functionality (Pipecat Issues)

The issue you encountered is that Pipecat and its dependencies (like Pillow) have compatibility problems with Python 3.13.

### Option 1: Use Python 3.11 or 3.12 (Recommended)

```bash
# Install Python 3.11 via Homebrew
brew install python@3.11

# Create new virtual environment with Python 3.11
python3.11 -m venv application/venv311

# Activate and install
source application/venv311/bin/activate
pip install -r requirements.txt

# Run full voice agent
python run.py
```

### Option 2: Install with --no-deps and manual dependencies

```bash
source application/venv/bin/activate

# Install Pipecat without dependencies
pip install pipecat-ai==0.0.36 --no-deps

# Install compatible versions manually
pip install numpy==1.26.4
pip install "Pillow>=10.0.0,<11.0.0"
pip install protobuf>=4.21.0
pip install azure-cognitiveservices-speech
pip install google-generativeai
pip install daily-python

# Test installation
python -c "import pipecat; print('Pipecat imported successfully')"
```

### Option 3: Use Docker (Most Reliable)

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "run.py"]
EOF

# Build and run
docker build -t voice-agent .
docker run -p 8000:8000 --env-file .env voice-agent
```

## Current File Structure

```
application/
├── app/
│   ├── main.py              # Full voice agent (needs Pipecat)
│   ├── main_simple.py       # Basic server (working now)
│   ├── core/config.py       # Configuration
│   └── agents/voice/simple/ # Voice pipeline code
├── run.py                   # Full application
├── run_simple.py           # Basic server (working now)
├── requirements.txt         # Full dependencies
├── requirements-basic.txt   # Basic dependencies (installed)
└── static/client.html       # Web interface
```

## Next Steps

1. **For immediate testing:** Use the basic server (already working)
2. **For full voice functionality:** Choose one of the options above
3. **Recommended:** Use Python 3.11 for best compatibility

## Environment Variables Status

Your .env file should have:
- ✅ DAILY_API_KEY (for voice transport)
- ✅ AZURE_OPENAI_API_KEY (for LLM)
- ✅ AZURE_OPENAI_ENDPOINT (for LLM)
- ✅ GOOGLE_CREDENTIALS_JSON (for STT/TTS)

## API Endpoints

- `GET /` - Web interface
- `GET /health` - Health check
- `GET /version` - Version info
- `POST /voice/connect` - Create voice session (basic mock for now)

The basic server provides the foundation, and once Pipecat is properly installed, you'll have full voice agent capabilities!
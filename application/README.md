# Simple Voice Agent

A clean, simple voice agent application built with Pipecat and FastAPI. This application provides real-time voice conversation capabilities with STT, LLM, and TTS integration.

## Features

- **Real-time Voice Processing**: Speech-to-Text via Google STT
- **AI-Powered Conversations**: Azure OpenAI for intelligent responses
- **Multiple TTS Options**: Google TTS (default) and ElevenLabs
- **Tool Integration**: Basic tools for time, calculations, and weather info
- **Web Interface**: Simple HTML client for testing
- **Daily.co Integration**: Real-time audio transport

## Architecture

1. **Voice Input**: User speaks → captured via Daily.co transport
2. **Speech-to-Text**: Google STT converts voice to text
3. **LLM Processing**: Azure OpenAI processes text and decides actions
4. **Tool Execution**: Calls basic utility functions (time, math, etc.)
5. **Response Generation**: LLM generates text response
6. **Text-to-Speech**: Google TTS or ElevenLabs converts to speech
7. **Voice Output**: Synthesized speech sent back via Daily.co

## Setup

### Prerequisites

- Python 3.8+
- Daily.co API key
- Azure OpenAI access
- Google Cloud credentials
- (Optional) ElevenLabs API key

### Installation

1. **Navigate to the application directory:**
   ```bash
   cd application
   ```

2. **Run the setup script (recommended):**
   ```bash
   ./setup.sh
   ```
   
   **OR manually set up:**
   ```bash
   # Create virtual environment
   python3 -m venv application/venv
   
   # Activate virtual environment
   source application/venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your API keys and credentials.

4. **Run the application:**
   ```bash
   # Make sure virtual environment is activated
   source application/venv/bin/activate
   python run.py
   ```

### Required Environment Variables

```bash
DAILY_API_KEY=your_daily_api_key
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
GOOGLE_CREDENTIALS_JSON=/path/to/google-credentials.json
```

### Optional Environment Variables

```bash
ELEVENLABS_API_KEY=your_elevenlabs_key  # For better TTS quality
PORT=8000                               # Server port
AZURE_OPENAI_MODEL=gpt-4               # Model to use
ENABLE_NOISE_REDUCE_FILTER=true        # Audio filtering
```

## Usage

1. Start the server: `python run.py`
2. Open `http://localhost:8000` in your browser
3. Fill in your name and TTS preferences
4. Click "Start Voice Session"
5. Speak to the voice agent!

## Available Tools

The voice agent has access to these basic tools:

- **get_current_time**: Get current date and time
- **calculate**: Perform mathematical calculations
- **get_weather_info**: Get weather information (placeholder)

## API Endpoints

- `POST /voice/connect`: Create a new voice session
- `GET /health`: Health check
- `GET /version`: Application version
- `GET /`: Serve test client

## Project Structure

```
application/
├── app/
│   ├── main.py                     # FastAPI server
│   ├── schemas.py                  # Pydantic models
│   ├── core/
│   │   ├── config.py              # Configuration
│   │   └── logger.py              # Logging setup
│   └── agents/voice/simple/
│       ├── __init__.py            # Voice agent pipeline
│       ├── tools/                 # Tool definitions
│       ├── prompts.py             # System prompts
│       ├── tts.py                 # TTS service selection
│       └── types.py               # Type definitions
├── static/
│   └── client.html                # Test client
├── requirements.txt               # Dependencies
├── run.py                        # Application entry point
└── .env.example                  # Environment template
```

## Differences from Original Clairvoyance

This simplified version:

- ✅ Removes Juspay/Breeze dependencies
- ✅ Simplifies tool system to basic utilities
- ✅ Removes MCP server complexity
- ✅ Focuses on core voice agent functionality
- ✅ Cleaner, more understandable codebase
- ✅ Easier setup and deployment

## Development

The application uses:

- **FastAPI**: Web framework
- **Pipecat**: Voice processing pipeline
- **Daily.co**: Real-time audio transport
- **Google Cloud**: STT services
- **Azure OpenAI**: Language model
- **ElevenLabs**: Optional high-quality TTS

## Troubleshooting

1. **Audio issues**: Check your microphone permissions
2. **API errors**: Verify all required environment variables are set
3. **Connection issues**: Ensure Daily.co API key is valid
4. **TTS issues**: Try switching between Google and ElevenLabs

For detailed logs, check the console output when running the server.
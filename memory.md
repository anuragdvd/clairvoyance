# Clairvoyance Project Memory

## Project Overview
**Clairvoyance** (formerly "Breeze Automatic") is a sophisticated, dual-component AI voice agent server designed to power advanced conversational AI experiences. It integrates real-time voice processing with dynamic tool usage and external service connections.

## Architecture & Core Components

### 1. FastAPI Server (`app/main.py`)
- **Primary Role**: Main server that acts as a Gemini Live Proxy and manages voice agent subprocesses
- **Key Features**:
  - WebSocket connections for Gemini Live API integration
  - Creates Daily.co rooms for voice sessions
  - Launches Pipecat voice agents as subprocesses
  - CORS middleware for cross-origin requests
  - Health and version endpoints

### 2. Pipecat Voice Agent (`app/agents/voice/automatic/`)
- **Framework**: Built on Pipecat framework for real-time voice processing
- **Pipeline Components**:
  - Speech-to-Text: Google STT Service
  - Language Model: Azure OpenAI (wrapped in LLMServiceWrapper)
  - Text-to-Speech: Multiple providers (Google, ElevenLabs)
  - Transport: Daily.co for audio streaming
  - VAD: Silero Voice Activity Detection

### 3. Dynamic Tool System
- **MCP Integration**: Model Context Protocol for remote tool server connections
- **Tool Types**:
  - System tools (always loaded)
  - Dummy tools (test mode)
  - Live integration tools (Juspay, Breeze analytics)
- **Conditional Loading**: Tools loaded based on mode and available tokens

## Key Features

### Operational Modes
- **LIVE Mode**: Real-time data fetching from external APIs
- **TEST Mode**: Uses dummy data for development/testing

### Authentication & Security
- Token-based authentication for external services
- Session-specific context management
- Secure handling of sensitive data (API keys, tokens)

### Multi-Provider Support
- **Analytics**: Juspay and Breeze API integrations
- **TTS**: Google TTS, ElevenLabs
- **STT**: Google Speech-to-Text
- **LLM**: Azure OpenAI

### Advanced Features
- Context summarization after specified conversation turns
- OpenTelemetry tracing with Langfuse integration
- Noise reduction filters
- Personalized system prompts
- RTVI (Real-Time Voice Interface) events

## Technology Stack

### Core Dependencies
- **FastAPI**: Web framework and API server
- **Pipecat-AI**: Voice processing pipeline framework
- **Google Cloud**: STT and TTS services
- **Azure OpenAI**: Language model services
- **Daily.co**: Real-time audio/video infrastructure

### Additional Libraries
- **WebSockets**: Real-time communication
- **aiohttp**: Async HTTP client
- **OpenTelemetry**: Observability and tracing
- **Langfuse**: LLM analytics and monitoring
- **python-dotenv**: Environment configuration

## Configuration Management

### Environment Variables (app/core/config.py)
- **Required**: DAILY_API_KEY, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, GOOGLE_CREDENTIALS_JSON, GEMINI_API_KEY
- **Optional**: TTS provider settings, VAD parameters, tracing configs
- **MCP Server**: AUTOMATIC_MCP_TOOL_SERVER_USAGE, AUTOMATIC_TOOL_MCP_SERVER_URL

### Runtime Configuration
- Port: 8000 (default)
- Host: 0.0.0.0
- Uvicorn with reload capability
- Configurable VAD parameters and audio processing

## Data Flow

### Voice Session Lifecycle
1. Client sends POST to `/agent/voice/automatic`
2. Server validates request and creates Daily.co room
3. Subprocess launched with Pipecat voice agent
4. Agent initializes tools based on mode and tokens
5. Real-time audio pipeline processes voice conversation
6. Tools execute actions via MCP server or direct API calls
7. Session ends on participant departure or timeout

### Tool Integration Flow
- Mode determination (LIVE/TEST)
- Token validation for external services
- Dynamic tool loading via MCP client
- Function registration with LLM service
- Real-time tool execution during conversation

## Directory Structure

```
app/
├── main.py                    # FastAPI server and subprocess management
├── core/
│   ├── config.py             # Environment configuration
│   └── logger.py             # Logging setup
├── agents/voice/automatic/    # Pipecat voice agent
│   ├── __init__.py           # Main agent pipeline
│   ├── prompts/              # System prompts
│   ├── services/             # LLM wrapper, MCP client
│   ├── tools/                # Tool definitions (system, dummy, live)
│   └── types/                # Type definitions and decoders
├── api/                      # External API clients
├── ws/                       # WebSocket handlers
└── services/                 # Shared services
```

## Key Files & Entry Points

- **run.py**: Application entry point (Uvicorn server launcher)
- **app/main.py**: FastAPI application with endpoints
- **app/agents/voice/automatic/__init__.py**: Voice agent main logic
- **app/core/config.py**: Central configuration management
- **requirements.txt**: Python dependencies

## Development & Deployment

### Setup Requirements
- Python 3.8+
- Google Cloud credentials
- Azure OpenAI access
- Daily.co API key
- Environment file with required variables

### Running the Server
```bash
python run.py
# Server starts on http://0.0.0.0:8000
```

### Testing
- Static HTML client available at `/static/client.html`
- Health check at `/health`
- Version info at `/version`

## Recent Changes (Git History)
- Beta release (#70)
- Context summarization feature (#56) - conversation summarization after specified turns
- Demo mode support for remote MCP Server (#69)
- Support for platform integrations and merchant ID handling

## Current Branch: release
Status: Clean working directory

This project represents a sophisticated voice AI agent with enterprise-grade features for real-time conversation processing and dynamic tool integration.
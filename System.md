# Clairvoyance System Architecture Analysis

## Overview
Clairvoyance is a sophisticated voice-enabled AI assistant platform called **"Breeze Automatic"** designed for D2C (Direct-to-Consumer) business owners. The system provides real-time voice interaction capabilities for business analytics and insights.

## Core Architecture Components

### 1. Dual Voice Interface System
The application implements two distinct voice interaction pathways:

#### Gemini Live Session (`app/ws/live_session.py:164`)
- **Technology**: Google Gemini Live API via WebSocket
- **Endpoint**: `/ws/live`
- **Features**: 
  - Real-time audio streaming
  - Automatic VAD (Voice Activity Detection)
  - Turn-based conversation management
  - Tool call processing with business context

#### Pipecat Voice Agent (`app/agents/voice/automatic/__init__.py:45`)
- **Technology**: Daily.co transport + Azure OpenAI + Google STT/TTS
- **Endpoint**: `/agent/voice/automatic`
- **Features**:
  - Multi-provider TTS support (Google, ElevenLabs)
  - Noise reduction filtering
  - RTVI event handling
  - Session-based subprocess management

### 2. FastAPI Application Server (`app/main.py:79`)
**Core Web Server** managing both voice interfaces with:
- CORS middleware for cross-origin requests
- Static file serving
- Process lifecycle management
- WebSocket connection handling
- Bot process tracking and cleanup

**Key Routes**:
- `/ws/live` - Gemini Live WebSocket endpoint
- `/agent/voice/automatic` - Pipecat bot creation endpoint
- `/` - Client HTML interface
- `/health` - Health check endpoint
- `/version` - Application version endpoint

### 3. Business Intelligence Layer

#### Authentication System (`app/api/auth.py`)
- Euler token validation for merchant authentication
- Breeze token fetching for platform access
- Session-based security management

#### Analytics Integration
- **Juspay Analytics** (`app/api/juspay_metrics.py`): Payment processing metrics and transaction data
- **Breeze Analytics** (`app/api/breeze_metrics.py`): Sales performance and business metrics
- **Shop Data** (`app/api/shops.py`): Merchant shop information and configuration

#### Data Pre-loading Strategy
The system pre-loads analytics data during session initialization:
- Today's data (both Juspay and Breeze)
- Weekly data (last 7 days)
- Timezone-aware processing (Asia/Kolkata)
- Fallback to dummy data for test mode

### 4. Tool System Architecture

#### MCP (Model Context Protocol) Integration
- **Remote Tool Server** (`app/agents/voice/automatic/services/mcp/automatic_client.py`): Extensible tool system via remote MCP server
- **Configuration-driven**: Enabled via `AUTOMATIC_MCP_TOOL_SERVER_USAGE` flag
- **Context injection**: Session ID, tokens, shop details automatically provided

#### Local Tool Providers (`app/tools/`)
- **Breeze Tools**: Analytics and business metrics
- **Juspay Tools**: Payment and transaction analytics  
- **Internet Tools**: Web search capabilities
- **System Tools**: Utility functions

#### Tool Execution Flow
1. LLM requests tool execution
2. Context parameters injected automatically
3. Async/sync function execution handled
4. Results formatted for conversational response
5. Error handling with graceful degradation

### 5. Configuration Management (`app/core/config.py`)

#### Environment-based Configuration
- **API Keys**: Gemini, Azure OpenAI, Daily, ElevenLabs, Google credentials
- **Service Endpoints**: Configurable URLs for external services
- **Feature Flags**: Tracing, search grounding, noise reduction
- **Voice Configuration**: TTS providers and voice selection

#### Critical Configuration Parameters
- VAD sensitivity and volume thresholds
- Context summarization settings
- Timeout configurations for sessions
- Audio processing parameters (sample rate, frame size)

### 6. AI Personality System (`app/agents/voice/automatic/prompts/system.py`)

#### Dynamic System Prompt Generation
- **Base personality**: Friendly business assistant with Indian English tone
- **User personalization**: Name-based customization
- **TTS optimization**: Provider-specific instructions for natural speech
- **Business context**: Analytics data integration for informed responses

#### Conversation Management
- **Context retention**: Automatic memory of time ranges and preferences
- **Number formatting**: Indian numbering system (lakh, crore)
- **Direct response protocol**: Lead with answers, then context
- **Error handling**: Graceful degradation with user-friendly messages

### 7. Session Management

#### WebSocket Session Lifecycle
1. **Connection establishment** with token validation
2. **Pre-Gemini API calls** for analytics data fetching
3. **Gemini session creation** with dynamic context
4. **Concurrent task management**: Keepalive, receive, forward
5. **Graceful cleanup** with resource deallocation

#### Process Management (Pipecat)
- **Subprocess tracking**: PID-based bot process registry
- **Resource cleanup**: Automatic termination on shutdown
- **Session isolation**: Unique session IDs for logging
- **Event-driven lifecycle**: Participant join/leave handling

## Data Flow Architecture

### 1. Session Initialization Flow
```
User Connection → Authentication → Analytics Fetch → AI Context Creation → Voice Session Start
```

### 2. Voice Interaction Flow
```
Audio Input → STT/Live Processing → LLM Processing → Tool Execution (if needed) → TTS/Audio Output
```

### 3. Tool Execution Flow
```
LLM Tool Request → Context Injection → Function Execution → Result Processing → Conversational Response
```

## Key Technical Learnings

### 1. Dual Interface Strategy
The system cleverly implements two voice interfaces to cover different use cases:
- **Gemini Live**: Real-time, low-latency for immediate responses
- **Pipecat**: Feature-rich with multiple provider support for flexibility

### 2. Context Management Excellence
- Pre-loads business data to avoid API calls for common queries
- Maintains conversation context across tool calls
- Implements smart timeframe persistence

### 3. Business-Focused Design
- Indian numbering system for local market relevance
- Merchant-centric terminology and workflows
- Analytics integration tailored for D2C businesses

### 4. Robust Error Handling
- Graceful degradation strategies
- Comprehensive logging with session IDs
- Automatic retry mechanisms for recoverable errors

### 5. Scalability Considerations
- Environment-based configuration
- Process isolation for concurrent sessions
- Modular tool system for extensibility

## Security Considerations

### Authentication Flow
- Token-based authentication with multiple providers
- Session-isolated credentials
- Secure API key management via environment variables

### Data Handling
- No persistent storage of sensitive data
- Session-scoped data lifecycle
- Secure WebSocket communication

## Performance Optimizations

### 1. Data Pre-loading
- Analytics data fetched once per session
- Cached for "today" and "weekly" queries
- Reduces API calls during conversation

### 2. Concurrent Processing
- Parallel task execution for session management
- Async/await pattern throughout
- Non-blocking audio processing

### 3. Resource Management
- Automatic cleanup of bot processes
- Session timeout handling
- Memory-efficient WebSocket management

## Deployment Architecture

### Process Model
- **Main FastAPI server**: Handles HTTP/WebSocket requests
- **Child processes**: Pipecat voice agents spawned as needed
- **Session isolation**: Each voice session runs independently

### External Dependencies
- **Google Gemini**: Live API and standard API
- **Azure OpenAI**: LLM processing for Pipecat
- **Daily.co**: WebRTC transport for voice
- **ElevenLabs/Google**: TTS services
- **Juspay/Breeze APIs**: Business analytics data

This architecture demonstrates a sophisticated approach to building a production-ready voice AI assistant with strong business context awareness and robust technical foundations.
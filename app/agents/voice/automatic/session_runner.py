import asyncio
import time
from typing import Optional
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.logger import logger, configure_session_logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.audio.filters.noisereduce_filter import NoisereduceFilter
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.audio.interruptions.min_words_interruption_strategy import MinWordsInterruptionStrategy
from app.agents.voice.automatic.services.llm_wrapper import LLMServiceWrapper
from pipecat.services.azure.llm import AzureLLMService
from pipecat.services.google.stt import GoogleSTTService
from pipecat.transcriptions.language import Language
from pipecat.frames.frames import TTSSpeakFrame, BotSpeakingFrame, LLMFullResponseEndFrame, BotInterruptionFrame, UserStartedSpeakingFrame
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIProcessor
from pipecat.services.google.rtvi import GoogleRTVIObserver

from app.core import config
from app.agents.voice.automatic.services.mcp.automatic_client import MCPClient
from .processors import LLMSpyProcessor
from .processors.stop_word_processor import StopWordProcessor
# Voice locking imports - wrapped in try/except for graceful fallback
try:
    from .processors.audio_buffer_processor import AudioBufferProcessor
    from .processors.speaker_filter_processor import SpeakerFilterProcessor
    from .services.speaker_diarization import SpeakerDiarizationService
    from .services.voice_enrollment import VoiceEnrollmentSystem
    VOICE_LOCKING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️  Voice locking dependencies not available: {e}")
    logger.warning("⚠️  Voice locking will be disabled - install torch and pyannote.audio to enable")
    VOICE_LOCKING_AVAILABLE = False
from .prompts import get_system_prompt
from .tools import initialize_tools
from .tts import get_tts_service
from app.agents.voice.automatic.types import (
    TTSProvider,
    Mode,
    decode_tts_provider,
    decode_voice_name,
    decode_mode,
)
from opentelemetry import trace
from langfuse import get_client

load_dotenv(override=True)

# import setup_tracing from tracing_setup.py file
from app.agents.voice.automatic.analytics.tracing_setup import setup_tracing


async def run_voice_pipeline(
    url: str,
    token: str,
    mode: Optional[str] = None,
    session_id: Optional[str] = None,
    euler_token: Optional[str] = None,
    breeze_token: Optional[str] = None,
    shop_url: Optional[str] = None,
    shop_id: Optional[str] = None,
    shop_type: Optional[str] = None,
    user_name: Optional[str] = None,
    tts_provider: Optional[str] = None,
    voice_name: Optional[str] = None,
    merchant_id: Optional[str] = None,
    platform_integrations: Optional[list] = None,
    shutdown_event: Optional[asyncio.Event] = None
):
    """
    Run the voice pipeline as an async function instead of subprocess.
    This is the async version of the main() function from __init__.py
    """
    
    # Start timing the entire pipeline setup
    pipeline_start_time = time.time()
    
    # Configure logger with session ID for all logs in this session
    if session_id:
        configure_session_logger(session_id)
        logger.info(f"🚀 Voice agent started with session ID: {session_id}")
        logger.info(f"⏱️  Pipeline setup started at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")

    # Decode TTS parameters
    tts_provider_enum = decode_tts_provider(tts_provider)
    voice_name_enum = decode_voice_name(voice_name)
    mode_enum = decode_mode(mode)

    # Initialize tools based on the mode and provided tokens
    # Only pass tokens if in live mode
    
    use_automatic_mcp_server = config.AUTOMATIC_MCP_TOOL_SERVER_USAGE or \
        (shop_id and shop_id in config.SHOPS_FOR_AUTOMATIC_MCP_SERVER)

    # Personalize the system prompt if a user name is provided
    prompt_start = time.time()
    system_prompt = get_system_prompt(user_name, tts_provider_enum)
    prompt_time = time.time() - prompt_start
    logger.info(f"⏱️  System prompt generated in {prompt_time*1000:.1f}ms")

    # Initialize Daily transport parameters
    daily_start = time.time()
    daily_params = DailyParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(
            sample_rate=16000,
            params=VADParams(
                confidence=config.VAD_CONFIDENCE,
                start_secs=0.30,
                stop_secs=1.00,
                min_volume=config.VAD_MIN_VOLUME,
            )
        ),
    )

    if config.ENABLE_NOISE_REDUCE_FILTER:
        logger.info("Noise reduction filter enabled.")
        daily_params.audio_in_filter = NoisereduceFilter()
    else:
        logger.info("Noise reduction filter disabled.")

    transport = DailyTransport(
        url,
        token,
        "Breeze Automatic Voice Agent",
        daily_params,
    )
    daily_time = time.time() - daily_start
    logger.info(f"⏱️  Daily transport initialized in {daily_time*1000:.1f}ms")

    # Initialize STT service
    stt_start = time.time()
    stt = GoogleSTTService(
        params=GoogleSTTService.InputParams(languages=[Language.EN_US, Language.EN_IN], enable_interim_results=False),
        credentials=config.GOOGLE_CREDENTIALS_JSON
    )
    stt_time = time.time() - stt_start
    logger.info(f"⏱️  Google STT service initialized in {stt_time*1000:.1f}ms")

    # Initialize TTS service
    tts_start = time.time()
    tts = get_tts_service(tts_provider=tts_provider_enum.value, voice_name=voice_name_enum.value)
    tts_time = time.time() - tts_start
    logger.info(f"⏱️  TTS service ({tts_provider_enum.value}) initialized in {tts_time*1000:.1f}ms")

    # Initialize LLM service
    llm_start = time.time()
    llm = LLMServiceWrapper(AzureLLMService(
        api_key=config.AZURE_OPENAI_API_KEY,
        endpoint=config.AZURE_OPENAI_ENDPOINT,
        model=config.AZURE_OPENAI_MODEL,
    ))
    llm_time = time.time() - llm_start
    logger.info(f"⏱️  Azure OpenAI LLM service initialized in {llm_time*1000:.1f}ms")

    # Initialize tools
    tools_start = time.time()
    if not use_automatic_mcp_server:
        logger.info("Initializing local function tools")
        if mode_enum == Mode.LIVE:
            tools, tool_functions = initialize_tools(
                mode=mode_enum.value,
                breeze_token=breeze_token,
                euler_token=euler_token,
                shop_url=shop_url,
                shop_id=shop_id,
                shop_type=shop_type,
                merchant_id=merchant_id,
            )
        else:
            tools, tool_functions = initialize_tools(
                mode=mode_enum.value,
                merchant_id=merchant_id,
            )
            
        for name, function in tool_functions.items():
            llm.register_function(name, function)
        
        tools_time = time.time() - tools_start
        logger.info(f"⏱️  Local tools ({len(tool_functions)} functions) initialized in {tools_time*1000:.1f}ms")
    else:
        logger.info(f"Initializing tools from remote MCP server")
        
        mcp_context = {
            "sessionId": session_id,
            "juspayToken": euler_token,
            "shopUrl": shop_url,
            "shopId": shop_id,
            "shopType": shop_type,
            "userId": user_name,
            "enableDemoMode": mode_enum != Mode.LIVE,
            "merchantId": merchant_id,
            "platformIntegrations": platform_integrations
        }
        mcp_client = MCPClient(
            server_url=config.AUTOMATIC_TOOL_MCP_SERVER_URL,
            auth_token=breeze_token,
            context=mcp_context
        )
        tools = await mcp_client.register_tools(llm)
        
        tools_time = time.time() - tools_start
        logger.info(f"⏱️  MCP tools registered in {tools_time*1000:.1f}ms")

    # Simplified event handler for TTS feedback
    @llm.event_handler("on_function_calls_started")
    async def on_function_calls_started(service, function_calls):
        # Only play the "checking" message if using Google TTS
        if tts_provider_enum == TTSProvider.GOOGLE:
            for function_call in function_calls:
                if function_call.function_name != "get_current_time":
                    await tts.queue_frame(TTSSpeakFrame("Let me check on that."))
                    break

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
    ]

    context = llm.create_summarizing_context(
        messages,
        tools,
    )

    context_aggregator = llm.create_context_aggregator(context)

    # RTVI events for Pipecat client UI
    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    # Create pipeline
    pipeline_create_start = time.time()
    
    # Add custom processors
    tool_call_processor = LLMSpyProcessor(rtvi)
    stop_word_processor = StopWordProcessor()
    
    # Initialize voice locking components if enabled
    audio_buffer_processor = None
    speaker_filter_processor = None
    
    if config.ENABLE_VOICE_LOCKING and VOICE_LOCKING_AVAILABLE:
        logger.info("🔊 ===== INITIALIZING VOICE LOCKING SYSTEM =====")
        logger.info(f"🔊 Voice locking enabled with config:")
        logger.info(f"🔊   - Similarity threshold: {config.SPEAKER_SIMILARITY_THRESHOLD}")
        logger.info(f"🔊   - Enrollment duration: {config.SPEAKER_ENROLLMENT_DURATION}s")
        logger.info(f"🔊   - Chunk size: {config.DIARIZATION_CHUNK_SIZE}s")
        logger.info(f"🔊   - Sensitivity: {config.VOICE_LOCK_SENSITIVITY}")
        
        # Initialize speaker diarization service
        logger.info("🔊 Creating speaker diarization service...")
        diarization_service = SpeakerDiarizationService(
            similarity_threshold=config.SPEAKER_SIMILARITY_THRESHOLD,
            min_segment_duration=0.5,
            sample_rate=16000
        )
        
        # Initialize diarization service (async)
        try:
            logger.info("🔊 Initializing diarization models (this may take a moment)...")
            await diarization_service.initialize()
            logger.info("✅ Speaker diarization service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize speaker diarization: {e}")
            logger.warning("⚠️  Continuing WITHOUT voice locking")
            config.ENABLE_VOICE_LOCKING = False
    elif config.ENABLE_VOICE_LOCKING and not VOICE_LOCKING_AVAILABLE:
        logger.warning("⚠️  Voice locking enabled but dependencies not available")
        logger.warning("⚠️  Install requirements: pip install torch torchaudio pyannote.audio")
        logger.warning("⚠️  Continuing WITHOUT voice locking")
        config.ENABLE_VOICE_LOCKING = False
    
    if config.ENABLE_VOICE_LOCKING and VOICE_LOCKING_AVAILABLE:
        # Create audio buffer processor with diarization callback
        logger.info("🔊 Creating audio buffer processor...")
        audio_buffer_processor = AudioBufferProcessor(
            chunk_duration=config.DIARIZATION_CHUNK_SIZE,
            buffer_size=10,
            sample_rate=16000,
            diarization_callback=diarization_service.identify_speakers
        )
        
        # Create speaker filter processor
        logger.info("🔊 Creating speaker filter processor...")
        speaker_filter_processor = SpeakerFilterProcessor(
            diarization_service=diarization_service,
            audio_buffer=audio_buffer_processor,
            sync_tolerance=1.0,
            enable_voice_locking=True
        )
        
        # Initialize voice enrollment system
        logger.info("🔊 Creating voice enrollment system...")
        enrollment_system = VoiceEnrollmentSystem(
            diarization_service=diarization_service,
            min_enrollment_duration=config.SPEAKER_ENROLLMENT_DURATION * 0.6,
            max_enrollment_duration=config.SPEAKER_ENROLLMENT_DURATION * 2.0,
            quality_threshold=config.AUDIO_QUALITY_THRESHOLD
        )
        
        logger.info("✅ ===== VOICE LOCKING SYSTEM READY =====")
        logger.info("🎯 The system will automatically enroll the first speaker and filter others")
    
    if not config.ENABLE_VOICE_LOCKING:
        logger.info("🔊 Voice locking is DISABLED - all speakers will be processed")

    # Build pipeline with conditional voice locking processors
    pipeline_processors = [
        transport.input(),
    ]
    
    # Add audio buffer processor first (before STT) if voice locking enabled
    if audio_buffer_processor:
        logger.info("🔊 Adding audio buffer processor to pipeline (before STT)")
        pipeline_processors.append(audio_buffer_processor)
    
    pipeline_processors.extend([
        stt,
        stop_word_processor,  # Add stop word detection after STT
    ])
    
    # Add speaker filter processor after STT if voice locking enabled
    if speaker_filter_processor:
        logger.info("🔊 Adding speaker filter processor to pipeline (after STT)")
        pipeline_processors.append(speaker_filter_processor)
    
    pipeline_processors.extend([
        rtvi,
        context_aggregator.user(),
        llm,
        tool_call_processor,
        tts,
        transport.output(),
        context_aggregator.assistant(),
    ])

    pipeline = Pipeline(pipeline_processors)
    
    pipeline_create_time = time.time() - pipeline_create_start
    logger.info(f"⏱️  Pipeline created with {len(pipeline._processors)} processors in {pipeline_create_time*1000:.1f}ms")

    user_name_for_trace = user_name or "guest"
    shopId = "euler" if euler_token and not shop_id else shop_id or "dummy"
    ist_time = datetime.now(ZoneInfo("Asia/Kolkata"))
    timestamp = ist_time.strftime("%Y-%m-%d_%H-%M-%S")
    conversation_id = f"{user_name_for_trace}-{shopId}-{timestamp}"

    # Create custom interruption strategy for non-stop words
    # This prevents interruption unless user says 2+ words (reduces false triggers)
    general_interruption_strategy = MinWordsInterruptionStrategy(min_words=2)
    
    task_params = {
        "idle_timeout_secs": 180.0,
        "idle_timeout_frames": (BotSpeakingFrame, LLMFullResponseEndFrame),
        "params": PipelineParams(
            allow_interruptions=True,
            interruption_strategies=[general_interruption_strategy]
        ),
        "cancel_on_idle_timeout": True,
        "observers": [GoogleRTVIObserver(rtvi)],
    }

    if config.ENABLE_TRACING:
        setup_tracing("breeze-voice-agent")
        task_params["conversation_id"] = conversation_id
        task_params["enable_tracing"] = True

    # Create pipeline task
    task_create_start = time.time()
    task = PipelineTask(pipeline, **task_params)
    task_create_time = time.time() - task_create_start
    logger.info(f"⏱️  Pipeline task created in {task_create_time*1000:.1f}ms")
    
    # Log total setup time
    total_setup_time = time.time() - pipeline_start_time
    logger.info(f"🎯 TOTAL PIPELINE SETUP TIME: {total_setup_time*1000:.1f}ms")

    @rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        await rtvi.set_bot_ready()

    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        connection_time = time.time() - pipeline_start_time
        logger.info(f"🔗 FIRST PARTICIPANT CONNECTED: {participant['id']}")
        logger.info(f"⏱️  CONNECTION ESTABLISHED IN: {connection_time*1000:.1f}ms from pipeline start")
        logger.info(f"🎤 Voice session ready for audio processing")
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport, participant, reason):
        logger.info(f"Participant left: {participant['id']}")
        await task.cancel()

    @task.event_handler("on_pipeline_cancelled")
    async def on_pipeline_cancelled(task, frame):
        logger.info("Pipeline task cancelled. Cancelling main task.")
        # In async version, we don't need to cancel the main task
        # The task will naturally complete when this function returns

    runner = PipelineRunner()

    async def run_pipeline():
        try:
            await runner.run(task)
        except asyncio.CancelledError:
            logger.info("Pipeline task cancelled. Exiting gracefully.")
            raise

    # Check for shutdown signal periodically
    async def shutdown_monitor():
        if shutdown_event:
            await shutdown_event.wait()
            logger.info("Shutdown signal received, cancelling pipeline")
            await task.cancel()

    try:
        if config.ENABLE_TRACING:
            langfuse_client = get_client()
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(conversation_id) as root_span:
                logger.info(f"Starting current span with conversation ID: {conversation_id}")
                root_span.set_attribute("conversation.id", conversation_id)
                root_span.set_attribute("conversation.type", "voice")
                root_span.set_attribute("user.name", user_name_for_trace)
                root_span.set_attribute("service.name", "breeze-voice-agent")
                langfuse_client.update_current_trace(user_id=user_name_for_trace)
                langfuse_client.update_current_trace(session_id=session_id)
                langfuse_client.update_current_trace(tags=[voice_name_enum.value])
                
                # Run pipeline with shutdown monitoring
                if shutdown_event:
                    pipeline_task = asyncio.create_task(run_pipeline())
                    monitor_task = asyncio.create_task(shutdown_monitor())
                    
                    done, pending = await asyncio.wait(
                        [pipeline_task, monitor_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    # Cancel any remaining tasks
                    for pending_task in pending:
                        pending_task.cancel()
                        try:
                            await pending_task
                        except asyncio.CancelledError:
                            pass
                else:
                    await run_pipeline()
        else:
            # Run pipeline with shutdown monitoring
            if shutdown_event:
                pipeline_task = asyncio.create_task(run_pipeline())
                monitor_task = asyncio.create_task(shutdown_monitor())
                
                done, pending = await asyncio.wait(
                    [pipeline_task, monitor_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                # Cancel any remaining tasks
                for pending_task in pending:
                    pending_task.cancel()
                    try:
                        await pending_task
                    except asyncio.CancelledError:
                        pass
            else:
                await run_pipeline()
                
    except asyncio.CancelledError:
        logger.info("Voice pipeline was cancelled")
        raise
    except Exception as e:
        logger.error(f"Voice pipeline failed with error: {e}", exc_info=True)
        # Don't re-raise here, let the session manager handle it
        raise
    finally:
        # Cleanup resources
        try:
            if 'transport' in locals():
                logger.info("Cleaning up transport connection")
                # Transport cleanup happens automatically
            if 'runner' in locals():
                logger.info("Pipeline runner cleanup completed")
            
            # Cleanup voice locking components
            if VOICE_LOCKING_AVAILABLE and config.ENABLE_VOICE_LOCKING:
                if 'audio_buffer_processor' in locals() and audio_buffer_processor:
                    await audio_buffer_processor.cleanup()
                if 'speaker_filter_processor' in locals() and speaker_filter_processor:
                    await speaker_filter_processor.cleanup()
                if 'diarization_service' in locals() and diarization_service:
                    await diarization_service.cleanup()
                if 'enrollment_system' in locals() and enrollment_system:
                    await enrollment_system.cleanup()
                logger.info("Voice locking components cleanup completed")
                
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}")
        logger.info("Voice pipeline completed")
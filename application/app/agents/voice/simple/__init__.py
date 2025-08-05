import asyncio
import sys
import argparse
from dotenv import load_dotenv

from app.core.logger import logger, configure_session_logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.audio.filters.noisereduce_filter import NoisereduceFilter
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.services.azure.llm import AzureLLMService
from pipecat.services.google.stt import GoogleSTTService
from pipecat.services.google.tts import GoogleTTSService
from pipecat.transcriptions.language import Language
from pipecat.frames.frames import TTSSpeakFrame, BotSpeakingFrame, LLMFullResponseEndFrame, AudioRawFrame, TTSAudioRawFrame, Frame, StartFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.processors.aggregators.llm_response import (
    LLMAssistantResponseAggregator,
    LLMUserResponseAggregator,
)
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext

from app.core import config
from .tools import initialize_tools
from .prompts import get_system_prompt
from .tts import get_tts_service
from .types import TTSProvider, decode_tts_provider
from app.transcript_client import get_transcript_client
from .transcript_processor import TranscriptProcessor
from .audio_debug_processor import AudioDebugProcessor
from .llm_response_processor import LLMResponseProcessor

load_dotenv(override=True)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", type=str, required=True, help="URL of the Daily room")
    parser.add_argument("-t", "--token", type=str, required=True, help="Daily token")
    parser.add_argument("--session-id", type=str, required=True, help="Session ID for logging")
    parser.add_argument("--user-name", type=str, help="User's name")
    parser.add_argument("--tts-provider", type=str, help="TTS provider to use")
    parser.add_argument("--voice-name", type=str, help="Voice name to use")
    args = parser.parse_args()

    # Configure logger with session ID
    configure_session_logger(args.session_id)
    logger.info(f"Voice agent started with session ID: {args.session_id}")

    # Decode TTS parameters
    tts_provider = decode_tts_provider(args.tts_provider)

    # Get system prompt
    system_prompt = get_system_prompt(args.user_name)

    # Configure Daily transport with explicit audio settings  
    daily_params = DailyParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        audio_out_sample_rate=16000,  # Match TTS sample rate
        audio_in_sample_rate=16000,   # Match STT sample rate
        audio_out_channels=1,         # Mono output
        audio_in_channels=1,          # Mono input
        vad_analyzer=SileroVADAnalyzer(
            sample_rate=16000,
            params=VADParams(
                confidence=0.6,    # Lower confidence for easier detection (was 0.85)
                start_secs=0.1,    # Faster start detection (was 0.30)
                stop_secs=0.5,     # Faster stop detection (was 1.00)
                min_volume=0.4,    # Lower volume threshold (was 0.75)
            )
        ),
    )
    
    logger.info(f"🎤 Daily params: audio_in={daily_params.audio_in_enabled}, audio_out={daily_params.audio_out_enabled}")

    if config.ENABLE_NOISE_REDUCE_FILTER:
        logger.info("Noise reduction filter enabled.")
        daily_params.audio_in_filter = NoisereduceFilter()
    else:
        logger.info("Noise reduction filter disabled.")

    transport = DailyTransport(
        args.url,
        args.token,
        "Voice Bot",  # Shorter bot name
        daily_params,
    )
    
    # Check Daily transport audio configuration
    logger.info(f"📡 Daily transport audio_out_enabled: {daily_params.audio_out_enabled}")
    logger.info(f"📡 Daily transport sample_rate: {getattr(daily_params, 'sample_rate', 'default')}")
    
    # Add transport debug logging
    @transport.event_handler("on_participant_joined")
    async def on_participant_joined_debug(transport, participant):
        logger.info(f"👥 Participant joined: {participant}")
        
    @transport.event_handler("on_call_state_updated") 
    async def on_call_state_updated(transport, state):
        logger.info(f"📞 Call state: {state}")

    # Initialize STT
    stt = GoogleSTTService(
        params=GoogleSTTService.InputParams(
            languages=[Language.EN_US], 
            enable_interim_results=False
        ),
        credentials=config.GOOGLE_CREDENTIALS_JSON
    )

    # Initialize TTS
    tts = get_tts_service(tts_provider.value, args.voice_name)
    
    # Debug the TTS service
    logger.info(f"🔊 TTS Service: {type(tts).__name__}")
    
    # Create TTS audio capture processor following PipeCat patterns
    class TTSAudioCapture(FrameProcessor):
        def __init__(self, session_id: str):
            super().__init__()
            self.session_id = session_id
            
        async def process_frame(self, frame: Frame, direction: FrameDirection):
            # Call parent first as per pattern
            await super().process_frame(frame, direction)
            
            # Capture TTS audio frames going downstream
            if direction == FrameDirection.DOWNSTREAM and isinstance(frame, TTSAudioRawFrame):
                try:
                    audio_data = frame.audio
                    
                    # Convert numpy array to bytes if needed
                    if hasattr(audio_data, 'tobytes'):
                        audio_bytes = audio_data.tobytes()
                    else:
                        audio_bytes = bytes(audio_data)
                    
                    logger.info(f"🎵 Captured TTS audio: {len(audio_bytes)} bytes for session {self.session_id}")
                    
                    # Send to WebSocket clients via API (non-blocking)
                    import aiohttp
                    import asyncio
                    
                    async def send_audio():
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.post(
                                    f"http://localhost:8000/api/audio/{self.session_id}",
                                    data=audio_bytes,
                                    headers={'Content-Type': 'application/octet-stream'},
                                    timeout=aiohttp.ClientTimeout(total=1.0)
                                ) as response:
                                    if response.status == 200:
                                        logger.debug(f"✅ Sent {len(audio_bytes)} bytes via processor")
                                    else:
                                        logger.warning(f"Audio API returned status {response.status}")
                        except Exception as e:
                            logger.error(f"Failed to send audio via processor: {e}")
                    
                    asyncio.create_task(send_audio())
                    
                except Exception as e:
                    logger.error(f"Error in TTS audio capture: {e}")
            
            # Always push frame downstream as per pattern
            await self.push_frame(frame, direction)
    
    # Create LLM response processor to extract visualization data and clean speech
    llm_response_processor = LLMResponseProcessor(args.session_id)
    
    # Create the audio capture processor
    tts_audio_capture = TTSAudioCapture(args.session_id)

    # Initialize LLM
    llm = AzureLLMService(
        api_key=config.AZURE_OPENAI_API_KEY,
        endpoint=config.AZURE_OPENAI_ENDPOINT,
        model=config.AZURE_OPENAI_MODEL,
    )

    # Initialize tools
    tools, tool_functions = initialize_tools()
    
    # Register functions with LLM
    for name, function in tool_functions.items():
        logger.info(f"Registering function: {name}")
        llm.register_function(name, function)

    # Set up messages
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
    ]

    # Create context and aggregator (v0.0.71 API)
    context = OpenAILLMContext(messages=messages, tools=tools)
    context_aggregator = llm.create_context_aggregator(context)

    # Create transcript processor
    transcript_processor = TranscriptProcessor(args.session_id)
    await transcript_processor.start()

    # Remove all custom processors to avoid Pipecat integration issues

    # Create pipeline - WebSocket audio only, no Daily.co audio output to avoid conflicts
    pipeline = Pipeline(
        [
            transport.input(),              # Audio from browser
            stt,                           # Speech to text
            context_aggregator.user(),     # User context
            llm,                           # LLM processing
            llm_response_processor,        # Extract visualization data & clean speech
            tts,                           # Text to speech (receives clean text)
            tts_audio_capture,             # Capture TTS audio for WebSocket streaming
            # Removed transport.output() to avoid audio feedback and VAD conflicts
            context_aggregator.assistant(), # Assistant context
        ]
    )

    # Create and configure task with aggressive interruption handling
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        idle_timeout_secs=180.0,
        idle_timeout_frames=(BotSpeakingFrame, LLMFullResponseEndFrame),
        cancel_on_idle_timeout=True,
    )

    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        logger.info(f"First participant joined: {participant['id']}")
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport, participant, reason):
        logger.info(f"Participant left: {participant['id']}")
        await task.cancel()

    @task.event_handler("on_pipeline_cancelled")
    async def on_pipeline_cancelled(task, frame):
        logger.info("Pipeline task cancelled. Cancelling main task.")
        main_task = asyncio.current_task()
        main_task.cancel()

    # Simple transcript monitor task - poll context for changes
    async def transcript_monitor():
        last_message_count = 1  # Start from 1 to skip system message
        while True:
            try:
                await asyncio.sleep(0.5)  # Check every 500ms
                current_messages = context.get_messages()
                current_count = len(current_messages)
                
                if current_count > last_message_count:
                    # New messages added (skip system messages)
                    new_messages = current_messages[last_message_count:]
                    for msg in new_messages:
                        role = msg.get("role", "")
                        content = msg.get("content", "")
                        # Skip system messages and only send user/assistant messages
                        if content and content.strip() and role in ["user", "assistant"]:
                            speaker = "user" if role == "user" else "assistant"
                            await transcript_processor.transcript_client.send_message(speaker, content.strip())
                            print(f"📝 {speaker.title()}: {content.strip()}")
                    
                    last_message_count = current_count
                    
            except Exception as e:
                print(f"❌ Transcript monitor error: {e}")
                await asyncio.sleep(1)

    # Start transcript monitor as background task
    monitor_task = asyncio.create_task(transcript_monitor())

    # Run the pipeline
    runner = PipelineRunner()

    try:
        await runner.run(task)
    except asyncio.CancelledError:
        logger.info("Main task cancelled. Exiting gracefully.")

if __name__ == "__main__":
    asyncio.run(main())
"""Pipecat voice pipeline factory for one SmallWebRTC connection."""

import aiohttp

from config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_TTS_MODEL,
    ELEVENLABS_VOICE_ID,
    GEMINI_MODEL,
    GOOGLE_API_KEY,
    GROQ_API_KEY,
    GROQ_MODEL,
    LITELLM_API_KEY,
    LITELLM_BASE_URL,
    LITELLM_MODEL,
    LLM_PROVIDER,
)
from prompt import system_prompt
from tools import book_appointment, cancel_appointment, check_doctor_availability

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.adapters.llm.schemas.function_schema import FunctionSchema
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.processors.frameworks.rtvi import (
    RTVIFunctionCallReportLevel,
    RTVIObserver,
    RTVIObserverParams,
    RTVIProcessor,
)
from pipecat.services.elevenlabs.stt import ElevenLabsSTTService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.groq.llm import GroqLLMService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport


async def _run_tool(params, tool):
    result = await tool(**dict(params.arguments))
    await params.result_callback(result)


def _tool_schemas() -> list[FunctionSchema]:
    return [
        FunctionSchema(
            name="check_doctor_availability",
            description="Find free doctor appointment slots. Use ISO dates. The result includes a spoken_summary for the assistant to say naturally; doctor_id and other fields are internal booking metadata.",
            properties={
                "doctor_name": {"type": "string", "description": "Optional partial doctor name."},
                "speciality": {"type": "string", "description": "Optional speciality."},
                "date": {"type": "string", "description": "Optional date in YYYY-MM-DD format."},
            },
            required=[],
        ),
        FunctionSchema(
            name="book_appointment",
            description="Book an appointment slot. Call ONLY AFTER checking availability, picking a slot, asking for the phone number, reading the phone number back digit-by-digit, and getting a clear yes from the caller. Set phone_confirmed=true only in that case.",
            properties={
                "phone_number": {"type": "string", "description": "10-digit phone number spoken by the caller."},
                "phone_confirmed": {"type": "boolean", "description": "Must be true. Only true after the caller said yes to your read-back confirmation."},
                "doctor_id": {"type": "integer", "description": "Doctor ID from check_doctor_availability results."},
                "date": {"type": "string", "description": "Slot date in YYYY-MM-DD format."},
                "time": {"type": "string", "description": "Slot time in HH:MM format (e.g. 10:00)."},
            },
            required=[],
        ),
        FunctionSchema(
            name="cancel_appointment",
            description="Cancel an existing appointment. Call ONLY AFTER asking for the phone number, reading it back digit-by-digit, and getting a clear yes from the caller.",
            properties={
                "phone_number": {"type": "string", "description": "10-digit phone number spoken by the caller."},
                "phone_confirmed": {"type": "boolean", "description": "Must be true after explicit caller confirmation."},
                "appointment_id": {"type": "integer", "description": "Optional appointment ID when the caller has multiple active appointments."},
            },
            required=[],
        ),
    ]


def _create_llm_service():
    """Create the configured LLM service (Groq direct, LiteLLM proxy, or Google Gemini)."""
    # 1. Direct Groq (recommended: fastest, no local proxy needed)
    if LLM_PROVIDER == "groq" or (GROQ_API_KEY and LLM_PROVIDER not in {"litellm", "google"}):
        return GroqLLMService(
            api_key=GROQ_API_KEY,
            settings=GroqLLMService.Settings(model=GROQ_MODEL, reasoning_effort="low"),
            system_instruction=system_prompt(),
        )

    # 2. LiteLLM Proxy (if explicitly selected)
    if LLM_PROVIDER == "litellm":
        return OpenAILLMService(
            api_key=LITELLM_API_KEY,
            base_url=LITELLM_BASE_URL,
            settings=OpenAILLMService.Settings(model=LITELLM_MODEL),
            system_instruction=system_prompt(),
        )

    # 3. Google Gemini
    if LLM_PROVIDER == "google" or GOOGLE_API_KEY:
        from pipecat.services.google.llm import GoogleLLMService

        return GoogleLLMService(
            api_key=GOOGLE_API_KEY,
            model=GEMINI_MODEL,
            system_instruction=system_prompt(),
        )

    # Fallback to direct Groq if key is available
    if GROQ_API_KEY:
        return GroqLLMService(
            api_key=GROQ_API_KEY,
            settings=GroqLLMService.Settings(model=GROQ_MODEL, reasoning_effort="low"),
            system_instruction=system_prompt(),
        )

    raise ValueError("No valid LLM configuration found. Please set GROQ_API_KEY or GOOGLE_API_KEY in .env")


async def run_bot(webrtc_connection) -> None:
    """Run one complete voice session and clean up its HTTP session."""
    async with aiohttp.ClientSession() as http_session:
        transport = SmallWebRTCTransport(
            webrtc_connection=webrtc_connection,
            params=TransportParams(audio_in_enabled=True, audio_out_enabled=True),
        )
        stt = ElevenLabsSTTService(api_key=ELEVENLABS_API_KEY, aiohttp_session=http_session)
        llm = _create_llm_service()
        tts = ElevenLabsTTSService(
            api_key=ELEVENLABS_API_KEY,
            settings=ElevenLabsTTSService.Settings(
                model=ELEVENLABS_TTS_MODEL,
                voice=ELEVENLABS_VOICE_ID,
            ),
        )

        llm.register_function("check_doctor_availability", lambda params: _run_tool(params, check_doctor_availability))
        llm.register_function("book_appointment", lambda params: _run_tool(params, book_appointment))
        llm.register_function("cancel_appointment", lambda params: _run_tool(params, cancel_appointment))

        context = LLMContext(tools=_tool_schemas())
        context.add_message(
            {
                "role": "developer",
                "content": "Start by greeting the caller, introducing yourself as Aria, and asking how you can help.",
            }
        )
        user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
            context,
            user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
        )

        rtvi = RTVIProcessor()
        rtvi_observer = RTVIObserver(
            rtvi=rtvi,
            params=RTVIObserverParams(
                function_call_report_level={"*": RTVIFunctionCallReportLevel.FULL}
            ),
        )

        pipeline = Pipeline(
            [
                transport.input(),
                rtvi,
                stt,
                user_aggregator,
                llm,
                tts,
                transport.output(),
                assistant_aggregator,
            ]
        )
        task = PipelineTask(
            pipeline,
            observers=[rtvi_observer],
            params=PipelineParams(
                enable_metrics=True,
            ),
        )

        has_started = False

        async def start_conversation():
            nonlocal has_started
            if not has_started:
                has_started = True
                await task.queue_frames([LLMRunFrame()])

        @rtvi.event_handler("on_client_ready")
        async def on_client_ready(rtvi_proc):
            await rtvi_proc.set_bot_ready()
            await start_conversation()

        @transport.event_handler("on_client_connected")
        async def on_client_connected(_transport, _client):
            await start_conversation()

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(_transport, _client):
            await task.cancel()

        await PipelineRunner().run(task)

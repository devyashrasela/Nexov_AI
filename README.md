# MediVoice

MediVoice is a browser-based voice assistant for City Care Clinic. A caller speaks
to Aria, the AI receptionist, to check doctor availability, book an appointment,
or cancel an existing appointment. The browser dashboard shows the live transcript,
doctors and slots, and appointments.

## Stack

- Python, FastAPI, Pipecat 1.16, and SmallWebRTC
- ElevenLabs STT and TTS
- LiteLLM proxy with Groq as the default LLM provider
- SQLAlchemy with SQLite by default and optional MySQL support
- React JavaScript, Vite, and custom CSS
- Silero VAD

## Architecture

```text
Browser React dashboard
  -> SmallWebRTC audio and Pipecat events
FastAPI server
  -> Pipecat: audio -> ElevenLabs STT -> LiteLLM/Groq -> ElevenLabs TTS -> audio
  -> appointment tools -> SQLAlchemy -> SQLite/MySQL
REST GET endpoints return doctors, slots, and appointments to the dashboard.
```

The three voice tools are `check_doctor_availability`, `book_appointment`, and
`cancel_appointment`. Booking and cancellation require a `phone_confirmed=true`
argument, so the confirmation rule is enforced in code as well as in the prompt.
The dashboard polls read-only endpoints every three seconds, which keeps it
reliable even if a real-time function-call event is missed.

## Prerequisites

- Python 3.12+
- Node.js 20+
- ElevenLabs API key and voice ID
- Groq API key

## Run locally

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, GROQ_API_KEY, and the LiteLLM settings.
python seed.py --reset
# In a second terminal/environment:
python3 -m venv .litellm-venv
.litellm-venv/bin/pip install -r litellm-requirements.txt
.litellm-venv/bin/python run_litellm_proxy.py --config litellm_config.yaml --port 4000

# In the backend environment:
uvicorn server:app --host 0.0.0.0 --port 7860 --reload
```

The default database is `backend/clinic.db`. Set `DATABASE_URL` to an Aiven
MySQL URI to use MySQL instead. The SQLite fallback remains available for a
fresh clone and for reviewers without hosted database access.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`, allow microphone access, and click **Start Call**.
The browser must run on localhost or HTTPS for microphone access.

## Demo conversation

1. Ask for a cardiologist tomorrow.
2. Choose one of the slots Aria offers.
3. Say a ten-digit Indian mobile number slowly.
4. Confirm the number when Aria reads it back.
5. Verify that the appointment appears and the slot becomes booked.
6. To demonstrate cancellation, ask Aria to cancel and confirm the same number.

## Project structure

```text
backend/
  bot.py       Pipecat pipeline and current SmallWebRTC session
  server.py    FastAPI REST and WebRTC signalling
  tools.py     Function-call handlers and confirmation guards
  store.py     Only database access module
  models.py    SQLAlchemy models
  phone.py     Speech-friendly phone normalization
  seed.py      Rolling seven-day demo data
  tests/       Phone, store, and tool-focused tests
frontend/
  src/         React dashboard, hooks, components, and CSS
```

## Design decisions

- SmallWebRTC avoids a third-party telephony or room account for the browser demo.
- SQLite is the default because it needs no setup; the SQLAlchemy store also
  supports hosted MySQL through `DATABASE_URL`.
- Phone confirmation is represented by an explicit tool argument and rejected
  by the backend when false.
- Database calls run in `asyncio.to_thread` so synchronous SQLAlchemy work does
  not block the voice event loop.
- REST polling is retained as a fallback because appointment updates matter more
  than depending on a single client event shape.

## Tests and checks

```bash
cd backend
PYTHONPATH=. pytest -q

cd ../frontend
npm run build
```

## Known limitations

- Live voice requires valid ElevenLabs and Groq credentials, plus the LiteLLM proxy.
- SmallWebRTC is intended for local/browser demonstration; production deployment
  would need HTTPS and suitable ICE/TURN configuration.
- The dashboard is intentionally read-only; all writes happen through the voice
  tools.
- This is appointment scheduling software, not a medical advice system.


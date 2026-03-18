# SautiCare Backend API 🎙️

SautiCare's high-performance backend is built with **FastAPI** to power an intelligent speech tutor application for learners with speech impairments. 

The architecture is tailored to handle dynamic machine learning workflows directly on the machine, bridging completely offline models for transcription and voice synthesis securely without external cloud billing for inferences.

##  Key Features
- **Offline Text-to-Speech (TTS):** Leverages `piper-tts` to locally synthesize clear, lifelike voice feedback. Supports real-time switching between Male and Female pronunciations.
- **Offline Speech-to-Text (ASR):** Utilizes `faster-whisper` (specifically the `base.en` model) to transcribe user microphone recordings securely, privately, and blisteringly fast. No system `ffmpeg` installations needed thanks to PyAV integrations.
- **Pronunciation Error Scoring:** Automatically analyzes recorded inputs against the expected lesson phrases by computing Word Error Rate (`WER`) and Character Error Rate (`CER`) via `jiwer`, blending it with Acoustic Confidence levels for comprehensive scoring.
- **Gamification & Analytics Engine:** Generates learner statistics, tracking daily participation length, consecutive login streaks, and automatic achievement unlock triggers.
- **Supabase Integration:** Syncs seamlessly with the Supabase Postgres database using direct REST integrations to manage states effortlessly.

##  Technology Stack
- **Framework:** FastAPI, Uvicorn (ASGI)
- **ML & Audio Engines:** `faster-whisper` (ASR), `piper-tts` (TTS), `PyAV` (Decoding), `jiwer` (Scoring), `numpy`
- **Database Binding:** Supabase Python SDK
- **Environment Management:** `python-dotenv`, `pydantic-settings`

##  Project Structure

```bash
sauticare-backend/
├── api/
│   ├── main.py            # FastAPI entrypoint, router definitions
│   ├── config.py          # Environment settings loader
│   ├── dependencies.py    # JWT Auth Guards and Dependency Injection
│   ├── ml/                # Wrappers for ML deployments (whisper_model.py)
│   ├── services/          # Core Business logic (asr_service.py, tts_service.py)
│   ├── api/v1/            # Feature endpoint routers (auth, lessons, practice, analytics)
│   └── schemas/           # Pydantic schemas for data validation
├── models/
│   └── piper/             # Contains the large `.onnx` TTS model weights and `.json` configs
├── requirements.txt       # Project dependencies
└── seed.py                # Database population script
```

##  Endpoints Overview

The API provides Swagger documentation out of the box. Key namespaces include:
- **`GET/POST /api/v1/auth/*`**: JWT Handshake, authentication, registration, and `/me` profiles.
- **`GET /api/v1/lessons/*`**: Fetch curated topics (Nutrition, Hygiene), difficulty levels, and syllabus.
- **`POST /api/v1/practice/attempt`**: ( Core Function) Accepts multipart `UploadFile` (audio), delegates it to `faster-whisper`, calculates scoring matrices, builds feedback, and logs results.
- **`POST /api/v1/voice/tts`**: Accepts a JSON text payload and language/gender preferences, generates an `onnx` response, and returns pure `audio/wav` blob blobs.
- **`GET /api/v1/analytics/*`**: Aggregates macro-level progression logic, dashboard summaries, and unlocked Badges/Achievements.

##  Setup & Development

### 1. Prerequisites
- Python 3.10+
- Activated virtual environment

```bash
python -m venv env
source env/bin/activate
```

### 2. Install Dependencies
Install all required libraries.
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file referencing `.env.example`:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# JWT Configuration
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256
```

### 4. Machine Learning Models
1. **TTS (Piper):** Ensure that `en_US-amy-low.onnx` and `en_US-hfc_male-medium.onnx` (and their respective `.json` files) exist inside the `models/piper/` directory.
2. **ASR (Whisper):** The `base.en` faster-whisper model dynamically fetches and caches itself securely to the disk on the first application launch.

### 5. Running the Backend
Boot up Uvicorn on localhost.
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
You can visually test the API endpoints by navigating to [http://localhost:8000/docs](http://localhost:8000/docs).
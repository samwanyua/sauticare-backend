from fastapi import APIRouter

router = APIRouter()

@router.get("/speak")
def speak(text: str):
    # TODO: integrate HuggingFace TTS model
    return {"audio_url": "fake_url.wav"}

from fastapi import APIRouter, UploadFile

router = APIRouter()

@router.post("/transcribe")
async def transcribe(file: UploadFile):
    # TODO: integrate HuggingFace Whisper API
    return {"text": "mock transcription (Whisper to be added later)"}

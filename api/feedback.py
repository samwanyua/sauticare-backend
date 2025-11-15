from fastapi import APIRouter
from difflib import SequenceMatcher

router = APIRouter()

@router.post("/score")
def score(lesson: str, transcription: str):
    accuracy = SequenceMatcher(None, lesson.lower(), transcription.lower()).ratio() * 100
    accuracy = round(accuracy)

    return {
        "lesson": lesson,
        "transcription": transcription,
        "accuracy": accuracy,
        "comment": "Good job!" if accuracy > 75 else "Keep practicing!"
    }

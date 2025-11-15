from fastapi import APIRouter

router = APIRouter()

@router.get("/levels")
def get_levels():
    return ["easy", "medium", "hard"]

@router.get("/{level}")
def get_lesson(level: str):
    # Later fetch from DB or JSON
    return {"level": level, "phrases": ["I wash my hands", "I eat fruits"]}

from fastapi import FastAPI
from app.api import auth, lessons, feedback, stt, tts

app = FastAPI(title="SautiCare Backend", version="0.1.0")

# Register routes
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(lessons.router, prefix="/api/lessons", tags=["Lessons"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(stt.router, prefix="/api/stt", tags=["Speech-To-Text"])
app.include_router(tts.router, prefix="/api/tts", tags=["Text-To-Speech"])

@app.get("/")
def root():
    return {"message": "SautiCare API is running"}

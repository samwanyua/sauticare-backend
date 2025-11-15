from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import auth
import lessons
import feedback
import stt
import tts
import profile

app = FastAPI(title="SautiCare Backend", version="0.1.0")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",  # add if you test via 127.0.0.1
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # all HTTP methods
    allow_headers=["*"],  # all headers
)


# --- Register routes ---
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(lessons.router, prefix="/api/lessons", tags=["Lessons"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(stt.router, prefix="/api/stt", tags=["Speech-To-Text"])
app.include_router(tts.router, prefix="/api/tts", tags=["Text-To-Speech"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])

@app.get("/")
def root():
    return {"message": "SautiCare API is running"}



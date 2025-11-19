from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import auth, lessons, feedback, stt, tts, profile
from api.db.database import Base, engine
from api import dashboard

app = FastAPI(
    title="SautiCare Backend",
    version="0.1.0"
)

# --- CORS ---
origins = [
    "https://speech-tutor-frontend.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Create tables automatically if needed ---
@app.on_event("startup")
def startup():
    try:
        Base.metadata.create_all(bind=engine)
        print(" Database connected & models created")
    except Exception as e:
        print(" Database error:", e)



# --- Register routers ---
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(lessons.router, prefix="/api/lessons", tags=["Lessons"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(stt.router, prefix="/api/stt", tags=["Speech-To-Text"])
app.include_router(tts.router, prefix="/api/tts", tags=["Text-To-Speech"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])


@app.get("/")
def root():
    return {"message": "SautiCare API is running"}

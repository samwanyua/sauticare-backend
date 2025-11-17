from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SautiCare Backend"
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str = "supersecret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Hugging Face
    HF_API_KEY: str = ""
    HF_STT_MODEL: str = ""
    HF_TTS_MODEL: str = ""

    class Config:
        env_file = ".env"
        extra = "allow"  
settings = Settings()

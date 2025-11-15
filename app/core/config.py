from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SautiCare Backend"

    # Database
    DATABASE_URL: str = "sqlite:///./sauticare.db"

    # JWT
    SECRET_KEY: str = "supersecret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Hugging Face (Set later)
    HF_API_KEY: str = ""
    HF_STT_MODEL: str = ""
    HF_TTS_MODEL: str = ""

    class Config:
        env_file = ".env"

settings = Settings()

# app/config.py
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Sauti Care API"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # ML Models
    WHISPER_MODEL_NAME: str = "whisper-small-finetuned-english"
    HF_SPACE_NAME: str = "ElizabethMwangi/whisper-kenyan-asr"
    
    # Storage
    STORAGE_BUCKET_AUDIO: str = "audio-samples"
    STORAGE_BUCKET_MODELS: str = "trained-models"
    STORAGE_BUCKET_ATTEMPTS: str = "practice-attempts"
    
    # CORS
    FRONTEND_URL: str
    ALLOWED_ORIGINS: str
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_AUDIO_FORMATS: str = "wav,mp3,m4a,ogg"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def allowed_audio_formats_list(self) -> List[str]:
        return [fmt.strip() for fmt in self.ALLOWED_AUDIO_FORMATS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
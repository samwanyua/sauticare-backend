# app/schemas/voice.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class VoiceSampleBase(BaseModel):
    transcription: Optional[str] = None
    duration_seconds: Optional[float] = None
    quality_score: Optional[float] = Field(None, ge=0, le=1)


class VoiceSampleCreate(VoiceSampleBase):
    learner_id: UUID


class VoiceSampleResponse(VoiceSampleBase):
    id: UUID
    learner_id: UUID
    audio_url: str
    used_for_training: bool
    recorded_at: datetime
    
    class Config:
        from_attributes = True


class VoiceUploadResponse(BaseModel):
    message: str
    sample_id: UUID
    transcription: str
    audio_url: str
    quality_score: float
    duration_seconds: float
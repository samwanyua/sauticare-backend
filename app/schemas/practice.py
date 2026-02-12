# app/schemas/practice.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class PracticeSessionCreate(BaseModel):
    lesson_id: UUID


class PracticeSessionResponse(BaseModel):
    id: UUID
    learner_id: UUID
    lesson_id: UUID
    started_at: datetime
    ended_at: Optional[datetime]
    total_attempts: int
    successful_attempts: int
    
    class Config:
        from_attributes = True


class PhraseAttemptCreate(BaseModel):
    session_id: UUID
    phrase_id: UUID
    reference_text: str


class PhraseAttemptResponse(BaseModel):
    id: UUID
    session_id: UUID
    phrase_id: UUID
    audio_url: str
    transcription: str
    confidence_score: float
    pronunciation_score: float
    feedback: Dict[str, Any]
    attempt_number: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class TranscriptionRequest(BaseModel):
    audio_file_key: str  # Temporary storage key
    phrase_id: UUID
    session_id: UUID
    learner_severity: str = "moderate"
    learner_etiology: str = "none"
    language: str = "english"
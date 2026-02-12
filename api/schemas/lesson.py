# app/schemas/lesson.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class LessonBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str  # 'nutrition' or 'hygiene'
    language: str  # 'en-KE' or 'sw'
    difficulty_level: int = Field(..., ge=1, le=5)
    content: Optional[Dict[str, Any]] = None


class LessonCreate(LessonBase):
    pass


class LessonResponse(LessonBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class LessonPhraseBase(BaseModel):
    phrase_text: str
    difficulty_level: int = Field(..., ge=1, le=5)
    phonetic_transcription: Optional[str] = None
    sequence_order: int


class LessonPhraseResponse(LessonPhraseBase):
    id: UUID
    lesson_id: UUID
    audio_url: Optional[str]
    
    class Config:
        from_attributes = True


class LessonWithPhrases(LessonResponse):
    phrases: List[LessonPhraseResponse] = []


class LessonProgressResponse(BaseModel):
    id: UUID
    learner_id: UUID
    lesson_id: UUID
    status: str
    completion_percentage: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True
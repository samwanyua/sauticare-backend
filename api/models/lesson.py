# api/models/lesson.py
from typing import Optional, Dict, Any, List
from datetime import datetime


class Lesson:
    """Lesson model for nutrition and hygiene content"""
    
    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        category: str,  # 'nutrition' or 'hygiene'
        language: str,  # 'en-KE' or 'sw'
        difficulty_level: int,
        content: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.title = title
        self.description = description
        self.category = category
        self.language = language
        self.difficulty_level = difficulty_level
        self.content = content
        self.created_at = created_at


class LessonPhrase:
    """Individual phrase within a lesson"""
    
    def __init__(
        self,
        id: str,
        lesson_id: str,
        phrase_text: str,
        difficulty_level: int,
        sequence_order: int,
        audio_url: Optional[str] = None,
        phonetic_transcription: Optional[str] = None
    ):
        self.id = id
        self.lesson_id = lesson_id
        self.phrase_text = phrase_text
        self.difficulty_level = difficulty_level
        self.sequence_order = sequence_order
        self.audio_url = audio_url
        self.phonetic_transcription = phonetic_transcription


class LessonProgress:
    """Track learner progress through lessons"""
    
    def __init__(
        self,
        id: str,
        learner_id: str,
        lesson_id: str,
        status: str,  # 'not_started', 'in_progress', 'completed'
        completion_percentage: float = 0.0,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ):
        self.id = id
        self.learner_id = learner_id
        self.lesson_id = lesson_id
        self.status = status
        self.completion_percentage = completion_percentage
        self.started_at = started_at
        self.completed_at = completed_at
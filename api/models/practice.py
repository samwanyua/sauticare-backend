# api/models/practice.py
from typing import Optional, Dict, Any
from datetime import datetime


class PracticeSession:
    """Practice session model"""
    
    def __init__(
        self,
        id: str,
        learner_id: str,
        lesson_id: str,
        started_at: datetime,
        ended_at: Optional[datetime] = None,
        total_attempts: int = 0,
        successful_attempts: int = 0
    ):
        self.id = id
        self.learner_id = learner_id
        self.lesson_id = lesson_id
        self.started_at = started_at
        self.ended_at = ended_at
        self.total_attempts = total_attempts
        self.successful_attempts = successful_attempts


class PhraseAttempt:
    """Individual phrase pronunciation attempt"""
    
    def __init__(
        self,
        id: str,
        session_id: str,
        phrase_id: str,
        audio_url: str,
        transcription: str,
        confidence_score: float,
        pronunciation_score: float,
        feedback: Dict[str, Any],
        attempt_number: int,
        created_at: datetime
    ):
        self.id = id
        self.session_id = session_id
        self.phrase_id = phrase_id
        self.audio_url = audio_url
        self.transcription = transcription
        self.confidence_score = confidence_score
        self.pronunciation_score = pronunciation_score
        self.feedback = feedback
        self.attempt_number = attempt_number
        self.created_at = created_at
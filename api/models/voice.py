# api/models/voice.py
from typing import Optional
from datetime import datetime


class VoiceSample:
    """Voice sample model for personalized ASR"""
    
    def __init__(
        self,
        id: str,
        learner_id: str,
        audio_url: str,
        transcription: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        quality_score: Optional[float] = None,
        used_for_training: bool = False,
        recorded_at: Optional[datetime] = None
    ):
        self.id = id
        self.learner_id = learner_id
        self.audio_url = audio_url
        self.transcription = transcription
        self.duration_seconds = duration_seconds
        self.quality_score = quality_score
        self.used_for_training = used_for_training
        self.recorded_at = recorded_at


class ModelVersion:
    """ASR model version tracking"""
    
    def __init__(
        self,
        id: str,
        learner_id: Optional[str],
        model_type: str,  # 'speaker_dependent' or 'speaker_independent'
        base_model: str,
        training_samples_count: int,
        model_url: Optional[str] = None,
        performance_metrics: Optional[dict] = None,
        is_active: bool = False,
        training_started_at: Optional[datetime] = None,
        training_completed_at: Optional[datetime] = None
    ):
        self.id = id
        self.learner_id = learner_id
        self.model_type = model_type
        self.base_model = base_model
        self.training_samples_count = training_samples_count
        self.model_url = model_url
        self.performance_metrics = performance_metrics
        self.is_active = is_active
        self.training_started_at = training_started_at
        self.training_completed_at = training_completed_at
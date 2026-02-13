# api/models/user.py
from typing import Optional
from datetime import datetime


class User:
    """User model representing database user"""
    
    def __init__(
        self,
        id: str,
        email: str,
        full_name: str,
        role: str,
        language_preference: str = "en-KE",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.email = email
        self.full_name = full_name
        self.role = role
        self.language_preference = language_preference
        self.created_at = created_at
        self.updated_at = updated_at


class LearnerProfile:
    """Learner profile with speech impairment details"""
    
    def __init__(
        self,
        id: str,
        user_id: str,
        date_of_birth: Optional[str] = None,
        impairment_type: Optional[str] = None,
        severity_level: Optional[str] = None,
        guardian_id: Optional[str] = None,
        teacher_id: Optional[str] = None,
        personalization_enabled: bool = True,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.user_id = user_id
        self.date_of_birth = date_of_birth
        self.impairment_type = impairment_type
        self.severity_level = severity_level
        self.guardian_id = guardian_id
        self.teacher_id = teacher_id
        self.personalization_enabled = personalization_enabled
        self.created_at = created_at
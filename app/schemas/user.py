# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: Literal["learner", "teacher", "guardian"]
    language_preference: str = "en-KE"
    
    # Learner-specific fields (optional)
    impairment_type: Optional[str] = None
    severity_level: Optional[Literal["mild", "moderate", "severe"]] = None
    date_of_birth: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None


class UserResponse(UserBase):
    id: UUID
    role: str
    language_preference: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class LearnerProfile(BaseModel):
    id: UUID
    user_id: UUID
    date_of_birth: Optional[str]
    impairment_type: Optional[str]
    severity_level: Optional[str]
    guardian_id: Optional[UUID]
    teacher_id: Optional[UUID]
    personalization_enabled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
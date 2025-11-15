# app/schemas/profile.py
from typing import List, Optional
from pydantic import BaseModel, EmailStr

class ProfileBase(BaseModel):
    preferred_name: str
    age: Optional[int] = None
    language: str = "english"
    bio: Optional[str] = None
    interests: Optional[List[str]] = []
    location: Optional[str] = None
    gender: Optional[str] = None
    education_level: Optional[str] = None  # "Primary School", "Secondary School", "University/College"

class ProfileCreate(ProfileBase):
    pass  # use same fields as base for creation

class ProfileUpdate(ProfileBase):
    pass  # same fields for update

class ProfileResponse(ProfileBase):
    user_id: int

    class Config:
        orm_mode = True

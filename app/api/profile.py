from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import Profile, User
from app.schemas.profile import ProfileCreate, ProfileResponse

router = APIRouter()

@router.post("/", response_model=ProfileResponse)
def create_or_update_profile(profile: ProfileCreate, db: Session = Depends(get_db)):
    db_profile = db.query(Profile).filter(Profile.user_id == profile.user_id).first()

    interests_str = ",".join(profile.interests) if profile.interests else None

    if db_profile:
        # Update existing profile
        db_profile.preferred_name = profile.preferred_name
        db_profile.age = profile.age
        db_profile.bio = profile.bio
        db_profile.interests = interests_str
        db_profile.location = profile.location
        db_profile.gender = profile.gender
        db_profile.education_level = profile.education_level
    else:
        # Create new profile
        db_profile = Profile(
            user_id=profile.user_id,
            preferred_name=profile.preferred_name,
            age=profile.age,
            bio=profile.bio,
            interests=interests_str,
            location=profile.location,
            gender=profile.gender,
            education_level=profile.education_level
        )
        db.add(db_profile)

    db.commit()
    db.refresh(db_profile)

    # Convert interests back to list for response
    db_profile.interests = db_profile.interests.split(",") if db_profile.interests else []
    return db_profile


@router.get("/{user_id}", response_model=ProfileResponse)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.interests = profile.interests.split(",") if profile.interests else []
    return profile

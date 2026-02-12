# app/api/v1/auth.py
from fastapi import APIRouter, HTTPException, Depends, status
from api.schemas.user import UserCreate, UserLogin, Token
from api.utils.supabase_client import supabase
from api.dependencies import get_current_user
from typing import Dict, List

router = APIRouter(prefix="/auth", tags=["authentication"])

# Allowed options
LANGUAGE_OPTIONS: List[str] = ["English", "Swahili"]
IMPAIRMENT_TYPES: List[str] = [
    "Cerebral Palsy",
    "Neurodevelopmental disorders",
    "Neurological disorders",
    "Multiple Sclerosis (MS)",
    "Parkinson’s Disease",
    "Autism Spectrum Disorder (ASD)",
    "Down Syndrome"
]
SEVERITY_LEVELS: List[str] = ["Mild", "Moderate", "Severe", "Profound"]


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """Register a new user"""
    try:
        # Validate language preference
        if user_data.language_preference not in LANGUAGE_OPTIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid language preference. Must be one of {LANGUAGE_OPTIONS}"
            )
        
        # If learner, validate impairment and severity
        if user_data.role == "learner":
            if user_data.impairment_type not in IMPAIRMENT_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid impairment type. Must be one of {IMPAIRMENT_TYPES}"
                )
            if user_data.severity_level not in SEVERITY_LEVELS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid severity level. Must be one of {SEVERITY_LEVELS}"
                )
        
        # Create user in Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "full_name": user_data.full_name,
                    "role": user_data.role
                }
            }
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User registration failed"
            )
        
        user_id = auth_response.user.id
        
        # Create profile
        profile_data = {
            "id": user_id,
            "full_name": user_data.full_name,
            "role": user_data.role,
            "language_preference": user_data.language_preference
        }
        supabase.table("profiles").insert(profile_data).execute()
        
        # If learner, create learner profile
        if user_data.role == "learner":
            learner_data = {
                "user_id": user_id,
                "impairment_type": user_data.impairment_type,
                "severity_level": user_data.severity_level,
                "date_of_birth": user_data.date_of_birth
            }
            supabase.table("learner_profiles").insert(learner_data).execute()
        
        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# app/api/v1/auth.py
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import List

from api.schemas.user import UserCreate, UserLogin, Token, User as UserSchema, LearnerProfile
from api.utils.supabase_client import supabase

router = APIRouter(prefix="/auth", tags=["authentication"])

# OAuth2 dependency for extracting Bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Allowed options
LANGUAGE_OPTIONS: List[str] = ["English", "Swahili"]
IMPAIRMENT_TYPES: List[str] = [
    "Cerebral Palsy",
    "Neurodevelopmental disorders",
    "Neurological disorders",
    "Multiple Sclerosis (MS)",
    "Parkinson's Disease",
    "Autism Spectrum Disorder (ASD)",
    "Down Syndrome"
]
SEVERITY_LEVELS: List[str] = ["Mild", "Moderate", "Severe", "Profound"]

# ✅ ADD THESE MAPPING DICTIONARIES
LANGUAGE_DB_MAP = {
    "English": "en-KE",
    "Swahili": "sw"
}

SEVERITY_DB_MAP = {
    "Mild": "mild",
    "Moderate": "moderate",
    "Severe": "severe",
    "Profound": "profound"
}


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """Register a new user"""
    try:
        # Validate inputs
        if user_data.language_preference not in LANGUAGE_OPTIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid language preference. Must be one of {LANGUAGE_OPTIONS}"
            )

        if user_data.role == "learner":
            # ✅ Check required fields
            if not user_data.impairment_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Impairment type is required for learners"
                )
            if not user_data.severity_level:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Severity level is required for learners"
                )
            if not user_data.date_of_birth:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Date of birth is required for learners"
                )
            
            # Validate values
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
        auth_response = supabase.auth.sign_up(
            {
                "email": user_data.email,
                "password": user_data.password,
                "options": {"data": {"full_name": user_data.full_name, "role": user_data.role}}
            }
        )

        if not auth_response.user:
            raise HTTPException(status_code=400, detail="User registration failed")

        user_id = auth_response.user.id

        # ✅ Convert language to database format
        db_language = LANGUAGE_DB_MAP.get(user_data.language_preference, "en-KE")

        # Insert profile
        profile_data = {
            "id": user_id,
            "full_name": user_data.full_name,
            "role": user_data.role,
            "language_preference": db_language,  # ✅ Use mapped value
        }
        supabase.table("profiles").insert(profile_data).execute()

        # Insert learner profile if needed
        if user_data.role == "learner":
            # ✅ Convert severity to database format (lowercase)
            db_severity = SEVERITY_DB_MAP.get(user_data.severity_level, "moderate")
            
            learner_data = {
                "user_id": user_id,
                "impairment_type": user_data.impairment_type,
                "severity_level": db_severity,  # ✅ Use mapped value (lowercase)
                "date_of_birth": user_data.date_of_birth
            }
            supabase.table("learner_profiles").insert(learner_data).execute()

        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "token_type": "bearer"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login existing user"""
    try:
        login_response = supabase.auth.sign_in_with_password(
            {"email": user_data.email, "password": user_data.password}
        )

        if not login_response.user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {
            "access_token": login_response.session.access_token,
            "refresh_token": login_response.session.refresh_token,
            "token_type": "bearer"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=UserSchema)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get the current authenticated user"""
    # Get user info from Supabase using the token
    user_resp = supabase.auth.get_user(token)
    if not user_resp.user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Get profile from 'profiles' table
    profile_resp = supabase.table("profiles").select("*").eq("id", user_resp.user.id).single().execute()
    if profile_resp.data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    user_data = {
        "id": user_resp.user.id,
        "full_name": profile_resp.data.get("full_name"),
        "email": user_resp.user.email,
        "role": profile_resp.data.get("role"),
        "language_preference": profile_resp.data.get("language_preference"),
        "learner_profile": None
    }

    # If learner, fetch learner_profile
    if user_data["role"] == "learner":
        learner_resp = supabase.table("learner_profiles").select("*").eq("user_id", user_resp.user.id).single().execute()
        if learner_resp.data:
            user_data["learner_profile"] = LearnerProfile(
                id=learner_resp.data.get("id"),
                user_id=learner_resp.data.get("user_id"),
                date_of_birth=learner_resp.data.get("date_of_birth"),
                impairment_type=learner_resp.data.get("impairment_type"),
                severity_level=learner_resp.data.get("severity_level"),
                guardian_id=learner_resp.data.get("guardian_id"),
                teacher_id=learner_resp.data.get("teacher_id"),
                personalization_enabled=learner_resp.data.get("personalization_enabled", False),
                created_at=learner_resp.data.get("created_at")
            )

    return user_data
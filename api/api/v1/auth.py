# app/api/v1/auth.py
from fastapi import APIRouter, HTTPException, Depends, status
from api.schemas.user import UserCreate, UserLogin, Token, UserResponse
from api.utils.supabase_client import supabase
from api.dependencies import get_current_user
from typing import Dict

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """Register a new user"""
    try:
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


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Authenticate user and return tokens"""
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


@router.post("/logout")
async def logout(current_user = Depends(get_current_user)):
    """Logout current user"""
    try:
        supabase.auth.sign_out()
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=Dict)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    try:
        # Get profile
        profile = supabase.table("profiles")\
            .select("*")\
            .eq("id", current_user.id)\
            .execute()
        
        if not profile.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        user_info = profile.data[0]
        
        # If learner, get learner profile
        if user_info["role"] == "learner":
            learner_profile = supabase.table("learner_profiles")\
                .select("*")\
                .eq("user_id", current_user.id)\
                .execute()
            
            if learner_profile.data:
                user_info["learner_profile"] = learner_profile.data[0]
        
        return user_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    try:
        auth_response = supabase.auth.refresh_session(refresh_token)
        
        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
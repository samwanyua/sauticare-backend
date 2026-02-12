# app/api/v1/practice.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from api.services.asr_service import asr_service
from api.services.storage_service import StorageService
from api.utils.supabase_client import supabase
from api.dependencies import get_current_user, get_learner_profile, validate_audio_file
from api.schemas.practice import (
    PracticeSessionCreate,
    PracticeSessionResponse,
    PhraseAttemptResponse,
    TranscriptionRequest
)
from api.config import settings
from typing import List
import tempfile
import os
from datetime import datetime

router = APIRouter(prefix="/practice", tags=["practice"])
storage_service = StorageService()


@router.post("/sessions", response_model=PracticeSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_practice_session(
    session_data: PracticeSessionCreate,
    learner_profile = Depends(get_learner_profile)
):
    """Create a new practice session"""
    try:
        session = {
            "learner_id": learner_profile["id"],
            "lesson_id": str(session_data.lesson_id)
        }
        
        result = supabase.table("practice_sessions").insert(session).execute()
        
        return result.data[0]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating practice session: {str(e)}"
        )


@router.get("/sessions", response_model=List[PracticeSessionResponse])
async def get_practice_sessions(
    limit: int = 50,
    learner_profile = Depends(get_learner_profile)
):
    """Get practice sessions for current learner"""
    try:
        sessions = supabase.table("practice_sessions")\
            .select("*")\
            .eq("learner_id", learner_profile["id"])\
            .order("started_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return sessions.data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching sessions: {str(e)}"
        )


@router.post("/sessions/{session_id}/end")
async def end_practice_session(
    session_id: str,
    learner_profile = Depends(get_learner_profile)
):
    """End a practice session"""
    try:
        result = supabase.table("practice_sessions")\
            .update({"ended_at": datetime.utcnow().isoformat()})\
            .eq("id", session_id)\
            .eq("learner_id", learner_profile["id"])\
            .execute()
        
        return {
            "message": "Session ended successfully",
            "session": result.data[0] if result.data else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ending session: {str(e)}"
        )


@router.post("/attempt", response_model=PhraseAttemptResponse)
async def submit_phrase_attempt(
    session_id: str,
    phrase_id: str,
    file: UploadFile = File(...),
    learner_profile = Depends(get_learner_profile)
):
    """Submit a phrase pronunciation attempt"""
    try:
        # Validate file
        await validate_audio_file(file)
        
        # Get phrase details
        phrase = supabase.table("lesson_phrases")\
            .select("*")\
            .eq("id", phrase_id)\
            .execute()
        
        if not phrase.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Phrase not found"
            )
        
        phrase_data = phrase.data[0]
        reference_text = phrase_data["phrase_text"]
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Upload to storage
        file.file.seek(0)
        audio_url = await storage_service.upload_audio(
            file,
            bucket=settings.STORAGE_BUCKET_ATTEMPTS,
            folder=f"{learner_profile['id']}/{session_id}"
        )
        
        # Get attempt number
        attempts = supabase.table("phrase_attempts")\
            .select("attempt_number")\
            .eq("session_id", session_id)\
            .eq("phrase_id", phrase_id)\
            .order("attempt_number", desc=True)\
            .limit(1)\
            .execute()
        
        attempt_number = (attempts.data[0]["attempt_number"] + 1) if attempts.data else 1
        
        # Transcribe with ASR
        language = "english" if learner_profile.get("language_preference") == "en-KE" else "swahili"
        
        transcription, metrics = await asr_service.transcribe_with_model(
            audio_path=tmp_path,
            language=language,
            severity=learner_profile.get("severity_level", "moderate"),
            etiology=learner_profile.get("impairment_type", "none").lower().replace(" ", "_"),
            reference_text=reference_text,
            use_prompt_tuning=True,
            context_preset="daily"
        )
        
        # Calculate pronunciation score
        scores = await asr_service.calculate_pronunciation_score(
            expected_text=reference_text,
            transcribed_text=transcription,
            audio_path=tmp_path
        )
        
        # Prepare feedback
        feedback = {
            "overall": "Good" if scores["pronunciation_score"] >= 70 else "Needs improvement",
            "wer": scores["word_error_rate"],
            "cer": scores["character_error_rate"],
            "audio_quality": scores["audio_quality"],
            "metrics": metrics
        }
        
        # Save attempt
        attempt_data = {
            "session_id": session_id,
            "phrase_id": phrase_id,
            "audio_url": audio_url,
            "transcription": transcription,
            "confidence_score": scores["confidence_score"],
            "pronunciation_score": scores["pronunciation_score"],
            "feedback": feedback,
            "attempt_number": attempt_number
        }
        
        result = supabase.table("phrase_attempts").insert(attempt_data).execute()
        
        # Update session stats
        is_successful = scores["pronunciation_score"] >= 70
        
        session_update = supabase.table("practice_sessions")\
            .select("total_attempts", "successful_attempts")\
            .eq("id", session_id)\
            .execute()
        
        if session_update.data:
            current = session_update.data[0]
            supabase.table("practice_sessions")\
                .update({
                    "total_attempts": current["total_attempts"] + 1,
                    "successful_attempts": current["successful_attempts"] + (1 if is_successful else 0)
                })\
                .eq("id", session_id)\
                .execute()
        
        # Update analytics
        from datetime import date
        today = date.today().isoformat()
        
        analytics = supabase.table("learner_analytics")\
            .select("*")\
            .eq("learner_id", learner_profile["id"])\
            .eq("date", today)\
            .execute()
        
        if analytics.data:
            current_analytics = analytics.data[0]
            supabase.table("learner_analytics")\
                .update({
                    "total_attempts": current_analytics["total_attempts"] + 1,
                    "successful_attempts": current_analytics["successful_attempts"] + (1 if is_successful else 0),
                    "average_pronunciation_score": (
                        (current_analytics["average_pronunciation_score"] * current_analytics["total_attempts"] + scores["pronunciation_score"])
                        / (current_analytics["total_attempts"] + 1)
                    )
                })\
                .eq("id", current_analytics["id"])\
                .execute()
        else:
            supabase.table("learner_analytics").insert({
                "learner_id": learner_profile["id"],
                "date": today,
                "total_attempts": 1,
                "successful_attempts": 1 if is_successful else 0,
                "average_pronunciation_score": scores["pronunciation_score"]
            }).execute()
        
        # Cleanup
        os.remove(tmp_path)
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        # Cleanup on error
        if 'tmp_path' in locals():
            try:
                os.remove(tmp_path)
            except:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting attempt: {str(e)}"
        )


@router.get("/attempts/{session_id}", response_model=List[PhraseAttemptResponse])
async def get_session_attempts(
    session_id: str,
    learner_profile = Depends(get_learner_profile)
):
    """Get all attempts for a practice session"""
    try:
        # Verify session belongs to learner
        session = supabase.table("practice_sessions")\
            .select("*")\
            .eq("id", session_id)\
            .eq("learner_id", learner_profile["id"])\
            .execute()
        
        if not session.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        attempts = supabase.table("phrase_attempts")\
            .select("*")\
            .eq("session_id", session_id)\
            .order("created_at")\
            .execute()
        
        return attempts.data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching attempts: {str(e)}"
        )
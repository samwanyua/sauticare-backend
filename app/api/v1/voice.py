# app/api/v1/voice.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from app.services.asr_service import asr_service
from app.services.storage_service import StorageService
from app.utils.supabase_client import supabase
from app.dependencies import get_current_user, get_learner_profile, validate_audio_file
from app.schemas.voice import VoiceUploadResponse, VoiceSampleResponse
from app.config import settings
from typing import List
import uuid
import tempfile
import os

router = APIRouter(prefix="/voice", tags=["voice"])
storage_service = StorageService()


@router.post("/upload-sample", response_model=VoiceUploadResponse)
async def upload_voice_sample(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    learner_profile = Depends(get_learner_profile)
):
    """Upload voice sample for personalized ASR training"""
    try:
        # Validate file
        await validate_audio_file(file)
        
        learner_id = learner_profile["id"]
        
        # Save to temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Upload to Supabase Storage
        file.file.seek(0)  # Reset file pointer
        audio_url = await storage_service.upload_audio(
            file, 
            folder=str(learner_id)
        )
        
        # Transcribe with ASR
        transcription, _ = await asr_service.transcribe_with_model(
            audio_path=tmp_path,
            language="english" if learner_profile.get("language_preference") == "en-KE" else "swahili",
            severity=learner_profile.get("severity_level", "moderate"),
            etiology=learner_profile.get("impairment_type", "none").lower().replace(" ", "_"),
            reference_text=""
        )
        
        # Calculate quality score
        quality_score = await asr_service.calculate_audio_quality(tmp_path)
        
        # Get duration
        file.file.seek(0)
        duration = await storage_service.get_audio_duration(file)
        
        # Save to database
        voice_sample = {
            "learner_id": learner_id,
            "audio_url": audio_url,
            "transcription": transcription,
            "quality_score": quality_score,
            "duration_seconds": duration
        }
        
        result = supabase.table("voice_samples").insert(voice_sample).execute()
        
        # Cleanup
        os.remove(tmp_path)
        
        return {
            "message": "Voice sample uploaded successfully",
            "sample_id": result.data[0]["id"],
            "transcription": transcription,
            "audio_url": audio_url,
            "quality_score": quality_score,
            "duration_seconds": duration
        }
        
    except Exception as e:
        # Cleanup on error
        if 'tmp_path' in locals():
            try:
                os.remove(tmp_path)
            except:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading voice sample: {str(e)}"
        )


@router.get("/samples", response_model=List[VoiceSampleResponse])
async def get_voice_samples(
    limit: int = 50,
    learner_profile = Depends(get_learner_profile)
):
    """Get all voice samples for current learner"""
    try:
        samples = supabase.table("voice_samples")\
            .select("*")\
            .eq("learner_id", learner_profile["id"])\
            .order("recorded_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return samples.data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching voice samples: {str(e)}"
        )


@router.delete("/samples/{sample_id}")
async def delete_voice_sample(
    sample_id: str,
    learner_profile = Depends(get_learner_profile)
):
    """Delete a voice sample"""
    try:
        # Get sample
        sample = supabase.table("voice_samples")\
            .select("*")\
            .eq("id", sample_id)\
            .eq("learner_id", learner_profile["id"])\
            .execute()
        
        if not sample.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice sample not found"
            )
        
        # Delete from database
        supabase.table("voice_samples").delete().eq("id", sample_id).execute()
        
        return {"message": "Voice sample deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting voice sample: {str(e)}"
        )
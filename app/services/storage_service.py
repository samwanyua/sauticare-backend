# app/services/storage_service.py
from fastapi import UploadFile, HTTPException
from app.utils.supabase_client import supabase
from app.config import settings
import uuid
import os
from typing import Optional
import librosa
import soundfile as sf


class StorageService:
    """Handle file uploads to Supabase Storage"""
    
    @staticmethod
    async def upload_audio(
        file: UploadFile, 
        bucket: str = settings.STORAGE_BUCKET_AUDIO,
        folder: Optional[str] = None
    ) -> str:
        """Upload audio file to Supabase Storage"""
        try:
            # Generate unique filename
            file_extension = file.filename.split(".")[-1]
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Create path
            if folder:
                file_path = f"{folder}/{unique_filename}"
            else:
                file_path = unique_filename
            
            # Read file content
            content = await file.read()
            
            # Upload to Supabase Storage
            result = supabase.storage.from_(bucket).upload(
                file_path,
                content,
                file_options={"content-type": file.content_type}
            )
            
            # Get public URL
            public_url = supabase.storage.from_(bucket).get_public_url(file_path)
            
            return public_url
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error uploading file: {str(e)}"
            )
    
    @staticmethod
    async def get_audio_duration(file: UploadFile) -> float:
        """Calculate audio duration in seconds"""
        try:
            # Save temporarily
            temp_path = f"/tmp/{uuid.uuid4()}.{file.filename.split('.')[-1]}"
            content = await file.read()
            
            with open(temp_path, "wb") as f:
                f.write(content)
            
            # Load audio
            audio, sr = librosa.load(temp_path, sr=None)
            duration = len(audio) / sr
            
            # Cleanup
            os.remove(temp_path)
            
            # Reset file pointer
            file.file.seek(0)
            
            return duration
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error calculating audio duration: {str(e)}"
            )
    
    @staticmethod
    async def delete_file(file_path: str, bucket: str) -> bool:
        """Delete file from Supabase Storage"""
        try:
            supabase.storage.from_(bucket).remove([file_path])
            return True
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False
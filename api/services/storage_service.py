# api/services/storage_service.py
from fastapi import UploadFile, HTTPException
from api.utils.supabase_client import supabase
from api.config import settings
import uuid
import os
from typing import Optional
import librosa
import soundfile as sf
import tempfile


class StorageService:
    """Handle file uploads to Supabase Storage"""
    
    @staticmethod
    async def upload_audio(
        file: UploadFile, 
        bucket: str = None,
        folder: Optional[str] = None
    ) -> str:
        """Upload audio file to Supabase Storage"""
        if bucket is None:
            bucket = settings.STORAGE_BUCKET_AUDIO
            
        try:
            # Generate unique filename
            file_extension = file.filename.split(".")[-1] if file.filename else "wav"
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
                file_options={"content-type": file.content_type or "audio/wav"}
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
            with tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=f".{file.filename.split('.')[-1]}"
            ) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_path = temp_file.name
            
            # Load audio
            audio, sr = librosa.load(temp_path, sr=None)
            duration = len(audio) / sr
            
            # Cleanup
            os.remove(temp_path)
            
            # Reset file pointer
            file.file.seek(0)
            
            return float(duration)
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error calculating audio duration: {str(e)}"
            )
    
    @staticmethod
    async def convert_audio_format(
        input_path: str, 
        output_format: str = "wav",
        sample_rate: int = 16000
    ) -> str:
        """Convert audio to specified format"""
        try:
            # Load audio
            audio, sr = librosa.load(input_path, sr=sample_rate)
            
            # Create output path
            output_path = input_path.rsplit(".", 1)[0] + f".{output_format}"
            
            # Save in new format
            sf.write(output_path, audio, sample_rate)
            
            return output_path
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error converting audio: {str(e)}"
            )
    
    @staticmethod
    async def delete_file(file_path: str, bucket: str) -> bool:
        """Delete file from Supabase Storage"""
        try:
            # Extract just the path from full URL if needed
            if file_path.startswith("http"):
                # Extract path after bucket name
                parts = file_path.split(f"/{bucket}/")
                if len(parts) > 1:
                    file_path = parts[1]
            
            supabase.storage.from_(bucket).remove([file_path])
            return True
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False
    
    @staticmethod
    async def get_file_size(file: UploadFile) -> int:
        """Get file size in bytes"""
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        return file_size


# Singleton instance
storage_service = StorageService()
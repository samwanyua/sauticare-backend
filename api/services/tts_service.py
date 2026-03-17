# api/services/tts_service.py
from typing import Optional
import tempfile
import os
import wave
from fastapi import HTTPException
from piper import PiperVoice

class TTSService:
    """Text-to-Speech service for generating audio from text"""
    
    def __init__(self):
        self.available_voices = {
            "en-KE": "en_US-amy-low.onnx",
            "sw": "en_US-hfc_male-medium.onnx"
        }
        self.models_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "models", "piper"
        )
        self.voices = {}
        
        # Pre-load voices initialized
        for lang, model_file in self.available_voices.items():
            model_path = os.path.join(self.models_dir, model_file)
            if os.path.exists(model_path):
                try:
                    self.voices[lang] = PiperVoice.load(model_path)
                except Exception as e:
                    print(f"Failed to load piper voice {model_file}: {e}")
                    
    async def synthesize_speech(
        self,
        text: str,
        language: str = "en-KE",
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate speech from text
        """
        try:
            if language not in self.voices:
                language = "en-KE"
                
            voice = self.voices.get(language)
            if not voice:
                raise HTTPException(status_code=500, detail="Voice model not available")
                
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                output_path = temp_file.name
                temp_file.close()
                
            with wave.open(output_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2) # 16-bit
                wav_file.setframerate(voice.config.sample_rate)
                voice.synthesize(text, wav_file)
                
            return output_path
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"TTS synthesis error: {str(e)}"
            )
            
    async def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        return list(self.available_voices.keys())

# Singleton instance
tts_service = TTSService()
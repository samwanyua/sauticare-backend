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
        # We now map voices by Gender + potentially language
        self.available_voices = {
            "female": "en_US-amy-low.onnx",
            "male": "en_US-hfc_male-medium.onnx"
        }
        self.models_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "models", "piper"
        )
        # Store loaded models (Lazy Loading)
        self.voices = {}

    def _get_voice(self, gender_key: str):
        """Lazy load the voice model on first use"""
        if gender_key in self.voices:
            return self.voices[gender_key]
            
        model_file = self.available_voices.get(gender_key)
        if not model_file:
            return None
            
        model_path = os.path.join(self.models_dir, model_file)
        if os.path.exists(model_path):
            try:
                print(f"Lazy loading Piper voice model: {model_file}...")
                self.voices[gender_key] = PiperVoice.load(model_path)
                return self.voices[gender_key]
            except Exception as e:
                print(f"Failed to load piper voice {model_file}: {e}")
        return None
                    
    async def synthesize_speech(
        self,
        text: str,
        gender: str = "female",
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate speech from text
        """
        try:
            # Map choice to available keys or default
            gender_key = "female" if gender.lower() == "female" else "male"
            
            voice = self._get_voice(gender_key)
            if not voice:
                # Fallback to whatever we have if requested gender is missing
                voice = self._get_voice("female") or self._get_voice("male")
            
            if not voice:
                raise HTTPException(status_code=500, detail="No voice models loaded successfully")
                
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                output_path = temp_file.name
                temp_file.close()
                
            with wave.open(output_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2) # 16-bit
                wav_file.setframerate(voice.config.sample_rate)
                
                # Manually aggregate audio data to be safe
                audio_data = b""
                for chunk in voice.synthesize(text):
                    if hasattr(chunk, "audio_int16_bytes"):
                        audio_data += chunk.audio_int16_bytes
                    elif hasattr(chunk, "audio"):
                        audio_data += chunk.audio
                    else:
                        audio_data += bytes(chunk)
                
                wav_file.writeframes(audio_data)
                
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
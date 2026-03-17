# app/services/asr_service.py
from gradio_client import Client, handle_file
from api.config import settings
from fastapi import HTTPException
import tempfile
import os
from typing import Dict, Tuple
import librosa
import numpy as np
from jiwer import wer, cer


class ASRService:
    """ASR Service using Hugging Face Whisper model offline"""
    
    def __init__(self):
        self.local_model = None
    
    def _get_model(self):
        if self.local_model is None:
            try:
                from api.ml.whisper_model import WhisperModel
                self.local_model = WhisperModel(model_name=settings.WHISPER_MODEL_NAME)
            except Exception as e:
                print(f"Failed to load local Whisper model: {e}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Could not load ASR model: {str(e)}"
                )
        return self.local_model
    
    async def transcribe_with_model(
        self,
        audio_path: str,
        model_name: str = "whisper-small-finetuned-english",
        language: str = "english",
        etiology: str = "none",
        severity: str = "moderate",
        use_prompt_tuning: bool = True,
        context_preset: str = "medical",
        custom_prompt: str = "",
        reference_text: str = ""
    ) -> Tuple[str, Dict]:
        """
        Transcribe audio using the Hugging Face model
        
        Returns:
            Tuple of (transcription, metrics_dict)
        """
        try:
            model = self._get_model()
            
            # Load audio for local model
            audio, sr = librosa.load(audio_path, sr=16000)
            
            # Map language string
            lang_code = "en" if "english" in language.lower() or language == "en-KE" else "sw"
            
            transcription = model.transcribe(
                audio,
                sample_rate=sr,
                language=lang_code
            )
            
            # Get model confidence score
            confidence = model.get_confidence_scores(audio, sample_rate=sr)
            
            metrics = {
                "confidence": float(confidence),
                "model_used": model.model_name
            }
            
            return transcription, metrics
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"ASR transcription error: {str(e)}"
            )
    
    async def calculate_pronunciation_score(
        self,
        expected_text: str,
        transcribed_text: str,
        audio_path: str
    ) -> Dict:
        """Calculate pronunciation accuracy metrics"""
        try:
            # Text similarity metrics
            word_error_rate = wer(expected_text, transcribed_text)
            char_error_rate = cer(expected_text, transcribed_text)
            
            # Calculate accuracy (inverse of WER)
            accuracy = max(0, 1 - word_error_rate) * 100
            
            # Audio quality metrics
            audio, sr = librosa.load(audio_path, sr=16000)
            
            # Energy calculation
            energy = float(np.sum(audio ** 2) / len(audio))
            
            # Zero crossing rate
            zcr = float(np.mean(librosa.feature.zero_crossing_rate(audio)))
            
            # SNR estimation
            snr = self._estimate_snr(audio)
            
            # Overall confidence score (weighted average with actual ML model score if possible)
            # Fetch model score if we can, but since this func takes audio_path, let's grab it
            try:
                model = self._get_model()
                model_confidence = model.get_confidence_scores(audio, sample_rate=16000)
            except:
                model_confidence = 0.5

            confidence_score = (
                (1 - word_error_rate) * 0.4 +
                (1 - char_error_rate) * 0.2 +
                min(snr / 30, 1) * 0.1 +
                model_confidence * 0.3
            )
            
            return {
                "pronunciation_score": round(accuracy, 2),
                "confidence_score": round(float(confidence_score), 3),
                "word_error_rate": round(word_error_rate, 3),
                "character_error_rate": round(char_error_rate, 3),
                "audio_quality": {
                    "energy": round(energy, 6),
                    "zero_crossing_rate": round(zcr, 6),
                    "snr_db": round(snr, 2)
                }
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error calculating pronunciation score: {str(e)}"
            )
    
    def _estimate_snr(self, audio: np.ndarray) -> float:
        """Estimate Signal-to-Noise Ratio in dB"""
        signal_power = np.mean(audio ** 2)
        noise_power = np.var(audio - np.mean(audio))
        
        if noise_power == 0:
            return 100.0
        
        snr = 10 * np.log10(signal_power / noise_power)
        return float(snr)
    
    async def calculate_audio_quality(self, audio_path: str) -> float:
        """Assess audio quality (0-1 score)"""
        try:
            audio, sr = librosa.load(audio_path, sr=16000)
            
            # Duration check
            duration = len(audio) / sr
            duration_score = min(duration / 3.0, 1.0)  # Ideal: 3+ seconds
            
            # SNR check
            snr = self._estimate_snr(audio)
            snr_score = min(snr / 30.0, 1.0)  # Ideal: 30+ dB
            
            # Energy check
            energy = np.sum(audio ** 2) / len(audio)
            energy_score = min(energy * 1000, 1.0)
            
            # Weighted average
            quality = (
                duration_score * 0.3 +
                snr_score * 0.5 +
                energy_score * 0.2
            )
            
            return round(quality, 3)
            
        except Exception as e:
            return 0.5  # Default medium quality if calculation fails


# Singleton instance
asr_service = ASRService()
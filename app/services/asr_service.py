# app/services/asr_service.py
from gradio_client import Client, handle_file
from app.config import settings
from fastapi import HTTPException
import tempfile
import os
from typing import Dict, Tuple
import librosa
import numpy as np
from jiwer import wer, cer


class ASRService:
    """ASR Service using Hugging Face Whisper model"""
    
    def __init__(self):
        self.client = None
        self.hf_space = settings.HF_SPACE_NAME
    
    def _get_client(self) -> Client:
        """Get or create Gradio client"""
        if self.client is None:
            try:
                self.client = Client(self.hf_space)
            except Exception as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Could not connect to ASR service: {str(e)}"
                )
        return self.client
    
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
            client = self._get_client()
            
            # Call the Hugging Face API
            result = client.predict(
                audio_path=handle_file(audio_path),
                model_name=model_name,
                language=language,
                etiology=etiology,
                severity=severity,
                use_prompt_tuning=use_prompt_tuning,
                context_preset=context_preset,
                custom_prompt=custom_prompt,
                reference_text=reference_text,
                api_name="/process_transcription_and_update_all"
            )
            
            # Parse results
            # result is a tuple of 6 elements based on the API docs
            transcription = result[0] if result else ""
            
            # Extract metrics from other outputs
            metrics = {
                "raw_output": result[1] if len(result) > 1 else "",
                "analysis": result[2] if len(result) > 2 else "",
                "details": result[3] if len(result) > 3 else "",
                "additional": result[4] if len(result) > 4 else "",
                "performance": result[5] if len(result) > 5 else "",
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
            
            # Overall confidence score (weighted average)
            confidence_score = (
                (1 - word_error_rate) * 0.5 +
                (1 - char_error_rate) * 0.3 +
                min(snr / 30, 1) * 0.2
            )
            
            return {
                "pronunciation_score": round(accuracy, 2),
                "confidence_score": round(confidence_score, 3),
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
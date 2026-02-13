# api/ml/pronunciation_scorer.py
import numpy as np
from jiwer import wer, cer
from typing import Dict, Tuple
import librosa


class PronunciationScorer:
    """Score pronunciation accuracy"""
    
    @staticmethod
    def calculate_scores(
        reference_text: str,
        hypothesis_text: str,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> Dict:
        """
        Calculate comprehensive pronunciation scores
        
        Args:
            reference_text: Expected/correct text
            hypothesis_text: Transcribed text from ASR
            audio: Audio signal
            sample_rate: Audio sample rate
            
        Returns:
            Dictionary with various scores and metrics
        """
        # Text-based metrics
        word_error_rate = wer(reference_text, hypothesis_text)
        char_error_rate = cer(reference_text, hypothesis_text)
        
        # Calculate accuracy (inverse of WER)
        accuracy = max(0, 1 - word_error_rate) * 100
        
        # Audio quality metrics
        energy = float(np.sum(audio ** 2) / len(audio))
        zcr = float(np.mean(librosa.feature.zero_crossing_rate(audio)))
        snr = PronunciationScorer._estimate_snr(audio)
        
        # Prosody features
        pitch = PronunciationScorer._extract_pitch(audio, sample_rate)
        
        # Overall confidence score (weighted combination)
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
            },
            "prosody": {
                "mean_pitch": round(pitch["mean"], 2),
                "pitch_std": round(pitch["std"], 2)
            }
        }
    
    @staticmethod
    def _estimate_snr(audio: np.ndarray) -> float:
        """Estimate Signal-to-Noise Ratio in dB"""
        signal_power = np.mean(audio ** 2)
        noise_power = np.var(audio - np.mean(audio))
        
        if noise_power == 0:
            return 100.0
        
        snr = 10 * np.log10(signal_power / noise_power)
        return float(snr)
    
    @staticmethod
    def _extract_pitch(audio: np.ndarray, sr: int) -> Dict:
        """Extract pitch features"""
        pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
        
        # Get pitch values where magnitude is highest
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        if len(pitch_values) == 0:
            return {"mean": 0.0, "std": 0.0}
        
        return {
            "mean": float(np.mean(pitch_values)),
            "std": float(np.std(pitch_values))
        }


# Singleton instance
pronunciation_scorer = PronunciationScorer()
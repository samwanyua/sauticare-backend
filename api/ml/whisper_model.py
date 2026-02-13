# api/ml/whisper_model.py
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from typing import Optional
import numpy as np


class WhisperModel:
    """Wrapper for Whisper ASR model"""
    
    def __init__(self, model_name: str = "openai/whisper-small"):
        self.model_name = model_name
        self.processor = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    def load_model(self):
        """Load the Whisper model and processor"""
        if self.model is None:
            self.processor = WhisperProcessor.from_pretrained(self.model_name)
            self.model = WhisperForConditionalGeneration.from_pretrained(self.model_name)
            self.model.to(self.device)
    
    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None
    ) -> str:
        """Transcribe audio to text"""
        if self.model is None:
            self.load_model()
        
        # Process audio
        input_features = self.processor(
            audio,
            sampling_rate=sample_rate,
            return_tensors="pt"
        ).input_features.to(self.device)
        
        # Generate transcription
        with torch.no_grad():
            if language:
                # Force specific language
                forced_decoder_ids = self.processor.get_decoder_prompt_ids(
                    language=language,
                    task="transcribe"
                )
                predicted_ids = self.model.generate(
                    input_features,
                    forced_decoder_ids=forced_decoder_ids
                )
            else:
                predicted_ids = self.model.generate(input_features)
        
        # Decode
        transcription = self.processor.batch_decode(
            predicted_ids,
            skip_special_tokens=True
        )[0]
        
        return transcription
    
    def get_confidence_scores(self, audio: np.ndarray, sample_rate: int = 16000):
        """Get confidence scores for transcription"""
        if self.model is None:
            self.load_model()
        
        input_features = self.processor(
            audio,
            sampling_rate=sample_rate,
            return_tensors="pt"
        ).input_features.to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                input_features,
                return_dict_in_generate=True,
                output_scores=True
            )
        
        # Calculate average confidence
        scores = torch.stack(outputs.scores, dim=1)
        probs = torch.nn.functional.softmax(scores, dim=-1)
        max_probs = torch.max(probs, dim=-1).values
        avg_confidence = torch.mean(max_probs).item()
        
        return avg_confidence
# api/ml/model_trainer.py
from typing import List, Dict, Optional
import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from torch.utils.data import Dataset, DataLoader
import numpy as np


class VoiceDataset(Dataset):
    """Dataset for voice samples"""
    
    def __init__(self, audio_files: List[str], transcriptions: List[str], processor):
        self.audio_files = audio_files
        self.transcriptions = transcriptions
        self.processor = processor
    
    def __len__(self):
        return len(self.audio_files)
    
    def __getitem__(self, idx):
        import librosa
        
        # Load audio
        audio, sr = librosa.load(self.audio_files[idx], sr=16000)
        
        # Process audio
        input_features = self.processor(
            audio,
            sampling_rate=16000,
            return_tensors="pt"
        ).input_features
        
        # Process text
        labels = self.processor.tokenizer(
            self.transcriptions[idx],
            return_tensors="pt"
        ).input_ids
        
        return {
            "input_features": input_features.squeeze(),
            "labels": labels.squeeze()
        }


class ModelTrainer:
    """Fine-tune Whisper model on learner-specific data"""
    
    def __init__(self, base_model: str = "openai/whisper-small"):
        self.base_model = base_model
        self.processor = WhisperProcessor.from_pretrained(base_model)
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    def prepare_for_training(self):
        """Load and prepare model for training"""
        self.model = WhisperForConditionalGeneration.from_pretrained(self.base_model)
        self.model.to(self.device)
        self.model.train()
    
    def train(
        self,
        audio_files: List[str],
        transcriptions: List[str],
        epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 1e-5
    ) -> Dict:
        """
        Fine-tune model on provided data
        
        Args:
            audio_files: List of paths to audio files
            transcriptions: Corresponding transcriptions
            epochs: Number of training epochs
            batch_size: Batch size for training
            learning_rate: Learning rate
            
        Returns:
            Training metrics
        """
        if self.model is None:
            self.prepare_for_training()
        
        # Create dataset and dataloader
        dataset = VoiceDataset(audio_files, transcriptions, self.processor)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # Setup optimizer
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate)
        
        # Training loop
        total_loss = 0
        for epoch in range(epochs):
            epoch_loss = 0
            for batch in dataloader:
                input_features = batch["input_features"].to(self.device)
                labels = batch["labels"].to(self.device)
                
                # Forward pass
                outputs = self.model(
                    input_features=input_features,
                    labels=labels
                )
                loss = outputs.loss
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
            
            avg_epoch_loss = epoch_loss / len(dataloader)
            total_loss += avg_epoch_loss
            print(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_epoch_loss:.4f}")
        
        avg_loss = total_loss / epochs
        
        return {
            "final_loss": avg_loss,
            "epochs": epochs,
            "samples_trained": len(audio_files)
        }
    
    def save_model(self, output_path: str):
        """Save fine-tuned model"""
        if self.model:
            self.model.save_pretrained(output_path)
            self.processor.save_pretrained(output_path)
    
    def evaluate(self, audio_files: List[str], transcriptions: List[str]) -> Dict:
        """Evaluate model performance"""
        self.model.eval()
        
        from jiwer import wer
        
        total_wer = 0
        predictions = []
        
        with torch.no_grad():
            for audio_file, reference in zip(audio_files, transcriptions):
                import librosa
                
                # Load and process audio
                audio, sr = librosa.load(audio_file, sr=16000)
                input_features = self.processor(
                    audio,
                    sampling_rate=16000,
                    return_tensors="pt"
                ).input_features.to(self.device)
                
                # Generate prediction
                predicted_ids = self.model.generate(input_features)
                prediction = self.processor.batch_decode(
                    predicted_ids,
                    skip_special_tokens=True
                )[0]
                
                predictions.append(prediction)
                
                # Calculate WER
                total_wer += wer(reference, prediction)
        
        avg_wer = total_wer / len(audio_files)
        accuracy = (1 - avg_wer) * 100
        
        return {
            "word_error_rate": round(avg_wer, 3),
            "accuracy": round(accuracy, 2),
            "num_samples": len(audio_files),
            "predictions": predictions
        }


# Singleton instance
model_trainer = ModelTrainer()
from faster_whisper import WhisperModel as FastWhisper
import os

class WhisperModel:
    def __init__(self, model_name="base.en"):
        # We use a base model to balance speed, memory, and transcription accuracy
        self.model_name = "base.en"
        print(f"Loading faster-whisper model: {self.model_name}")
        self.model = FastWhisper(self.model_name, device="cpu", compute_type="int8")
        
    def transcribe(self, audio, sample_rate=16000, language="en"):
        # faster-whisper can take a path or numpy array
        # we will use the local path when possible
        segments, info = self.model.transcribe(audio, beam_size=5, language=language)
        transcription = " ".join([segment.text for segment in segments])
        return transcription.strip()
        
    def get_confidence_scores(self, audio, sample_rate=16000):
        # We can simulate confidence using the faster-whisper segment probabilities
        # but for simplicity since we want one score, we will transcribe and average
        segments, info = self.model.transcribe(audio, beam_size=5)
        # return average confidence
        probs = [segment.no_speech_prob for segment in segments]
        if not probs:
            return 0.5
        # confidence is inverse of no_speech_prob
        avg_confidence = 1 - (sum(probs) / len(probs))
        return float(avg_confidence)
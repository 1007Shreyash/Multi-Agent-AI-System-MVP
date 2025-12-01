# Developed by Shreyash Chougule
# Project: Agentic AI MVP - Whisper Agent (Powered by Groq)

import os
from groq import Groq

class WhisperAgent:
    def __init__(self, api_key=None):
        """
        Initialize the WhisperAgent with a Groq API key.
        Using Groq for faster, free-tier friendly transcription.
        """
        if api_key is None:
            raise ValueError("Groq API key is required for WhisperAgent")
        
        self.client = Groq(api_key=api_key)

    def transcribe_audio(self, audio_file_path):
        """
        Transcribes audio using the Whisper-large-v3 model on Groq.
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-large-v3", 
                    file=audio_file,
                    response_format="json"
                )
            
            return {
                "status": "success",
                "transcription": transcription.text
            }
        except Exception as e:
            print(f"Error in WhisperAgent (Groq): {e}")
            return {"status": "error", "message": str(e)}
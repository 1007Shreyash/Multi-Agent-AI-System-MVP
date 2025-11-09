# Developed by Shreyash Chougule
# Email: shreyash.v.chougule1903@gmail.com
# Project: Multi-Agent AI System (MVP)

import os
from openai import OpenAI

class WhisperAgent:
    def __init__(self, api_key=None):
        """
        Initialize the WhisperAgent with an OpenAI API key.
        """
        if api_key is None:
            raise ValueError("OpenAI API key is required for WhisperAgent")
        
        # Initialize the OpenAI client *only* for transcription
        self.client = OpenAI(api_key=api_key)

    def transcribe_audio(self, audio_file_path):
        """
        Transcribes audio using the Whisper-1 model.
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            
            return {
                "status": "success",
                "transcription": transcription.text
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
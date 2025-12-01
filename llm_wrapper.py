# Developed by Shreyash Chougule
# Project: Agentic AI MVP - LLM Wrapper (Gemini -> Groq)

from groq import Groq

class FakeGeminiResponse:
    """Mimics the response object from Google Gemini"""
    def __init__(self, text):
        self.text = text

class LLMWrapper:
    """
    A wrapper that makes Groq look and act exactly like the Gemini SDK.
    This allows us to switch LLMs without rewriting all our agents.
    """
    def __init__(self, api_key, model_name="llama3-70b-8192", system_instruction=None):
        self.client = Groq(api_key=api_key)
        self.model_name = model_name
        self.system_instruction = system_instruction

    def generate_content(self, prompt, generation_config=None, safety_settings=None):
        """
        Mimics model.generate_content() but calls Groq Llama 3.
        """
        messages = []
        
        # Add system instruction if it exists
        if self.system_instruction:
            messages.append({"role": "system", "content": self.system_instruction})
            
        # Add user prompt
        messages.append({"role": "user", "content": prompt})

        try:
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                temperature=0.1, # Keep it precise for JSON
            )
            
            content = chat_completion.choices[0].message.content
            return FakeGeminiResponse(content)
            
        except Exception as e:
            return FakeGeminiResponse(f"Error calling Groq: {str(e)}")
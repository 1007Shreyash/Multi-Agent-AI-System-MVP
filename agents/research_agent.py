# Developed by Shreyash Chougule
# Email: shreyash.v.chougule1903@gmail.com
# Project: Multi-Agent AI System (MVP)

import google.generativeai as genai

class ResearchAgent:
    def __init__(self, model):
        """
        Initialize the agent with a Gemini model.
        """
        self.model = model

    def handle_task(self, user_request, safety_settings):
        """
        Generates a direct response to a research-related request.
        """
        prompt = f"""
        You are an autonomous research assistant. Your goal is to EXECUTE the user's request, not ask for clarification.

        User Request: '{user_request}'

        Your task:
        1.  Analyze the request.
        2.  If the request is clear (e.g., 'what are the latest AI frameworks'), provide a detailed, comprehensive answer.
        3.  If the request is VAGUE (e.g., 'tell me about AI'), you must CHOOSE a good, high-level topic (like 'What is AI and its main branches?') and provide a full answer.
        
        **Do not ask for more information.** Just perform the task.
        Provide *only* the research findings.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                safety_settings=safety_settings
            )
            
            # Add a header for clarity in the UI
            return f"🔍 **Research Agent:**\n\n{response.text}"
        except Exception as e:
            return f"❌ Error in Research Agent: {str(e)}"
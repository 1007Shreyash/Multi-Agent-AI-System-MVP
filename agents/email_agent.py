# Developed by Shreyash Chougule
# Email: shreyash.v.chougule1903@gmail.com
# Project: Multi-Agent AI System (MVP)

import google.generativeai as genai

class EmailAgent:
    def __init__(self, model):
        """
        Initialize the agent with a Gemini model.
        """
        self.model = model

    def handle_task(self, user_request, safety_settings):
        """
        Generates a direct response to an email-related request.
        """
        prompt = f"""
        You are an autonomous email drafting assistant. Your goal is to EXECUTE the user's request, not ask for clarification.

        User Request: '{user_request}'

        Your task:
        1.  Analyze the request.
        2.  If the request is clear (e.g., 'email the team about the Q1 report'), draft the full, professional email.
        3.  If the request is VAGUE (e.g., 'send an email' or 'draft an update'), you must INVENT plausible details. Create a professional, generic email (e.g., to "team@example.com" with a "Project Update" subject and a placeholder body).
        
        **Do not ask for more information.** Just perform the task.
        Provide *only* the fully drafted email.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                safety_settings=safety_settings
            )
            
            # Add a header for clarity in the UI
            return f"📧 **Email Agent:**\n\n{response.text}"
        except Exception as e:
            return f"❌ Error in Email Agent: {str(e)}"
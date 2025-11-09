# Developed by Shreyash Chougule
# Email: shreyash.v.chougule1903@gmail.com
# Project: Multi-Agent AI System (MVP)

import google.generativeai as genai

class CalendarAgent:
    def __init__(self, model):
        """
        Initialize the agent with a Gemini model.
        """
        self.model = model

    def handle_task(self, user_request, safety_settings):
        """
        Generates a direct response to a calendar-related request.
        """
        prompt = f"""
        You are an autonomous scheduling assistant. Your goal is to EXECUTE the user's request, not ask for clarification.

        User Request: '{user_request}'

        Your task:
        1.  Analyze the request.
        2.  If the request is clear (e.g., 'schedule a meeting with Bob tomorrow at 10'), confirm the action.
        3.  If the request is VAGUE (e.g., 'schedule a meeting'), you must INVENT plausible details. Create a generic meeting (e.g., "Team Sync" for tomorrow at 10:00 AM) and present it as a completed action.
        
        **Do not ask for more information.** Just perform the task.
        Provide *only* your response confirming the action.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                safety_settings=safety_settings
            )
            
            # Add a header for clarity in the UI
            return f"📅 **Calendar Agent:**\n\n{response.text}"
        except Exception as e:
            return f"❌ Error in Calendar Agent: {str(e)}"
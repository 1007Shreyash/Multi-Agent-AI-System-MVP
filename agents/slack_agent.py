# Developed by Shreyash Chougule
# Email: shreyash.v.chougule1903@gmail.com
# Project: Multi-Agent AI System (MVP)

import google.generativeai as genai

class SlackAgent:
    def __init__(self, model):
        """
        Initialize the agent with a Gemini model.
        """
        self.model = model

    def handle_task(self, user_request, safety_settings):
        """
        Generates a direct response to a slack/communication-related request.
        """
        prompt = f"""
        You are an autonomous team communication assistant. Your goal is to EXECUTE the user's request, not ask for clarification.

        User Request: '{user_request}'

        Your task:
        1.  Analyze the request.
        2.  If the request is clear (e.g., 'tell #general we are pushing the update'), draft the professional message.
        3.  If the request is VAGUE (e.g., 'send a message'), you must INVENT plausible details. Create a generic message (e.g., a "Team Update" to the "#general" channel).
        
        **Do not ask for more information.** Just perform the task.
        Provide *only* the drafted message.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                safety_settings=safety_settings
            )
            
            # Add a header for clarity in the UI
            return f"💬 **Slack Agent:**\n\n{response.text}"
        except Exception as e:
            return f"❌ Error in Slack Agent: {str(e)}"
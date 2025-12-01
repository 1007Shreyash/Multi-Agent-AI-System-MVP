# Developed by Shreyash Chougule
# Email: shreyash.v.chougule1903@gmail.com
# Project: Multi-Agent AI System (MVP)

import google.generativeai as genai

class NotionAgent:
    def __init__(self, model):
        """
        Initialize the agent with a Gemini model.
        """
        self.model = model

    def handle_task(self, user_request, safety_settings):
        """
        Generates a direct response to a notion/notes-related request.
        """
        prompt = f"""
        You are a helpful note-taking and knowledge-base assistant. A user has made the following request:
        '{user_request}'

        Your task is to:
        1.  Analyze the request.
        2.  Generate a well-structured page or set of notes based on the request.
        3.  Use Markdown for formatting (e.g., headers, bullet points).
        4.  If the request is vague, ask for clarifying details.
        
        Provide *only* the formatted notes or your clarifying questions.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                safety_settings=safety_settings
            )
            
            # Add a header for clarity in the UI
            return f"📝 **Notion Agent:**\n\n{response.text}"
        except Exception as e:
            return f"❌ Error in Notion Agent: {str(e)}"
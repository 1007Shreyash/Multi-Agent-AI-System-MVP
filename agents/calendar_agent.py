# Developed by Shreyash Chougule
# Project: Agentic AI MVP

import json
from datetime import datetime, timedelta

class CalendarAgent:
    def __init__(self, model, calendar_manager=None):
        self.model = model
        self.calendar_manager = calendar_manager

    def handle_task(self, user_request, safety_settings):
        """
        1. Extracts parameters (Title, Time) using Gemini.
        2. Calls the Real Google Calendar API.
        """
        # Get current time for context
        now = datetime.now().isoformat()
        
        prompt = f"""
        You are a scheduling assistant. 
        User Request: '{user_request}'
        Current Time: {now}

        Task: Extract event details.
        
        Return JSON ONLY:
        {{
            "summary": "Meeting Title",
            "start_time": "YYYY-MM-DDTHH:MM:SS" (Calculate exact future date based on 'tomorrow', 'next friday', etc.),
            "duration": 60 (default to 60 unless specified)
        }}
        """
        
        try:
            # 1. Ask Gemini to interpret the date/time
            response = self.model.generate_content(prompt, safety_settings=safety_settings)
            
            clean_text = response.text.strip()
            if clean_text.startswith("```json"): clean_text = clean_text[7:]
            if clean_text.endswith("```"): clean_text = clean_text[:-3]
            
            event_data = json.loads(clean_text)
            
            # 2. Execute Real API Call
            if self.calendar_manager:
                result = self.calendar_manager.create_event(
                    event_data.get("summary", "New Event"),
                    event_data.get("start_time"),
                    event_data.get("duration", 60)
                )
                return f"📅 **Calendar Agent:**\n\n{result}"
            else:
                return "⚠️ **System:** Calendar Manager not connected."
                
        except Exception as e:
            return f"❌ Error in Calendar Agent: {str(e)}"
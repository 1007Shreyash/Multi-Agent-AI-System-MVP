# Developed by Shreyash Chougule
# Project: Agentic AI MVP - Real Google Calendar Integration

from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

class CalendarManager:
    def __init__(self, service_account_info):
        """
        Connects to Google Calendar API using Service Account.
        """
        scopes = ['https://www.googleapis.com/auth/calendar']
        creds = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=scopes
        )
        self.service = build('calendar', 'v3', credentials=creds)
        
        # Get specific calendar ID from secrets, default to primary
        self.calendar_id = service_account_info.get("calendar_id", "primary")

    def create_event(self, summary, start_time_str, duration_minutes=60):
        """
        Creates a real event and returns a PUBLIC verification link.
        """
        try:
            # 1. Clean the time string
            clean_time_str = start_time_str.replace("Z", "")
            
            # 2. Parse time
            start_dt = datetime.fromisoformat(clean_time_str)
            end_dt = start_dt + timedelta(minutes=duration_minutes)
            
            # 3. Define Timezone
            user_timezone = 'Asia/Kolkata' 

            event = {
                'summary': summary,
                'description': "Scheduled by Agentic AI",
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': user_timezone,
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': user_timezone,
                },
            }

            self.service.events().insert(
                calendarId=self.calendar_id, 
                body=event
            ).execute()
            
            formatted_time = start_dt.strftime('%I:%M %p')
            
            # --- THE MAGIC LINK ---
            # We build the link automatically using your ID. 
            # ctz=Asia/Kolkata ensures the recruiter sees the time in YOUR timezone (IST).
            public_link = f"https://calendar.google.com/calendar/embed?src={self.calendar_id}&mode=WEEK&ctz=Asia/Kolkata"
            
            return f"✅ **Success!** Event created for {formatted_time}.\n👀 **Verify here:** [Live Demo Calendar]({public_link})"
        
        except Exception as e:
            return f"❌ Calendar Error: {str(e)}"
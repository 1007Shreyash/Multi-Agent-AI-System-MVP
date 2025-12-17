# Developed by Shreyash Chougule
# Project: Agentic AI MVP - Intelligent Email Agent

import json
import re

class EmailAgent:
    def __init__(self, model, email_manager=None):
        self.model = model
        self.email_manager = email_manager

    def format_for_email(self, text):
        if not text: return ""
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        text = text.replace("\n", "<br>")
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'#{1,6}\s+(.*?)(<br>|$)', r'<h3>\1</h3>', text)
        text = re.sub(r'(<br>|^)\s*\*\s', r'\1 &bull; ', text)
        return f"""<div style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">{text}</div>"""

    def handle_task(self, user_request, safety_settings):
        if not self.email_manager:
            return "⚠️ **System:** Email Manager not connected. Check secrets."

        prompt = f"""
        You are an intelligent Email Assistant.
        INPUT CONTEXT: '{user_request}'
        
        TASK: Determine action ("READ" or "SEND").
        
        IF SENDING:
        - Analyze the "CONTEXT FROM PREVIOUS STEPS" (if available).
        - EXTRACT only the relevant info.
        - Write a clean, natural email body.
        - Recipient: If the user says "team", use "team@placeholder.com".
        
        CRITICAL JSON RULES:
        1. Return Valid JSON.
        2. Escape all newlines in the body with \\n.
        
        Return JSON ONLY: 
        {{ 
            "action": "SEND",
            "to_email": "recipient@example.com", 
            "subject": "Subject...",
            "body": "Full email body..."
        }}
        OR {{ "action": "READ" }}
        """
        
        try:
            response = self.model.generate_content(prompt, safety_settings=safety_settings)
            
            # --- FIX: Check for Empty Response ---
            if not response or not response.text:
                return "⚠️ **Email Agent Error:** The AI returned an empty response. Please try again."

            text = response.text.strip()
            
            # Clean Markdown wrappers
            if text.startswith("```"):
                start = text.find("{")
                end = text.rfind("}") + 1
                if start != -1 and end != -1: text = text[start:end]
            
            # --- FIX: Handle Empty Parsed Text ---
            if not text:
                return "⚠️ **Email Agent Error:** Could not extract JSON from AI response."

            try:
                data = json.loads(text, strict=False)
            except json.JSONDecodeError:
                # If JSON fails, return the raw text so you at least see what happened
                return f"⚠️ **Email Parsing Error:** The AI did not return valid JSON.\nRaw Output: {text[:100]}..."

            action = data.get("action")
            
            if action == "READ":
                emails = self.email_manager.get_unread_emails(limit=5)
                return f"📬 **Inbox Summary:**\n\n{emails}"
            
            elif action == "SEND":
                to_email = data.get("to_email")
                
                if "example.com" in to_email or "placeholder.com" in to_email:
                    to_email = self.email_manager.email 
                    note = "_(Redirected to your email)_"
                else:
                    note = ""

                raw_body = data.get("body", "No content")
                html_body = self.format_for_email(raw_body)

                result = self.email_manager.send_email(to_email, data.get("subject"), html_body)
                
                return f"📧 **Email Agent:**\n\n{result} {note}\n\n**Draft Sent:**\n> {raw_body[:200]}..."
            
            else:
                return f"❌ Could not determine email action."

        except Exception as e:
            return f"⚠️ Critical Email Error: {str(e)}"

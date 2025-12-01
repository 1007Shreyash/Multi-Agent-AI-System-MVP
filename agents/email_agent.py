# Developed by Shreyash Chougule
# Project: Agentic AI MVP - Intelligent Email Agent

import json
import re

class EmailAgent:
    def __init__(self, model, email_manager=None):
        self.model = model
        self.email_manager = email_manager

    def format_for_email(self, text):
        """
        Converts Markdown (from AI) to HTML (for Gmail).
        This ensures the email looks professional.
        """
        # 1. Escape HTML first
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # 2. Convert Newlines to <br> (Critical for Email)
        text = text.replace("\n", "<br>")
        
        # 3. Convert **Bold** to <b>Bold</b>
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # 4. Convert Headers (###) to <h3>
        text = re.sub(r'#{1,6}\s+(.*?)(<br>|$)', r'<h3>\1</h3>', text)
        
        # 5. Convert Bullet Points (* ) to HTML lists
        # Simple replacement for visual clarity
        text = re.sub(r'(<br>|^)\s*\*\s', r'\1 &bull; ', text)
        
        # 6. Wrap in a nice font div
        return f"""
        <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
            {text}
        </div>
        """

    def handle_task(self, user_request, safety_settings):
        if not self.email_manager:
            return "⚠️ **System:** Email Manager not connected. Check secrets."

        prompt = f"""
        You are an intelligent Email Assistant.
        INPUT CONTEXT: '{user_request}'
        
        TASK: Determine action ("READ" or "SEND").
        
        IF SENDING:
        - LOOK for "HISTORY OF PREVIOUS STEPS" in the input. That is the content you must email.
        - Create a subject line based on that content.
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
            text = response.text.strip()
            if text.startswith("```"):
                start = text.find("{")
                end = text.rfind("}") + 1
                if start != -1 and end != -1: text = text[start:end]
            
            data = json.loads(text, strict=False)
            action = data.get("action")
            
            if action == "READ":
                emails = self.email_manager.get_unread_emails(limit=5)
                return f"📬 **Inbox Summary:**\n\n{emails}"
            
            elif action == "SEND":
                to_email = data.get("to_email")
                
                # Smart Recipient Replacement
                if "example.com" in to_email or "placeholder.com" in to_email:
                    to_email = self.email_manager.email 
                    note = "_(Redirected to your email)_"
                else:
                    note = ""

                # --- FIX: Format Body as HTML ---
                raw_body = data.get("body")
                html_body = self.format_for_email(raw_body)

                result = self.email_manager.send_email(
                    to_email,
                    data.get("subject"),
                    html_body # Send the formatted HTML
                )
                
                return f"📧 **Email Agent:**\n\n{result} {note}\n\n**Draft Sent:**\n> {raw_body[:200]}..."
            
            else:
                return f"❌ Could not determine email action."

        except Exception as e:
            return f"⚠️ Email Error (JSON): {e}"
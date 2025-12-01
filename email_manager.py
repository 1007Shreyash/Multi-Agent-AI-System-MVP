# Developed by Shreyash Chougule
# Project: Agentic AI MVP - Real Gmail Integration (IMAP/SMTP)

import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.header import decode_header

class EmailManager:
    def __init__(self, email_address, app_password):
        """
        Handles Real Email Sending (SMTP) and Reading (IMAP).
        """
        self.email = email_address
        self.password = app_password
        self.smtp_server = "smtp.gmail.com"
        self.imap_server = "imap.gmail.com"

    def send_email(self, to_email, subject, body):
        """
        Sends a real email using SMTP.
        FIX: Sends as 'html' so bold/formatting works.
        """
        try:
            # --- FIX: Set subtype to 'html' ---
            msg = MIMEText(body, 'html')
            msg['Subject'] = subject
            msg['From'] = self.email
            msg['To'] = to_email

            with smtplib.SMTP_SSL(self.smtp_server, 465) as server:
                server.login(self.email, self.password)
                server.send_message(msg)
            
            return f"✅ **Success!** Email sent to {to_email}"
        except Exception as e:
            return f"❌ Email Send Error: {str(e)}"

    def get_unread_emails(self, limit=5):
        """
        Fetches the last N unread emails from the inbox.
        """
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email, self.password)
            mail.select("inbox")

            status, messages = mail.search(None, 'UNSEEN')
            if status != "OK": return "No unread emails found."

            email_ids = messages[0].split()
            latest_ids = email_ids[-limit:]
            
            summaries = []
            
            for e_id in reversed(latest_ids):
                _, msg_data = mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                        
                        sender = msg.get("From")
                        
                        body = "No text content"
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode()
                            
                        snippet = body.strip()[:100].replace("\n", " ")
                        summaries.append(f"📧 **From:** {sender}\n**Subject:** {subject}\n**Snippet:** {snippet}...\n")

            mail.close()
            mail.logout()
            
            if not summaries:
                return "📭 Inbox is clear! No unread emails."
            
            return "\n".join(summaries)

        except Exception as e:
            return f"❌ Email Read Error: {str(e)}"
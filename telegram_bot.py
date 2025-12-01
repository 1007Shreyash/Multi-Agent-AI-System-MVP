# Developed by Shreyash Chougule
# Project: Agentic AI MVP - Telegram Interface

import os
import re
import telebot
import toml
from pathlib import Path

# Import your existing system
from agents.parent_agent import ParentAgent
from notion_manager import NotionManager
from agents.whisper_agent import WhisperAgent
from email_manager import EmailManager
from calendar_manager import CalendarManager # <--- Make sure this is imported

# 1. Load Secrets
try:
    secrets_path = Path(".streamlit/secrets.toml")
    secrets = toml.load(secrets_path)
    print("✅ Secrets loaded successfully.")
except Exception as e:
    print(f"❌ Error loading secrets: {e}")
    exit()

BOT_TOKEN = secrets["telegram_bot_token"]
ALLOWED_USER_ID = str(secrets["telegram_allowed_user_id"])

# 2. Initialize Bot
bot = telebot.TeleBot(BOT_TOKEN)

try:
    # A. Notion
    db = NotionManager(
        api_key=secrets["notion_api_key"],
        task_db_id=secrets["notion_task_db_id"],
        xp_db_id=secrets["notion_xp_db_id"]
    )
    print("✅ Notion connected.")
    
    # B. Whisper (Groq)
    whisper_agent = WhisperAgent(api_key=secrets["groq_api_key"])
    print("✅ Whisper connected.")

    # C. Google Calendar (THIS WAS MISSING IN YOUR SNIPPET)
    calendar_manager = None
    if "google_calendar" in secrets:
        try:
            cal_creds = dict(secrets["google_calendar"])
            calendar_manager = CalendarManager(cal_creds)
            print("✅ Google Calendar connected.")
        except Exception as e:
            print(f"❌ Calendar Connection Failed: {e}")
    else:
        print("⚠️ WARNING: [google_calendar] section missing in secrets.")

    # D. Email Manager
    email_manager = None
    if "email" in secrets:
        try:
            email_manager = EmailManager(
                secrets["email"]["email_address"],
                secrets["email"]["app_password"]
            )
            print("✅ Gmail connected.")
        except Exception as e:
            print(f"❌ Email Connection Failed: {e}")    

    # E. Parent Agent (The Brain)
    parent_agent = ParentAgent(
        db=db,
        user_id="telegram_user",
        
        # --- FIX: PASS GROQ KEY HERE ---
        google_api_key=secrets["groq_api_key"], 
        # (We call it google_api_key in the init to keep the class compatible, 
        # but inside ParentAgent it now feeds the LLMWrapper which expects a Groq key)
        
        calendar_manager=calendar_manager,
        email_manager=email_manager 
    )
    
    print("✅ System fully initialized.")
except Exception as e:
    print(f"❌ Initialization Error: {e}")

print("🤖 Telegram Bot is running... (Press Ctrl+C to stop)")

# --- HELPER: Advanced HTML Formatter ---
def format_for_telegram(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r'#{1,6}\s+(.*?)\n', r'<b>\1</b>\n', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?<!\*)\*(.*?)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    text = re.sub(r'^\s*\*\s', '• ', text, flags=re.MULTILINE)
    return text

# --- HELPER: Smart Splitter ---
def send_long_message(chat_id, text):
    max_length = 4000
    current_chunk = ""
    lines = text.split('\n')

    for line in lines:
        if len(current_chunk) + len(line) + 1 < max_length:
            current_chunk += line + "\n"
        else:
            if current_chunk:
                send_safe_chunk(chat_id, current_chunk)
            current_chunk = line + "\n"

    if current_chunk:
        send_safe_chunk(chat_id, current_chunk)

def send_safe_chunk(chat_id, text):
    formatted_text = format_for_telegram(text)
    try:
        bot.send_message(chat_id, formatted_text, parse_mode="HTML")
    except Exception as e:
        print(f"⚠️ Telegram HTML Error: {e}") 
        bot.send_message(chat_id, text)

# --- SECURITY CHECK ---
def is_authorized(message):
    user_id = str(message.from_user.id)
    if user_id != ALLOWED_USER_ID:
        print(f"⚠️ Unauthorized access attempt from ID: {user_id}")
        bot.reply_to(message, f"⛔ Access Denied. Your ID: {user_id}")
        return False
    return True

# --- HANDLERS ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if is_authorized(message):
        bot.reply_to(message, "👋 System Online. Send text or voice to add tasks to Notion.")

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    if not is_authorized(message): return

    try:
        print(f"🎤 Received voice message from {message.from_user.first_name}")
        bot.reply_to(message, "👂 Listening...")
        
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_path = f"voice_{message.message_id}.ogg"
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        transcription = whisper_agent.transcribe_audio(file_path)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        if transcription["status"] == "success":
            user_text = transcription["transcription"]
            bot.reply_to(message, f"🗣️ **You said:** {user_text}")
            process_request(message, user_text)
        else:
            error_msg = transcription.get('message', 'Unknown error')
            print(f"❌ Whisper Error: {error_msg}")
            bot.reply_to(message, f"❌ Transcription Error: {error_msg}")
            
    except Exception as e:
        print(f"❌ Voice Handling Error: {e}")
        bot.reply_to(message, f"❌ Voice Handling Error: {e}")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if is_authorized(message):
        process_request(message, message.text)

def process_request(message, text):
    print(f"📥 Processing: '{text}'")
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        response = parent_agent.handle_request(text)
        print("✅ Agent response received.")
        send_long_message(message.chat.id, response)
        print("📤 Reply sent to Telegram.")
        
    except Exception as e:
        error_msg = f"❌ Error processing request: {str(e)}"
        print(error_msg)
        bot.reply_to(message, error_msg)

# --- START POLLING ---
bot.infinity_polling()
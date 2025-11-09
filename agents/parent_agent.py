# Developed by Shreyash Chougule
# Email: shreyash.v.chougule1903@gmail.com
# Project: Multi-Agent AI System (MVP)

import os
import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from agents.context_manager import ContextManager
from agents.xp_agent import XPAgent
from agents.email_agent import EmailAgent
from agents.research_agent import ResearchAgent
from agents.report_agent import ReportAgent
from agents.paei_personality import PAEIPersonality
from agents.calendar_agent import CalendarAgent
from agents.notion_agent import NotionAgent
from agents.slack_agent import SlackAgent

class ParentAgent:
    def __init__(self, db=None, user_id=None, google_api_key=None):
        if google_api_key:
            genai.configure(api_key=google_api_key)
        
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        
        self.db = db
        self.user_id = user_id
        
        self.context_manager = ContextManager()
        self.xp_agent = XPAgent(db=db, user_id=user_id)
        
        self.email_agent = EmailAgent(model=self.model)
        self.research_agent = ResearchAgent(model=self.model)
        self.report_agent = ReportAgent(model=self.model, db=db, user_id=user_id)
        
        self.paei_personality = PAEIPersonality(db=db, user_id=user_id)
        
        self.calendar_agent = CalendarAgent(model=self.model)
        self.notion_agent = NotionAgent(model=self.model)
        self.slack_agent = SlackAgent(model=self.model)
        
        # Set safety settings to be less restrictive
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        # Generation config to ensure JSON output where needed
        self.json_generation_config = genai.GenerationConfig(
            response_mime_type="application/json"
        )

    def handle_request(self, user_input):
        try:
            # Get the context *before* the task (used for intent)
            context = self.context_manager.get_context()
            
            intent = self._analyze_intent(user_input, context)
            
            # Handle potential failure in intent analysis
            if intent.get("agent") is None or "Error" in intent.get("reasoning", ""):
                result = self._handle_general(user_input)
                intent["agent"] = "general"
                xp_earned = self.xp_agent.calculate_xp_for_task("simple")
            
            elif intent["agent"] == "email":
                result = self._handle_email(user_input)
                xp_earned = self.xp_agent.calculate_xp_for_task("email")
            elif intent["agent"] == "research":
                result = self._handle_research(user_input)
                xp_earned = self.xp_agent.calculate_xp_for_task("research")
            elif intent["agent"] == "report":
                result = self._handle_report() 
                xp_earned = self.xp_agent.calculate_xp_for_task("report")
            elif intent["agent"] == "calendar":
                result = self._handle_calendar(user_input)
                xp_earned = self.xp_agent.calculate_xp_for_task("complex")
            elif intent["agent"] == "notion":
                result = self._handle_notion(user_input)
                xp_earned = self.xp_agent.calculate_xp_for_task("complex")
            elif intent["agent"] == "slack":
                result = self._handle_slack(user_input)
                xp_earned = self.xp_agent.calculate_xp_for_task("email")
            else: 
                result = self._handle_general(user_input)
                xp_earned = self.xp_agent.calculate_xp_for_task("simple")
            
            xp_info = self.xp_agent.add_xp(xp_earned, intent["agent"])
            
            # Now, update the context *after* the task is done
            self.context_manager.update_context(intent["agent"])
            # Get the *new* context to display in the response
            updated_context = self.context_manager.get_context()
            
            response = self._compile_response(result, xp_info, updated_context) # <-- Uses new context
            
            if self.db and self.user_id:
                self.db.log_chat(self.user_id, user_input, response, intent["agent"])
                self.db.update_agent_metrics(self.user_id, intent["agent"], xp_earned)
            
            return response
            
        except Exception as e:
            return f"❌ Error: {str(e)}\n\nPlease try again or rephrase your request."

    def _analyze_intent(self, user_input, context):
        prompt = f"""Analyze this user request and determine which agent should handle it:
User Input: "{user_input}"
Context: Energy Level {context['energy_level']}/1G0, Flow State: {context['flow_state']}

Agents available:
- "email": For drafting, sending, or managing emails
- "research": For searching information, finding resources, or investigating topics
- "report": For generating reports, summaries, or performance analytics
- "calendar": For scheduling events, managing calendar, or checking availability
- "notion": For creating notes, pages, or managing knowledge base
- "slack": For sending messages, team communication, or notifications
- "general": For general questions or tasks not fitting other categories

Respond in JSON format with:
- "agent": the agent name to use
- "parameters": any extracted details (like recipient, subject, query, etc.)
- "reasoning": brief explanation of why this agent was chosen"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.json_generation_config,
                safety_settings=self.safety_settings
            )
            
            clean_json = response.text.strip().replace("```json", "").replace("```", "")
            intent_data = json.loads(clean_json)
            
            if "agent" not in intent_data or intent_data["agent"] not in ["email", "research", "report", "calendar", "notion", "slack", "general"]:
                intent_data["agent"] = "general"
                intent_data["reasoning"] = "LLM returned invalid or no agent, defaulting to general."

            return intent_data
        except Exception as e:
            return {
                "agent": "general",
                "parameters": {},
                "reasoning": f"Error in intent analysis: {str(e)}"
            }

    def _handle_email(self, user_input):
        return self.email_agent.handle_task(user_input, self.safety_settings)

    def _handle_research(self, user_input):
        return self.research_agent.handle_task(user_input, self.safety_settings)

    def _handle_report(self):
        return self.report_agent.generate_xp_report(self.xp_agent, self.context_manager)
    
    def _handle_calendar(self, user_input):
        return self.calendar_agent.handle_task(user_input, self.safety_settings)

    def _handle_notion(self, user_input):
        return self.notion_agent.handle_task(user_input, self.safety_settings)

    def _handle_slack(self, user_input):
        return self.slack_agent.handle_task(user_input, self.safety_settings)

    def _handle_general(self, user_input):
        system_prompt = "You are a helpful AI assistant. Provide clear, concise, and friendly responses."
        
        try:
            chat_model = genai.GenerativeModel(
                'gemini-2.5-flash-preview-05-20',
                system_instruction=system_prompt
            )
            response = chat_model.generate_content(
                user_input,
                safety_settings=self.safety_settings
            )
            
            return f"💬 **Response:**\n\n{response.text}"
        except Exception as e:
            return f"I can help with various tasks like sending emails, researching topics, or generating reports. What would you like to do?"

    def _compile_response(self, result, xp_info, context):
        response = f"{result}\n\n"
        response += f"---\n"
        response += f"**✨ XP Earned:** +{xp_info['xp_earned']} XP | "
        response += f"**Level {xp_info['level']}** ({xp_info['total_xp']} total XP) | "
        response += f"**Tasks:** {xp_info['tasks_completed']}\n"
        response += f"**⚡ Energy:** {context['energy_level']}/100 | "
        response += f"**Flow State:** {context['flow_state'].capitalize()}"
        
        return response
    
    def get_xp_stats(self):
        return self.xp_agent.get_stats()
    
    def get_context(self):
        return self.context_manager.get_context()
    
    def get_personality_profile(self):
        return self.paei_personality.get_personality_profile()
    
    def get_personality_recommendations(self):
        return self.paei_personality.get_personality_recommendations()
    
    def get_personality_badge(self):
        return self.paei_personality.get_personality_badge()
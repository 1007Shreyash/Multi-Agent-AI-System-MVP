# Developed by Shreyash Chougule
# Project: Multi-Agent AI System (MVP)

import os
import json
import time
<<<<<<< HEAD
from llm_wrapper import LLMWrapper 
=======
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
>>>>>>> 80e94f5bf5950bea36b97466b105b71a9062ba7a

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
<<<<<<< HEAD
    def __init__(self, db=None, user_id=None, google_api_key=None, calendar_manager=None, email_manager=None):
        self.model = LLMWrapper(api_key=google_api_key, model_name="llama-3.3-70b-versatile")
=======
    def __init__(self, db=None, user_id=None, google_api_key=None):
        if google_api_key:
            genai.configure(api_key=google_api_key)
        
        # Using Gemini 2.0 Flash Lite for speed and reliability
        self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
>>>>>>> 80e94f5bf5950bea36b97466b105b71a9062ba7a
        
        self.db = db
        self.user_id = user_id
        self.calendar_manager = calendar_manager
        self.email_manager = email_manager
        
        self.context_manager = ContextManager()
        self.xp_agent = XPAgent(db=db, user_id=user_id)
        
        self.email_agent = EmailAgent(model=self.model, email_manager=self.email_manager)
        self.calendar_agent = CalendarAgent(model=self.model, calendar_manager=self.calendar_manager)
        self.research_agent = ResearchAgent(model=self.model)
        self.report_agent = ReportAgent(model=self.model, db=db, user_id=user_id)
        self.paei_personality = PAEIPersonality(db=db, user_id=user_id)
<<<<<<< HEAD
        self.notion_agent = NotionAgent(model=self.model)
        self.slack_agent = SlackAgent(model=self.model)
        
        self.safety_settings = {} 
        self.json_generation_config = {}

    def handle_request(self, user_input):
        try:
            time.sleep(0.5)
            context = self.context_manager.get_context()
            
            analysis = self._analyze_intent(user_input, context)
            steps = analysis.get("steps", [])
            paei_analysis = analysis.get("paei_analysis", "Processing request.")
            
            final_response_text = ""
            total_xp = 0

            # --- FIX 1: Cumulative Context Log ---
            # We store ALL past results here so the Email Agent sees everything (Research, etc.)
            execution_log = "" 
            
            for i, step in enumerate(steps, 1):
                agent_name = step.get("agent")
                instruction = step.get("instruction")
                
                # Pass full history to the current agent
                if execution_log:
                    instruction += f"\n\n[HISTORY OF PREVIOUS STEPS]:\n{execution_log}"

                result = self._route_agent(agent_name, instruction)
                
                # Append result to history
                execution_log += f"--- Result from {agent_name} ---\n{result}\n\n"
                
                xp = self.xp_agent.calculate_xp_for_task(agent_name)
                total_xp += xp
                
                if len(steps) > 1:
                    final_response_text += f"**Step {i} ({agent_name.title()}):**\n{result}\n\n"
                else:
                    final_response_text += f"{result}\n\n"
                
                if self.db:
                    paei_map = {
                        "email": "Administrator", "calendar": "Administrator",
                        "research": "Producer", "report": "Producer",
                        "notion": "Entrepreneur", "general": "Entrepreneur",
                        "slack": "Integrator"
                    }
                    personality = paei_map.get(agent_name, "Integrator")
                    self.db.add_task(instruction[:50]+"...", personality, xp, status="Done")
                    self.xp_agent.add_xp(xp, agent_name)
                    self.db.update_agent_metrics(self.user_id, agent_name, xp)

            self.context_manager.update_context(steps[-1]["agent"] if steps else "general")
            updated_context = self.context_manager.get_context()
            
            xp_info = {"xp_earned": total_xp, "level": self.xp_agent.get_stats()['level']}
=======
        self.calendar_agent = CalendarAgent(model=self.model)
        self.notion_agent = NotionAgent(model=self.model)
        self.slack_agent = SlackAgent(model=self.model)
        
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        self.json_generation_config = genai.GenerationConfig(
            response_mime_type="application/json"
        )

    def handle_request(self, user_input):
        try:
            # Add a small delay to avoid hitting rate limits instantly
            time.sleep(1)
            
            context = self.context_manager.get_context()
            intent = self._analyze_intent(user_input, context)
            
            # Error Handling within Intent
            if intent.get("agent") == "general" and "Error" in intent.get("reasoning", ""):
                 # Fallback to general, passing the error reasoning internally if needed
                 pass
            
            # Routing
            if intent["agent"] == "email":
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
            
            # XP and Context Updates
            xp_info = self.xp_agent.add_xp(xp_earned, intent["agent"])
            self.context_manager.update_context(intent["agent"])
            updated_context = self.context_manager.get_context()
            
            response = self._compile_response(result, xp_info, updated_context)
>>>>>>> 80e94f5bf5950bea36b97466b105b71a9062ba7a
            
            return self._compile_response(final_response_text, xp_info, updated_context, paei_analysis)
            
        except Exception as e:
<<<<<<< HEAD
            return f"❌ Error: {str(e)}"

    def _route_agent(self, agent_name, instruction):
        if agent_name == "email": return self.email_agent.handle_task(instruction, self.safety_settings)
        elif agent_name == "research": return self.research_agent.handle_task(instruction, self.safety_settings)
        elif agent_name == "report": return self.report_agent.generate_xp_report(self.xp_agent, self.context_manager)
        elif agent_name == "calendar": return self.calendar_agent.handle_task(instruction, self.safety_settings)
        elif agent_name == "notion": return self.notion_agent.handle_task(instruction, self.safety_settings)
        elif agent_name == "slack": return self.slack_agent.handle_task(instruction, self.safety_settings)
        else: return self._handle_general(instruction)

    def _analyze_intent(self, user_input, context):
        # --- FIX 2: STRICTER RULES ---
        prompt = f"""You are the Executive OS. Break down the user request.
        User Request: "{user_input}"
        Context: Energy {context['energy_level']}
        
        Agents Available: calendar, email, research, report, notion, slack, general.
=======
            if "429" in str(e):
                return "⏳ **API Rate Limit Reached:** Please wait a moment. The free tier allows limited requests per minute."
            return f"❌ Error: {str(e)}"

    def _analyze_intent(self, user_input, context):
        prompt = f"""Route this user request. 
User Input: "{user_input}"
Context: Energy {context['energy_level']}

Agents: "email", "research", "report", "calendar", "notion", "slack", "general".

Return JSON ONLY: {{ "agent": "name", "reasoning": "why" }}"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.json_generation_config,
                safety_settings=self.safety_settings
            )
            
            clean_text = response.text.strip()
            if clean_text.startswith("```json"): clean_text = clean_text[7:]
            if clean_text.endswith("```"): clean_text = clean_text[:-3]
            
            intent_data = json.loads(clean_text)
            
            # Fix: Handle List vs Dictionary return types
            if isinstance(intent_data, list):
                if len(intent_data) > 0:
                    intent_data = intent_data[0] 
                else:
                    return {"agent": "general", "reasoning": "Empty list returned"}

            valid = ["email", "research", "report", "calendar", "notion", "slack", "general"]
            if intent_data.get("agent") not in valid:
                return {"agent": "general", "reasoning": "Invalid agent name returned"}

            return intent_data
        except Exception as e:
            return {"agent": "general", "reasoning": f"Error: {str(e)}"}

    def _handle_email(self, user_input): return self.email_agent.handle_task(user_input, self.safety_settings)
    def _handle_research(self, user_input): return self.research_agent.handle_task(user_input, self.safety_settings)
    def _handle_report(self): return self.report_agent.generate_xp_report(self.xp_agent, self.context_manager)
    def _handle_calendar(self, user_input): return self.calendar_agent.handle_task(user_input, self.safety_settings)
    def _handle_notion(self, user_input): return self.notion_agent.handle_task(user_input, self.safety_settings)
    def _handle_slack(self, user_input): return self.slack_agent.handle_task(user_input, self.safety_settings)
    
    def _handle_general(self, user_input):
        try:
            chat_model = genai.GenerativeModel('gemini-2.0-flash-lite', system_instruction="You are a helpful AI.")
            response = chat_model.generate_content(user_input, safety_settings=self.safety_settings)
            return f"💬 **Response:**\n\n{response.text}"
        except Exception as e:
            return f"I can help with various tasks. Error: {e}"
>>>>>>> 80e94f5bf5950bea36b97466b105b71a9062ba7a

        RULES:
        1. ONLY use agents explicitly requested or logically required.
        2. Do NOT add a 'report' step unless the user specifically asks for "performance report" or "stats".
        3. Do NOT add a 'notion' step unless the user says "save this".
        4. If the user asks to "Research X and email it", the steps are [research, email]. Do NOT add 'report'.

        Return JSON ONLY:
        {{
            "paei_analysis": "Reasoning based on Producer/Admin/Entrepreneur/Integrator perspectives.",
            "steps": [
                {{ "agent": "agent_name", "instruction": "specific instruction" }}
            ]
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"): text = text[7:]
            if text.endswith("```"): text = text[:-3]
            data = json.loads(text)
            
            if "steps" not in data or not isinstance(data["steps"], list):
                return {"steps": [{"agent": "general", "instruction": user_input}], "paei_analysis": "General execution."}
            return data
        except Exception as e:
            return {"steps": [{"agent": "general", "instruction": f"Intent Error: {e}"}], "paei_analysis": "Error."}

    def _handle_general(self, i):
        try:
            chat_model = LLMWrapper(api_key=self.model.client.api_key, model_name="llama-3.3-70b-versatile", system_instruction="You are a helpful AI.")
            return f"💬 **Response:**\n\n{chat_model.generate_content(i).text}"
        except Exception as e: return f"Error: {e}"

    def _compile_response(self, result, xp_info, context, paei_analysis):
        response = f"🧠 **Executive Thought:** _{paei_analysis}_\n\n"
        response += f"{result}"
        response += f"---\n"
<<<<<<< HEAD
        response += f"**✨ Total XP:** +{xp_info.get('xp_earned', 0)} XP | **Level:** {xp_info['level']}"
=======
        response += f"**✨ XP Earned:** +{xp_info['xp_earned']} XP | "
        response += f"**Level {xp_info['level']}** ({xp_info['total_xp']} total XP) | "
        response += f"**Tasks:** {xp_info['tasks_completed']}\n"
        response += f"**⚡ Energy:** {context['energy_level']}/100 | "
        response += f"**Flow State:** {context['flow_state'].capitalize()}"
>>>>>>> 80e94f5bf5950bea36b97466b105b71a9062ba7a
        return response
    
    def get_xp_stats(self): return self.xp_agent.get_stats()
    def get_context(self): return self.context_manager.get_context()
    def get_personality_profile(self): return self.paei_personality.get_personality_profile()
    def get_personality_recommendations(self): return self.paei_personality.get_personality_recommendations()
<<<<<<< HEAD
    def get_personality_badge(self): return self.paei_personality.get_personality_badge()
=======
    def get_personality_badge(self): return self.paei_personality.get_personality_badge()
>>>>>>> 80e94f5bf5950bea36b97466b105b71a9062ba7a

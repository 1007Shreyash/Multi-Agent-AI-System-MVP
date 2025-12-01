# Developed by Shreyash Chougule
# Email: shreyash.v.chougule1903@gmail.com
# Project: Multi-Agent AI System (MVP)

import os
import json
import time
from llm_wrapper import LLMWrapper 

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
    def __init__(self, db=None, user_id=None, google_api_key=None, calendar_manager=None, email_manager=None):
        """
        The Brain. Now powered by GROQ (Llama 3.3) via Wrapper.
        """
        # Connect to Groq via LLM Wrapper
        # Note: google_api_key argument now holds the Groq Key
        self.model = LLMWrapper(api_key=google_api_key, model_name="llama-3.3-70b-versatile")
        
        self.db = db
        self.user_id = user_id
        self.calendar_manager = calendar_manager
        self.email_manager = email_manager
        
        self.context_manager = ContextManager()
        self.xp_agent = XPAgent(db=db, user_id=user_id)
        
        # --- CHILD AGENTS (With Managers) ---
        self.email_agent = EmailAgent(model=self.model, email_manager=self.email_manager)
        self.calendar_agent = CalendarAgent(model=self.model, calendar_manager=self.calendar_manager)
        
        # Standard Agents
        self.research_agent = ResearchAgent(model=self.model)
        self.report_agent = ReportAgent(model=self.model, db=db, user_id=user_id)
        self.paei_personality = PAEIPersonality(db=db, user_id=user_id)
        self.notion_agent = NotionAgent(model=self.model)
        self.slack_agent = SlackAgent(model=self.model)
        
        # Config placeholders (kept for compatibility)
        self.safety_settings = {} 
        self.json_generation_config = {}

    def handle_request(self, user_input):
        try:
            time.sleep(0.5)
            context = self.context_manager.get_context()
            
            # 1. Analyze Intent
            analysis = self._analyze_intent(user_input, context)
            steps = analysis.get("steps", [])
            paei_analysis = analysis.get("paei_analysis", "Processing request.")
            
            final_response_text = ""
            total_xp = 0

            # 2. Execute Steps
            previous_output = ""
            
            for i, step in enumerate(steps, 1):
                agent_name = step.get("agent")
                instruction = step.get("instruction")
                
                if previous_output:
                    instruction += f"\n[Context from previous step: {previous_output}]"

                result = self._route_agent(agent_name, instruction)
                previous_output = result
                
                xp = self.xp_agent.calculate_xp_for_task(agent_name)
                total_xp += xp
                
                final_response_text += f"**Step {i} ({agent_name.title()}):**\n{result}\n\n"
                
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
            
            return self._compile_response(final_response_text, xp_info, updated_context, paei_analysis)
            
        except Exception as e:
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
        prompt = f"""You are the Executive OS. Break down the user request.
        User Request: "{user_input}"
        Context: Energy {context['energy_level']}
        
        Agents Available: calendar, email, research, report, notion, slack, general.

        IF COMPLEX (e.g., "Schedule X and Email Y"):
        Return a list of steps.
        
        Return JSON ONLY:
        {{
            "paei_analysis": "Reasoning based on Producer/Admin/Entrepreneur/Integrator.",
            "steps": [
                {{ "agent": "calendar", "instruction": "..." }},
                {{ "agent": "email", "instruction": "..." }}
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
            chat_model = LLMWrapper(
                api_key=self.model.client.api_key, 
                model_name="llama-3.3-70b-versatile",
                system_instruction="You are a helpful AI."
            )
            return f"💬 **Response:**\n\n{chat_model.generate_content(i).text}"
        except Exception as e: return f"Error: {e}"

    def _compile_response(self, result, xp_info, context, paei_analysis):
        response = f"🧠 **Executive Thought:** _{paei_analysis}_\n\n"
        response += f"{result}"
        response += f"---\n"
        response += f"**✨ Total XP:** +{xp_info.get('xp_earned', 0)} XP | **Level:** {xp_info['level']}"
        return response
    
    def get_xp_stats(self): return self.xp_agent.get_stats()
    def get_context(self): return self.context_manager.get_context()
    def get_personality_profile(self): return self.paei_personality.get_personality_profile()
    def get_personality_recommendations(self): return self.paei_personality.get_personality_recommendations()
    def get_personality_badge(self): return self.paei_personality.get_personality_badge()

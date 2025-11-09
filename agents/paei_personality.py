# Developed by Shreyash Chougule
# Email: shreyash.v.chougule1903@gmail.com
# Project: Multi-Agent AI System (MVP)

class PAEIPersonality:
    """
    Manages the PAEI personality profile based on agent usage.
    P = Producer (Research, Report)
    A = Administrator (Email, Calendar)
    E = Entrepreneur (Notion, General)
    I = Integrator (Slack)
    """
    def __init__(self, db=None, user_id=None):
        self.db = db
        self.user_id = user_id
        self.agent_to_paei = {
            "research": "P",
            "report": "P",
            "email": "A",
            "calendar": "A",
            "notion": "E",
            "general": "E",
            "slack": "I"
        }
        self.paei_details = {
            "P": {
                "name": "Producer",
                "badge": "🚀",
                "desc": "You are results-focused and action-oriented. You excel at getting things done."
            },
            "A": {
                "name": "Administrator",
                "badge": "🗂️",
                "desc": "You are organized, systematic, and process-oriented. You bring order to chaos."
            },
            "E": {
                "name": "Entrepreneur",
                "badge": "💡",
                "desc": "You are a creative, innovative, and strategic thinker. You see the big picture."
            },
            "I": {
                "name": "Integrator",
                "badge": "🤝",
                "desc": "You are collaborative and people-focused. You build strong teams and connections."
            }
        }
        self.recommendations = {
            "P": [
                "Delegate smaller tasks to maintain high output.",
                "Take short breaks to avoid burnout.",
                "Set clear, achievable daily goals."
            ],
            "A": [
                "Don't be afraid to innovate on existing processes.",
                "Schedule time for creative thinking.",
                "Use templates to streamline your administrative tasks."
            ],
            "E": [
                "Collaborate with 'A' types to bring your ideas to life.",
                "Break down big ideas into smaller, actionable steps.",
                "Set clear priorities to focus your creative energy."
            ],
            "I": [
                "Use your people skills to unblock team members.",
                "Facilitate meetings to ensure all voices are heard.",
                "Organize team-building activities to boost morale."
            ]
        }

    def get_personality_profile(self):
        """
        Calculates the user's PAEI profile from database metrics.
        """
        scores = {"P": 0, "A": 0, "E": 0, "I": 0}
        total_calls = 0
        
        if self.db and self.user_id:
            agent_metrics = self.db.get_agent_metrics(self.user_id)
            if not agent_metrics:
                return self._default_profile() # Return default if no history

            for metric in agent_metrics:
                agent_name = metric.get("agent")
                call_count = metric.get("calls", 0)
                trait = self.agent_to_paei.get(agent_name)
                
                if trait:
                    scores[trait] += call_count
                    total_calls += call_count
        else:
            return self._default_profile()

        if total_calls == 0:
            return self._default_profile()

        # Calculate percentages
        percent_scores = {k: (v / total_calls) * 100 for k, v in scores.items()}
        
        # Find dominant trait
        dominant_trait = max(percent_scores, key=percent_scores.get)
        
        # If all scores are 0, default to 'I'
        if percent_scores[dominant_trait] == 0:
            dominant_trait = "I"

        return {
            "scores": percent_scores,
            "dominant_trait": self.paei_details[dominant_trait]["name"],
            "dominant_score": percent_scores[dominant_trait],
            "profile_description": self.paei_details[dominant_trait]["desc"],
            "dominant_trait_short": dominant_trait
        }

    def _default_profile(self):
        """Returns a default profile for new users."""
        return {
            "scores": {"P": 0, "A": 0, "E": 0, "I": 0},
            "dominant_trait": "Integrator",
            "dominant_score": 0,
            "profile_description": self.paei_details["I"]["desc"],
            "dominant_trait_short": "I"
        }

    def get_personality_badge(self):
        """Gets the emoji badge for the dominant trait."""
        profile = self.get_personality_profile()
        trait_short = profile["dominant_trait_short"]
        return self.paei_details[trait_short]["badge"]

    def get_personality_recommendations(self):
        """Gets personalized recommendations based on the dominant trait."""
        profile = self.get_personality_profile()
        trait_short = profile["dominant_trait_short"]
        return self.recommendations[trait_short]
# Developed by Shreyash Chougule
# Email: shreyash.v.chougule1903@gmail.com
# Project: Multi-Agent AI System (MVP)

class ReportAgent:
    def __init__(self, model, db=None, user_id=None):
        """
        Initialize the agent with a Gemini model and database connection.
        """
        self.model = model
        self.db = db
        self.user_id = user_id

    def generate_xp_report(self, xp_agent, context_manager):
        """
        Generates a summary report based on user stats.
        This agent now gets data from other agents, so it doesn't need to call the LLM.
        """
        try:
            xp_stats = xp_agent.get_stats()
            context = context_manager.get_context()
            
            report = f"📊 **Your Performance Report**\n\n"
            report += f"Here's a snapshot of your recent activity:\n\n"
            report += f"- **Level:** {xp_stats['level']}\n"
            report += f"- **Total XP:** {xp_stats['total_xp']}\n"
            report += f"- **Tasks Completed:** {xp_stats['tasks_completed']}\n"
            report += f"- **Current Energy:** {context['energy_level']}/100\n"
            report += f"- **Current Flow State:** {context['flow_state'].capitalize()}\n\n"
            
            if self.db and self.user_id:
                agent_metrics = self.db.get_agent_metrics(self.user_id)
                if agent_metrics:
                    most_used = agent_metrics[0]
                    report += f"**Your Top Agent:** `{most_used['agent']}` (called {most_used['calls']} times)."
                else:
                    report += "Start completing tasks to see your agent analytics!"
            
            return report
            
        except Exception as e:
            return f"❌ Error generating report: {str(e)}"
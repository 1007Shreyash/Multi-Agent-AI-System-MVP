# Developed by Shreyash Chougule
# Email: shreyash.v.chougule1903@gmail.com
# Project: Multi-Agent AI System (MVP)

class ContextManager:
    """
    Manages the user's dynamic context, like energy and flow state.
    This is a simple in-memory simulation for the MVP.
    """
    def __init__(self):
        # Default state
        self.context = {
            "energy_level": 80,   # Example starting energy
            "flow_state": "focused", # Can be 'focused', 'distracted', 'relaxed'
            "focus_score": 90,    # Example focus
        }

    def get_context(self):
        """
        Returns the current context.
        (No longer modifies the state)
        """
        return self.context

    def update_context(self, action_type):
        """
        Updates the context based on a completed action.
        """
        # Apply energy cost based on task type
        if action_type in ["research", "report", "complex"]:
            self.context["energy_level"] -= 5
            self.context["flow_state"] = "deep_work"
        elif action_type in ["email", "simple", "general", "calendar", "notion", "slack"]:
            self.context["energy_level"] -= 2
            self.context["flow_state"] = "focused"
        else:
            # Default cost for any other task
            self.context["energy_level"] -= 1
        
        # Ensure energy doesn't go below 0
        if self.context["energy_level"] < 0:
            self.context["energy_level"] = 0
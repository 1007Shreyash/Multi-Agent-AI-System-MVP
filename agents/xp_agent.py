# Developed by Shreyash Chougule
# Email: shreyash.v.chougule1903@gmail.com
# Project: Multi-Agent AI System (MVP)

import math

class XPAgent:
    """
    Manages all logic for experience points (XP), leveling, and tasks.
    It communicates with the database but contains no AI model itself.
    """
    def __init__(self, db=None, user_id=None):
        self.db = db
        self.user_id = user_id
        
        # Base XP needed for level 1 to 2
        self.base_xp = 100 
        # Multiplier for each subsequent level (exponential growth)
        self.level_multiplier = 1.5 
        
        # XP rewards for different task complexities
        self.task_xp_rewards = {
            "simple": 10,     # e.g., general query
            "email": 25,      # e.g., email, slack
            "research": 50,   # e.g., research task
            "report": 75,     # e.g., generating a report
            "complex": 100    # e.g., calendar, notion
        }

    def get_xp_for_level(self, level):
        """
        Calculates the total XP needed to reach a specific level.
        Formula: base_xp * (multiplier ^ (level - 1))
        """
        if level <= 1:
            return 0
        return int(self.base_xp * math.pow(self.level_multiplier, level - 2))

    def get_current_level_progress(self, total_xp):
        """
        Calculates the user's current level based on their total XP.
        """
        level = 1
        xp_needed = self.base_xp
        
        while total_xp >= xp_needed:
            total_xp -= xp_needed
            level += 1
            xp_needed = int(xp_needed * self.level_multiplier)
            
        return level, total_xp, xp_needed # level, xp_into_current_level, xp_needed_for_next_level

    def get_stats(self):
        """
        Fetches current stats from the DB and calculates progress.
        """
        if not self.db or not self.user_id:
            return {
                "level": 1, "total_xp": 0, "tasks_completed": 0,
                "xp_to_next_level": self.base_xp, "progress_percent": 0
            }
            
        stats = self.db.get_xp_progress(self.user_id)
        
        level, xp_in_level, xp_for_next = self.get_current_level_progress(stats['total_xp'])
        
        progress_percent = 0
        if xp_for_next > 0:
            progress_percent = math.floor((xp_in_level / xp_for_next) * 100)
            
        return {
            "level": level,
            "total_xp": stats['total_xp'],
            "tasks_completed": stats['tasks_completed'],
            "xp_to_next_level": xp_for_next - xp_in_level,
            "progress_percent": progress_percent
        }

    def calculate_xp_for_task(self, task_type):
        """
        Returns the appropriate XP for a given task type.
        """
        return self.task_xp_rewards.get(task_type, self.task_xp_rewards['simple'])

    def add_xp(self, xp_earned, task_type):
        """
        Adds XP to the user, updates their stats, and logs the task.
        """
        if not self.db or not self.user_id:
            return self.get_stats()
            
        # 1. Get current stats from DB
        current_stats = self.db.get_xp_progress(self.user_id)
        
        # 2. Calculate new totals
        new_total_xp = current_stats.get('total_xp', 0) + xp_earned
        new_tasks_completed = current_stats.get('tasks_completed', 0) + 1
        
        # 3. Calculate new level
        new_level, _, _ = self.get_current_level_progress(new_total_xp)
        
        # 4. Update the database
        self.db.update_xp_progress(
            self.user_id, 
            new_total_xp, 
            new_level, 
            new_tasks_completed
        )
        
        # 5. Add the specific task to history
        self.db.add_task_to_history(
            self.user_id,
            task_type,
            xp_earned,
            new_tasks_completed
        )
        
        # 6. Get the new stats
        new_stats = self.get_stats()
        
        # 7. Add the 'xp_earned' to the stats to be returned
        new_stats['xp_earned'] = xp_earned
        
        return new_stats
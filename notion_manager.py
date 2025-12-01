# Developed by Shreyash Chougule
# Project: Agentic AI MVP - Notion Integration

from notion_client import Client
from datetime import datetime

class NotionManager:
    def __init__(self, api_key, task_db_id, xp_db_id):
        """
        Handles connection to Notion.
        Replaces Firebase as the primary OS database.
        """
        self.notion = Client(auth=api_key)
        self.task_db_id = task_db_id
        self.xp_db_id = xp_db_id

    # --- USER MANAGEMENT ---
    def get_or_create_user(self, session_id):
        return session_id

    # --- RESET FUNCTION (The Fix) ---
    def clear_user_data(self, user_id):
        """
        Archives all pages in the connected databases to 'reset' the app.
        """
        try:
            # 1. Archive all Tasks
            tasks = self.notion.databases.query(database_id=self.task_db_id).get("results", [])
            for page in tasks:
                self.notion.pages.update(page_id=page["id"], archived=True)
            
            # 2. Archive all XP Logs
            logs = self.notion.databases.query(database_id=self.xp_db_id).get("results", [])
            for page in logs:
                self.notion.pages.update(page_id=page["id"], archived=True)
                
            print("Data reset successfully (archived in Notion).")
            return True
        except Exception as e:
            print(f"Error clearing Notion data: {e}")
            return False

    # --- TASK OPERATIONS ---
    def add_task(self, title, paei_type, xp_reward, due_date=None, status="Not started"):
        """
        Creates a task in Notion. 
        Now accepts a 'status' argument to mark completed actions as 'Done'.
        """
        properties = {
            "Task Name": {"title": [{"text": {"content": title}}]},
            "PAEI": {"select": {"name": paei_type}},
            "XP": {"number": xp_reward},
            "Status": {"status": {"name": status}} # <--- FIX: Uses variable, not hardcoded string
        }
        
        if due_date:
            properties["Due Date"] = {"date": {"start": due_date}}

        try:
            self.notion.pages.create(
                parent={"database_id": self.task_db_id},
                properties=properties
            )
            return True
        except Exception as e:
            print(f"Error adding task: {e}")
            return False

    def get_task_history(self, user_id, limit=50):
        try:
            # Query XP Log DB instead of Task DB to match Sidebar stats
            response = self.notion.databases.query(
                database_id=self.xp_db_id,
                page_size=limit,
                sorts=[{"timestamp": "created_time", "direction": "descending"}]
            )
            
            results = response.get("results", [])
            total_fetched = len(results)
            history = []
            
            for index, page in enumerate(results):
                props = page["properties"]
                
                # Get Log Name (Title)
                title_list = props.get("Log Name", {}).get("title", [])
                title = title_list[0]["text"]["content"] if title_list else "XP Event"
                
                # Get XP Amount
                raw_xp = props.get("Amount", {}).get("number")
                xp = raw_xp if raw_xp is not None else 0
                
                # Get Date
                created_time_str = page.get("created_time")
                created_time = None
                if created_time_str:
                    try:
                        created_time = datetime.fromisoformat(created_time_str.replace("Z", "+00:00"))
                    except ValueError:
                        created_time = None
                
                task_num = total_fetched - index
                
                history.append({
                    "task_number": task_num, 
                    "type": title,
                    "xp": xp,
                    "created_at": created_time
                })
            return history
        except Exception as e:
            print(f"Error fetching history: {e}")
            return []

    # --- XP OPERATIONS ---
    def log_xp(self, amount, personality_type, context_note="Task Completed"):
        try:
            self.notion.pages.create(
                parent={"database_id": self.xp_db_id},
                properties={
                    "Log Name": {"title": [{"text": {"content": f"XP Gain: {personality_type}"}}]},
                    "Amount": {"number": amount},
                    "Personality": {"select": {"name": personality_type}},
                    "Context": {"rich_text": [{"text": {"content": context_note}}]}
                }
            )
            return True
        except Exception as e:
            print(f"Error logging XP: {e}")
            return False

    def get_xp_stats(self):
        stats = {"Producer": 0, "Administrator": 0, "Entrepreneur": 0, "Integrator": 0}
        try:
            response = self.notion.databases.query(database_id=self.xp_db_id)
            for page in response.get("results", []):
                props = page.get("properties", {})
                p_select = props.get("Personality", {}).get("select")
                
                raw_amount = props.get("Amount", {}).get("number")
                amount = raw_amount if raw_amount is not None else 0
                
                if p_select:
                    p_type = p_select.get("name")
                    if p_type in stats:
                        stats[p_type] += amount
            return stats
        except Exception as e:
            print(f"Error stats: {e}")
            return stats

    # --- AGENT METRICS ---
    def get_agent_metrics(self, user_id):
        metrics = {}
        try:
            response = self.notion.databases.query(database_id=self.xp_db_id)
            for page in response.get("results", []):
                props = page.get("properties", {})
                raw_amount = props.get("Amount", {}).get("number")
                xp = raw_amount if raw_amount is not None else 0
                
                context_list = props.get("Context", {}).get("rich_text", [])
                if context_list:
                    text = context_list[0]["text"]["content"].lower()
                    agent_name = "general"
                    if "email" in text: agent_name = "email"
                    elif "research" in text: agent_name = "research"
                    elif "calendar" in text: agent_name = "calendar"
                    elif "notion" in text: agent_name = "notion"
                    elif "slack" in text: agent_name = "slack"
                    elif "report" in text: agent_name = "report"
                    
                    if agent_name not in metrics:
                        metrics[agent_name] = {"calls": 0, "xp_generated": 0}
                    metrics[agent_name]["calls"] += 1
                    metrics[agent_name]["xp_generated"] += xp
            
            results = []
            for agent, data in metrics.items():
                results.append({
                    "agent": agent,
                    "calls": data["calls"],
                    "xp_generated": data["xp_generated"],
                    "last_used": None 
                })
            results.sort(key=lambda x: x['calls'], reverse=True)
            return results
        except Exception as e:
            print(f"Error calculating agent metrics: {e}")
            return []

    def get_xp_progress(self, user_id):
         stats = self.get_xp_stats()
         total_xp = sum(stats.values())
         
         tasks_completed = 0
         try:
            response = self.notion.databases.query(database_id=self.xp_db_id)
            tasks_completed = len(response.get("results", []))
         except:
            tasks_completed = 0

         return {
             "total_xp": total_xp,
             "level": 1 + int(total_xp / 100),
             "tasks_completed": tasks_completed 
         }

    # --- STUBS ---
    def log_chat(self, user_id, user_input, agent_response, agent_used): pass 
    def get_chat_history(self, user_id, limit=20): return []
    def update_agent_metrics(self, user_id, agent_name, xp_earned): pass
# Developed by Shreyash Chougule
# Email: shreyash.v.chougule1903@gmail.com
# Project: Multi-Agent AI System (MVP)

import os
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

class Database:
    def __init__(self, creds_dict):
        self.available = False
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(creds_dict)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            self.available = True
        except Exception as e:
            self.available = False

    def init_tables(self):
        if self.available:
            pass
        pass

    def get_or_create_user(self, session_id):
        if not self.available:
            return None
        
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where(filter=FieldFilter('session_id', '==', session_id)).limit(1).stream()
            existing_user = next(query, None)
            
            if existing_user:
                user_id = existing_user.id
                users_ref.document(user_id).update({
                    'last_active': firestore.SERVER_TIMESTAMP
                })
                return user_id
            else:
                new_user_data = {
                    'session_id': session_id,
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'last_active': firestore.SERVER_TIMESTAMP
                }
                update_time, user_ref = users_ref.add(new_user_data)
                user_id = user_ref.id
                
                xp_data = {
                    'total_xp': 0,
                    'level': 1,
                    'tasks_completed': 0,
                    'updated_at': firestore.SERVER_TIMESTAMP
                }
                self.db.collection('xp_progress').document(user_id).set(xp_data)
                
                return user_id
                
        except Exception as e:
            return None

    def get_xp_progress(self, user_id):
        if not self.available or user_id is None:
            return {"total_xp": 0, "level": 1, "tasks_completed": 0}
        
        try:
            doc_ref = self.db.collection('xp_progress').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                xp_data = {"total_xp": 0, "level": 1, "tasks_completed": 0}
                doc_ref.set(xp_data)
                return xp_data
        except Exception as e:
            return {"total_xp": 0, "level": 1, "tasks_completed": 0}

    def update_xp_progress(self, user_id, total_xp, level, tasks_completed):
        if not self.available or user_id is None:
            return

        try:
            doc_ref = self.db.collection('xp_progress').document(user_id)
            doc_ref.update({
                'total_xp': total_xp,
                'level': level,
                'tasks_completed': tasks_completed,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            pass

    def add_task_to_history(self, user_id, task_type, xp_earned, task_number):
        if not self.available or user_id is None:
            return
            
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_ref.collection('task_history').add({
                'task_type': task_type,
                'xp_earned': xp_earned,
                'task_number': task_number,
                'created_at': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            pass

    def get_task_history(self, user_id, limit=50):
        if not self.available or user_id is None:
            return []
            
        try:
            docs = self.db.collection('users').document(user_id) \
                         .collection('task_history') \
                         .order_by('created_at', direction=firestore.Query.DESCENDING) \
                         .limit(limit) \
                         .stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                results.append({
                    "type": data.get('task_type'),
                    "xp": data.get('xp_earned'),
                    "task_number": data.get('task_number'),
                    "created_at": data.get('created_at')
                })
            return results
        except Exception as e:
            return []

    def log_chat(self, user_id, user_input, agent_response, agent_used):
        if not self.available or user_id is None:
            return
            
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_ref.collection('chat_logs').add({
                'user_input': user_input,
                'agent_response': agent_response,
                'agent_used': agent_used,
                'created_at': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            pass

    def get_chat_history(self, user_id, limit=20):
        if not self.available or user_id is None:
            return []
        
        try:
            docs = self.db.collection('users').document(user_id) \
                         .collection('chat_logs') \
                         .order_by('created_at', direction=firestore.Query.DESCENDING) \
                         .limit(limit) \
                         .stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                results.append({
                    "input": data.get('user_input'),
                    "response": data.get('agent_response'),
                    "agent": data.get('agent_used'),
                    "timestamp": data.get('created_at')
                })
            return results
        except Exception as e:
            return []

    def clear_user_data(self, user_id):
        if not self.available or user_id is None:
            return
            
        try:
            self.db.collection('users').document(user_id).delete()
            self.db.collection('xp_progress').document(user_id).delete()
            
        except Exception as e:
            pass

    def update_agent_metrics(self, user_id, agent_name, xp_earned):
        if not self.available or user_id is None:
            return

        try:
            doc_id = f"{user_id}_{agent_name}"
            doc_ref = self.db.collection('agent_metrics').document(doc_id)
            
            @firestore.transactional
            def update_in_transaction(transaction, doc_ref):
                doc = doc_ref.get(transaction=transaction)
                if doc.exists:
                    new_call_count = doc.get('call_count') + 1
                    new_xp = doc.get('total_xp_generated') + xp_earned
                    
                    transaction.update(doc_ref, {
                        'call_count': new_call_count,
                        'total_xp_generated': new_xp,
                        'last_used': firestore.SERVER_TIMESTAMP
                    })
                else:
                    transaction.set(doc_ref, {
                        'user_id': user_id,
                        'agent_name': agent_name,
                        'call_count': 1,
                        'total_xp_generated': xp_earned,
                        'last_used': firestore.SERVER_TIMESTAMP
                    })
            
            transaction = self.db.transaction()
            update_in_transaction(transaction, doc_ref)
            
        except Exception as e:
            pass

    def get_agent_metrics(self, user_id):
        if not self.available or user_id is None:
            return []
            
        try:
            docs = self.db.collection('agent_metrics') \
                         .where(filter=FieldFilter('user_id', '==', user_id)) \
                         .stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                results.append({
                    "agent": data.get('agent_name'),
                    "calls": data.get('call_count'),
                    "xp_generated": data.get('total_xp_generated'),
                    "last_used": data.get('last_used')
                })
            
            # Sort results in Python instead of in the query
            results.sort(key=lambda x: x['calls'], reverse=True)
            
            return results
        except Exception as e:
            return []
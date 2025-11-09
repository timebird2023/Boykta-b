import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from src.config import SUBSCRIBERS_DB, DB_DIR

class SubscriberManager:
    def __init__(self):
        self.db_file = SUBSCRIBERS_DB
        self.subscribers = self._load_subscribers()
    
    def _load_subscribers(self) -> Dict:
        os.makedirs(DB_DIR, exist_ok=True)
        
        if self.db_file.exists():
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading subscribers: {e}")
                return {}
        return {}
    
    def _save_subscribers(self):
        os.makedirs(DB_DIR, exist_ok=True)
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.subscribers, f, ensure_ascii=False, indent=2)
    
    def subscribe(self, user_id: str, name: str = "", location: Optional[Dict] = None) -> bool:
        if user_id in self.subscribers:
            self.subscribers[user_id]['active'] = True
            self.subscribers[user_id]['updated_at'] = datetime.now().isoformat()
        else:
            self.subscribers[user_id] = {
                'id': user_id,
                'name': name,
                'active': True,
                'location': location or {},
                'preferences': {
                    'morning_azkar': True,
                    'evening_azkar': True,
                    'sleep_azkar': True,
                    'prayer_times': True
                },
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        
        self._save_subscribers()
        print(f"✓ User {user_id} subscribed")
        return True
    
    def unsubscribe(self, user_id: str) -> bool:
        if user_id in self.subscribers:
            self.subscribers[user_id]['active'] = False
            self.subscribers[user_id]['updated_at'] = datetime.now().isoformat()
            self._save_subscribers()
            print(f"✓ User {user_id} unsubscribed")
            return True
        return False
    
    def is_subscribed(self, user_id: str) -> bool:
        return user_id in self.subscribers and self.subscribers[user_id].get('active', False)
    
    def get_subscriber(self, user_id: str) -> Optional[Dict]:
        return self.subscribers.get(user_id)
    
    def get_all_active_subscribers(self) -> List[Dict]:
        return [sub for sub in self.subscribers.values() if sub.get('active', False)]
    
    def update_location(self, user_id: str, location: Dict) -> bool:
        if user_id in self.subscribers:
            self.subscribers[user_id]['location'] = location
            self.subscribers[user_id]['updated_at'] = datetime.now().isoformat()
            self._save_subscribers()
            return True
        return False
    
    def update_preferences(self, user_id: str, preferences: Dict) -> bool:
        if user_id in self.subscribers:
            self.subscribers[user_id]['preferences'].update(preferences)
            self.subscribers[user_id]['updated_at'] = datetime.now().isoformat()
            self._save_subscribers()
            return True
        return False
    
    def get_stats(self) -> Dict:
        total = len(self.subscribers)
        active = len([s for s in self.subscribers.values() if s.get('active', False)])
        inactive = total - active
        
        return {
            'total': total,
            'active': active,
            'inactive': inactive,
            'with_location': len([s for s in self.subscribers.values() if s.get('location')])
        }

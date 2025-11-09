import requests
from typing import Dict, List, Optional
from src.config import FACEBOOK_PAGE_ACCESS_TOKEN, GRAPH_API_URL, FACEBOOK_PAGE_ID

class FacebookAPI:
    def __init__(self):
        self.access_token = FACEBOOK_PAGE_ACCESS_TOKEN
        self.page_id = FACEBOOK_PAGE_ID
        self.api_url = GRAPH_API_URL
        
    def post_to_page(self, message: str) -> Optional[Dict]:
        if not self.access_token or not self.page_id:
            print("Facebook credentials not configured")
            return None
        
        url = f"{self.api_url}/{self.page_id}/feed"
        
        payload = {
            'message': message,
            'access_token': self.access_token
        }
        
        try:
            response = requests.post(url, data=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            print(f"✓ Posted to Facebook page: {result.get('id')}")
            return result
        except requests.exceptions.RequestException as e:
            print(f"✗ Error posting to Facebook: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
    
    def send_message(self, recipient_id: str, message: str) -> Optional[Dict]:
        if not self.access_token:
            print("Facebook credentials not configured")
            return None
        
        url = f"{self.api_url}/me/messages"
        
        payload = {
            'recipient': {'id': recipient_id},
            'message': {'text': message},
            'access_token': self.access_token
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            print(f"✓ Sent message to {recipient_id}")
            return result
        except requests.exceptions.RequestException as e:
            print(f"✗ Error sending message: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
    
    def send_quick_replies(self, recipient_id: str, text: str, quick_replies: List[Dict]) -> Optional[Dict]:
        if not self.access_token:
            print("Facebook credentials not configured")
            return None
        
        url = f"{self.api_url}/me/messages"
        
        payload = {
            'recipient': {'id': recipient_id},
            'message': {
                'text': text,
                'quick_replies': quick_replies
            },
            'access_token': self.access_token
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            print(f"✓ Sent quick replies to {recipient_id}")
            return result
        except requests.exceptions.RequestException as e:
            print(f"✗ Error sending quick replies: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
    
    def send_buttons(self, recipient_id: str, text: str, buttons: List[Dict]) -> Optional[Dict]:
        if not self.access_token:
            print("Facebook credentials not configured")
            return None
        
        url = f"{self.api_url}/me/messages"
        
        payload = {
            'recipient': {'id': recipient_id},
            'message': {
                'attachment': {
                    'type': 'template',
                    'payload': {
                        'template_type': 'button',
                        'text': text,
                        'buttons': buttons
                    }
                }
            },
            'access_token': self.access_token
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            print(f"✓ Sent button template to {recipient_id}")
            return result
        except requests.exceptions.RequestException as e:
            print(f"✗ Error sending buttons: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
    
    def send_generic_template(self, recipient_id: str, elements: List[Dict]) -> Optional[Dict]:
        if not self.access_token:
            print("Facebook credentials not configured")
            return None
        
        url = f"{self.api_url}/me/messages"
        
        payload = {
            'recipient': {'id': recipient_id},
            'message': {
                'attachment': {
                    'type': 'template',
                    'payload': {
                        'template_type': 'generic',
                        'elements': elements
                    }
                }
            },
            'access_token': self.access_token
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            print(f"✓ Sent generic template to {recipient_id}")
            return result
        except requests.exceptions.RequestException as e:
            print(f"✗ Error sending generic template: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        if not self.access_token:
            return None
        
        url = f"{self.api_url}/{user_id}"
        params = {
            'fields': 'first_name,last_name,profile_pic',
            'access_token': self.access_token
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"✗ Error getting user profile: {e}")
            return None
    
    def send_audio(self, recipient_id: str, audio_url: str, text: str = '') -> Optional[Dict]:
        """
        إرسال ملف صوتي إلى المستخدم
        
        Args:
            recipient_id: معرف المستخدم
            audio_url: رابط الملف الصوتي
            text: نص اختياري يرسل مع الملف
        """
        if not self.access_token:
            print("Facebook credentials not configured")
            return None
        
        url = f"{self.api_url}/me/messages"
        
        # إرسال النص أولاً إذا وجد
        if text:
            self.send_message(recipient_id, text)
        
        # إرسال الملف الصوتي
        payload = {
            'recipient': {'id': recipient_id},
            'message': {
                'attachment': {
                    'type': 'audio',
                    'payload': {
                        'url': audio_url,
                        'is_reusable': True
                    }
                }
            },
            'access_token': self.access_token
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            print(f"✓ Sent audio to {recipient_id}")
            return result
        except requests.exceptions.RequestException as e:
            print(f"✗ Error sending audio: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None

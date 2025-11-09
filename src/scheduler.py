from datetime import datetime
from typing import List, Dict
from src.facebook_api import FacebookAPI
from src.content_manager import ContentManager
from src.subscriber_manager import SubscriberManager
from src.prayer_times import PrayerTimesService
from src.config import MORNING_AZKAR_TIME, EVENING_AZKAR_TIME, SLEEP_AZKAR_TIME

class Scheduler:
    def __init__(self):
        self.fb_api = FacebookAPI()
        self.content_manager = ContentManager()
        self.subscriber_manager = SubscriberManager()
        self.prayer_service = PrayerTimesService()
    
    def post_random_content_to_page(self) -> bool:
        print(f"[{datetime.now()}] Posting random content to page...")
        
        content = self.content_manager.get_random_content()
        
        if not content:
            print("No content available to post")
            return False
        
        result = self.fb_api.post_to_page(content['formatted'])
        
        if result:
            print(f"✓ Posted {content['type']} content successfully")
            return True
        else:
            print("✗ Failed to post content")
            return False
    
    def send_timed_notifications(self) -> Dict:
        print(f"[{datetime.now()}] Checking for timed notifications...")
        
        current_time = datetime.now().strftime("%H:%M")
        
        results = {
            'morning_azkar': 0,
            'evening_azkar': 0,
            'sleep_azkar': 0,
            'prayer_times': 0
        }
        
        subscribers = self.subscriber_manager.get_all_active_subscribers()
        
        if not subscribers:
            print("No active subscribers")
            return results
        
        if current_time == MORNING_AZKAR_TIME:
            results['morning_azkar'] = self._send_morning_azkar(subscribers)
        
        if current_time == EVENING_AZKAR_TIME:
            results['evening_azkar'] = self._send_evening_azkar(subscribers)
        
        if current_time == SLEEP_AZKAR_TIME:
            results['sleep_azkar'] = self._send_sleep_azkar(subscribers)
        
        results['prayer_times'] = self._send_prayer_time_notifications(subscribers)
        
        return results
    
    def _send_morning_azkar(self, subscribers: List[Dict]) -> int:
        print("Sending morning azkar...")
        count = 0
        
        azkar_content = self.content_manager.get_random_azkar('أذكار الصباح')
        
        if not azkar_content:
            print("No morning azkar available")
            return 0
        
        message = f"""🌅 صباح الخير

{azkar_content['formatted']}

وفقك الله لكل خير 🤲"""
        
        for subscriber in subscribers:
            if subscriber.get('preferences', {}).get('morning_azkar', True):
                result = self.fb_api.send_message(subscriber['id'], message)
                if result:
                    count += 1
        
        print(f"✓ Sent morning azkar to {count} subscribers")
        return count
    
    def _send_evening_azkar(self, subscribers: List[Dict]) -> int:
        print("Sending evening azkar...")
        count = 0
        
        azkar_content = self.content_manager.get_random_azkar('أذكار المساء')
        
        if not azkar_content:
            print("No evening azkar available")
            return 0
        
        message = f"""🌆 مساء الخير

{azkar_content['formatted']}

تقبل الله منك 🤲"""
        
        for subscriber in subscribers:
            if subscriber.get('preferences', {}).get('evening_azkar', True):
                result = self.fb_api.send_message(subscriber['id'], message)
                if result:
                    count += 1
        
        print(f"✓ Sent evening azkar to {count} subscribers")
        return count
    
    def _send_sleep_azkar(self, subscribers: List[Dict]) -> int:
        print("Sending sleep azkar...")
        count = 0
        
        azkar_content = self.content_manager.get_random_azkar('أذكار النوم')
        
        if not azkar_content:
            print("No sleep azkar available")
            return 0
        
        message = f"""🌙 تصبح على خير

{azkar_content['formatted']}

نوماً هنيئاً وراحة مباركة 🤲"""
        
        for subscriber in subscribers:
            if subscriber.get('preferences', {}).get('sleep_azkar', True):
                result = self.fb_api.send_message(subscriber['id'], message)
                if result:
                    count += 1
        
        print(f"✓ Sent sleep azkar to {count} subscribers")
        return count
    
    def _send_prayer_time_notifications(self, subscribers: List[Dict]) -> int:
        print("Checking prayer times...")
        count = 0
        
        locations_checked = set()
        
        for subscriber in subscribers:
            if not subscriber.get('preferences', {}).get('prayer_times', True):
                continue
            
            location = subscriber.get('location', {})
            city = location.get('city', 'Riyadh')
            country = location.get('country', 'Saudi Arabia')
            
            location_key = f"{city}_{country}"
            
            if location_key in locations_checked:
                continue
            
            locations_checked.add(location_key)
            
            prayer_times = self.prayer_service.get_prayer_times(city, country)
            
            if not prayer_times:
                continue
            
            current_prayer = self.prayer_service.is_prayer_time(prayer_times, tolerance_minutes=5)
            
            if current_prayer:
                prayer_time = prayer_times.get(current_prayer)
                message = self.prayer_service.format_prayer_time_message(current_prayer, prayer_time, city)
                
                for sub in subscribers:
                    sub_location = sub.get('location', {})
                    if sub_location.get('city') == city and sub_location.get('country') == country:
                        if sub.get('preferences', {}).get('prayer_times', True):
                            result = self.fb_api.send_message(sub['id'], message)
                            if result:
                                count += 1
        
        if count > 0:
            print(f"✓ Sent prayer time notifications to {count} subscribers")
        
        return count

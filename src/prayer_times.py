import requests
from typing import Dict, Optional
from datetime import datetime

class PrayerTimesService:
    def __init__(self):
        self.api_url = "https://api.aladhan.com/v1"
    
    def get_prayer_times(self, city: str, country: str, method: int = 2) -> Optional[Dict]:
        url = f"{self.api_url}/timingsByCity"
        
        params = {
            'city': city,
            'country': country,
            'method': method
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') == 200 and data.get('data'):
                timings = data['data']['timings']
                return {
                    'Fajr': timings.get('Fajr'),
                    'Dhuhr': timings.get('Dhuhr'),
                    'Asr': timings.get('Asr'),
                    'Maghrib': timings.get('Maghrib'),
                    'Isha': timings.get('Isha'),
                    'date': data['data']['date']['readable'],
                    'hijri': data['data']['date']['hijri']['date']
                }
            
            return None
        except Exception as e:
            print(f"Error fetching prayer times: {e}")
            return None
    
    def format_prayer_time_message(self, prayer_name: str, time: str, city: str) -> str:
        prayer_names_ar = {
            'Fajr': 'الفجر',
            'Dhuhr': 'الظهر',
            'Asr': 'العصر',
            'Maghrib': 'المغرب',
            'Isha': 'العشاء'
        }
        
        prayer_dua = {
            'Fajr': 'اللَّهُمَّ بَارِكْ لَنَا فِي بُكُورِهَا',
            'Dhuhr': 'اللَّهُمَّ إِنِّي أَسْأَلُكَ خَيْرَ هَذَا الْيَوْمِ',
            'Asr': 'أَسْتَغْفِرُ اللَّهَ الَّذِي لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ وَأَتُوبُ إِلَيْهِ',
            'Maghrib': 'اللَّهُمَّ إِنِّي أَسْأَلُكَ خَيْرَ هَذِهِ اللَّيْلَةِ',
            'Isha': 'اللَّهُمَّ بِكَ أَمْسَيْنَا وَبِكَ أَصْبَحْنَا'
        }
        
        prayer_ar = prayer_names_ar.get(prayer_name, prayer_name)
        dua = prayer_dua.get(prayer_name, '')
        
        message = f"""🕌 حان الآن موعد صلاة {prayer_ar}

⏰ الوقت: {time}
📍 {city}

{dua}

لا تنسَ الصلاة في وقتها 🤲"""
        
        return message
    
    def get_next_prayer(self, timings: Dict) -> Optional[tuple]:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        prayers = [
            ('Fajr', timings.get('Fajr')),
            ('Dhuhr', timings.get('Dhuhr')),
            ('Asr', timings.get('Asr')),
            ('Maghrib', timings.get('Maghrib')),
            ('Isha', timings.get('Isha'))
        ]
        
        for prayer_name, prayer_time in prayers:
            if prayer_time and current_time < prayer_time:
                return (prayer_name, prayer_time)
        
        return ('Fajr', timings.get('Fajr'))
    
    def is_prayer_time(self, timings: Dict, tolerance_minutes: int = 5) -> Optional[str]:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        for prayer_name, prayer_time in timings.items():
            if prayer_name in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
                if prayer_time and abs(self._time_diff_minutes(current_time, prayer_time)) <= tolerance_minutes:
                    return prayer_name
        
        return None
    
    def _time_diff_minutes(self, time1: str, time2: str) -> int:
        try:
            t1 = datetime.strptime(time1, "%H:%M")
            t2 = datetime.strptime(time2, "%H:%M")
            diff = abs((t2 - t1).total_seconds() / 60)
            return int(diff)
        except:
            return 999

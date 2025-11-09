
import random
from typing import Dict, Optional, List
from pathlib import Path

class AudioManager:
    """مدير الملفات الصوتية للقرآن الكريم"""
    
    def __init__(self):
        # يمكنك إضافة روابط الملفات الصوتية هنا
        # مثال: ملفات من موقع everyayah.com أو أي مصدر آخر
        self.audio_base_urls = {
            'abdulbasit': 'https://everyayah.com/data/Abdul_Basit_Murattal_192kbps/',
            'husary': 'https://everyayah.com/data/Husary_128kbps/',
            'minshawi': 'https://everyayah.com/data/Minshawy_Murattal_128kbps/',
            'sudais': 'https://everyayah.com/data/Abdurrahmaan_As-Sudais_192kbps/',
        }
        
        self.readers = {
            'abdulbasit': 'عبد الباسط عبد الصمد',
            'husary': 'محمود خليل الحصري',
            'minshawi': 'محمد صديق المنشاوي',
            'sudais': 'عبد الرحمن السديس'
        }
    
    def get_verse_audio_url(self, surah: int, verse: int, reader: str = 'abdulbasit') -> Optional[str]:
        """
        الحصول على رابط الملف الصوتي لآية معينة
        
        Args:
            surah: رقم السورة (1-114)
            verse: رقم الآية
            reader: القارئ (abdulbasit, husary, minshawi, sudais)
        
        Returns:
            رابط الملف الصوتي
        """
        if reader not in self.audio_base_urls:
            reader = 'abdulbasit'
        
        base_url = self.audio_base_urls[reader]
        # تنسيق الرابط: surah_verse.mp3 (مثال: 001001.mp3 للفاتحة آية 1)
        filename = f"{surah:03d}{verse:03d}.mp3"
        return base_url + filename
    
    def get_random_reader(self) -> str:
        """اختيار قارئ عشوائي"""
        return random.choice(list(self.audio_base_urls.keys()))
    
    def get_reader_name(self, reader: str) -> str:
        """الحصول على اسم القارئ بالعربية"""
        return self.readers.get(reader, reader)

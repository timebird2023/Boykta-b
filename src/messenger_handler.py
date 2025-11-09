from typing import Dict, Optional
from src.facebook_api import FacebookAPI
from src.subscriber_manager import SubscriberManager
from src.content_manager import ContentManager
from src.audio_manager import AudioManager
from src.config import DEVELOPER_NAME, DEVELOPER_FACEBOOK

class MessengerHandler:
    def __init__(self):
        self.fb_api = FacebookAPI()
        self.subscriber_manager = SubscriberManager()
        self.content_manager = ContentManager()
        self.audio_manager = AudioManager()
    
    def handle_message(self, sender_id: str, message_text: str):
        message_text_lower = message_text.lower().strip()
        
        if any(greeting in message_text_lower for greeting in ['مرحبا', 'السلام', 'هلا', 'اهلا', 'بداية', 'ابدأ', 'start', 'hi', 'hello']):
            self.send_welcome_message(sender_id)
        elif 'اشتراك' in message_text_lower or 'subscribe' in message_text_lower:
            self.handle_subscribe(sender_id)
        elif 'إلغاء' in message_text_lower or 'unsubscribe' in message_text_lower:
            self.handle_unsubscribe(sender_id)
        elif 'معلومات' in message_text_lower or 'عن' in message_text_lower or 'info' in message_text_lower:
            self.send_info_message(sender_id)
        elif 'آية' in message_text_lower or 'قرآن' in message_text_lower:
            self.send_random_quran(sender_id)
        elif 'حديث' in message_text_lower:
            self.send_random_hadith(sender_id)
        elif 'ذكر' in message_text_lower or 'أذكار' in message_text_lower:
            self.send_random_azkar(sender_id)
        elif 'صوت' in message_text_lower or 'تلاوة' in message_text_lower or 'استماع' in message_text_lower:
            self.send_random_quran_audio(sender_id)
        else:
            self.send_welcome_message(sender_id)
    
    def handle_postback(self, sender_id: str, payload: str):
        if payload == 'SUBSCRIBE':
            self.handle_subscribe(sender_id)
        elif payload == 'UNSUBSCRIBE':
            self.handle_unsubscribe(sender_id)
        elif payload == 'INFO':
            self.send_info_message(sender_id)
        elif payload == 'GET_STARTED':
            self.send_welcome_message(sender_id)
        elif payload == 'RANDOM_QURAN':
            self.send_random_quran(sender_id)
        elif payload == 'RANDOM_HADITH':
            self.send_random_hadith(sender_id)
        elif payload == 'RANDOM_AZKAR':
            self.send_random_azkar(sender_id)
        elif payload == 'AUDIO_QURAN':
            self.send_random_quran_audio(sender_id)
        elif payload.startswith('LOCATION_'):
            city = payload.replace('LOCATION_', '')
            self.handle_location_selection(sender_id, city)
        else:
            self.send_welcome_message(sender_id)
    
    def send_welcome_message(self, sender_id: str):
        welcome_text = f"""السلام عليكم ورحمة الله وبركاته 🌙

مرحباً بك في ناشر الخير - بوتك الديني الشامل!

يسعدني أن أقدم لك:
📖 آيات قرآنية
📚 أحاديث نبوية وقدسية
🤲 أذكار متنوعة
⏰ تذكيرات أوقات الصلاة

اختر ما تريد من القائمة أدناه:"""
        
        is_subscribed = self.subscriber_manager.is_subscribed(sender_id)
        
        buttons = []
        
        if is_subscribed:
            buttons.append({
                'type': 'postback',
                'title': '🔕 إلغاء الإشعارات',
                'payload': 'UNSUBSCRIBE'
            })
        else:
            buttons.append({
                'type': 'postback',
                'title': '🔔 تفعيل الإشعارات',
                'payload': 'SUBSCRIBE'
            })
        
        buttons.extend([
            {
                'type': 'postback',
                'title': 'ℹ️ معلومات عن الصفحة',
                'payload': 'INFO'
            },
            {
                'type': 'postback',
                'title': '📖 آية عشوائية',
                'payload': 'RANDOM_QURAN'
            }
        ])
        
        # إضافة قائمة سريعة للتلاوة
        quick_replies = [
            {
                'content_type': 'text',
                'title': '🎧 تلاوة صوتية',
                'payload': 'AUDIO_QURAN'
            }
        ]
        
        self.fb_api.send_buttons(sender_id, welcome_text, buttons)
    
    def handle_subscribe(self, sender_id: str):
        user_profile = self.fb_api.get_user_profile(sender_id)
        name = user_profile.get('first_name', '') if user_profile else ''
        
        self.subscriber_manager.subscribe(sender_id, name)
        
        message = f"""✅ تم تفعيل الإشعارات بنجاح يا {name}!

سوف تصلك:
🌅 أذكار الصباح (6:00 صباحاً)
🌆 أذكار المساء (5:00 مساءً)
🌙 أذكار النوم (10:00 مساءً)
🕌 تذكيرات أوقات الصلاة

هل تريد تحديد موقعك الجغرافي لتلقي تذكيرات الصلاة الدقيقة؟"""
        
        quick_replies = [
            {
                'content_type': 'text',
                'title': '🇩🇿 الجزائر',
                'payload': 'LOCATION_Algiers'
            },
            {
                'content_type': 'text',
                'title': '🇸🇦 السعودية',
                'payload': 'LOCATION_Riyadh'
            },
            {
                'content_type': 'text',
                'title': '🇪🇬 مصر',
                'payload': 'LOCATION_Cairo'
            },
            {
                'content_type': 'text',
                'title': 'لاحقاً',
                'payload': 'LATER'
            }
        ]
        
        self.fb_api.send_quick_replies(sender_id, message, quick_replies)
    
    def handle_unsubscribe(self, sender_id: str):
        self.subscriber_manager.unsubscribe(sender_id)
        
        message = """🔕 تم إلغاء الإشعارات بنجاح.

لن تصلك التذكيرات الموقوتة، لكن يمكنك دائماً التفاعل معي للحصول على المحتوى الديني.

لتفعيل الإشعارات مرة أخرى، اضغط على "تفعيل الإشعارات" ✅"""
        
        self.fb_api.send_message(sender_id, message)
        self.send_welcome_message(sender_id)
    
    def handle_location_selection(self, sender_id: str, city: str):
        location = {
            'city': city,
            'country': self._get_country_from_city(city)
        }
        
        self.subscriber_manager.update_location(sender_id, location)
        
        message = f"""✅ تم تحديد موقعك: {self._get_city_arabic_name(city)}

سوف تصلك تذكيرات دقيقة بأوقات الصلاة حسب موقعك.

جزاك الله خيراً! 🤲"""
        
        self.fb_api.send_message(sender_id, message)
    
    def _get_country_from_city(self, city: str) -> str:
        city_countries = {
            'Algiers': 'Algeria',
            'Riyadh': 'Saudi Arabia',
            'Cairo': 'Egypt',
            'Dubai': 'UAE',
            'Tunis': 'Tunisia',
            'Casablanca': 'Morocco'
        }
        return city_countries.get(city, 'Saudi Arabia')
    
    def _get_city_arabic_name(self, city: str) -> str:
        arabic_names = {
            'Algiers': 'الجزائر',
            'Riyadh': 'الرياض',
            'Cairo': 'القاهرة',
            'Dubai': 'دبي',
            'Tunis': 'تونس',
            'Casablanca': 'الدار البيضاء'
        }
        return arabic_names.get(city, city)
    
    def send_info_message(self, sender_id: str):
        info_text = f"""ℹ️ معلومات عن ناشر الخير

🌟 بوت ديني شامل يقدم محتوى إسلامي موثوق

📚 المحتوى:
• القرآن الكريم (6,236 آية)
• الأحاديث النبوية (+50,000 حديث)
• الأحاديث القدسية (40 حديث)
• الأذكار المتنوعة (صباح، مساء، نوم، مناسبات)

⏰ الخدمات:
• نشر آلي على الصفحة كل ساعة
• اشتراكات ذكية للتذكيرات الموقوتة
• تنبيهات أوقات الصلاة حسب موقعك

👨‍💻 المطور: {DEVELOPER_NAME}
{DEVELOPER_FACEBOOK}

جزاكم الله خيراً على استخدام البوت! 🤲"""
        
        self.fb_api.send_message(sender_id, info_text)
    
    def send_random_quran(self, sender_id: str):
        content = self.content_manager.get_random_quran_verse()
        if content:
            self.fb_api.send_message(sender_id, content['formatted'])
        else:
            self.fb_api.send_message(sender_id, "عذراً، حدث خطأ في جلب الآية.")
    
    def send_random_hadith(self, sender_id: str):
        content = self.content_manager.get_random_hadith()
        if content:
            self.fb_api.send_message(sender_id, content['formatted'])
        else:
            self.fb_api.send_message(sender_id, "عذراً، حدث خطأ في جلب الحديث.")
    
    def send_random_azkar(self, sender_id: str):
        content = self.content_manager.get_random_azkar()
        if content:
            self.fb_api.send_message(sender_id, content['formatted'])
        else:
            self.fb_api.send_message(sender_id, "عذراً، حدث خطأ في جلب الذكر.")
    
    def send_random_quran_audio(self, sender_id: str):
        """إرسال آية قرآنية مع تلاوة صوتية"""
        content = self.content_manager.get_random_quran_verse()
        if content:
            # اختيار قارئ عشوائي
            reader = self.audio_manager.get_random_reader()
            reader_name = self.audio_manager.get_reader_name(reader)
            
            # الحصول على رابط الملف الصوتي
            audio_url = self.audio_manager.get_verse_audio_url(
                content['surah'],
                content['verse_number'],
                reader
            )
            
            # إرسال النص أولاً
            text_message = f"{content['formatted']}\n\n🎧 بصوت القارئ: {reader_name}"
            self.fb_api.send_message(sender_id, text_message)
            
            # إرسال الملف الصوتي
            self.fb_api.send_audio(sender_id, audio_url)
        else:
            self.fb_api.send_message(sender_id, "عذراً، حدث خطأ في جلب الآية.")

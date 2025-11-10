from flask import Flask, request, jsonify
import os
import requests
import logging
import json
from pymongo import MongoClient # للتخزين الدائم (MongoDB Atlas)
import datetime
import random

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ==================== الإعدادات الثابتة ====================
VERIFY_TOKEN = "boykta2030"
PAGE_ID = "876149952244490"
PAGE_ACCESS_TOKEN_VALUE = "EAAOY2RA6HZCMBP7gRUZCgBkZBEE5YTKxj7BtXeY8PdAfDgatki7qbMZCvuXbdoXLZCwKkKFWdU9TuFe3D1OmT8nfeVvl8PuOvLxzcdLZBD3ZBGjhU0VvmyZApyHsrBwfhMLrrOZCzkw15T5viRGsOP1lgp6kZB7KFEmzptEjHIAShu8nGWIawjICnXfVVqlt03hcf4748ZCogZDZD"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", PAGE_ACCESS_TOKEN_VALUE)
FB_MESSAGES_API = "https://graph.facebook.com/v18.0/me/messages"
FB_POSTING_API = f"https://graph.facebook.com/v18.0/{PAGE_ID}/feed" 

# 🌟 رابط MongoDB Atlas - يجب الحصول عليه من حسابك الخاص 🌟
MONGO_URI = os.environ.get("MONGO_URI", "YOUR_MONGO_CONNECTION_STRING")
CRON_SECRET_TOKEN = os.environ.get("CRON_SECRET_TOKEN", "EXTERNAL_CRON_TRIGGER_2025")

# ==================== دوال قاعدة البيانات (MongoDB) ====================

def get_db_collection(collection_name):
    """الاتصال بقاعدة البيانات والحصول على مجموعة معينة."""
    try:
        client = MongoClient(MONGO_URI)
        db = client.nashir_khair # اسم قاعدة البيانات
        return db[collection_name]
    except Exception as e:
        logging.error(f"MongoDB connection failed: {e}")
        return None

def is_subscribed(user_id):
    """التحقق من حالة اشتراك المستخدم."""
    collection = get_db_collection("subscribers")
    if collection:
        return collection.find_one({"_id": user_id, "subscribed": True}) is not None
    return False

# ==================== دوال الإرسال والنشر ====================

def send_message(recipient_id, message_data):
    """إرسال رسالة إلى الماسنجر."""
    payload = {'recipient': {'id': recipient_id}, 'message': message_data}
    try:
        requests.post(FB_MESSAGES_API, params={'access_token': PAGE_ACCESS_TOKEN}, json=payload)
    except Exception as e:
        logging.error(f"Failed to send message: {e}")

def post_to_page(message_text):
    """نشر المحتوى على صفحة فيسبوك."""
    try:
        requests.post(FB_POSTING_API, params={'access_token': PAGE_ACCESS_TOKEN}, json={'message': message_text})
    except Exception as e:
        logging.error(f"Failed to post to page: {e}")

# ==================== منطق الردود والأزرار ====================

def get_welcome_buttons(user_id):
    """بناء الأزرار التفاعلية."""
    subscribed = is_subscribed(user_id)
    sub_text = "🔔 إيقاف الإشعارات" if subscribed else "✅ تفعيل الإشعارات"
    sub_payload = "ACTION_UNSUBSCRIBE" if subscribed else "ACTION_SUBSCRIBE"
    
    return [
        {'type': 'postback', 'title': sub_text, 'payload': sub_payload},
        {'type': 'postback', 'title': 'ℹ️ معلومات عن البوت والمطور', 'payload': 'ACTION_INFO'},
        {'type': 'web_url', 'url': 'https://www.facebook.com/sharer/sharer.php?u=YOUR_PAGE_URL', 'title': '↩️ شارك بوت ناشر الخير'}
    ]

def send_initial_menu(sender_id):
    """إرسال رسالة الترحيب ووصف الخدمات."""
    # (نص رسالة الترحيب)
    message = "مرحباً! أنا بوت **ناشر الخير**، نظام آلي لخدمة نشر المحتوى الديني الموثوق..."
    buttons = get_welcome_buttons(sender_id)
    
    message_data = {
        'attachment': {
            'type': 'template',
            'payload': {
                'template_type': 'button',
                'text': message,
                'buttons': buttons
            }
        }
    }
    send_message(sender_id, message_data)

def handle_postback(sender_id, payload):
    """معالجة حدث Postback (الأزرار)."""
    collection = get_db_collection("subscribers")
    
    if payload == 'ACTION_SUBSCRIBE':
        collection.update_one({'_id': sender_id}, {'$set': {'subscribed': True, 'date': datetime.datetime.now()}}, upsert=True)
        send_message(sender_id, {"text": "✅ تم تفعيل خدمة الإشعارات بنجاح!"})
    elif payload == 'ACTION_UNSUBSCRIBE':
        collection.update_one({'_id': sender_id}, {'$set': {'subscribed': False}}, upsert=True)
        send_message(sender_id, {"text": "🔔 تم إلغاء خدمة الإشعارات."})
    elif payload == 'ACTION_INFO':
        send_message(sender_id, {"text": "المطور: يونس لعلجي (Younes Laldji) - https://www.facebook.com/2007younes"})
        
    # إعادة إرسال القائمة المحدثة
    send_initial_menu(sender_id) 

# ==================== منطق الجدولة عبر الاستدعاء الخارجي ====================

def run_auto_post():
    """النشر كل ساعتين."""
    # يجب قراءة المحتوى من ملفات data.
    content = f"**بسم الله الرحمن الرحيم.** (آية/حديث جديد في {datetime.datetime.now().hour} صباحاً). #بويكتا"
    post_to_page(content)

def run_subscription_messages():
    """إرسال محتوى الأذكار للمشتركين."""
    collection = get_db_collection("subscribers")
    if collection:
        # 🌟 فكرة الجدولة الواحدة: نحدد نوع المحتوى بناءً على الوقت 🌟
        current_hour = datetime.datetime.now().hour
        zekr_text = None
        
        if 5 <= current_hour < 12: zekr_text = "**أذكار الصباح**"
        elif 16 <= current_hour < 20: zekr_text = "**أذكار المساء**"
        
        if zekr_text:
            # نسحب جميع المشتركين النشطين
            subscribers = collection.find({"subscribed": True})
            message = {"text": f"{zekr_text}\n\n(نص الذكر هنا...) #بويكتا"}
            
            for sub in subscribers:
                send_message(sub['_id'], message)
            
# ==================== نقاط النهاية (Endpoints) ====================

@app.route('/webhook', methods=['GET'])
def verify():
    # ... (كود التحقق) ...
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args.get("hub.challenge"), 200
    return "Hello World", 200

@app.route('/webhook', methods=['POST'])
def handle_facebook_events():
    """معالجة رسائل الماسنجر."""
    data = request.get_json()
    if 'object' in data and data['object'] == 'page':
        for entry in data['entry']:
            for event in entry.get('messaging', []):
                sender_id = event['sender']['id']
                if event.get('message'):
                    send_initial_menu(sender_id)
                elif event.get('postback'):
                    handle_postback(sender_id, event['postback']['payload'])
    return "OK", 200

@app.route('/api/trigger', methods=['GET'])
def external_cron_trigger():
    """نقطة نهاية سرية تُستخدم لاستدعاء الجدولة من خدمة خارجية."""
    if request.args.get('secret_token') != CRON_SECRET_TOKEN:
        return jsonify({"status": "error", "message": "Unauthorized access."}), 403
    
    # تحديد النشر (كل ساعتين) والأذكار (حسب الوقت)
    current_hour = datetime.datetime.now().hour
    
    # النشر كل ساعتين (نعتمد على التوكن الخارجي للتشغيل)
    if current_hour % 2 == 0:
        run_auto_post()
    
    # إرسال الأذكار الموقوتة
    run_subscription_messages()
        
    return jsonify({"status": "success", "triggered_at": datetime.datetime.now().isoformat()}), 200

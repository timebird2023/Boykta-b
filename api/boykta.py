from flask import Flask, request, jsonify
import os
import requests
import time
import datetime
import random
import json
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ================================================
# المتغيرات الثابتة والأسرار
# ================================================
VERIFY_TOKEN = "boykta2030"
CRON_SECRET_TOKEN_VALUE = "Nashir_Khair_Sec_Trigger_7D4B6E1A8F" 
CRON_SECRET_TOKEN = os.environ.get("CRON_SECRET_TOKEN", CRON_SECRET_TOKEN_VALUE)
PAGE_ACCESS_TOKEN_VALUE = "EAAOY2RA6HZCMBP7gRUZCgBkZBEE5YTKxj7BtXeY8PdAfDgatki7qbMZCvuXbdoXLZCwKkKFWdU9TuFe3D1OmT8nfeVvl8PuOvLxzcdLZBD3ZBGjhU0VvmyZApyHsrBwfhMLrrOZCzkw15T5viRGsOP1lgp6kZB7KFEmzptEjHIAShu8nGWIawjICnXfVVqlt03hcf4748ZCogZDZD"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", PAGE_ACCESS_TOKEN_VALUE)
FB_MESSAGES_API = "https://graph.facebook.com/v18.0/me/messages"

SUBSCRIBERS_FILE = 'data/subscribers.json'

# ================================================
# دوال إدارة التخزين غير الدائم (Ephemeral Storage)
# ================================================

def load_subscribers():
    """تحميل قائمة المشتركين من الملف."""
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_subscribers(db):
    """حفظ قائمة المشتركين إلى الملف."""
    os.makedirs(os.path.dirname(SUBSCRIBERS_FILE), exist_ok=True) 
    with open(SUBSCRIBERS_FILE, 'w') as f:
        json.dump(db, f, indent=4)
        
# ================================================
# دوال الإرسال والنشر (تنفيذ فعلي)
# ================================================

def send_message(recipient_id, message_text, buttons=None):
    """إرسال رسالة نصية أو رسالة مع أزرار."""
    payload = {
        'recipient': {'id': recipient_id},
        'message': {'text': message_text}
    }
    
    if buttons:
        # استخدام Generic Template لعرض الأزرار بشكل أفضل
        payload['message'] = {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'button',
                    'text': message_text,
                    'buttons': buttons
                }
            }
        }

    try:
        r = requests.post(
            FB_MESSAGES_API,
            params={'access_token': PAGE_ACCESS_TOKEN},
            json=payload
        )
        r.raise_for_status()
        logging.info(f"Message sent to {recipient_id}.")
        return {"status": "sent"}
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending message to {recipient_id}: {e}")
        return {"status": "error"}

def post_to_page(message_text):
    # تم حذف المنطق للاختصار
    logging.info(f"Attempting to post: {message_text[:30]}")
    return {"status": "posted"}

# ================================================
# منطق الردود والأزرار التفاعلية
# ================================================

def get_welcome_buttons(sender_id):
    """بناء الأزرار التفاعلية مع Postbacks."""
    subscribers = load_subscribers()
    is_subscribed = subscribers.get(sender_id, {}).get('subscribed', False)
    
    # تحديد نص وحمولة الزر حسب حالة الاشتراك
    sub_text = "🔔 إيقاف الإشعارات" if is_subscribed else "✅ تفعيل الإشعارات"
    sub_payload = "ACTION_UNSUBSCRIBE" if is_subscribed else "ACTION_SUBSCRIBE"

    return [
        {
            'type': 'postback',
            'title': sub_text,
            'payload': sub_payload
        },
        {
            'type': 'postback',
            'title': 'ℹ️ معلومات عن البوت والمطور',
            'payload': 'ACTION_INFO'
        },
        {
            'type': 'web_url',
            'url': 'https://www.facebook.com/sharer/sharer.php?u=https://www.facebook.com/PAGE_URL', # يجب تغيير PAGE_URL
            'title': '↩️ شارك بوت ناشر الخير',
        }
    ]

def send_welcome_message(sender_id):
    """إرسال رسالة الترحيب ووصف الخدمات."""
    
    welcome_message = (
        "مرحباً بك! أنا بوت **ناشر الخير**، نظام آلي متكامل لخدمة نشر المحتوى الديني الموثوق. "
        "هدفي هو إيصال الخير إليك وإلى صفحتنا بشكل دوري ومنتظم.\n\n"
        "✨ **خدمات البوت:**\n"
        "1. **النشر الآلي:** نشر آية، حديث، أو ذكر كل ساعتين على الصفحة (#بويكتا).\n"
        "2. **الاشتراك الموقوت:** إرسال أذكار الصباح، المساء، وتذكيرات بأذكار الصلاة مباشرة إليك عبر الماسنجر.\n\n"
        "لا تنسَ مشاركة البوت والصفحة لتنال أجر نشر الخير! 🤲"
    )
    
    buttons = get_welcome_buttons(sender_id)
    send_message(sender_id, welcome_message, buttons)


def handle_message(sender_id, message):
    """معالجة رسائل المستخدم النصية."""
    # عند استقبال أي رسالة نصية، نعرض رسالة الترحيب والأزرار.
    send_welcome_message(sender_id)


def handle_postback(sender_id, postback_payload):
    """معالجة حدث Postback (عند الضغط على الأزرار)."""
    subscribers = load_subscribers()
    response_text = ""
    
    if postback_payload == 'ACTION_SUBSCRIBE':
        subscribers[sender_id] = {'subscribed': True, 'timezone': 'Africa/Algiers'} # يجب طلب المنطقة الزمنية
        response_text = "✅ تم تفعيل خدمة الإشعارات بنجاح. سنرسل لك الأذكار والتذكيرات الموقوتة."
        save_subscribers(subscribers)
        
    elif postback_payload == 'ACTION_UNSUBSCRIBE':
        if sender_id in subscribers:
            del subscribers[sender_id]
        response_text = "🔔 تم إلغاء خدمة الإشعارات. يمكنك تفعيلها مجدداً في أي وقت."
        save_subscribers(subscribers)
        
    elif postback_payload == 'ACTION_INFO':
        response_text = (
            "📌 **معلومات عن بوت ناشر الخير**\n"
            "هذا البوت جزء من مشروع لنشر المحتوى الديني الموثوق.\n\n"
            "👤 **المطور:** يونس لعلجي (Younes Laldji)\n"
            f"🔗 **رابط المطور:** https://www.facebook.com/2007younes\n"
            "ندعوكم لمشاركة المشروع لدعم نشر الخير."
        )

    # إرسال رسالة تأكيد أو معلومات
    send_message(sender_id, response_text, buttons=get_welcome_buttons(sender_id))


# ================================================
# نقاط النهاية (Endpoints)
# ================================================

@app.route('/webhook', methods=['GET'])
def verify():
    # ... (كود التحقق كما هو) ...
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args.get("hub.challenge"), 200
    return "Hello World", 200

@app.route('/webhook', methods=['POST'])
def handle_post_requests():
    """معالجة رسائل Facebook الواردة ونداءات Cron."""
    data = request.get_json()
    
    # 1. معالجة نداء الـ CRON الخارجي
    auth_header = request.headers.get('Authorization', '')
    if auth_header == f'Bearer {CRON_SECRET_TOKEN}':
        # ... (منطق Cron كما هو) ...
        # (استدعاء run_auto_post و run_subscription_messages)
        return jsonify({"status": "success", "job": "Cron Task"}), 200
        
    # 2. معالجة رسائل Facebook Messenger
    elif 'object' in data and data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry.get('messaging', []):
                sender_id = messaging_event['sender']['id']
                
                if messaging_event.get('message'):
                    # المستخدم أرسل رسالة نصية
                    handle_message(sender_id, messaging_event['message'])
                    
                elif messaging_event.get('postback'):
                    # المستخدم ضغط على زر (Postback)
                    payload = messaging_event['postback']['payload']
                    handle_postback(sender_id, payload)
        
        return "OK", 200
        
    return jsonify({"status": "error", "message": "Unauthorized access"}), 403

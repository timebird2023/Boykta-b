from flask import Flask, request, jsonify
import os
import requests
import time
import datetime
import random
from utils.content_manager import get_random_post, get_timed_zekr 

app = Flask(__name__)

#================================================
# المتغيرات الثابتة والأسرار - يجب تعيينها في بيئة Vercel
#================================================
VERIFY_TOKEN = "boykta2023"

# التوكن السري المُولَّد - قم بتعيينه في متغيرات بيئة Vercel
CRON_SECRET_TOKEN_VALUE = "Nashir_Khair_Sec_Trigger_7D4B6E1A8F" 
CRON_SECRET_TOKEN = os.environ.get("CRON_SECRET_TOKEN", CRON_SECRET_TOKEN_VALUE)

PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "EAAOY2RA6HZCMBP7gRUZCgBkZBEE5YTKxj7BtXeY8PdAfDgatki7qbMZCvuXbdoXLZCwKkKFWdU9TuFe3D1OmT8nfeVvl8PuOvLxzcdLZBD3ZBGjhU0VvmyZApyHsrBwfhMLrrOZCzkw15T5viRGsOP1lgp6kZB7KFEmzptEjHIAShu8nGWIawjICnXfVVqlt03hcf4748ZCogZDZD")
FB_MESSAGES_API = "https://graph.facebook.com/v18.0/me/messages"
FB_POSTING_API = f"https://graph.facebook.com/v18.0/me/feed?access_token={PAGE_ACCESS_TOKEN}"

# قاعدة بيانات وهمية للمشتركين (لغرض العرض)
SUBSCRIPTIONS_DB = {
    "123456789": {"subscribed": True, "timezone": "Africa/Algiers"},
    "987654321": {"subscribed": True, "timezone": "Europe/Paris"}
}

#================================================
# دوال المساعدة (للمحاكاة)
#================================================

def send_message(recipient_id, message_text, buttons=None):
    """إرسال رسالة نصية أو رسالة مع أزرار عبر Messenger API (محاكاة)."""
    print(f"*** SIMULATION: Sending message to {recipient_id}...")
    # ... الكود الفعلي لـ requests.post هنا ...
    return {"status": "sent"}

def post_to_page(message_text):
    """نشر المحتوى على صفحة فيسبوك (محاكاة)."""
    print(f"*** SIMULATION: Posting to Page: {message_text[:30]}...")
    # ... الكود الفعلي لـ requests.post هنا ...
    return {"status": "posted"}

#================================================
# منطق التشغيل التلقائي (يتم استدعاؤه بواسطة Cron)
#================================================

def run_auto_post():
    """ينفذ اختيار عشوائي وينشر على الصفحة."""
    post_content = get_random_post()
    if post_content.get("text"):
        response = post_to_page(post_content["text"])
        return f"Post attempt: {response}"
    return "No valid content found for posting."

def run_subscription_messages():
    """يرسل رسائل موقوتة لجميع المشتركين (أذكار الصباح، المساء، الصلاة)."""
    count = 0
    current_hour = datetime.datetime.now().hour
    zekr_category = None
    
    # تحديد فئة الذكر بناءً على الوقت (محاكاة بسيطة)
    if 5 <= current_hour < 12: 
        zekr_category = "أذكار الصباح"
    elif 16 <= current_hour < 20: 
        zekr_category = "أذكار المساء"
    elif current_hour == 22:
        zekr_category = "أذكار النوم" 
    
    if zekr_category:
        timed_zekr = get_timed_zekr(zekr_category)
        if timed_zekr:
            message = f"**{zekr_category}**\n{timed_zekr['text']}\n- المرجع: {timed_zekr['reference']}"
            
            for user_id, user_data in SUBSCRIPTIONS_DB.items():
                if user_data.get('subscribed'):
                    send_message(user_id, message)
                    count += 1
        
    return f"Sent {count} subscription messages. (Category: {zekr_category})"

#================================================
# نقاط النهاية (Endpoints)
#================================================

@app.route('/webhook', methods=['GET'])
def verify():
    """التحقق من الويب هوك."""
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args.get("hub.challenge"), 200
    return "Hello World", 200

@app.route('/webhook', methods=['POST'])
def handle_post_requests():
    """معالجة رسائل Facebook الواردة ونداءات Cron."""
    data = request.get_json()
    
    # 1. معالجة نداء الـ CRON الخارجي (التحقق من التوكن السري)
    auth_header = request.headers.get('Authorization', '')
    if auth_header == f'Bearer {CRON_SECRET_TOKEN}':
        job_type = data.get('job_type')
        if job_type == 'page_post':
            result = run_auto_post()
        elif job_type == 'subscription_message':
            result = run_subscription_messages()
        else:
            return jsonify({"status": "error", "message": "Invalid job type"}), 400
        return jsonify({"status": "success", "job": job_type, "result": result}), 200
        
    # 2. معالجة رسائل Facebook Messenger
    elif 'object' in data and data['object'] == 'page':
        # ... منطق معالجة رسائل فيسبوك ...
        return "OK", 200
        
    # 3. محاولة اتصال غير مصرح بها
    return jsonify({"status": "error", "message": "Unauthorized access"}), 403

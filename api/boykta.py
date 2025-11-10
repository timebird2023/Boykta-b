from flask import Flask, request, jsonify
import os
import requests
import time
import datetime
import random
import json

#================================================
# المتغيرات الثابتة والأسرار - يجب تعيينها في بيئة Vercel
#================================================
app = Flask(__name__)

#================================================
# المتغيرات الثابتة والأسرار
#================================================
VERIFY_TOKEN = "boykta2030" # تم تحديثه ليتوافق مع الاتفاق الأخير

# التوكن السري المُولَّد - قم بتعيينه في متغيرات بيئة Vercel
CRON_SECRET_TOKEN_VALUE = "Nashir_Khair_Sec_Trigger_7D4B6E1A8F" 
CRON_SECRET_TOKEN = os.environ.get("CRON_SECRET_TOKEN", CRON_SECRET_TOKEN_VALUE)

# مفتاح الوصول للصفحة (تم إضافته)
PAGE_ACCESS_TOKEN_VALUE = "EAAOY2RA6HZCMBP7gRUZCgBkZBEE5YTKxj7BtXeY8PdAfDgatki7qbMZCvuXbdoXLZCwKkKFWdU9TuFe3D1OmT8nfeVvl8PuOvLxzcdLZBD3ZBGjhU0VvmyZApyHsrBwfhMLrrOZCzkw15T5viRGsOP1lgp6kZB7KFEmzptEjHIAShu8nGWIawjICnXfVVqlt03hcf4748ZCogZDZD"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", PAGE_ACCESS_TOKEN_VALUE)

FB_MESSAGES_API = "https://graph.facebook.com/v18.0/me/messages"
FB_POSTING_API = f"https://graph.facebook.com/v18.0/me/feed?access_token={PAGE_ACCESS_TOKEN}"

# مسار ملف المشتركين (للتخزين غير الدائم المطلوب)
SUBSCRIBERS_FILE = 'data/subscribers.json'

#================================================
# دوال إدارة التخزين غير الدائم (Ephemeral Storage)
#================================================

def load_subscribers():
    """تحميل قائمة المشتركين من الملف."""
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {} # إرجاع قاموس فارغ إذا كان الملف فارغًا أو تالفًا
    return {}

def save_subscribers(db):
    """حفظ قائمة المشتركين إلى الملف."""
    # التأكد من وجود مجلد data قبل الكتابة
    os.makedirs(os.path.dirname(SUBSCRIBERS_FILE), exist_ok=True) 
    with open(SUBSCRIBERS_FILE, 'w') as f:
        json.dump(db, f, indent=4)
        
#================================================
# دوال الإرسال والنشر (تم إزالة المحاكاة - الآن تتطلب التنفيذ الفعلي)
#================================================

def send_message(recipient_id, message_text, buttons=None):
    """إرسال رسالة نصية أو رسالة مع أزرار عبر Messenger API."""
    
    # *** يجب إضافة كود requests.post الفعلي هنا ***
    print(f"*** ACTION: Attempting to send message to {recipient_id}...")
    
    # payload = { ... } # تهيئة البيانات
    # requests.post(FB_MESSAGES_API, params={'access_token': PAGE_ACCESS_TOKEN}, json=payload)
    
    return {"status": "sent"}

def post_to_page(message_text):
    """نشر المحتوى على صفحة فيسبوك."""
    
    # *** يجب إضافة كود requests.post الفعلي هنا ***
    print(f"*** ACTION: Attempting to post to Page: {message_text[:30]}...")

    # payload = { ... } # تهيئة البيانات
    # requests.post(FB_POSTING_API, json=payload)

    return {"status": "posted"}

#================================================
# منطق التشغيل التلقائي (يتم استدعاؤه بواسطة Cron)
#================================================

# ملاحظة: تم إزالة استيراد get_random_post و get_timed_zekr 
# يجب عليك توفير هذه الدوال في ملف utils/content_manager.py

def run_auto_post():
    """ينفذ اختيار عشوائي وينشر على الصفحة."""
    # هذا مجرد مثال على المحتوى، يجب استبداله بـ get_random_post()
    post_content = {"text": f"آية عشوائية أو حديث مع #بويكتا في وقت: {time.ctime()}"} 
    
    if post_content.get("text"):
        response = post_to_page(post_content["text"])
        return f"Post attempt: {response}"
    return "No valid content found for posting."

def run_subscription_messages():
    """يرسل رسائل موقوتة لجميع المشتركين."""
    count = 0
    current_hour = datetime.datetime.now().hour
    
    # 1. تحديد فئة الذكر (أذكار الصباح، المساء، الصلاة)
    # (المنطق هنا يستخدم الوقت المحلي للخادم، قد يحتاج لتعديل)
    zekr_category = "أذكار الصباح" if 5 <= current_hour < 12 else "أذكار المساء"
    
    if zekr_category:
        # يجب استبدال النص الثابت بـ get_timed_zekr(zekr_category)
        message = f"رسالة موقوتة لـ {zekr_category} مع #بويكتا" 
        
        # 2. جلب المشتركين من الملف
        subscribers = load_subscribers()
        
        for user_id, user_data in subscribers.items():
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
        # *** يجب إضافة منطق معالجة رسائل فيسبوك والـ Postbacks (أزرار الاشتراك/الإلغاء) هنا ***
        
        # مثال على منطق تسجيل/إلغاء الاشتراك باستخدام الملف المؤقت:
        # subscribers = load_subscribers()
        # subscribers['user_id_here'] = {'subscribed': True, 'timezone': '...'}
        # save_subscribers(subscribers)
        
        return "OK", 200
        
    # 3. محاولة اتصال غير مصرح بها
    return jsonify({"status": "error", "message": "Unauthorized access"}), 403

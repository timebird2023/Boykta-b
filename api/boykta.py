from flask import Flask, request, jsonify
import os
import requests
import logging
import json
import datetime
import random
import mysql.connector

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ==================== الإعدادات والثوابت ====================
VERIFY_TOKEN = "boykta2030"
PAGE_ID = "876149952244490"
PAGE_ACCESS_TOKEN_VALUE = "EAAOY2RA6HZCMBP7gRUZCgBkZBEE5YTKxj7BtXeY8PdAfDgatki7qbMZCvuXbdoXLZCwKkKFWdU9TuFe3D1OmT8nfeVvl8PuOvLxzcdLZBD3ZBGjhU0VvmyZApyHsrBwfhMLrrOZCzkw15T5viRGsOP1lgp6kZB7KFEmzptEjHIAShu8nGWIawjICnXfVVqlt03hcf4748ZCogZDZD"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", PAGE_ACCESS_TOKEN_VALUE)
FB_MESSAGES_API = "https://graph.facebook.com/v18.0/me/messages"
FB_POSTING_API = f"https://graph.facebook.com/v18.0/{PAGE_ID}/feed" 

# 🌟 التوكن السري للجدولة الخارجية 🌟
CRON_SECRET_TOKEN = os.environ.get("CRON_SECRET_TOKEN", "EXTERNAL_CRON_TRIGGER_2025")

# ==================== إعدادات MySQL ====================
DB_CONFIG = {
    'host': '91.99.159.222',
    'port': 3306,
    'user': 'u14327_RhcKAWDyUk',
    'password': 'jyqqilvgovMHH@lugFU91zp9',
    'database': 's14327_boykta', 
    'connect_timeout': 10
}

# ==================== دوال قاعدة البيانات ====================

def get_db_connection():
    """إنشاء اتصال بقاعدة البيانات."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        logging.error(f"MySQL connection failed: {err}")
        return None

def initialize_db():
    """إنشاء جدول المشتركين إذا لم يكن موجوداً (يتم استدعاؤه عند بدء التشغيل)."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # أمر SQL لإنشاء الجدول
            create_table_query = """
            CREATE TABLE IF NOT EXISTS subscribers (
                psid VARCHAR(255) PRIMARY KEY,
                subscribed BOOLEAN NOT NULL,
                last_activity DATETIME
            );
            """
            cursor.execute(create_table_query)
            conn.commit()
            logging.info("Database table 'subscribers' checked/created successfully.")
        except mysql.connector.Error as err:
            logging.error(f"Error creating table: {err}")
        finally:
            conn.close()

def toggle_subscription(user_id, status):
    """تفعيل/إلغاء الاشتراك."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = "INSERT INTO subscribers (psid, subscribed, last_activity) VALUES (%s, %s, NOW()) ON DUPLICATE KEY UPDATE subscribed = %s, last_activity = NOW()"
        cursor.execute(query, (user_id, status, status))
        conn.commit()
        conn.close()
        return True
    return False

def is_subscribed(user_id):
    """التحقق من حالة الاشتراك."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT subscribed FROM subscribers WHERE psid = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result and result['subscribed'] == 1
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

# ==================== منطق الجدولة والنشر ====================

def run_auto_post():
    """تنفيذ النشر كل ساعتين."""
    # 🚨 يجب هنا استبدال هذا النص بقراءة عشوائية من مجلد data/ 🚨
    content = f"**بسم الله الرحمن الرحيم.** (آية/حديث جديد في {datetime.datetime.now().hour} صباحاً). #بويكتا"
    post_to_page(content)

def run_subscription_messages():
    """إرسال محتوى الأذكار للمشتركين."""
    conn = get_db_connection()
    if not conn: return
    
    cursor = conn.cursor(dictionary=True)
    try:
        # ... (منطق تحديد نوع الذكر وسحب المشتركين وإرسال الرسائل) ...
        pass
    finally:
        conn.close()

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
    # ... (منطق معالجة الأزرار) ...
    send_initial_menu(sender_id) 

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
    # ... (منطق معالجة الرسائل) ...
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
    """نقطة نهاية سري يُستخدم لاستدعاء الجدولة من خدمة خارجية."""
    if request.args.get('secret_token') != CRON_SECRET_TOKEN:
        return jsonify({"status": "error", "message": "Unauthorized access."}), 403
    
    # ... (منطق النشر كل ساعتين وإرسال الأذكار) ...
    current_hour = datetime.datetime.now().hour
    if current_hour % 2 == 0:
        run_auto_post()
    
    run_subscription_messages()
        
    return jsonify({"status": "success", "triggered_at": datetime.datetime.now().isoformat()}), 200

# 🚨 يتم استدعاء تهيئة قاعدة البيانات عند بدء تشغيل الخادم 🚨
initialize_db()

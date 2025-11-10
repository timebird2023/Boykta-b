from flask import Flask, request, jsonify
import os
import requests
import logging
import json
import datetime
import random
import mysql.connector
from pathlib import Path # استخدام مكتبة pathlib الحديثة للتعامل مع المسارات

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

# ==================== إعدادات تحميل البيانات ====================
DATA_DIR = Path(__file__).parent / 'data'
APP_DATA = {} # القاموس العالمي لتخزين كل محتوى JSON المحمل

def load_all_app_data():
    """
    تحميل جميع ملفات JSON من المجلدات الفرعية (azkar, hadith, quran) داخل مجلد data.
    """
    global APP_DATA
    data = {}
    
    if not DATA_DIR.is_dir():
        logging.error(f"Data directory not found: {DATA_DIR}. Cannot load content.")
        return {}

    for folder_path in DATA_DIR.iterdir():
        if folder_path.is_dir():
            folder_name = folder_path.name
            data[folder_name] = {}
            logging.info(f"Loading data from folder: {folder_name}")
            
            for file_path in folder_path.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        # المفتاح هو اسم الملف بدون اللاحقة (مثل 'bukhari', 'quran', 'azkar')
                        data_key = file_path.stem
                        data[folder_name][data_key] = json.load(f)
                    logging.info(f"  - Loaded file: {file_path.name}")
                except json.JSONDecodeError:
                    logging.error(f"  - ERROR: JSON Decode failed in: {file_path.name}")
                except Exception as e:
                    logging.error(f"  - ERROR: Failed to read file {file_path.name}: {e}")
                    
    APP_DATA = data
    logging.info(f"✅ Data loading complete. Available categories: {list(APP_DATA.keys())}")

def get_random_content():
    """اختيار محتوى ديني عشوائي (آية، حديث، أو ذكر) ونص مصدره."""
    
    # قائمة الفئات المتوفرة التي نريد النشر منها (مثل hadith, quran)
    publishable_categories = ['hadith', 'quran']
    
    # فلترة الفئات المتاحة والتحقق من أنها غير فارغة
    valid_categories = [c for c in publishable_categories if c in APP_DATA and APP_DATA[c]]
    
    if not valid_categories:
        return "عفواً، لا توجد بيانات للنشر (hadith أو quran).", "System"

    # اختيار فئة عشوائية (مثلاً: hadith)
    category = random.choice(valid_categories)
    
    # اختيار مصدر عشوائي داخل الفئة (مثلاً: bukhari, muslim, quran)
    sources = APP_DATA[category]
    source_key = random.choice(list(sources.keys()))
    content_list = sources[source_key]
    
    chosen_item = None
    
    # التعامل مع البيانات، بافتراض أنها قائمة أو قاموس
    if isinstance(content_list, list) and content_list:
        chosen_item = random.choice(content_list)
    elif isinstance(content_list, dict) and content_list:
        # إذا كان قاموساً، نفترض أن القيم هي العناصر
        chosen_item = random.choice(list(content_list.values()))
    
    if chosen_item:
        # محاولة استخراج النص (يجب تكييف هذا حسب بنية ملفاتك الفعلية)
        if isinstance(chosen_item, str):
            content_text = chosen_item
        elif isinstance(chosen_item, dict):
            # محاولة استخراج نص من مفاتيح شائعة (text, content, ayah)
            content_text = chosen_item.get('text') or chosen_item.get('content') or chosen_item.get('ayah') or str(chosen_item)
        else:
            content_text = str(chosen_item)
        
        # تنسيق اسم المصدر (مثلاً: Hadith/bukhari)
        source_name = f"({category}/{source_key})"
        return content_text, source_name
    
    return "عفواً، لم نتمكن من العثور على محتوى مناسب.", f"{category}/{source_key}"


def get_random_azkar():
    """اختيار ذكر عشوائي من ملف azkar.json."""
    if 'azkar' in APP_DATA and 'azkar' in APP_DATA['azkar']:
        azkar_list = APP_DATA['azkar']['azkar']
        
        chosen_item = None
        if isinstance(azkar_list, list) and azkar_list:
            chosen_item = random.choice(azkar_list)
        elif isinstance(azkar_list, dict) and azkar_list:
             chosen_item = random.choice(list(azkar_list.values()))
             
        if chosen_item:
            if isinstance(chosen_item, str):
                return chosen_item
            elif isinstance(chosen_item, dict):
                # البحث عن مفتاح نصي للذكر (يجب تكييف هذا)
                return chosen_item.get('text') or chosen_item.get('content') or str(chosen_item)
            return str(chosen_item)
            
    return "لا يوجد ذكر لارساله حالياً."

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
    """تنفيذ النشر العشوائي (آية/حديث) على الصفحة كل ساعتين."""
    content, source = get_random_content()
    
    # تنسيق الرسالة للنشر
    message = f"**{content}**\n\nالمصدر: {source}\n\n#ناشر_الخير #بويكتا"
    
    logging.info(f"Attempting to post: {message}")
    post_to_page(message)
    

def run_subscription_messages():
    """إرسال محتوى الأذكار للمشتركين."""
    conn = get_db_connection()
    if not conn: 
        logging.error("Cannot connect to DB for subscription messages.")
        return
    
    # 1. الحصول على الذكر العشوائي
    azkar_content = get_random_azkar()
    if azkar_content == "لا يوجد ذكر لارساله حالياً.":
        logging.warning("No Azkar content available to send.")
        conn.close()
        return
        
    # 2. سحب المشتركين النشطين
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT psid FROM subscribers WHERE subscribed = TRUE")
        subscribers = cursor.fetchall()
        
        message_data = {'text': f"💬 ذكر اليوم:\n\n{azkar_content}\n\nلإيقاف الإشعارات اضغط على زر 'إيقاف الإشعارات' في القائمة الرئيسية."}
        
        # 3. إرسال الرسائل
        for sub in subscribers:
            send_message(sub['psid'], message_data)
        
        logging.info(f"Sent Azkar message to {len(subscribers)} subscribers.")
        
    except mysql.connector.Error as err:
        logging.error(f"Error fetching subscribers: {err}")
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
        {'type': 'postback', 'title': '📖 آية أو حديث عشوائي', 'payload': 'ACTION_RANDOM_CONTENT'},
        {'type': 'postback', 'title': 'ℹ️ معلومات عن البوت والمطور', 'payload': 'ACTION_INFO'},
    ]

def send_initial_menu(sender_id, custom_message=None):
    """إرسال رسالة الترحيب ووصف الخدمات."""
    message = custom_message if custom_message else "مرحباً! أنا بوت **ناشر الخير**، نظام آلي لخدمة نشر المحتوى الديني الموثوق...\n\nاختر من القائمة أدناه:"
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
    
    if payload == 'ACTION_SUBSCRIBE':
        toggle_subscription(sender_id, True)
        send_initial_menu(sender_id, "تم تفعيل إشعارات الأذكار بنجاح! شكراً لك.")
    
    elif payload == 'ACTION_UNSUBSCRIBE':
        toggle_subscription(sender_id, False)
        send_initial_menu(sender_id, "تم إيقاف إشعارات الأذكار بنجاح. يمكنك تفعيلها مجدداً في أي وقت.")
        
    elif payload == 'ACTION_RANDOM_CONTENT':
        content, source = get_random_content()
        message = f"**{content}**\n\nالمصدر: {source}"
        send_message(sender_id, {'text': message})
        
    elif payload == 'ACTION_INFO':
        info_message = "🤖 أنا بوت **ناشر الخير**، مطور من قبل @boykta. مهمتي هي نشر المحتوى الديني الموثوق (أحاديث، آيات، أذكار) تلقائياً على صفحة فيسبوك وإرسال الأذكار للمشتركين."
        send_message(sender_id, {'text': info_message})
    
    else:
        send_initial_menu(sender_id) 

# ==================== نقاط النهاية (Endpoints) ====================

@app.route('/webhook', methods=['GET'])
def verify():
    # التحقق من التوكين
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args.get("hub.challenge"), 200
    return "Hello World", 200

@app.route('/webhook', methods=['POST'])
def handle_facebook_events():
    data = request.get_json()
    if 'object' in data and data['object'] == 'page':
        for entry in data['entry']:
            for event in entry.get('messaging', []):
                sender_id = event['sender']['id']
                if event.get('message'):
                    send_initial_menu(sender_id) # عرض القائمة عند استلام رسالة نصية
                elif event.get('postback'):
                    handle_postback(sender_id, event['postback']['payload'])
    return "OK", 200

@app.route('/api/trigger', methods=['GET'])
def external_cron_trigger():
    """نقطة نهاية سري يُستخدم لاستدعاء الجدولة من خدمة خارجية."""
    if request.args.get('secret_token') != CRON_SECRET_TOKEN:
        return jsonify({"status": "error", "message": "Unauthorized access."}), 403
    
    current_hour = datetime.datetime.now().hour
    
    # النشر التلقائي كل ساعتين (مثلاً 0, 2, 4, ...)
    if current_hour % 2 == 0:
        run_auto_post()
    
    # إرسال رسائل الأذكار (يمكنك تحديد ساعات محددة هنا إذا لزم الأمر)
    run_subscription_messages()
        
    return jsonify({"status": "success", "triggered_at": datetime.datetime.now().isoformat()}), 200

# 🚨 يتم استدعاء تهيئة قاعدة البيانات وتحميل البيانات عند بدء تشغيل الخادم 🚨
initialize_db()
load_all_app_data()

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

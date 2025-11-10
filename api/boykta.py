from flask import Flask, request, jsonify
import os
import requests
import logging
import json
import datetime
import random
import mysql.connector
from pathlib import Path

app = Flask(__name__)
# رفع مستوى تسجيل المعلومات لرؤية التفاصيل
logging.basicConfig(level=logging.DEBUG) 

# ==================== الإعدادات والثوابت ====================
VERIFY_TOKEN = "boykta2030"
PAGE_ID = "876149952244490"
PAGE_ACCESS_TOKEN_VALUE = "EAAOY2RA6HZCMBP7gRUZCgBkZBEE5YTKxj7BtXeY8PdAfDgatki7qbMZCvuXbdoXLZCwKkKFWdU9TuFe3D1OmT8nfeVvl8PuOvLxzcdLZBD3ZBGjhU0VzHSrBwfhMLrrOZCzkw15T5viRGsOP1lgp6kZB7KFEmzptEjHIAShu8nGWIawjICnXfVVqlt03hcf4748ZCogZDZD"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", PAGE_ACCESS_TOKEN_VALUE)
FB_MESSAGES_API = "https://graph.facebook.com/v18.0/me/messages"
FB_POSTING_API = f"https://graph.facebook.com/v18.0/{PAGE_ID}/feed" 

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
    تحميل جميع ملفات JSON من المجلدات الفرعية مع تسجيل مفصل للأخطاء.
    """
    global APP_DATA
    data = {}
    
    logging.info(f"Attempting to load data from path: {DATA_DIR.resolve()}")
    
    if not DATA_DIR.is_dir():
        # هذا الخطأ هو السبب الأكثر شيوعاً للفشل في بيئات مثل Vercel إذا لم يتم رفع مجلد data بالشكل المطلوب
        logging.error(f"❌ FATAL ERROR: Data directory not found at {DATA_DIR.resolve()}.")
        return {}

    for folder_path in DATA_DIR.iterdir():
        if folder_path.is_dir():
            folder_name = folder_path.name
            data[folder_name] = {}
            logging.info(f"Loading data from folder: {folder_name}")
            
            json_files_found = 0
            
            for file_path in folder_path.glob("*.json"):
                json_files_found += 1
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data_key = file_path.stem
                        data[folder_name][data_key] = json.load(f)
                    logging.debug(f"  - Loaded file: {file_path.name} successfully.")
                except json.JSONDecodeError as e:
                    logging.error(f"  - ❌ JSON ERROR in {file_path.name}: {e}")
                except Exception as e:
                    logging.error(f"  - ❌ FAILED to read file {file_path.name}: {e}")
            
            if json_files_found == 0:
                 logging.warning(f"  - ⚠️ WARNING: No .json files found in {folder_name}/")
                 
            if data[folder_name]:
                logging.info(f"✅ Folder '{folder_name}' loaded with {len(data[folder_name])} source(s).")
            else:
                 logging.info(f"Empty or failed to load data for folder '{folder_name}'.")

    APP_DATA = data
    logging.info(f"==================================================")
    logging.info(f"✅ GLOBAL DATA LOAD COMPLETE. Final structure keys: {list(APP_DATA.keys())}")
    logging.info(f"✅ Keys in 'hadith': {list(APP_DATA.get('hadith', {}).keys())}")
    logging.info(f"✅ Keys in 'quran': {list(APP_DATA.get('quran', {}).keys())}")
    logging.info(f"✅ Keys in 'azkar': {list(APP_DATA.get('azkar', {}).keys())}")
    logging.info(f"==================================================")

# ==================== منطق استخراج المحتوى (تم التأكيد على صحته) ====================

def get_random_content():
    """
    اختيار محتوى ديني عشوائي (آية، حديث) ونص مصدره.
    المنطق صحيح للتعامل مع بنية quran.json و hadith/*.json.
    """
    
    # قائمة الفئات المتوفرة للنشر (القرآن والأحاديث)
    publishable_categories = ['hadith', 'quran']
    
    # فلترة الفئات المتاحة والتحقق من أنها غير فارغة
    valid_categories = [c for c in publishable_categories if c in APP_DATA and APP_DATA[c]]
    
    if not valid_categories:
        logging.error("ATTEMPT FAILED: No valid data found in APP_DATA for 'hadith' or 'quran'.")
        # هذا هو سبب ظهور رسالة الخطأ "عفواً، لا توجد بيانات للنشر" في الكود الأول
        return "عفواً، لا توجد بيانات للنشر (hadith أو quran).", "System"

    # اختيار فئة عشوائية (hadith أو quran)
    category = random.choice(valid_categories)
    sources = APP_DATA[category]
    source_key = random.choice(list(sources.keys())) # مثلاً: qudsi40 أو quran
    source_data = sources[source_key]
    
    content_text = None
    
    if category == 'quran':
        # بنية القرآن: قائمة سور، وكل سورة قائمة آيات، والآية تحتوي على 'text'
        try:
            # اختيار سورة عشوائية
            random_surah = random.choice(source_data)
            surah_name = random_surah.get('name', 'سورة غير معروفة')
            verses = random_surah.get('verses', [])
            
            if verses:
                # اختيار آية عشوائية
                random_verse = random.choice(verses)
                ayah_text = random_verse.get('text', 'آية غير متوفرة')
                ayah_id = random_verse.get('id', 0)
                
                content_text = f"﴿{ayah_text}﴾"
                source_name = f"القرآن الكريم - {surah_name}، الآية: {ayah_id}"
            
        except Exception as e:
            logging.error(f"Error processing Quran data: {e}")
            
    elif category == 'hadith':
        # بنية الحديث: قاموس يحتوي على 'hadiths' وهي قائمة، والحديث يحتوي على 'arabic'
        try:
            hadiths_list = source_data.get('hadiths', [])
            if hadiths_list:
                # اختيار حديث عشوائي
                random_hadith = random.choice(hadiths_list)
                hadith_text = random_hadith.get('arabic', 'حديث غير متوفر')
                
                # استخراج اسم المصدر لجعله أكثر وضوحاً
                book_title = source_data.get('metadata', {}).get('arabic', {}).get('title', source_key)
                
                content_text = hadith_text
                source_name = f"الحديث الشريف - {book_title}"
                
        except Exception as e:
            logging.error(f"Error processing Hadith data: {e}")
            
    if content_text:
        return content_text, source_name
    
    logging.warning(f"Could not find a publishable item in source: {category}/{source_key}")
    return "عفواً، لم نتمكن من العثور على محتوى مناسب.", f"{category}/{source_key} - Data Structure Error"


def get_random_azkar():
    """
    اختيار ذكر عشوائي من ملف azkar.json.
    المنطق صحيح للتعامل مع بنية azkar.json.
    """
    if 'azkar' in APP_DATA and 'azkar' in APP_DATA['azkar']:
        azkar_data = APP_DATA['azkar'].get('azkar', {}) # الحصول على محتوى azkar.json

        # افتراض أن الذكر موجود في مفتاح 'rows' كقائمة قوائم
        azkar_rows = azkar_data.get('rows', [])
        
        if azkar_rows and isinstance(azkar_rows, list):
            # اختيار صف عشوائي
            random_row = random.choice(azkar_rows)
            
            # الذكر هو العنصر الثاني (Index 1) في الصف، مع التأكد من وجوده
            if len(random_row) > 1:
                zekr_text = random_row[1]
                # إزالة أي مسافات زائدة
                return zekr_text.strip()
            
    return "لا يوجد ذكر لارساله حالياً."

# ==================== دوال قاعدة البيانات (بدون تغيير) ====================

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

# ==================== دوال الإرسال والنشر (بدون تغيير) ====================

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

# ==================== منطق الجدولة والنشر (بدون تغيير) ====================

def run_auto_post():
    """تنفيذ النشر العشوائي (آية/حديث) على الصفحة كل ساعتين."""
    content, source = get_random_content()
    
    message = f"**{content}**\n\nالمصدر: {source}\n\n#ناشر_الخير #بويكتا"
    
    logging.info(f"Attempting to post: {message}")
    post_to_page(message)
    

def run_subscription_messages():
    """إرسال محتوى الأذكار للمشتركين."""
    conn = get_db_connection()
    if not conn: 
        logging.error("Cannot connect to DB for subscription messages.")
        return
    
    azkar_content = get_random_azkar()
    if azkar_content == "لا يوجد ذكر لارساله حالياً.":
        logging.warning("No Azkar content available to send.")
        conn.close()
        return
        
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT psid FROM subscribers WHERE subscribed = TRUE")
        subscribers = cursor.fetchall()
        
        message_data = {'text': f"💬 ذكر اليوم:\n\n{azkar_content}\n\nلإيقاف الإشعارات اضغط على زر 'إيقاف الإشعارات' في القائمة الرئيسية."}
        
        for sub in subscribers:
            send_message(sub['psid'], message_data)
        
        logging.info(f"Sent Azkar message to {len(subscribers)} subscribers.")
        
    except mysql.connector.Error as err:
        logging.error(f"Error fetching subscribers: {err}")
    finally:
        conn.close()

# ==================== منطق الردود والأزرار (القائمة الأصلية Button Template) ====================

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
    """إرسال رسالة الترحيب ووصف الخدمات باستخدام قالب الأزرار."""
    message = custom_message if custom_message else "مرحباً! أنا بوت **ناشر الخير**، نظام آلي لخدمة نشر المحتوى الديني الموثوق...\n\nاختر من القائمة أدناه:"
    buttons = get_welcome_buttons(sender_id)
    
    # قالب الأزرار (Button Template)
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
                    # هذا الجزء يُسبب الرد على أي رسالة باستدعاء القائمة
                    send_initial_menu(sender_id)
                elif event.get('postback'):
                    handle_postback(sender_id, event['postback']['payload'])
    return "OK", 200

@app.route('/api/trigger', methods=['GET'])
def external_cron_trigger():
    """نقطة نهاية سري يُستخدم لاستدعاء الجدولة من خدمة خارجية."""
    if request.args.get('secret_token') != CRON_SECRET_TOKEN:
        return jsonify({"status": "error", "message": "Unauthorized access."}), 403
    
    current_hour = datetime.datetime.now().hour
    
    if current_hour % 2 == 0:
        run_auto_post()
    
    run_subscription_messages()
        
    return jsonify({"status": "success", "triggered_at": datetime.datetime.now().isoformat()}), 200

# 🚨 يتم استدعاء تهيئة قاعدة البيانات وتحميل البيانات عند بدء تشغيل الخادم 🚨
initialize_db()
load_all_app_data()

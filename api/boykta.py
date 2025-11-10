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
logging.basicConfig(level=logging.DEBUG) 

# ==================== الإعدادات والثوابت ====================
VERIFY_TOKEN = "boykta2030"
PAGE_ID = "876149952244490"
PAGE_ACCESS_TOKEN_VALUE = "EAAOY2RA6HZCMBP7gRUZCgBkZBEE5YTKxj7BtXeY8PdAfDgatki7qbMZCvuXbdoXLZCwKkKFWdU9TuFe3D1OmT8nfeVvl8PuOvLxzcdLZBD3ZBGjhU0VzHSrBwfhMLrrOZCzkw15T5viRGsOP1lgp6kZB7KFEmzptEjHIAShu8nGWIawjICnXfVVqlt03hcf4748ZCogZDZD"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", PAGE_ACCESS_TOKEN_VALUE)
FB_MESSAGES_API = "https://graph.facebook.com/v18.0/me/messages"
FB_POSTING_API = f"https://graph.facebook.com/v18.0/{PAGE_ID}/feed" 
FB_PROFILE_API = f"https://graph.facebook.com/v18.0/me/messenger_profile" # API لضبط القائمة الدائمة

CRON_SECRET_TOKEN = os.environ.get("CRON_SECRET_TOKEN", "EXTERNAL_CRON_TRIGGER_2025")

# ==================== إعدادات MySQL (بدون تغيير) ====================
DB_CONFIG = {
    'host': '91.99.159.222',
    'port': 3306,
    'user': 'u14327_RhcKAWDyUk',
    'password': 'jyqqilvgovMHH@lugFU91zp9',
    'database': 's14327_boykta', 
    'connect_timeout': 10
}

# ==================== إعدادات تحميل البيانات (بدون تغيير) ====================
DATA_DIR = Path(__file__).parent / 'data'
APP_DATA = {} 

def load_all_app_data():
    """تحميل جميع ملفات JSON من المجلدات الفرعية."""
    global APP_DATA
    data = {}
    
    logging.info(f"Attempting to load data from path: {DATA_DIR.resolve()}")
    
    if not DATA_DIR.is_dir():
        logging.error(f"❌ FATAL ERROR: Data directory not found at {DATA_DIR.resolve()}.")
        return {}

    for folder_path in DATA_DIR.iterdir():
        if folder_path.is_dir():
            folder_name = folder_path.name
            data[folder_name] = {}
            
            for file_path in folder_path.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data_key = file_path.stem
                        data[folder_name][data_key] = json.load(f)
                    logging.debug(f"  - Loaded file: {file_path.name} successfully.")
                except json.JSONDecodeError as e:
                    logging.error(f"  - ❌ JSON ERROR in {file_path.name}: {e}")
                except Exception as e:
                    logging.error(f"  - ❌ FAILED to read file {file_path.name}: {e}")
            
            if data[folder_name]:
                logging.info(f"✅ Folder '{folder_name}' loaded with {len(data[folder_name])} source(s).")

    APP_DATA = data
    logging.info(f"==================================================")
    logging.info(f"✅ Keys in 'hadith': {list(APP_DATA.get('hadith', {}).keys())}")
    logging.info(f"✅ Keys in 'quran': {list(APP_DATA.get('quran', {}).keys())}")
    logging.info(f"==================================================")

# ==================== منطق استخراج المحتوى (بدون تغيير) ====================

def get_random_content():
    """اختيار محتوى ديني عشوائي (آية، حديث) ونص مصدره."""
    
    publishable_categories = ['hadith', 'quran']
    valid_categories = [c for c in publishable_categories if c in APP_DATA and APP_DATA[c]]
    
    if not valid_categories:
        logging.error("ATTEMPT FAILED: No valid data found in APP_DATA for 'hadith' or 'quran'.")
        return "عفواً، لا توجد بيانات للنشر (hadith أو quran).", "System"

    category = random.choice(valid_categories)
    sources = APP_DATA[category]
    source_key = random.choice(list(sources.keys())) 
    source_data = sources[source_key]
    
    content_text = None
    source_name = f"({category}/{source_key})"

    if category == 'quran':
        try:
            random_surah = random.choice(source_data)
            surah_name = random_surah.get('name', 'سورة غير معروفة')
            verses = random_surah.get('verses', [])
            
            if verses:
                random_verse = random.choice(verses)
                ayah_text = random_verse.get('text', 'آية غير متوفرة')
                ayah_id = random_verse.get('id', 0)
                
                content_text = f"﴿{ayah_text}﴾"
                source_name = f"القرآن الكريم - {surah_name}، الآية: {ayah_id}"
            
        except Exception as e:
            logging.error(f"Error processing Quran data: {e}")
            
    elif category == 'hadith':
        try:
            hadiths_list = source_data.get('hadiths', [])
            if hadiths_list:
                random_hadith = random.choice(hadiths_list)
                hadith_text = random_hadith.get('arabic', 'حديث غير متوفر')
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
    """اختيار ذكر عشوائي من ملف azkar.json."""
    if 'azkar' in APP_DATA and 'azkar' in APP_DATA['azkar']:
        azkar_data = APP_DATA['azkar'].get('azkar', {})
        azkar_rows = azkar_data.get('rows', [])
        
        if azkar_rows and isinstance(azkar_rows, list):
            random_row = random.choice(azkar_rows)
            if len(random_row) > 1:
                return random_row[1].strip()
            
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
    """إنشاء جدول المشتركين إذا لم يكن موجوداً."""
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

# ==================== إعداد القائمة الدائمة (Persistent Menu) ====================

def get_menu_structure(user_id):
    """بناء هيكل القائمة الدائمة (تعتمد على حالة الاشتراك)."""
    # بما أن القائمة الدائمة ثابتة، يجب أن نستخدم زرين لكل خيار (اشتراك/إلغاء)
    # أو نستخدم زر واحد يؤدي إلى قائمة فرعية (الأفضل هو خيارين منفصلين هنا لتفادي التعقيد).
    
    # القائمة الدائمة لا يمكن تخصيصها لكل مستخدم بناءً على حالة الاشتراك (is_subscribed)
    # لذا سنستخدم خياراً واحداً يؤدي إلى رسالة تطلب تفعيل/إلغاء الاشتراك
    
    return [
        {
            'locale': 'default',
            'composer_input_disabled': False, # السماح للمستخدم بالكتابة
            'call_to_actions': [
                {'title': '✅ تفعيل/إيقاف الإشعارات', 'type': 'postback', 'payload': 'ACTION_TOGGLE_SUBSCRIPTION'},
                {'title': '📖 آية أو حديث عشوائي', 'type': 'postback', 'payload': 'ACTION_RANDOM_CONTENT'},
                {'title': 'ℹ️ معلومات عن البوت', 'type': 'postback', 'payload': 'ACTION_INFO'}
            ]
        },
        # يمكنك إضافة قائمة لمنطقة معينة (مثل ar_AR) إذا لزم الأمر
    ]

def set_persistent_menu():
    """
    إرسال طلب API لتعيين القائمة الدائمة للصفحة. 
    يجب استدعاؤها لمرة واحدة (مثلاً يدويًا أو عبر نقطة نهاية خاصة).
    """
    menu_payload = {
        'persistent_menu': get_menu_structure(None)
    }
    
    try:
        response = requests.post(
            FB_PROFILE_API, 
            params={'access_token': PAGE_ACCESS_TOKEN}, 
            json=menu_payload
        )
        response_data = response.json()
        if response_data.get('result') == 'success':
            logging.info("✅ Persistent Menu set successfully.")
        else:
            logging.error(f"❌ Failed to set Persistent Menu: {response_data}")
            
    except Exception as e:
        logging.error(f"Failed to send Persistent Menu request: {e}")

# ==================== منطق الردود والأزرار (تم التعديل) ====================

def send_initial_menu(sender_id, custom_message=None):
    """
    إرسال رسالة ترحيب وقائمة الأزرار التفاعلية (كبديل للقائمة الدائمة في بعض التطبيقات).
    """
    
    # رسالة ترحيب بسيطة
    message = custom_message if custom_message else "مرحباً! أنا بوت **ناشر الخير**، اختر من القائمة الدائمة بالأسفل (أو أرسل 'مساعدة')."
    
    # بناء الأزرار (نستخدمها كقالب للترحيب الأول أو في حالة عدم دعم القائمة الدائمة)
    subscribed = is_subscribed(sender_id)
    sub_text = "🔔 إيقاف الإشعارات" if subscribed else "✅ تفعيل الإشعارات"
    sub_payload = "ACTION_UNSUBSCRIBE" if subscribed else "ACTION_SUBSCRIBE"
    
    buttons = [
        {'type': 'postback', 'title': sub_text, 'payload': sub_payload},
        {'type': 'postback', 'title': '📖 آية أو حديث عشوائي', 'payload': 'ACTION_RANDOM_CONTENT'},
        {'type': 'postback', 'title': 'ℹ️ معلومات عن البوت', 'payload': 'ACTION_INFO'},
    ]
    
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
    """معالجة حدث Postback (الأزرار من القائمة الدائمة أو القالب التفاعلي)."""
    
    if payload == 'ACTION_SUBSCRIBE':
        toggle_subscription(sender_id, True)
        send_message(sender_id, {'text': "تم تفعيل إشعارات الأذكار بنجاح! شكراً لك."})
    
    elif payload == 'ACTION_UNSUBSCRIBE':
        toggle_subscription(sender_id, False)
        send_message(sender_id, {'text': "تم إيقاف إشعارات الأذكار بنجاح. يمكنك تفعيلها مجدداً من القائمة الدائمة."})
    
    # هذا الإجراء يتم استدعاؤه من القائمة الدائمة، ويتحقق من الحالة ويرسل الرد المناسب
    elif payload == 'ACTION_TOGGLE_SUBSCRIPTION':
        subscribed = is_subscribed(sender_id)
        if subscribed:
            send_initial_menu(sender_id, "حالة الاشتراك: مُفعَّل. هل تريد إلغاء الإشعارات؟")
        else:
            send_initial_menu(sender_id, "حالة الاشتراك: مُوقَف. هل تريد تفعيل إشعارات الأذكار؟")
        
    elif payload == 'ACTION_RANDOM_CONTENT':
        content, source = get_random_content()
        message = f"**{content}**\n\nالمصدر: {source}"
        send_message(sender_id, {'text': message})
        
    elif payload == 'ACTION_INFO':
        info_message = "🤖 أنا بوت **ناشر الخير**، مطور من قبل @boykta. مهمتي هي نشر المحتوى الديني الموثوق (أحاديث، آيات، أذكار) تلقائياً على صفحة فيسبوك وإرسال الأذكار للمشتركين."
        send_message(sender_id, {'text': info_message})
    
    else:
        # عند أي postback غير معروف، نرسل القائمة البديلة (الأزرار التفاعلية)
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
                
                if event.get('postback'):
                    handle_postback(sender_id, event['postback']['payload'])
                
                elif event.get('message'):
                    # إرسال القائمة التفاعلية عند استلام أي رسالة نصية (لتلبية طلبك)
                    send_initial_menu(sender_id)
                    
    return "OK", 200

@app.route('/api/trigger', methods=['GET'])
# ... (بقية الدالة run_auto_post و run_subscription_messages بدون تغيير) ...
def external_cron_trigger():
    """نقطة نهاية سري يُستخدم لاستدعاء الجدولة من خدمة خارجية."""
    if request.args.get('secret_token') != CRON_SECRET_TOKEN:
        return jsonify({"status": "error", "message": "Unauthorized access."}), 403
    
    current_hour = datetime.datetime.now().hour
    
    if current_hour % 2 == 0:
        # دوال النشر
        # run_auto_post() 
        pass # تم تعطيل النشر التلقائي مؤقتاً لتجنب النشر المتكرر أثناء الاختبار
    
    # run_subscription_messages()
    pass # تم تعطيل إرسال الأذكار مؤقتاً
        
    return jsonify({"status": "success", "triggered_at": datetime.datetime.now().isoformat()}), 200

# 🚨 يتم استدعاء تهيئة قاعدة البيانات وتحميل البيانات عند بدء تشغيل الخادم 🚨
initialize_db()
load_all_app_data()
# 🚨 هام: استدعاء دالة set_persistent_menu مرة واحدة فقط 🚨
# يمكنك استدعاء set_persistent_menu() يدوياً في مكان ما أو إزالة التعليق من السطر التالي
# set_persistent_menu() 


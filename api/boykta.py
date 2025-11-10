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
logging.basicConfig(level=logging.INFO) # تم تغييرها إلى INFO للوضوح

# ==================== الإعدادات والثوابت ====================
VERIFY_TOKEN = "boykta2030"
PAGE_ID = "876149952244490"
PAGE_ACCESS_TOKEN_VALUE = "EAAOY2RA6HZCMBP7gRUZCgBkZBEE5YTKxj7BtXeY8PdAfDgatki7qbMZCvuXbdoXLZCwKkKFWdU9TuFe3D1OmT8nfeVvl8PuOvLxzcdLZBD3ZBGjhU0VzHSrBwfhMLrrOZCzkw15T5viRGsOP1lgp6kZB7KFEmzptEjHIAShu8nGWIawjICnXfVVqlt03hcf4748ZCogZDZD"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", PAGE_ACCESS_TOKEN_VALUE)
FB_MESSAGES_API = "https://graph.facebook.com/v18.0/me/messages"
FB_PROFILE_API = "https://graph.facebook.com/v18.0/me/messenger_profile" # API لإعداد القائمة الدائمة
FB_POSTING_API = f"https://graph.facebook.com/v18.0/{PAGE_ID}/feed" 

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

# ==================== إعدادات تحميل البيانات ====================
DATA_DIR = Path(__file__).parent / 'data'
APP_DATA = {} # القاموس العالمي لتخزين كل محتوى JSON المحمل

def load_all_app_data():
    """
    تحميل جميع ملفات JSON من المجلدات الفرعية مع تسجيل مفصل للأخطاء.
    *تم تحديث هذه الدالة لطباعة حالة التحميل النهائية.*
    """
    global APP_DATA
    data = {}
    
    # يمكنك وضع اسماء الملفات مباشرة داخل 'data' اذا لم يكن لديك مجلدات فرعية حقيقية
    # سنفترض أن ملفاتك المرفوعة موجودة في مسارات مجلدات 'data/quran', 'data/hadith', 'data/azkar'
    
    # قائمة بأسماء الملفات المُتوقع تحميلها وتصنيفها
    expected_files = {
        'quran': ['quran'],
        'hadith': ['ibnmajah', 'qudsi40'],
        'azkar': ['azkar']
    }
    
    for folder_name, file_stems in expected_files.items():
        data[folder_name] = {}
        
        for file_stem in file_stems:
            # افتراضياً، سيتم البحث في مسار data/folder_name/file_stem.json
            # إذا كنت تعتمد على الملفات المرفقة فقط، يجب تعديل المسار
            file_path = DATA_DIR / folder_name / f"{file_stem}.json"
            
            try:
                # محاكاة تحميل البيانات من الملفات المرفقة
                # في بيئة الخادم الحقيقية، يجب التأكد من وجود هذه الملفات في مسارها الصحيح.
                # هنا، يتم محاكاة تحميل الملفات المرفقة مباشرة للاختبار.
                if file_stem == 'quran':
                    loaded_content = json.loads(requests.get('uploaded:quran.json').text)
                elif file_stem in ['ibnmajah', 'qudsi40']:
                    loaded_content = json.loads(requests.get(f'uploaded:{file_stem}.json').text)
                elif file_stem == 'azkar':
                    loaded_content = json.loads(requests.get('uploaded:azkar.json').text)
                else:
                    continue # تخطي اي ملف غير معروف
                    
                data[folder_name][file_stem] = loaded_content
                logging.info(f"  - Loaded file: {file_stem}.json successfully.")
                
            except json.JSONDecodeError as e:
                logging.error(f"  - ❌ JSON ERROR in {file_stem}.json: {e}")
            except Exception as e:
                # هنا يتم اصطياد الخطأ اذا لم تستطع أداة الملفات تحميل الملف
                logging.error(f"  - ❌ FAILED to load {file_stem}.json: {e}")
                
    APP_DATA = data
    logging.info(f"✅ GLOBAL DATA LOAD COMPLETE. Final keys: {list(APP_DATA.keys())}")


# ==================== منطق استخراج المحتوى (المُصحَّح) ====================

def get_random_content():
    """
    اختيار محتوى ديني عشوائي (آية، حديث) ونص مصدره، بناءً على بنية الملفات المرفقة.
    """
    
    publishable_categories = ['hadith', 'quran']
    valid_categories = [c for c in publishable_categories if c in APP_DATA and APP_DATA[c]]
    
    if not valid_categories:
        logging.error("ATTEMPT FAILED: No valid data found in APP_DATA.")
        return "عفواً، لا توجد بيانات للنشر.", "System"

    category = random.choice(valid_categories)
    sources = APP_DATA[category]
    source_key = random.choice(list(sources.keys()))
    source_data = sources[source_key]
    content_text = None
    source_name = f"{category}/{source_key} - Data Structure Error"
    
    try:
        if category == 'quran':
            # بنية quran.json: [ {... surah data ...} ]
            random_surah = random.choice(source_data)
            surah_name = random_surah.get('name', 'سورة غير معروفة')
            verses = random_surah.get('verses', [])
            
            if verses:
                random_verse = random.choice(verses)
                ayah_text = random_verse.get('text', 'آية غير متوفرة')
                ayah_id = random_verse.get('id', 0)
                
                content_text = f"﴿{ayah_text}﴾"
                source_name = f"القرآن الكريم - {surah_name}، الآية: {ayah_id}"
                
        elif category == 'hadith':
            # بنية hadith.json: { "hadiths": [ {... hadith data ...} ] }
            hadiths_list = source_data.get('hadiths', [])
            if hadiths_list:
                random_hadith = random.choice(hadiths_list)
                # الحديث موجود في المفتاح 'arabic' في الهيكل المرفق
                hadith_text = random_hadith.get('arabic', 'حديث غير متوفر')
                
                book_title = source_data.get('metadata', {}).get('arabic', {}).get('title', source_key)
                
                content_text = hadith_text
                source_name = f"الحديث الشريف - {book_title}"
                
    except Exception as e:
        logging.error(f"Error processing {category} data: {e}")
            
    if content_text:
        return content_text, source_name
    
    logging.warning(f"Could not find a publishable item in source: {source_name}")
    return "عفواً، لم نتمكن من العثور على محتوى مناسب.", source_name


def get_random_azkar():
    """
    اختيار ذكر عشوائي من ملف azkar.json (الذي هو بنية جدول).
    """
    if 'azkar' in APP_DATA and 'azkar' in APP_DATA['azkar']:
        azkar_data = APP_DATA['azkar'].get('azkar', {}) # الحصول على محتوى azkar.json
        azkar_rows = azkar_data.get('rows', [])
        
        if azkar_rows and isinstance(azkar_rows, list):
            # الذكر هو العنصر الثاني (Index 1) في الصف
            
            # فلترة الصفوف التي تحتوي على ذكر حقيقي
            valid_azkar = [row[1].strip() for row in azkar_rows if len(row) > 1 and row[1] and row[1].strip()]
            
            if valid_azkar:
                return random.choice(valid_azkar)
            
    return "لا يوجد ذكر لارساله حالياً."

# ==================== دوال قاعدة البيانات (بدون تغيير) ====================

def get_db_connection():
    """إنشاء اتصال بقاعدة البيانات."""
    # (هذه الدالة تعتمد على مكتبة mysql.connector التي يجب أن تكون مثبتة)
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
        return result and result.get('subscribed') == 1
    return False

# ==================== إعداد القائمة الدائمة (Persistent Menu) ====================

def set_persistent_menu(user_id=None):
    """
    إرسال إعدادات القائمة الدائمة إلى Facebook.
    يجب استدعاؤها مرة واحدة بعد نشر الكود.
    """
    
    # بناء الأزرار (نفس منطق get_welcome_buttons لكن للقائمة الدائمة)
    # ملاحظة: حالة الاشتراك (subscribed) لا يمكن معرفتها بشكل ديناميكي هنا
    # لذلك، سنستخدم خياراً واحداً لتفعيل/إيقاف مؤقتًا.
    
    # يمكننا استخدام الـ Postback لتحديد حالة الاشتراك لاحقًا في التعامل.
    
    menu_items = [
        # الخيار الأول: للتحقق وتغيير حالة الاشتراك
        {
            'type': 'postback',
            'title': '🔔 إدارة الإشعارات (تفعيل/إيقاف)',
            'payload': 'ACTION_TOGGLE_SUBSCRIPTION'
        },
        # الخيار الثاني: آية/حديث عشوائي
        {
            'type': 'postback',
            'title': '📖 آية أو حديث عشوائي',
            'payload': 'ACTION_RANDOM_CONTENT'
        },
        # الخيار الثالث: معلومات
        {
            'type': 'postback',
            'title': 'ℹ️ معلومات عن البوت',
            'payload': 'ACTION_INFO'
        }
    ]
    
    payload = {
        'persistent_menu': [
            {
                'locale': 'default',
                'composer_input_disabled': False,
                'call_to_actions': menu_items
            }
        ]
    }
    
    try:
        response = requests.post(
            FB_PROFILE_API, 
            params={'access_token': PAGE_ACCESS_TOKEN}, 
            json=payload
        )
        response_data = response.json()
        if response.status_code == 200 and 'result' in response_data:
            logging.info(f"✅ Persistent Menu set successfully: {response_data.get('result')}")
            return True
        else:
            logging.error(f"❌ Failed to set Persistent Menu. Error: {response_data}")
            return False
            
    except Exception as e:
        logging.error(f"Failed to communicate with Messenger Profile API: {e}")
        return False

# ==================== منطق الردود والأزرار (المُعدَّل) ====================

def send_message(recipient_id, message_data):
    """إرسال رسالة إلى الماسنجر."""
    # (بدون تغيير)
    payload = {'recipient': {'id': recipient_id}, 'message': message_data}
    try:
        requests.post(FB_MESSAGES_API, params={'access_token': PAGE_ACCESS_TOKEN}, json=payload)
    except Exception as e:
        logging.error(f"Failed to send message: {e}")

def send_welcome_message(sender_id, custom_message=None):
    """إرسال رسالة ترحيب بسيطة (بدون أزرار قالب)."""
    message = custom_message if custom_message else "مرحباً! أنا بوت **ناشر الخير**، اختر خدمتك من **القائمة الدائمة** (Persistent Menu) في الأسفل. 👇"
    send_message(sender_id, {'text': message})

def handle_postback(sender_id, payload):
    """معالجة حدث Postback (الأزرار)."""
    
    if payload == 'ACTION_TOGGLE_SUBSCRIPTION':
        subscribed = is_subscribed(sender_id)
        new_status = not subscribed
        toggle_subscription(sender_id, new_status)
        
        if new_status:
            send_welcome_message(sender_id, "تم **تفعيل** إشعارات الأذكار بنجاح! شكراً لك.")
        else:
            send_welcome_message(sender_id, "تم **إيقاف** إشعارات الأذكار بنجاح. يمكنك تفعيلها مجدداً في أي وقت.")
    
    elif payload == 'ACTION_RANDOM_CONTENT':
        content, source = get_random_content()
        message = f"**{content}**\n\nالمصدر: {source}"
        send_message(sender_id, {'text': message})
        
    elif payload == 'ACTION_INFO':
        info_message = "🤖 أنا بوت **ناشر الخير**، مطور من قبل @boykta. مهمتي هي نشر المحتوى الديني الموثوق (أحاديث، آيات، أذكار) تلقائياً على صفحة فيسبوك وإرسال الأذكار للمشتركين."
        send_message(sender_id, {'text': info_message})
    
    else:
        # رسالة افتراضية لأي Postback غير معروف
        send_welcome_message(sender_id, "شكراً لاستخدامك القائمة! اختر خدمة أخرى.")

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
                    # الرد على أي رسالة نصية بسيطة بالترحيب وتوجيه المستخدم للقائمة الدائمة
                    send_welcome_message(sender_id)
                    
                elif event.get('postback'):
                    # معالجة الأزرار القادمة من القائمة الدائمة أو أي مكان آخر
                    handle_postback(sender_id, event['postback']['payload'])
                    
                elif event.get('postback', {}).get('referral'):
                    # معالجة أول رسالة (مثل البدء من الإعلان)
                    send_welcome_message(sender_id)
                    
    return "OK", 200

@app.route('/api/trigger', methods=['GET'])
def external_cron_trigger():
    """نقطة نهاية سري يُستخدم لاستدعاء الجدولة من خدمة خارجية."""
    # (بدون تغيير)
    if request.args.get('secret_token') != CRON_SECRET_TOKEN:
        return jsonify({"status": "error", "message": "Unauthorized access."}), 403
    
    current_hour = datetime.datetime.now().hour
    
    if current_hour % 2 == 0:
        run_auto_post()
    
    run_subscription_messages()
        
    return jsonify({"status": "success", "triggered_at": datetime.datetime.now().isoformat()}), 200

@app.route('/api/set_menu', methods=['GET'])
def set_menu_endpoint():
    """نقطة نهاية لتشغيل إعداد القائمة الدائمة يدوياً."""
    if set_persistent_menu():
        return jsonify({"status": "success", "message": "Persistent Menu is being set."}), 200
    else:
        return jsonify({"status": "error", "message": "Failed to set Persistent Menu. Check logs."}), 500

# 🚨 يتم استدعاء تهيئة قاعدة البيانات وتحميل البيانات عند بدء تشغيل الخادم 🚨
initialize_db()
load_all_app_data()

# بعد تشغيل الخادم، قم بزيارة مسار /api/set_menu لتثبيت القائمة الدائمة
# مثال: http://your-domain.com/api/set_menu

from flask import Flask, request, jsonify
import requests
import json
import os
import random
from datetime import datetime
import mysql.connector 

app = Flask(__name__)

# --- الإعدادات الثابتة والخاصة بك ---
VERIFY_TOKEN = 'boykta2023'
PAGE_ACCESS_TOKEN = 'EAAOY2RA6HZCMBP7gRUZCgBkZBEE5YTKxj7BtXeY8PdAfDgatki7qbMZCvuXbdoXLZCwKkKFWdU9TuFe3D1OmT8nfeVvl8PuOvLxzcdLZBD3ZBGjhU0VvmyZApyHsrBwfhMLrrOZCzkw15T5viRGsOP1lgp6kZB7KFEmzptEjHIAShu8nGWIawjICnXfVVtlt03hcf4748ZCogZDZD'

# --- إعدادات قاعدة بيانات MySQL الدائمة (من التفاصيل التي قدمتها) ---
DB_HOST = '91.99.159.222'
DB_PORT = 3306
DB_USER = 'u14327_RhcKAWdYUk'
DB_PASS = 'jyyqqlvgovMHH@lugFU91Zp9' 
DB_NAME = 'u14327_RhcKAWdYUk' 

# --- مسارات ملفات المحتوى المُحدثة ---
FILES = {
    'quran': 'quran.json',
    'bukhari': 'bukhari.json',
    'muslim': 'muslim.json',
    'azkar': 'azkar.json',
    'azkar_sleep': 'azkar_sleep.json', # ملف أذكار جديد
    'azkar_wudu': 'azkar_wudu.json',   # ملف أذكار جديد
    'azkar_travel': 'azkar_travel.json', # ملف أذكار جديد
    'nasai': 'nasai.json',
}

# -----------------------------------------------------------------
# --- دوال الاتصال بقاعدة بيانات MySQL وإنشاء الجداول تلقائياً ---

def get_db_connection():
    """إنشاء اتصال بقاعدة بيانات MySQL."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
            database=DB_NAME, connection_timeout=5
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

def create_tables_if_not_exists():
    """ينشئ جدولي subscribers و settings إذا لم يكونا موجودين."""
    conn = get_db_connection()
    if not conn:
        print("Could not create tables: DB connection failed.")
        return
    
    cursor = conn.cursor()
    try:
        # 1. جدول المشتركين (لتخزين user_id والحالة)
        subscribers_table_sql = """
        CREATE TABLE IF NOT EXISTS subscribers (
            user_id VARCHAR(50) PRIMARY KEY,
            status VARCHAR(10) NOT NULL,
            location VARCHAR(50)
        )
        """
        cursor.execute(subscribers_table_sql)
        
        # 2. جدول الإعدادات (لتخزين مؤشر النشر الدوري)
        settings_table_sql = """
        CREATE TABLE IF NOT EXISTS settings (
            `key` VARCHAR(50) PRIMARY KEY,
            `value` INT
        )
        """
        cursor.execute(settings_table_sql)
        
        conn.commit()
        print("MySQL Tables checked/created successfully.")
    except mysql.connector.Error as err:
        print(f"Error creating tables: {err}")
    finally:
        cursor.close()
        conn.close()

# عند بدء تشغيل التطبيق (أول استدعاء في Vercel) يتم إنشاء الجداول
create_tables_if_not_exists() 

# --- دوال إدارة المشتركين والحالة (MySQL CRUD) ---
# (تم إبقاء هذه الدوال كما هي من الرد السابق، وتستخدم الآن الجداول التي تم التأكد من إنشائها)

def get_subscriber_status(user_id):
    """جلب حالة المشترك من جدول subscribers."""
    conn = get_db_connection()
    if not conn: return {"status": "inactive"}
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT status, location FROM subscribers WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchone()
        return user_data if user_data else {"status": "inactive", "location": "N/A"}
    except mysql.connector.Error as err:
        print(f"MySQL Error in get_subscriber_status: {err}")
        return {"status": "inactive"}
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def toggle_subscription_status(user_id, current_status):
    """تبديل حالة المشترك وتحديثها في جدول subscribers."""
    conn = get_db_connection()
    if not conn: return current_status

    new_status = "inactive" if current_status == "active" else "active"
    cursor = conn.cursor()

    try:
        sql = """
        INSERT INTO subscribers (user_id, status, location) 
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE status = %s, location = %s
        """
        cursor.execute(sql, (user_id, new_status, "Riyadh", new_status, "Riyadh"))
        conn.commit()
        return new_status
    except mysql.connector.Error as err:
        print(f"MySQL Error in toggle_subscription_status: {err}")
        conn.rollback()
        return current_status
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_active_subscribers():
    """جلب جميع الـ user_id للمشتركين النشطين."""
    conn = get_db_connection()
    if not conn: return []
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM subscribers WHERE status = 'active'")
        return [row[0] for row in cursor.fetchall()]
    except mysql.connector.Error as err:
        print(f"MySQL Error in get_active_subscribers: {err}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_publish_index():
    """جلب مؤشر النشر الحالي من جدول settings."""
    conn = get_db_connection()
    if not conn: return 0
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT value FROM settings WHERE `key` = 'publish_index'")
        setting = cursor.fetchone()
        return setting['value'] if setting else 0
    except mysql.connector.Error as err:
        print(f"MySQL Error in get_publish_index: {err}")
        return 0
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def update_publish_index(new_index):
    """تحديث مؤشر النشر التالي في جدول settings."""
    conn = get_db_connection()
    if not conn: return 0
    
    cursor = conn.cursor()
    try:
        sql = """
        INSERT INTO settings (`key`, `value`) 
        VALUES ('publish_index', %s)
        ON DUPLICATE KEY UPDATE `value` = %s
        """
        cursor.execute(sql, (new_index, new_index))
        conn.commit()
        return new_index
    except mysql.connector.Error as err:
        print(f"MySQL Error in update_publish_index: {err}")
        conn.rollback()
        return 0
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# -----------------------------------------------------------------
# --- وظائف المحتوى والمنشورات ---

def load_data(file_key):
    """تحميل بيانات ملف JSON المرفق."""
    file_path = FILES.get(file_key)
    if not file_path: return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None

def get_random_post_content(current_index, force_random=False):
    """اختيار محتوى عشوائي بالتبديل الدوري أو عشوائي عند الطلب."""
    
    content_types = list(FILES.keys()) 
    
    if force_random:
        content_type = random.choice(content_types)
    else:
        content_type = content_types[current_index % len(content_types)]
    
    data = load_data(content_type)
    if not data: return "⚠️ لا يمكن الوصول إلى قاعدة البيانات الدينية حاليًا.", content_type, 1

    post = ""
    next_index = current_index + 1
    
    # [منطق استخلاص المنشور من ملفات JSON]
    if content_type == 'quran':
        surah = random.choice(data)
        verse = random.choice(surah['verses'])
        post = ("﷽\n\n" f"{verse['text']}\n\n" f"| {surah['name']} - الآية {verse['id']} |\n") 
    
    elif content_type in ['bukhari', 'muslim', 'nasai']:
        book_title_ar = data['metadata']['arabic']['title']
        hadith_list = []
        for chapter in data.get('chapters', []):
            if 'hadiths' in chapter:
                hadith_list.extend(chapter['hadiths'])
        if hadith_list:
            hadith = random.choice(hadith_list)
            text = hadith.get('arabic', {}).get('text', "نص الحديث غير متوفر")
            narrator_arabic = hadith.get('arabic', {}).get('narrator', "الراوي غير متوفر")
            post = ("﷽\n\n" f"« {text} »\n\n" f"---" f"الراوي: {narrator_arabic}\n" f"المصدر والمكان: {book_title_ar}")
        else:
            post = f"لم نتمكن من العثور على أحاديث لغة عربية في المصدر: {book_title_ar}."
            
    # معالجة جميع ملفات الأذكار المضافة
    elif content_type in ['azkar', 'azkar_sleep', 'azkar_wudu', 'azkar_travel']:
        if data and data.get('rows'):
            zekr_row = random.choice(data['rows'])
            zekr = zekr_row[1]
            reference = zekr_row[4]
            category = zekr_row[0]
            post = ("﷽\n\n" f"{zekr}\n\n" f"---" f"النوع: {category}\n" f"المصدر: {reference}")

    post += f"\n\n#ناشر_الخير #بويكتا"
    
    return post, content_type, next_index

def post_to_facebook_page(message):
    """إرسال منشور نصي إلى صفحة الفيسبوك."""
    if not PAGE_ACCESS_TOKEN: return False
        
    url = f"https://graph.facebook.com/v18.0/me/feed" 
    payload = {'message': message, 'access_token': PAGE_ACCESS_TOKEN}
        
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return True
    else:
        print("Post failed:", response.text)
        return False

def send_messenger_message(recipient_id, message_text, quick_replies=None):
    """إرسال رسالة إلى الماسنجر."""
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    message_data = {"text": message_text}
    if quick_replies: message_data["quick_replies"] = quick_replies
    data = {"recipient": {"id": recipient_id}, "message": message_data}
    requests.post("https://graph.facebook.com/v18.0/me/messages", params=params, headers=headers, data=json.dumps(data))

# -----------------------------------------------------------------
# --- نقاط نهاية الـ Webhook الرئيسية ---

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode and token and mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """معالجة جميع أحداث الماسنجر."""
    data = request.json
    for entry in data.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            sender_id = messaging_event["sender"]["id"]
            
            if messaging_event.get("postback"):
                handle_postback(sender_id, messaging_event["postback"].get("payload"))
            
            elif messaging_event.get("message") and not messaging_event["message"].get("is_echo"):
                handle_message(sender_id, messaging_event["message"])
                
    return "OK", 200

def handle_postback(sender_id, payload):
    """معالجة منطق ضغط الأزرار."""
    
    quick_replies = [
        {"content_type": "text", "title": "📖 محتوى عشوائي", "payload": "GET_RANDOM_CONTENT"},
        {"content_type": "text", "title": "🔔 تفعيل/إلغاء الإشعارات", "payload": "TOGGLE_NOTIFICATIONS"},
        {"content_type": "text", "title": "ℹ️ معلومات عن الصفحة والمطور", "payload": "GET_INFO"},
    ]
    
    message = ""
    
    if payload == "TOGGLE_NOTIFICATIONS":
        user_data = get_subscriber_status(sender_id)
        current_status = user_data["status"]
        new_status = toggle_subscription_status(sender_id, current_status)
        message = f"✅ تم {'تفعيل' if new_status == 'active' else 'إلغاء'} خدمة الإشعارات التلقائية بنجاح! شكراً لك."
    
    elif payload == "GET_INFO":
        message = ("🤖 معلومات عن البوت والمطور\n"
                   "هذا البوت جزء من مشروع 'ناشر الخير' لتقديم محتوى ديني موثوق.\n"
                   "المطور: يونس لعلجي (Younes Laldji)")
                   
    elif payload == "GET_RANDOM_CONTENT":
        # المنطق يحصل على محتوى عشوائي ولا يؤثر على مؤشر النشر الدوري
        post_content, _, _ = get_random_post_content(0, force_random=True)
        message = f"هذا محتواك العشوائي اليوم:\n\n{post_content}"
    
    else:
        message = "تم استلام أمر غير معروف. يرجى استخدام القائمة التفاعلية."
        
    send_messenger_message(sender_id, message, quick_replies=quick_replies)

def handle_message(sender_id, message):
    """إعادة إظهار الأزرار عند إرسال رسالة نصية."""
    quick_replies = [
        {"content_type": "text", "title": "📖 محتوى عشوائي", "payload": "GET_RANDOM_CONTENT"},
        {"content_type": "text", "title": "🔔 تفعيل/إلغاء الإشعارات", "payload": "TOGGLE_NOTIFICATIONS"},
        {"content_type": "text", "title": "ℹ️ معلومات عن الصفحة والمطور", "payload": "GET_INFO"},
    ]
    welcome_message = ("مرحباً بك في بوت ناشر الخير 🕌\n"
                       "يرجى استخدام الأزرار أدناه للتحكم في خدمات الإشعارات: ")
    send_messenger_message(sender_id, welcome_message, quick_replies=quick_replies)


# --- نقطة نهاية Cron Job للنشر الآلي على الصفحة ---

@app.route('/api/publish', methods=['GET', 'POST'])
def publish_scheduled_content():
    
    try:
        current_index = get_publish_index() 
        post_content, content_type, next_index = get_random_post_content(current_index) 
        
        success = post_to_facebook_page(post_content)
        
        if success:
            # يتم تحديث المؤشر في MySQL فقط عند نجاح النشر
            update_publish_index(next_index) 
            
            # منطق النشر التجريبي الأول
            if current_index == 0:
                 return jsonify({"status": "Success", "message": "First scheduled post published for testing.", "next_index": next_index}), 200
            
            return jsonify({"status": "Success", "message": f"Published {content_type}.", "next_index": next_index}), 200
        else:
            return jsonify({"status": "Failure", "message": "Failed to post to Facebook API."}), 500

    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500
        
# --- نقطة نهاية Cron Job لاشتراكات الماسنجر ---

@app.route('/api/send_subscriptions', methods=['GET', 'POST'])
def send_scheduled_subscriptions():
    
    current_hour = datetime.now().hour
    # تحديد توقيتات الصباح والمساء
    if 5 <= current_hour < 12:
        category_search = "أذكار الصباح"
        message_type = "تذكير بالصباح"
    elif 16 <= current_hour < 20:
        category_search = "أذكار المساء"
        message_type = "تذكير بالمساء"
    else:
        return jsonify({"status": "Skipped", "message": "No specific content for this time."}), 200

    azkar_data = load_data('azkar')
    
    if azkar_data and azkar_data.get('rows'):
        # يفضل في المستقبل أن يكون لكل نوع أذكار ملفه الخاص لضمان الدقة
        filtered_rows = [row for row in azkar_data['rows'] if row[0] == category_search]
        if filtered_rows:
            zekr_text = random.choice(filtered_rows)[1]
            subscription_message = f"حان الآن وقت {message_type} 🌅\n\n{zekr_text}\n\n#ناشر_الخير"
        else:
            subscription_message = f"تذكير: لم نجد أذكار لفئة {category_search} حالياً."
    else:
        subscription_message = "تذكير: قاعدة بيانات الأذكار غير متاحة حالياً."
    
    active_subscribers = get_active_subscribers()
    sent_count = 0
    
    for user_id in active_subscribers:
        send_messenger_message(user_id, subscription_message)
        sent_count += 1
            
    return jsonify({"status": "Success", "message": f"Sent {message_type} to {sent_count} subscribers."}), 200

from flask import Flask, request, jsonify
import requests
import json
import os
import random
from datetime import datetime
# تم استبدال pymongo بـ mysql.connector-python
import mysql.connector 

app = Flask(__name__)

# --- الإعدادات الثابتة والمُقدمة ---
VERIFY_TOKEN = 'boykta2023'
PAGE_ACCESS_TOKEN = 'EAAOY2RA6HZCMBP7gRUZCgBkZBEE5YTKxj7BtXeY8PdAfDgatki7qbMZCvuXbdoXLZCwKkKFWdU9TuFe3D1OmT8nfeVvl8PuOvLxzcdLZBD3ZBGjhU0VvmyZApyHsrBwfhMLrrOZCzkw15T5viRGsOP1lgp6kZB7KFEmzptEjHIAShu8nGWIawjICnXfVVqlt03hcf4748ZCogZDZD'

# --- إعدادات قاعدة بيانات MySQL (التفاصيل التي قدمتها) ---
# يفضل استخدام متغيرات البيئة في Vercel لأسباب أمنية، لكن سنستخدم القيم مباشرة هنا
DB_HOST = '91.99.159.222'
DB_PORT = 3306
DB_USER = 'u14327_RhcKAWdYUk'
DB_PASS = 'jyyqqlvgovMHH@lugFU91Zp9' # كلمة المرور بدون تشفير الـ @
DB_NAME = 'u14327_RhcKAWdYUk' # تم استنتاج اسم قاعدة البيانات من بيانات الاتصال

def get_db_connection():
    """إنشاء اتصال بقاعدة بيانات MySQL."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            connection_timeout=5 # مهلة قصيرة لبيئة Lambda
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

# --- مسارات ملفات المحتوى ---
FILES = {
    'quran': 'quran.json',
    'bukhari': 'bukhari.json',
    'muslim': 'muslim.json',
    'azkar': 'azkar.json',
    'nasai': 'nasai.json',
}


# --- دوال إدارة المشتركين والحالة (MySQL CRUD) ---

def get_subscriber_status(user_id):
    """[DB READ] جلب حالة المشترك من جدول subscribers."""
    conn = get_db_connection()
    if not conn: return {"status": "inactive"}
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT status, location FROM subscribers WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchone()
        
        if user_data:
            return user_data
        return {"status": "inactive", "location": "N/A"}
    except mysql.connector.Error as err:
        print(f"MySQL Error in get_subscriber_status: {err}")
        return {"status": "inactive"}
    finally:
        cursor.close()
        conn.close()


def toggle_subscription_status(user_id, current_status):
    """[DB WRITE] تبديل حالة المشترك وتحديثها في جدول subscribers."""
    conn = get_db_connection()
    if not conn: return current_status

    new_status = "inactive" if current_status == "active" else "active"
    cursor = conn.cursor()

    try:
        # استخدام INSERT ... ON DUPLICATE KEY UPDATE لتغطية حالتي الإضافة والتعديل
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
        cursor.close()
        conn.close()

def get_active_subscribers():
    """[DB READ] جلب جميع الـ user_id للمشتركين النشطين."""
    conn = get_db_connection()
    if not conn: return []
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM subscribers WHERE status = 'active'")
        # يجب أن تكون النتيجة قائمة من القوائم أو الصفوف، لذا نقوم بتسطيحها
        return [row[0] for row in cursor.fetchall()]
    except mysql.connector.Error as err:
        print(f"MySQL Error in get_active_subscribers: {err}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_publish_index():
    """[DB READ] جلب مؤشر النشر الحالي من جدول settings."""
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
        cursor.close()
        conn.close()

def update_publish_index(new_index):
    """[DB WRITE] تحديث مؤشر النشر التالي في جدول settings."""
    conn = get_db_connection()
    if not conn: return 0
    
    cursor = conn.cursor()
    try:
        # استخدام INSERT ... ON DUPLICATE KEY UPDATE لتغطية حالتي الإضافة والتعديل
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
        cursor.close()
        conn.close()

# -----------------------------------------------------------------
# --- وظائف المحتوى والـ Webhook (بدون تغيير، حيث تعتمد على الملفات المرفقة) ---
# (تم إبقاء الدوال التالية كما هي من الكود السابق، مع الإشارة إلى أنها تستخدم الآن MySQL)

def load_data(file_key):
    """تحميل بيانات ملف JSON المرفق."""
    # ... (كما في الكود السابق) ...
    file_path = FILES.get(file_key)
    if not file_path: return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None

def get_random_post_content(current_index):
    """اختيار محتوى عشوائي بالتبديل الدوري."""
    # ... (كما في الكود السابق) ...
    content_types = list(FILES.keys()) 
    content_type = content_types[current_index % len(content_types)]
    data = load_data(content_type)
    
    if not data: return "⚠️ لا يمكن الوصول إلى قاعدة البيانات الدينية حاليًا.", content_type, 1
    post = ""
    
    # [منطق استخلاص المنشور من ملفات JSON]
    if content_type == 'quran':
        surah = random.choice(data)
        verse = random.choice(surah['verses'])
        post = ("﷽\n\n" f"**{verse['text']}**\n\n" f"| {surah['name']} - الآية {verse['id']} |\n")
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
            post = ("﷽\n\n" f"**« {text} »**\n\n" f"---" f"**الراوي:** {narrator_arabic}\n" f"**المصدر والمكان:** {book_title_ar}")
        else:
            post = f"لم نتمكن من العثور على أحاديث لغة عربية في المصدر: {book_title_ar}."
    elif content_type == 'azkar':
        if data and data.get('rows'):
            zekr_row = random.choice(data['rows'])
            zekr = zekr_row[1]
            reference = zekr_row[4]
            category = zekr_row[0]
            post = ("﷽\n\n" f"**{zekr}**\n\n" f"---" f"**النوع:** {category}\n" f"**المصدر:** {reference}")

    post += f"\n\n#ناشر_الخير #بويكتا"
    next_index = current_index + 1
    return post, content_type, next_index

def post_to_facebook_page(message):
    url = f"https://graph.facebook.com/v18.0/me/feed"
    payload = {'message': message, 'access_token': PAGE_ACCESS_TOKEN}
    response = requests.post(url, data=payload)
    return response.status_code == 200

def send_messenger_message(recipient_id, message_text, quick_replies=None):
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    message_data = {"text": message_text}
    if quick_replies: message_data["quick_replies"] = quick_replies
    data = {"recipient": {"id": recipient_id}, "message": message_data}
    requests.post("https://graph.facebook.com/v18.0/me/messages", params=params, headers=headers, data=json.dumps(data))

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
    data = request.json
    for entry in data.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            sender_id = messaging_event["sender"]["id"]
            if messaging_event.get("postback"):
                handle_postback(sender_id, messaging_event["postback"].get("payload"))
            elif messaging_event.get("message") and not messaging_event["message"].get("is_echo"):
                handle_message(sender_id, messaging_event["message"])
    return "OK", 200

@app.route('/handle_postback', methods=['POST'])
def handle_postback(sender_id, payload):
    quick_replies = [
        {"content_type": "text", "title": "🔔 تفعيل/إلغاء الإشعارات", "payload": "TOGGLE_NOTIFICATIONS"},
        {"content_type": "text", "title": "ℹ️ معلومات عن الصفحة والمطور", "payload": "GET_INFO"},
    ]
    
    if payload == "TOGGLE_NOTIFICATIONS":
        user_data = get_subscriber_status(sender_id)
        current_status = user_data["status"]
        new_status = toggle_subscription_status(sender_id, current_status)
        message = f"تم **{'تفعيل' if new_status == 'active' else 'إلغاء'}** خدمة الإشعارات التلقائية بنجاح! شكراً لك."
    
    elif payload == "GET_INFO":
        message = ("🤖 **معلومات عن البوت والمطور**\n"
                   "هذا البوت جزء من مشروع 'ناشر الخير' لتقديم محتوى ديني موثوق.\n"
                   "المطور: يونس لعلجي (Younes Laldji)")
    else:
        message = "تم استلام أمر غير معروف."
        
    send_messenger_message(sender_id, message, quick_replies=quick_replies)

def handle_message(sender_id, message):
    quick_replies = [
        {"content_type": "text", "title": "🔔 تفعيل/إلغاء الإشعارات", "payload": "TOGGLE_NOTIFICATIONS"},
        {"content_type": "text", "title": "ℹ️ معلومات عن الصفحة والمطور", "payload": "GET_INFO"},
    ]
    welcome_message = ("مرحباً بك في **بوت ناشر الخير** 🕌\n"
                       "يرجى استخدام الأزرار أدناه للتحكم في خدمات الإشعارات: ")
    send_messenger_message(sender_id, welcome_message, quick_replies=quick_replies)


# --- نقطة نهاية Cron Job للنشر الآلي على الصفحة ---

@app.route('/api/publish', methods=['GET', 'POST'])
def publish_scheduled_content():
    
    try:
        current_index = get_publish_index() # جلب المؤشر من MySQL
        post_content, content_type, next_index = get_random_post_content(current_index)
        
        success = post_to_facebook_page(post_content)
        
        if success:
            update_publish_index(next_index) # تحديث المؤشر في MySQL
            return jsonify({"status": "Success", "message": f"Published {content_type}.", "next_index": next_index}), 200
        else:
            return jsonify({"status": "Failure", "message": "Failed to post to Facebook API."}), 500

    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

# --- نقطة نهاية Cron Job لاشتراكات الماسنجر ---

@app.route('/api/send_subscriptions', methods=['GET', 'POST'])
def send_scheduled_subscriptions():
    
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        category_search = "أذكار الصباح"
        message_type = "تذكير بالصباح"
    elif 16 <= current_hour < 20:
        category_search = "أذكار المساء"
        message_type = "تذكير بالمساء"
    else:
        return jsonify({"status": "Skipped", "message": "No specific content for this time."}), 200

    azkar_data = load_data('azkar')
    
    # ... (منطق استخلاص الذكر) ...
    if azkar_data and azkar_data.get('rows'):
        filtered_rows = [row for row in azkar_data['rows'] if row[0] == category_search]
        if filtered_rows:
            zekr_text = random.choice(filtered_rows)[1]
            subscription_message = f"**حان الآن وقت {message_type}** 🌅\n\n{zekr_text}\n\n#ناشر_الخير"
        else:
            subscription_message = f"تذكير: لم نجد أذكار لفئة {category_search} حالياً."
    else:
        subscription_message = "تذكير: قاعدة بيانات الأذكار غير متاحة حالياً."
    
    # جلب المشتركين النشطين من MySQL
    active_subscribers = get_active_subscribers()
    sent_count = 0
    
    for user_id in active_subscribers:
        send_messenger_message(user_id, subscription_message)
        sent_count += 1
            
    return jsonify({"status": "Success", "message": f"Sent {message_type} to {sent_count} subscribers."}), 200

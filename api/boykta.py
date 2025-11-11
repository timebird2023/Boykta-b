from flask import Flask, request, jsonify
import requests
import json
import os
import random
from datetime import datetime

app = Flask(__name__)

# --- الإعدادات الثابتة والخاصة بك ---
VERIFY_TOKEN = 'boykta2023'
PAGE_ACCESS_TOKEN = 'EAAOY2RA6HZCMBP7gRUZCgBkZBEE5YTKxj7BtXeY8PdAfDgatki7qbMZCvuXbdoXLZCwKkKFWdU9TuFe3D1OmT8nfeVvl8PuOvLxzcdLZBD3ZBGjhU0VvmyZApyHsrBwfhMLrrOZCzkw15T5viRGsOP1lgp6kZB7KFEmzptEjHIAShu8nGWIawjICnXfVVtlt03hcf4748ZCogZDZD'

# --- قاعدة بيانات مؤقتة في الذاكرة (لحل مشكلة عدم الاستجابة) ---
# تنبيه: يتم مسح هذه البيانات عند إعادة تشغيل Vercel Function
TEMP_SUBSCRIPTIONS = {} 
TEMP_PUBLISH_INDEX = 0

# --- مسارات ملفات المحتوى المُحدثة ---
FILES = {
    'quran': 'quran.json',
    'bukhari': 'bukhari.json',
    'muslim': 'muslim.json',
    'azkar': 'azkar.json',
    'azkar_sleep': 'azkar_sleep.json', 
    'azkar_wudu': 'azkar_wudu.json',   
    'azkar_travel': 'azkar_travel.json', 
    'nasai': 'nasai.json',
}

# -----------------------------------------------------------------
# --- دوال إدارة المشتركين والحالة (الاعتماد على الذاكرة المؤقتة) ---

def get_subscriber_status(user_id):
    """جلب حالة المشترك من الذاكرة المؤقتة."""
    return TEMP_SUBSCRIPTIONS.get(user_id, {"status": "inactive", "location": "N/A"})

def toggle_subscription_status(user_id, current_status):
    """تبديل حالة المشترك في الذاكرة المؤقتة."""
    new_status = "inactive" if current_status == "active" else "active"
    TEMP_SUBSCRIPTIONS[user_id] = {"status": new_status, "location": "Riyadh"} 
    return new_status

def get_active_subscribers():
    """جلب جميع الـ user_id للمشتركين النشطين من الذاكرة المؤقتة."""
    return [uid for uid, data in TEMP_SUBSCRIPTIONS.items() if data['status'] == 'active']

def get_publish_index():
    """جلب مؤشر النشر الحالي من الذاكرة المؤقتة."""
    global TEMP_PUBLISH_INDEX
    return TEMP_PUBLISH_INDEX

def update_publish_index(new_index):
    """تحديث مؤشر النشر التالي في الذاكرة المؤقتة."""
    global TEMP_PUBLISH_INDEX
    TEMP_PUBLISH_INDEX = new_index
    return TEMP_PUBLISH_INDEX

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
        # طباعة الخطأ في سجلات Vercel إذا لم يتم العثور على ملف
        print(f"Error loading data file: {file_path}. Error: {e}")
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
        # يجب أن يكون هذا المنطق مرناً لاستخراج البيانات من جميع ملفات الحديث
        try:
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
        except Exception:
             # في حال كان هيكل الملف مختلفًا (لم تتم معالجته بشكل كامل في الـ snippets)
             post = f"﷽\n\n فشل استخلاص الحديث من مصدر {content_type}. (الرجاء التأكد من هيكل الملف)"

            
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
        # طباعة فشل النشر بالتفصيل
        print(f"Facebook Post Failed. Status: {response.status_code}, Response: {response.text}")
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
    """التحقق من الـ Webhook (عند الإعداد)."""
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
    # التحقق من نوع الحدث لمنع التعطل غير الضروري
    if data.get("object") != "page":
        return "OK", 200

    for entry in data.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            sender_id = messaging_event["sender"]["id"]
            
            if messaging_event.get("postback"):
                handle_postback(sender_id, messaging_event["postback"].get("payload"))
            
            elif messaging_event.get("message") and not messaging_event["message"].get("is_echo"):
                handle_message(sender_id, messaging_event["message"])
                
    return "OK", 200

def handle_postback(sender_id, payload):
    """معالجة منطق ضغط الأزرار (Postback)."""
    
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
        # رسالة رد واضحة
        message = f"✅ تم {'تفعيل' if new_status == 'active' else 'إلغاء'} خدمة الإشعارات التلقائية بنجاح! \n\nتذكير: يتم حفظ بياناتك مؤقتاً في ذاكرة البوت، وقد تفقد في حال إعادة التشغيل."
    
    elif payload == "GET_INFO":
        message = ("🤖 معلومات عن البوت والمطور\n"
                   "هذا البوت جزء من مشروع 'ناشر الخير' لتقديم محتوى ديني موثوق.\n"
                   "المطور: يونس لعلجي (Younes Laldji)")
                   
    elif payload == "GET_RANDOM_CONTENT":
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
@app.route('/publish', methods=['GET', 'POST'])
def publish_scheduled_content():
    
    try:
        current_index = get_publish_index() 
        post_content, content_type, next_index = get_random_post_content(current_index) 
        
        success = post_to_facebook_page(post_content)
        
        if success:
            update_publish_index(next_index) 
            
            if current_index == 0:
                 return jsonify({"status": "Success", "message": "First scheduled post published for testing.", "next_index": next_index}), 200
            
            return jsonify({"status": "Success", "message": f"Published {content_type}.", "next_index": next_index}), 200
        else:
            # خطأ 500 يظهر في Cron-Job.org كـ Failed
            return jsonify({"status": "Failure", "message": "Failed to post to Facebook API. Check Token/Permissions."}), 500

    except Exception as e:
        # خطأ 500 يظهر في Cron-Job.org كـ Failed
        print(f"CRON JOB PUBLISH ERROR: {e}")
        return jsonify({"status": "Error", "message": f"Server error during publish: {str(e)}"}), 500
        
# --- نقطة نهاية Cron Job لاشتراكات الماسنجر ---
@app.route('/send_subscriptions', methods=['GET', 'POST'])
def send_scheduled_subscriptions():
    
    try:
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
        
    except Exception as e:
        print(f"CRON JOB SUBSCRIPTIONS ERROR: {e}")
        return jsonify({"status": "Error", "message": f"Server error during subscription send: {str(e)}"}), 500

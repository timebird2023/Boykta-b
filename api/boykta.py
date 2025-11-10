from flask import Flask, request, jsonify
import os
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ==================== الإعدادات الثابتة ====================
VERIFY_TOKEN = "boykta2030"
PAGE_ACCESS_TOKEN_VALUE = "EAAOY2RA6HZCMBP7gRUZCgBkZBEE5YTKxj7BtXeY8PdAfDgatki7qbMZCvuXbdoXLZCwKkKFWdU9TuFe3D1OmT8nfeVvl8PuOvLxzcdLZBD3ZBGjhU0VvmyZApyHsrBwfhMLrrOZCzkw15T5viRGsOP1lgp6kZB7KFEmzptEjHIAShu8nGWIawjICnXfVVqlt03hcf4748ZCogZDZD"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", PAGE_ACCESS_TOKEN_VALUE)
FB_MESSAGES_API = "https://graph.facebook.com/v18.0/me/messages"
FB_POSTING_API = "https://graph.facebook.com/v18.0/{page_id}/feed" 

# 🌟 البيانات المخصصة 🌟
EXTERNAL_PROCESSOR_URL = "http://91.99.159.222:5000/process_message" 
SYNC_SECRET_TOKEN = os.environ.get("SYNC_SECRET_TOKEN", "Nashir_Khair_Sync_2025") 


@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args.get("hub.challenge"), 200
    return "Hello World", 200

@app.route('/webhook', methods=['POST'])
def handle_facebook_events():
    data = request.get_json()
    if 'object' in data and data['object'] == 'page':
        data['PAGE_ACCESS_TOKEN'] = PAGE_ACCESS_TOKEN
        data['SYNC_SECRET_TOKEN'] = SYNC_SECRET_TOKEN
        
        try:
            requests.post(EXTERNAL_PROCESSOR_URL, json=data, timeout=20)
            return "OK", 200
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to proxy to external host: {e}")
            return "OK", 200
        
    return "OK", 200

@app.route('/api/send_response', methods=['POST'])
def send_response():
    """يستقبل أمر الرد/النشر من الخادم الخارجي ويرسله إلى فيسبوك."""
    data = request.get_json()
    if data.get('SYNC_SECRET_TOKEN') != SYNC_SECRET_TOKEN:
        return jsonify({"status": "error", "message": "Unauthorized access."}), 403
    
    recipient_id = data.get('recipient_id')
    message_data = data.get('message_data')
    post_message = data.get('post_message')

    try:
        if post_message:
            # حالة النشر على الصفحة
            api_url = FB_POSTING_API.format(page_id=recipient_id) 
            r = requests.post(api_url, params={'access_token': PAGE_ACCESS_TOKEN}, json={'message': post_message})
        elif recipient_id and message_data:
            # حالة الرد على الماسنجر
            r = requests.post(FB_MESSAGES_API, params={'access_token': PAGE_ACCESS_TOKEN}, json={'recipient': {'id': recipient_id}, 'message': message_data})
            
        r.raise_for_status()
        return jsonify({"status": "sent"}), 200
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending message to FB: {e}")
        return jsonify({"status": "error"}), 500

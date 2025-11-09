from flask import Flask, request, jsonify
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import VERIFY_TOKEN
from src.messenger_handler import MessengerHandler

app = Flask(__name__)
messenger_handler = MessengerHandler()

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print('Webhook verified successfully')
        return challenge, 200
    else:
        print('Webhook verification failed')
        return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.get_json()
    
    if data.get('object') == 'page':
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                sender_id = messaging_event['sender']['id']
                
                if messaging_event.get('message'):
                    message = messaging_event['message']
                    
                    if message.get('text'):
                        message_text = message['text']
                        messenger_handler.handle_message(sender_id, message_text)
                    
                    elif message.get('quick_reply'):
                        payload = message['quick_reply']['payload']
                        messenger_handler.handle_postback(sender_id, payload)
                
                elif messaging_event.get('postback'):
                    payload = messaging_event['postback']['payload']
                    messenger_handler.handle_postback(sender_id, payload)
        
        return 'OK', 200
    
    return 'Not Found', 404

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'running',
        'bot': 'ناشر الخير - Nasher Al-Khair',
        'version': '1.0.0',
        'developer': 'Younes Laldji'
    }), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

from flask import Flask, jsonify
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scheduler import Scheduler

app = Flask(__name__)
scheduler = Scheduler()

@app.route('/api/post', methods=['GET', 'POST'])
def auto_post():
    try:
        result = scheduler.post_random_content_to_page()
        return jsonify({
            'success': result,
            'message': 'Content posted successfully' if result else 'Failed to post content'
        }), 200 if result else 500
    except Exception as e:
        print(f"Error in auto_post: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/send-notifications', methods=['GET', 'POST'])
def send_notifications():
    try:
        results = scheduler.send_timed_notifications()
        return jsonify({
            'success': True,
            'results': results
        }), 200
    except Exception as e:
        print(f"Error in send_notifications: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

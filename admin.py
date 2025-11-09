from flask import Flask, render_template_string, jsonify
from src.subscriber_manager import SubscriberManager
from src.content_manager import ContentManager
from src.scheduler import Scheduler
from datetime import datetime
import json
from pathlib import Path

app = Flask(__name__)

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم ناشر الخير</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            direction: rtl;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-icon {
            font-size: 3em;
            margin-bottom: 10px;
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        .stat-label {
            color: #666;
            font-size: 1.1em;
        }
        .content-section {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .content-section h2 {
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 15px;
            border-bottom: 1px solid #eee;
        }
        .info-row:last-child {
            border-bottom: none;
        }
        .info-label {
            font-weight: bold;
            color: #333;
        }
        .info-value {
            color: #666;
        }
        .action-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .btn {
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.3s;
            color: white;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }
        .btn-primary {
            background: #667eea;
        }
        .btn-primary:hover {
            background: #5568d3;
        }
        .btn-success {
            background: #48bb78;
        }
        .btn-success:hover {
            background: #38a169;
        }
        .btn-info {
            background: #4299e1;
        }
        .btn-info:hover {
            background: #3182ce;
        }
        .footer {
            text-align: center;
            color: white;
            margin-top: 30px;
            padding: 20px;
        }
        .status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }
        .status-active {
            background: #48bb78;
            color: white;
        }
        .status-inactive {
            background: #f56565;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌙 ناشر الخير</h1>
            <p>لوحة التحكم والإدارة</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-value">{{ stats.total }}</div>
                <div class="stat-label">إجمالي المستخدمين</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">✅</div>
                <div class="stat-value">{{ stats.active }}</div>
                <div class="stat-label">المشتركون النشطون</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📍</div>
                <div class="stat-value">{{ stats.with_location }}</div>
                <div class="stat-label">مع موقع جغرافي</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📝</div>
                <div class="stat-value">{{ content_stats.total }}</div>
                <div class="stat-label">المحتوى المنشور</div>
            </div>
        </div>

        <div class="content-section">
            <h2>📊 إحصائيات المحتوى</h2>
            <div class="info-row">
                <span class="info-label">📖 آيات قرآنية منشورة</span>
                <span class="info-value">{{ content_stats.quran }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">📚 أحاديث نبوية منشورة</span>
                <span class="info-value">{{ content_stats.hadith }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">✨ أحاديث قدسية منشورة</span>
                <span class="info-value">{{ content_stats.qudsi }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">🤲 أذكار منشورة</span>
                <span class="info-value">{{ content_stats.azkar }}</span>
            </div>
        </div>

        <div class="content-section">
            <h2>⚙️ معلومات النظام</h2>
            <div class="info-row">
                <span class="info-label">حالة البوت</span>
                <span class="status status-active">نشط ✓</span>
            </div>
            <div class="info-row">
                <span class="info-label">آخر تحديث</span>
                <span class="info-value">{{ current_time }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">الإصدار</span>
                <span class="info-value">1.0.0</span>
            </div>
            <div class="info-row">
                <span class="info-label">المطور</span>
                <span class="info-value">Younes Laldji</span>
            </div>
        </div>

        <div class="content-section">
            <h2>🎯 إجراءات سريعة</h2>
            <div class="action-buttons">
                <button class="btn btn-primary" onclick="testPost()">📤 نشر محتوى تجريبي</button>
                <button class="btn btn-success" onclick="sendNotifications()">🔔 إرسال الإشعارات</button>
                <button class="btn btn-info" onclick="refreshStats()">🔄 تحديث الإحصائيات</button>
            </div>
        </div>

        <div class="footer">
            <p>ناشر الخير © 2025 - جميع الحقوق محفوظة</p>
            <p>تم التطوير بواسطة Younes Laldji</p>
        </div>
    </div>

    <script>
        function testPost() {
            if (confirm('هل تريد نشر محتوى تجريبي على الصفحة؟')) {
                fetch('/api/post', {method: 'POST'})
                    .then(res => res.json())
                    .then(data => {
                        alert(data.success ? 'تم النشر بنجاح!' : 'فشل النشر: ' + data.message);
                        if (data.success) location.reload();
                    })
                    .catch(err => alert('حدث خطأ: ' + err));
            }
        }

        function sendNotifications() {
            if (confirm('هل تريد إرسال الإشعارات للمشتركين؟')) {
                fetch('/api/send-notifications', {method: 'POST'})
                    .then(res => res.json())
                    .then(data => {
                        alert(data.success ? 'تم إرسال الإشعارات بنجاح!' : 'فشل الإرسال');
                        if (data.success) location.reload();
                    })
                    .catch(err => alert('حدث خطأ: ' + err));
            }
        }

        function refreshStats() {
            location.reload();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def admin_dashboard():
    subscriber_manager = SubscriberManager()
    content_manager = ContentManager()
    
    stats = subscriber_manager.get_stats()
    
    content_stats = {
        'quran': len(content_manager.posted_content.get('quran', [])),
        'hadith': len(content_manager.posted_content.get('hadith', [])),
        'qudsi': len(content_manager.posted_content.get('qudsi', [])),
        'azkar': len(content_manager.posted_content.get('azkar', [])),
        'total': sum([
            len(content_manager.posted_content.get('quran', [])),
            len(content_manager.posted_content.get('hadith', [])),
            len(content_manager.posted_content.get('qudsi', [])),
            len(content_manager.posted_content.get('azkar', []))
        ])
    }
    
    return render_template_string(
        ADMIN_TEMPLATE,
        stats=stats,
        content_stats=content_stats,
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

@app.route('/api/stats')
def get_stats():
    subscriber_manager = SubscriberManager()
    content_manager = ContentManager()
    
    return jsonify({
        'subscribers': subscriber_manager.get_stats(),
        'content': content_manager.posted_content
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

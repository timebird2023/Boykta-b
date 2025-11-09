import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / '.env')

FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN', '')
FACEBOOK_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID', '')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'boykta2025')
DEVELOPER_NAME = os.getenv('DEVELOPER_NAME', 'Younes Laldji')
DEVELOPER_FACEBOOK = os.getenv('DEVELOPER_FACEBOOK', 'https://www.facebook.com/2007younes')
POST_INTERVAL_HOURS = int(os.getenv('POST_INTERVAL_HOURS', '1'))

DATA_DIR = BASE_DIR / 'data'
DB_DIR = BASE_DIR / 'db'
SUBSCRIBERS_DB = DB_DIR / 'subscribers.json'
POSTED_CONTENT_DB = DB_DIR / 'posted_content.json'

GRAPH_API_VERSION = 'v21.0'
GRAPH_API_URL = f'https://graph.facebook.com/{GRAPH_API_VERSION}'

MORNING_AZKAR_TIME = '06:00'
EVENING_AZKAR_TIME = '17:00'
SLEEP_AZKAR_TIME = '22:00'

import json
import random
import os
from pathlib import Path
from typing import Dict, List, Optional
from src.config import DATA_DIR, POSTED_CONTENT_DB, DB_DIR

class ContentManager:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.posted_content_file = POSTED_CONTENT_DB
        self.posted_content = self._load_posted_content()
        
    def _load_posted_content(self) -> Dict:
        os.makedirs(DB_DIR, exist_ok=True)
        
        if self.posted_content_file.exists():
            with open(self.posted_content_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'quran': [],
            'hadith': [],
            'azkar': [],
            'qudsi': []
        }
    
    def _save_posted_content(self):
        with open(self.posted_content_file, 'w', encoding='utf-8') as f:
            json.dump(self.posted_content, f, ensure_ascii=False, indent=2)
    
    def _mark_as_posted(self, content_type: str, content_id: str):
        if content_id not in self.posted_content[content_type]:
            self.posted_content[content_type].append(content_id)
            self._save_posted_content()
    
    def _is_posted(self, content_type: str, content_id: str) -> bool:
        return content_id in self.posted_content.get(content_type, [])
    
    def _reset_category_if_exhausted(self, content_type: str, total_count: int):
        if len(self.posted_content[content_type]) >= total_count:
            print(f"All {content_type} content posted. Resetting...")
            self.posted_content[content_type] = []
            self._save_posted_content()
    
    def get_random_quran_verse(self) -> Optional[Dict]:
        quran_file = self.data_dir / 'quran' / 'quran.json'
        
        if not quran_file.exists():
            return None
        
        with open(quran_file, 'r', encoding='utf-8') as f:
            verses = json.load(f)
        
        if not verses:
            return None
        
        self._reset_category_if_exhausted('quran', len(verses))
        
        unposted_verses = [v for v in verses if not self._is_posted('quran', str(v.get('id', v.get('verse', ''))))]
        
        if not unposted_verses:
            self.posted_content['quran'] = []
            self._save_posted_content()
            unposted_verses = verses
        
        verse = random.choice(unposted_verses)
        verse_id = str(verse.get('id', verse.get('verse', '')))
        self._mark_as_posted('quran', verse_id)
        
        return {
            'type': 'quran',
            'text': verse.get('text', verse.get('verse', '')),
            'surah': verse.get('surah', verse.get('chapter', '')),
            'verse_number': verse.get('verse', verse.get('id', '')),
            'formatted': f"📖 {verse.get('text', '')}\n\n﴿ سورة {self._get_surah_name(verse.get('surah', 1))} - آية {verse.get('verse', '')} ﴾\n\n#بويكتا"
        }
    
    def _get_surah_name(self, surah_number: int) -> str:
        surah_names = {
            1: "الفاتحة", 2: "البقرة", 3: "آل عمران", 4: "النساء", 5: "المائدة",
            6: "الأنعام", 7: "الأعراف", 8: "الأنفال", 9: "التوبة", 10: "يونس",
            11: "هود", 12: "يوسف", 13: "الرعد", 14: "إبراهيم", 15: "الحجر",
            16: "النحل", 17: "الإسراء", 18: "الكهف", 19: "مريم", 20: "طه",
            21: "الأنبياء", 22: "الحج", 23: "المؤمنون", 24: "النور", 25: "الفرقان",
            26: "الشعراء", 27: "النمل", 28: "القصص", 29: "العنكبوت", 30: "الروم",
            31: "لقمان", 32: "السجدة", 33: "الأحزاب", 34: "سبأ", 35: "فاطر",
            36: "يس", 37: "الصافات", 38: "ص", 39: "الزمر", 40: "غافر"
        }
        return surah_names.get(surah_number, str(surah_number))
    
    def get_random_hadith(self) -> Optional[Dict]:
        hadith_dir = self.data_dir / 'hadith'
        
        if not hadith_dir.exists():
            return None
        
        hadith_files = list(hadith_dir.glob('*.json'))
        hadith_files = [f for f in hadith_files if 'qudsi' not in f.name]
        
        if not hadith_files:
            return None
        
        hadith_file = random.choice(hadith_files)
        
        with open(hadith_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'hadiths' in data:
            hadiths = data['hadiths']
        elif isinstance(data, list):
            hadiths = data
        else:
            return None
        
        if not hadiths:
            return None
        
        unposted_hadiths = [h for h in hadiths if not self._is_posted('hadith', str(h.get('id', '')))]
        
        if not unposted_hadiths:
            hadith = random.choice(hadiths)
        else:
            hadith = random.choice(unposted_hadiths)
        
        hadith_id = str(hadith.get('id', ''))
        self._mark_as_posted('hadith', hadith_id)
        
        book_names = {
            'bukhari': 'صحيح البخاري',
            'muslim': 'صحيح مسلم',
            'abudawud': 'سنن أبي داود',
            'tirmidhi': 'سنن الترمذي',
            'nasai': 'سنن النسائي',
            'ibnmajah': 'سنن ابن ماجه'
        }
        
        book_name = book_names.get(hadith_file.stem, hadith_file.stem)
        
        return {
            'type': 'hadith',
            'text': hadith.get('arabic', ''),
            'book': book_name,
            'formatted': f"📚 {hadith.get('arabic', '')}\n\n﴿ {book_name} ﴾\n\n#بويكتا"
        }
    
    def get_random_hadith_qudsi(self) -> Optional[Dict]:
        qudsi_file = self.data_dir / 'hadith' / 'qudsi40.json'
        
        if not qudsi_file.exists():
            return None
        
        with open(qudsi_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'hadiths' in data:
            hadiths = data['hadiths']
        elif isinstance(data, list):
            hadiths = data
        else:
            return None
        
        if not hadiths:
            return None
        
        self._reset_category_if_exhausted('qudsi', len(hadiths))
        
        unposted = [h for h in hadiths if not self._is_posted('qudsi', str(h.get('id', '')))]
        
        if not unposted:
            self.posted_content['qudsi'] = []
            self._save_posted_content()
            unposted = hadiths
        
        hadith = random.choice(unposted)
        hadith_id = str(hadith.get('id', ''))
        self._mark_as_posted('qudsi', hadith_id)
        
        return {
            'type': 'qudsi',
            'text': hadith.get('arabic', ''),
            'formatted': f"✨ {hadith.get('arabic', '')}\n\n﴿ الأحاديث القدسية ﴾\n\n#بويكتا"
        }
    
    def get_random_azkar(self, category: Optional[str] = None) -> Optional[Dict]:
        azkar_file = self.data_dir / 'azkar' / 'azkar.json'
        
        if not azkar_file.exists():
            return None
        
        with open(azkar_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'rows' in data:
            azkar_rows = data['rows']
            azkar = []
            for row in azkar_rows:
                if isinstance(row, list) and len(row) >= 4:
                    azkar.append({
                        'category': row[0] if len(row) > 0 else '',
                        'zekr': row[1] if len(row) > 1 else '',
                        'count': int(row[3]) if len(row) > 3 and str(row[3]).isdigit() else 1,
                    })
        elif isinstance(data, list):
            azkar = data
        else:
            return None
        
        if not azkar:
            return None
        
        if category:
            azkar = [a for a in azkar if a.get('category', '') == category]
        
        if not azkar:
            return None
        
        self._reset_category_if_exhausted('azkar', len(azkar))
        
        unposted = [a for a in azkar if not self._is_posted('azkar', str(a.get('zekr', ''))[:50])]
        
        if not unposted:
            zekr = random.choice(azkar)
        else:
            zekr = random.choice(unposted)
        
        zekr_id = str(zekr.get('zekr', ''))[:50]
        self._mark_as_posted('azkar', zekr_id)
        
        count = zekr.get('count', 1)
        count_text = f" ({count}×)" if count > 1 else ""
        
        return {
            'type': 'azkar',
            'text': zekr.get('zekr', ''),
            'category': zekr.get('category', ''),
            'count': count,
            'formatted': f"🤲 {zekr.get('zekr', '')}{count_text}\n\n﴿ {zekr.get('category', 'الأذكار')} ﴾\n\n#بويكتا"
        }
    
    def get_random_content(self) -> Optional[Dict]:
        content_types = [
            ('quran', self.get_random_quran_verse),
            ('hadith', self.get_random_hadith),
            ('qudsi', self.get_random_hadith_qudsi),
            ('azkar', self.get_random_azkar),
        ]
        
        random.shuffle(content_types)
        
        for content_type, getter in content_types:
            content = getter()
            if content:
                return content
        
        return None
    
    def get_morning_azkar(self) -> List[Dict]:
        return self._get_azkar_by_category('أذكار الصباح')
    
    def get_evening_azkar(self) -> List[Dict]:
        return self._get_azkar_by_category('أذكار المساء')
    
    def get_sleep_azkar(self) -> List[Dict]:
        return self._get_azkar_by_category('أذكار النوم')
    
    def _get_azkar_by_category(self, category: str) -> List[Dict]:
        azkar_file = self.data_dir / 'azkar' / 'azkar.json'
        
        if not azkar_file.exists():
            return []
        
        with open(azkar_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'rows' in data:
            azkar_rows = data['rows']
            azkar = []
            for row in azkar_rows:
                if isinstance(row, list) and len(row) >= 4:
                    azkar.append({
                        'category': row[0] if len(row) > 0 else '',
                        'zekr': row[1] if len(row) > 1 else '',
                        'count': int(row[3]) if len(row) > 3 and str(row[3]).isdigit() else 1,
                    })
        elif isinstance(data, list):
            azkar = data
        else:
            return []
        
        return [a for a in azkar if a.get('category', '') == category]

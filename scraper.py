"""
Lex.uz Avtomatik Scraper
Har kuni qonunlarni parsing qilib, JSON formatda saqlaydi
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional
import time

# ==============================================================================
# QONUNLAR RO'YXATI
# ==============================================================================
LAWS_TO_SCRAPE = {
    "Konstitutsiya": "https://lex.uz/docs/-6445145",
    "Mehnat_Kodeksi": "https://lex.uz/docs/-6257288",
    "Fuqarolik_Kodeksi": "https://lex.uz/docs/-111189",
    "Jinoyat_Kodeksi": "https://lex.uz/docs/-111453",
    "Oila_Kodeksi": "https://lex.uz/docs/-104720",
    "Mamuriy_Javobgarlik_Kodeksi": "https://lex.uz/docs/-97664",
    "Soliq_Kodeksi": "https://lex.uz/docs/-4674902",
    "Yer_Kodeksi": "https://lex.uz/docs/-152653",
    "Uy_Joy_Kodeksi": "https://lex.uz/docs/-106136",
    "Suv_Kodeksi": "https://lex.uz/docs/-7655343",
    "Kiberxavfsizlik_Qonuni": "https://lex.uz/docs/-5960604",
    "Axborotlashtirish_Qonuni": "https://lex.uz/docs/-83472",
    "Shaxsiy_Malumotlar_Qonuni": "https://lex.uz/docs/-4396419",
    "Talim_Qonuni": "https://lex.uz/docs/-16188",
    "Maktabgacha_Talim_Qonuni": "https://lex.uz/docs/-4646908",
    "Tadbirkorlik_Kafolatlari_Qonuni": "https://lex.uz/docs/-2081",
    "Tabiatni_Muhofaza_Qilish_Qonuni": "https://lex.uz/docs/-107115",
    "Fuqarolik_Protsessual_Kodeksi": "https://lex.uz/docs/-3517337",
    "Mamuriy_Sud_Ishlarini_Yuritish_Kodeksi": "https://lex.uz/docs/-3527353",
    "Saylov_Kodeksi": "https://lex.uz/docs/-4386848"
}

# Output papka
OUTPUT_DIR = "lex_structured"
LOG_FILE = "logs/scraper.log"

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def log_message(message: str):
    """Log xabarlarini faylga va consolega yozish"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\\n")


def clean_text(text: str) -> str:
    """Matnni tozalash"""
    if not text:
        return ""
    
    # Ortiqcha bo'shliqlarni olib tashlash
    text = re.sub(r'\\s+', ' ', text)
    text = text.strip()
    
    return text


def extract_article_number(text: str) -> Optional[str]:
    """Modda raqamini ajratib olish"""
    # "1-modda", "Modda 1", "Статья 1" formatlarini qo'llab-quvvatlash
    patterns = [
        r'(\\d+)-modda',
        r'modda\\s+(\\d+)',
        r'(\\d+)-статья',
        r'статья\\s+(\\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def scrape_law_document(url: str, doc_name: str) -> Dict[str, dict]:
    """Bitta qonun hujjatini parsing qilish"""
    log_message(f"🔄 Parsing: {doc_name} - {url}")
    
    try:
        # HTTP request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # HTML parsing
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Asosiy kontent
        content_div = soup.find(id="divBody")
        if not content_div:
            log_message(f"⚠️ divBody topilmadi: {doc_name}")
            return {}
        
        articles = {}
        current_article_num = None
        current_title = ""
        current_content = []
        
        # Matnni olish
        full_text = clean_text(content_div.get_text())
        
        # Barcha elementlarni ketma-ket o'qish
        elements = content_div.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'div', 'span'])
        
        if not elements:
            # Agar elementlar bo'lmasa, butun matnni saqlash
            articles["1"] = {
                "title": doc_name,
                "content": full_text
            }
            log_message(f"✅ Tayyor: {doc_name} - Butun matn saqlandi ({len(full_text)} belgi)")
            return articles

        for element in elements:
            text = clean_text(element.get_text())
            
            if not text:
                continue
            
            # Modda raqamini topish
            article_num = extract_article_number(text)
            
            if article_num:
                # Oldingi moddani saqlash
                if current_article_num and current_content:
                    articles[current_article_num] = {
                        "title": current_title,
                        "content": "\\n".join(current_content)
                    }
                
                # Yangi modda boshlash
                current_article_num = article_num
                current_title = text
                current_content = []
            else:
                # Modda mazmunini qo'shish
                if current_article_num:
                    current_content.append(text)
                else:
                    # Agar hali modda boshlanmagan bo'lsa, kirish qismi sifatida saqlash
                    current_content.append(text)
        
        # Oxirgi moddani saqlash
        if current_article_num and current_content:
            articles[current_article_num] = {
                "title": current_title,
                "content": "\\n".join(current_content)
            }
        elif not articles and current_content:
            # Agar hech qanday modda topilmasa, lekin matn bo'lsa
            articles["1"] = {
                "title": doc_name,
                "content": "\\n".join(current_content)
            }
        
        log_message(f"✅ Tayyor: {doc_name} - {len(articles)} ta qism topildi")
        return articles
        
    except requests.exceptions.RequestException as e:
        log_message(f"❌ HTTP xato ({doc_name}): {e}")
        return {}
    except Exception as e:
        log_message(f"❌ Parsing xato ({doc_name}): {e}")
        return {}


def save_to_json(data: Dict, filename: str):
    """Ma'lumotni JSON faylga saqlash"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log_message(f"💾 Saqlandi: {filepath}")
    except Exception as e:
        log_message(f"❌ Saqlashda xato ({filename}): {e}")


def scrape_all_laws():
    """Barcha qonunlarni parsing qilish"""
    log_message("=" * 70)
    log_message("🚀 LEX.UZ SCRAPER BOSHLANDI")
    log_message("=" * 70)
    
    total = len(LAWS_TO_SCRAPE)
    success_count = 0
    
    for i, (doc_name, url) in enumerate(LAWS_TO_SCRAPE.items(), 1):
        log_message(f"\\n📊 Progress: {i}/{total}")
        
        articles = scrape_law_document(url, doc_name)
        
        if articles:
            save_to_json(articles, f"{doc_name}.json")
            success_count += 1
        
        # Server'ga yukni kamaytirish uchun kutish
        if i < total:
            time.sleep(2)
    
    log_message("\\n" + "=" * 70)
    log_message(f"✅ YAKUNLANDI: {success_count}/{total} ta hujjat muvaffaqiyatli")
    log_message("=" * 70)


def update_single_law(doc_name: str):
    """Bitta qonunni yangilash"""
    if doc_name not in LAWS_TO_SCRAPE:
        log_message(f"❌ Qonun topilmadi: {doc_name}")
        log_message(f"Mavjud qonunlar: {', '.join(LAWS_TO_SCRAPE.keys())}")
        return
    
    url = LAWS_TO_SCRAPE[doc_name]
    articles = scrape_law_document(url, doc_name)
    
    if articles:
        save_to_json(articles, f"{doc_name}.json")


def list_scraped_laws():
    """Parsing qilingan qonunlar ro'yxati"""
    if not os.path.exists(OUTPUT_DIR):
        log_message("📭 Hali hech qanday qonun parsing qilinmagan")
        return
    
    files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.json')]
    
    if not files:
        log_message("📭 Hali hech qanday qonun parsing qilinmagan")
        return
    
    log_message(f"\\n📚 Parsing qilingan qonunlar ({len(files)} ta):")
    log_message("=" * 70)
    
    for filename in sorted(files):
        filepath = os.path.join(OUTPUT_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            doc_name = filename.replace('.json', '')
            article_count = len(data)
            file_size = os.path.getsize(filepath) / 1024  # KB
            
            log_message(f"📄 {doc_name}")
            log_message(f"   └─ Moddalar: {article_count} ta")
            log_message(f"   └─ Hajm: {file_size:.1f} KB")
            log_message("")
        except:
            log_message(f"⚠️ {filename} - o'qishda xato")


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            list_scraped_laws()
        elif command == "update":
            if len(sys.argv) > 2:
                doc_name = sys.argv[2]
                update_single_law(doc_name)
            else:
                log_message("❌ Qonun nomini kiriting: python auto_scraper.py update Konstitutsiya")
        else:
            log_message(f"❌ Noma'lum buyruq: {command}")
            log_message("Mavjud buyruqlar: list, update")
    else:
        # Barcha qonunlarni parsing qilish
        scrape_all_laws()

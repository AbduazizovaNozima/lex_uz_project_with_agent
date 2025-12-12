# import aiohttp
# import asyncio
# from bs4 import BeautifulSoup
#
#
# class KunUzScraper:
#     def __init__(self):
#         self.base_url = "https://kun.uz"
#         self.headers = {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#         }
#
#     async def fetch_page(self, session, url):
#         try:
#             async with session.get(url, headers=self.headers, timeout=10) as response:
#                 if response.status == 200:
#                     return await response.text()
#             return None
#         except:
#             return None
#
#     async def get_article_details(self, session, url):
#         html = await self.fetch_page(session, url)
#         if not html:
#             return None, None
#
#         soup = BeautifulSoup(html, 'html.parser')
#
#         # 1. RASM QIDIRISH
#         img_url = None
#         # Meta image (eng sifatlisi)
#         meta_img = soup.find("meta", property="og:image")
#         if meta_img:
#             img_url = meta_img.get("content")
#
#         if not img_url:
#             main_div = soup.find("div", class_="main-img")
#             if main_div and main_div.find("img"):
#                 img_url = main_div.find("img").get("src")
#
#         if img_url:
#             if img_url.startswith("//"):
#                 img_url = "https:" + img_url
#             elif img_url.startswith("/"):
#                 img_url = self.base_url + img_url
#         else:
#             img_url = "https://storage.kun.uz/source/thumbnails/_medium/11/default-news_medium.jpg"
#
#         # 2. ASOSIY MATNNI OLISH (AI xulosa qilishi uchun)
#         raw_text = ""
#         content_div = soup.find("div", class_="single-content")
#
#         if content_div:
#             # Barcha paragraflarni olamiz
#             paragraphs = content_div.find_all("p")
#             text_parts = []
#             for p in paragraphs:
#                 text = p.get_text(strip=True)
#                 # Juda qisqa yoki reklama matnlarini tashlab ketamiz
#                 if len(text) > 30 and "foto:" not in text.lower():
#                     text_parts.append(text)
#
#             # AIga juda ko'p tekst yubormaslik uchun birinchi 3-4 ta paragrafni olamiz
#             # Bu xulosa chiqarish uchun yetarli
#             raw_text = " ".join(text_parts[:4])
#
#         if not raw_text:
#             raw_text = "Maqola matni topilmadi."
#
#         # Matnni juda uzun bo'lib ketishini oldini olamiz (Token limit uchun)
#         return img_url, raw_text[:1500]
#
#     async def get_news_async(self, category: str = None, limit: int = 5):
#         url = f"{self.base_url}/uz/news/list"
#         if category:
#             if category in ['jahon', 'uzbekistan', 'iqtisodiyot', 'jamiyat', 'sport', 'texnologiya', 'talim', 'moliya', 'avto', 'kuchmas-mulk', 'ayollar-dunyosi', 'soglom-hayot', 'turizm']:
#                 url = f"{self.base_url}/news/category/{category}"
#             elif category == 'tech':
#                 url = f"{self.base_url}/news/category/texnologiya"
#
#         print(f"🔎 SCRAPER: {url} ro'yxati olinmoqda...")
#
#         async with aiohttp.ClientSession() as session:
#             html = await self.fetch_page(session, url)
#             if not html: return []
#
#             soup = BeautifulSoup(html, 'html.parser')
#             links = soup.find_all('a', href=True)
#
#             news_items = []
#             seen_urls = set()
#
#             for link in links:
#                 href = link.get('href', '')
#                 if '/news/20' not in href: continue
#                 full_url = href if href.startswith('http') else self.base_url + href
#                 if full_url in seen_urls: continue
#                 seen_urls.add(full_url)
#
#                 title = link.get_text(strip=True)
#                 if len(title) < 15: continue
#
#                 # Sana
#                 date = "Bugun"
#                 try:
#                     p = link.find_parent("div")
#                     if p and p.find("span", class_="date"):
#                         date = p.find("span", class_="date").get_text(strip=True)
#                 except:
#                     pass
#
#                 news_items.append({"title": title, "url": full_url, "date": date})
#                 if len(news_items) >= limit: break
#
#             print(f"🚀 {len(news_items)} ta yangilik MATNI yuklanmoqda (AI uchun)...")
#             tasks = [self.get_article_details(session, item['url']) for item in news_items]
#             results = await asyncio.gather(*tasks)
#
#             final_news = []
#             for i, item in enumerate(news_items):
#                 img, raw_text = results[i]
#                 item['image_url'] = img
#                 item['raw_text'] = raw_text  # <--- BU YERDA ENDI ASOSIY MATN BOR
#                 final_news.append(item)
#
#             return final_news

#-------------------------------------------------------------------------


# import requests
# from bs4 import BeautifulSoup
# import os
# import re
#
# DATA_FOLDER = "lex_data"
# if not os.path.exists(DATA_FOLDER):
#     os.makedirs(DATA_FOLDER)
#
# URLS = {
#     "Konstitutsiya": "https://lex.uz/docs/6445145",
#     "Mehnat_Kodeksi": "https://lex.uz/docs/6257288",
#     "Fuqarolik_Kodeksi": "https://lex.uz/docs/111189"
# }
#
#
# def clean_text_content(text):
#     # 1. [O'KOZ: ...] kabi katta bloklarni olib tashlash
#     text = re.sub(r'\[.*?\]', '', text, flags=re.DOTALL)
#
#     # 2. Menyular va tugmalarni olib tashlash
#     garbage_phrases = [
#         "Аудиони тинглаш", "Ҳужжат элементидан ҳавола олиш",
#         "Ҳужжатга таклиф юбориш", "Техник хатолик",
#         "Қонунчиликка таклиф бериш", "Юклаб олиш", "Чоп этиш",
#         "Кейинги таҳрирга ҳавола", "Олдинги таҳрирга ҳавола",
#         "Ўзгартиришлар манбаси", "Расмий нашр манбаси"
#     ]
#
#     for phrase in garbage_phrases:
#         text = text.replace(phrase, "")
#
#     # 3. Ortiqcha bo'shliqlarni tozalash
#     lines = text.split('\n')
#     cleaned_lines = []
#     for line in lines:
#         line = line.strip()
#         # Raqamlar yoki juda qisqa ma'nosiz so'zlarni tashlaymiz
#         if len(line) < 3:
#             continue
#         cleaned_lines.append(line)
#
#     return "\n".join(cleaned_lines)
#
#
# def scrape():
#     print("🧹 Kuchaytirilgan Scraping boshlandi...")
#     headers = {"User-Agent": "Mozilla/5.0"}
#
#     for name, url in URLS.items():
#         try:
#             print(f"📥 Yuklanmoqda: {name}...")
#             response = requests.get(url, headers=headers)
#             soup = BeautifulSoup(response.content, 'html.parser')
#
#             content_div = soup.find(class_="lx_text") or soup.body
#             raw_text = content_div.get_text(separator="\n")
#
#             final_text = clean_text_content(raw_text)
#
#             with open(f"{DATA_FOLDER}/{name}.txt", "w", encoding="utf-8") as f:
#                 f.write(final_text)
#             print(f"✅ {name} tozalab saqlandi. (Hajmi: {len(final_text)} belgi)")
#
#         except Exception as e:
#             print(f"❌ Xatolik {name}: {e}")
#
#
# if __name__ == "__main__":
#     scrape()


import os
import re
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# ============================================================================
# KONFIGURATSIYA
# ============================================================================
DATA_FOLDER = "lex_data"
STRUCTURED_FOLDER = "lex_structured"

for folder in [DATA_FOLDER, STRUCTURED_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

URLS = {
    "Konstitutsiya": "https://lex.uz/docs/-6445145",
    "Mehnat_Kodeksi": "https://lex.uz/docs/-6257288",
    "Fuqarolik_Kodeksi": "https://lex.uz/docs/-111189",
    "Jinoyat_Kodeksi": "https://lex.uz/docs/-111453",
    "Oila_Kodeksi": "https://lex.uz/docs/-104720",
    "Ma'muriy_Javobgarlik_Kodeksi": "https://lex.uz/docs/-97664",
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


# ============================================================================
# SELENIUM DRIVER YARATISH
# ============================================================================
def create_driver():
    """Headless Chrome driver yaratish"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ko'rinmas rejim
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    return driver


# ============================================================================
# MODDALARNI AJRATISH
# ============================================================================
def extract_articles(text: str) -> dict:
    """Matndan moddalarni ajratish"""
    articles = {}

    # Turli formatdagi moddalar uchun patternlar
    patterns = [
        r'^(\d+)-modda\.\s*([^\n]+)',
        r'^(\d+)-модда\.\s*([^\n]+)',
        r'^Modda\s+(\d+)\.\s*([^\n]+)',
        r'^Модда\s+(\d+)\.\s*([^\n]+)',
        r'^Статья\s+(\d+)\.\s*([^\n]+)',
        r'^(\d+)-statiya\.\s*([^\n]+)'
    ]

    lines = text.split('\n')
    current_article = None
    current_content = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Modda boshlanishini tekshirish
        found = False
        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                # Oldingi moddani saqlash
                if current_article:
                    articles[current_article['number']] = {
                        'title': current_article['title'],
                        'content': '\n'.join(current_content).strip()
                    }

                # Yangi modda
                # Ba'zi patternlarda guruhlar joylashuvi farq qilishi mumkin
                if match.lastindex >= 2:
                    if match.group(1).isdigit():
                        num = match.group(1)
                        title = match.group(2).strip()
                    else:
                        num = match.group(2)
                        title = match.group(1).strip()
                else:
                    # Fallback
                    num = match.group(1)
                    title = ""

                current_article = {
                    'number': num,
                    'title': title
                }
                current_content = []
                found = True
                break

        # Modda mazmunini yig'ish
        if not found:
            if current_article:
                current_content.append(line)
            # Agar hali birorta modda topilmagan bo'lsa, lekin matn kelsa (kirish qismi)
            # uni '0' yoki 'kirish' deb saqlashimiz mumkin, lekin hozircha tashlab ketamiz

    # Oxirgi moddani saqlash
    if current_article:
        articles[current_article['number']] = {
            'title': current_article['title'],
            'content': '\n'.join(current_content).strip()
        }

    return articles


# ============================================================================
# MATNNI TOZALASH
# ============================================================================
def clean_text(text: str) -> str:
    """Keraksiz ma'lumotlarni olib tashlash"""

    # Garbage frazalar
    garbage = [
        "Аудиони тинглаш",
        "Ҳужжат элементидан ҳавола олиш",
        "Техник хатолик",
        "Қонунчиликка таклиф бериш",
        "Жўнатиш",
        "Бекор қилиш",
        "Юклаб олиш",
        "Чоп этиш",
        "Кейинги таҳрирга ҳавола",
        "Олдинги таҳрирга ҳавола",
        "Ўзгартиришлар манбаси",
        "Расмий нашр манбаси",
        "Қўшимча маълумот",
        "Ҳужжат матни",
        "Матнни кўчириш",
        "Файл",
        "Word",
        "PDF"
    ]

    for phrase in garbage:
        text = text.replace(phrase, "")

    # Bo'shliqlarni normallash
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Raqamlar bilan boshlanadigan va juda qisqa qatorlarni tozalash (masalan sahifa raqamlari)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if len(line) < 3 and line.isdigit():
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


# ============================================================================
# SELENIUM BILAN SCRAPING
# ============================================================================
def scrape_with_selenium(url: str, name: str) -> tuple:
    """Selenium orqali sahifani yuklab olish"""

    driver = None
    try:
        print(f"  🌐 Brauzer ochilmoqda...")
        driver = create_driver()

        print(f"  📥 Sahifa yuklanmoqda...")
        driver.get(url)

        # JavaScript ishga tushishini kutish
        print(f"  ⏳ JavaScript ishga tushishi kutilmoqda...")
        time.sleep(10)  # Ko'proq vaqt beramiz

        # Turli selectorlarni sinab ko'ramiz
        selectors = [
            (By.CLASS_NAME, "lx_text"),
            (By.CLASS_NAME, "document-content"),
            (By.ID, "content"),
            (By.CSS_SELECTOR, "div.lx_text"),
            (By.CSS_SELECTOR, "div[class*='text']"),
            (By.XPATH, "//div[contains(@class, 'lx_text')]"),
            (By.TAG_NAME, "body") # Fallback
        ]

        raw_text = None

        for selector_type, selector_value in selectors:
            try:
                print(f"  🔍 {selector_value} topilmoqda...")
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((selector_type, selector_value))
                )
                content = driver.find_element(selector_type, selector_value)
                raw_text = content.text

                if raw_text and len(raw_text) > 500:  # Kamida 500 ta belgi bo'lsa
                    print(f"  ✅ Kontent topildi: {selector_value} ({len(raw_text)} belgi)")
                    break
            except:
                continue

        # Agar hech narsa topilmasa, page_source dan parsing qilamiz
        if not raw_text or len(raw_text) < 500:
            print(f"  ⚠️  Selector ishlamadi, HTML parsing...")
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # lx_text class'ini qidiramiz
            content_div = soup.find(class_="lx_text")
            if content_div:
                raw_text = content_div.get_text(separator="\n")
                print(f"  ✅ BeautifulSoup orqali topildi ({len(raw_text)} belgi)")
            else:
                raw_text = soup.body.get_text(separator="\n") if soup.body else ""
                print(f"  ⚠️  Body dan olindi ({len(raw_text)} belgi)")

        if not raw_text:
            return ("❌ Kontent topilmadi", {})

        print(f"  🧹 Matn tozalanmoqda...")
        cleaned_text = clean_text(raw_text)

        print(f"  📊 Moddalar ajratilmoqda...")
        articles = extract_articles(cleaned_text)

        print(f"  ✅ {len(articles)} ta modda topildi")

        # Debug: agar 0 ta modda bo'lsa, birinchi 500 belgini ko'rsatamiz
        if len(articles) == 0:
            print(f"  🔍 DEBUG - Birinchi 500 belgi:")
            print(f"  {cleaned_text[:500]}")

        return (cleaned_text, articles)

    except Exception as e:
        import traceback
        return (f"❌ Xato: {str(e)}\n{traceback.format_exc()}", {})

    finally:
        if driver:
            driver.quit()


# ============================================================================
# BARCHA HUJJATLARNI YUKLAB OLISH
# ============================================================================
def scrape_all():
    """Barcha qonun hujjatlarini yuklab olish"""

    print("\n" + "=" * 70)
    print("🚀 SELENIUM BILAN LEX.UZ SCRAPER BOSHLANDI")
    print("=" * 70 + "\n")

    success_count = 0
    fail_count = 0

    for i, (name, url) in enumerate(URLS.items(), 1):
        print(f"\n[{i}/{len(URLS)}] 📚 {name}")
        print(f"      🔗 {url}")

        # Ma'lumotni olish
        raw_text, articles = scrape_with_selenium(url, name)

        # Saqlash
        if not raw_text.startswith("❌"):
            # 1. To'liq matn
            filepath = f"{DATA_FOLDER}/{name}.txt"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(raw_text)
            print(f"  💾 To'liq matn: {filepath}")

            # 2. JSON
            if articles:
                json_path = f"{STRUCTURED_FOLDER}/{name}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(articles, f, ensure_ascii=False, indent=2)
                print(f"  📦 JSON: {json_path} ({len(articles)} modda)")

            success_count += 1
        else:
            print(f"  {raw_text}")
            fail_count += 1

        # Kutish (lex.uz ni ortiqcha yuklamaslik uchun)
        if i < len(URLS):
            time.sleep(3)

    # Yakuniy statistika
    print("\n" + "=" * 70)
    print(f"✅ Muvaffaqiyatli: {success_count}")
    print(f"❌ Xatolar: {fail_count}")
    print(f"📁 Fayllar: {os.path.abspath(DATA_FOLDER)}")
    print(f"📦 JSON: {os.path.abspath(STRUCTURED_FOLDER)}")
    print("=" * 70 + "\n")


# ============================================================================
# MODDA QIDIRISH
# ============================================================================
def search_article(doc_name: str, article_number: str):
    """Aniq moddani JSON dan qidirish"""
    json_path = f"{STRUCTURED_FOLDER}/{doc_name}.json"

    if not os.path.exists(json_path):
        print(f"❌ {doc_name} topilmadi")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    if article_number in articles:
        article = articles[article_number]
        print(f"\n{'=' * 70}")
        print(f"📄 {doc_name} - {article_number}-modda")
        print(f"{'=' * 70}")
        print(f"\n📌 {article['title']}\n")
        print(article['content'])
        print(f"\n{'=' * 70}\n")
    else:
        print(f"❌ {article_number}-modda topilmadi")
        if articles:
            available = sorted(articles.keys(), key=int)
            print(f"💡 Mavjud moddalar: {', '.join(available[:10])}...")


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    print("🔥 Selenium bilan Scraper\n")

    while True:
        print("\n" + "=" * 70)
        print("1. Barcha hujjatlarni yuklab olish")
        print("2. Mavjud fayllarni ko'rish")
        print("3. Aniq moddani qidirish")
        print("0. Chiqish")
        print("=" * 70)

        choice = input("\nTanlang: ").strip()

        if choice == "1":
            scrape_all()
        elif choice == "2":
            print(f"\n📂 {DATA_FOLDER}:")
            for f in os.listdir(DATA_FOLDER):
                print(f"  📄 {f}")

            print(f"\n📂 {STRUCTURED_FOLDER}:")
            for f in os.listdir(STRUCTURED_FOLDER):
                print(f"  📦 {f}")
        elif choice == "3":
            doc = input("Hujjat nomi: ").strip()
            num = input("Modda raqami: ").strip()
            search_article(doc, num)
        elif choice == "0":
            break








# 🤖 Lex.uz AI Assistant

O'zbekiston qonunchilik bo'yicha professional AI yordamchi - avtomatik parsing, session management va chiroyli UI bilan.

## ✨ Xususiyatlar

- 🔄 **Avtomatik Parsing**: Lex.uz dan 20+ qonunni avtomatik parsing qilish
- 📅 **Har Kuni Yangilanish**: Cron job orqali avtomatik yangilanish
- 💬 **Session Management**: Ko'p foydalanuvchi va chat tarixi
- 🎨 **Zamonaviy UI**: Streamlit asosida chiroyli interfeys
- ⚡ **Tez Qidiruv**: Vector database bilan semantic search
- 🤖 **Multi-Agent System**: AutoGen bilan professional javoblar

## 📋 Qo'llab-quvvatlanadigan Qonunlar

1. Konstitutsiya
2. Mehnat Kodeksi
3. Fuqarolik Kodeksi
4. Jinoyat Kodeksi
5. Oila Kodeksi
6. Soliq Kodeksi
7. Yer Kodeksi
8. Suv Kodeksi
9. Uy-Joy Kodeksi
10. Ma'muriy Javobgarlik Kodeksi
11. Jinoyat Protsessual Kodeksi
12. Fuqarolik Protsessual Kodeksi
13. Iqtisodiy Protsessual Kodeksi
14. Ma'muriy Sud Ishlarini Yuritish Kodeksi
15. Budjet Kodeksi
16. Shaharsozlik Kodeksi
17. Bojxona Kodeksi
18. Havo Kodeksi
19. Jinoyat Ijroiya Kodeksi
20. Saylov Kodeksi

## 🚀 O'rnatish

### 1. Repository'ni clone qilish

```bash
git clone <repository-url>
cd langchain_first_project
```

### 2. Virtual environment yaratish

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\\Scripts\\activate  # Windows
```

### 3. Dependencies o'rnatish

```bash
pip install -r requirements.txt
```

### 4. Environment variables

`.env` fayl yarating va quyidagilarni qo'shing:

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/lexuz_db
```

### 5. Database setup (PostgreSQL + pgvector)

```bash
# PostgreSQL o'rnatish
sudo apt-get install postgresql postgresql-contrib

# pgvector extension o'rnatish
# https://github.com/pgvector/pgvector

# Database yaratish
createdb lexuz_db
```

### 6. Dastlabki parsing

```bash
python auto_scraper.py
```

Bu 20 ta qonunni parsing qilib, `lex_structured/` papkaga saqlaydi.

### 7. Cron job o'rnatish (ixtiyoriy)

```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

## 🎯 Ishga Tushirish

### API Server

```bash
python api.py
```

Server `http://localhost:8000` da ishga tushadi.

### Frontend

Yangi terminalda:

```bash
streamlit run frontend.py
```

Browser'da `http://localhost:8501` ochiladi.

## 📖 Foydalanish

### Web Interface

1. Browserda `http://localhost:8501` ochish
2. "Yangi Chat" tugmasini bosish
3. Savolingizni yozish
4. Javobni olish

### API

```bash
# Health check
curl http://localhost:8000/health

# Chat
curl -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "question": "Mehnat kodeksi 131-modda haqida",
    "session_id": "optional-session-id"
  }'

# Sessionlar ro'yxati
curl http://localhost:8000/sessions

# Yangi session
curl -X POST http://localhost:8000/sessions/new

# Session tarixini olish
curl http://localhost:8000/sessions/{session_id}/history
```

### Auto Scraper

```bash
# Barcha qonunlarni parsing qilish
python auto_scraper.py

# Parsing qilingan qonunlar ro'yxati
python auto_scraper.py list

# Bitta qonunni yangilash
python auto_scraper.py update Konstitutsiya
```

## 📁 Fayl Tuzilmasi

```
langchain_first_project/
├── api.py                 # FastAPI backend
├── frontend.py            # Streamlit UI
├── agents.py              # AutoGen agents
├── database.py            # Vector database
├── session_manager.py     # Session management
├── auto_scraper.py        # Auto parsing
├── knowledge_base.py      # Site guides
├── setup_cron.sh          # Cron setup
├── .env                   # Environment variables
├── requirements.txt       # Dependencies
├── sessions/              # Session storage
├── lex_structured/        # Parsed JSON files
└── logs/                  # Log files
```

## 🔧 Konfiguratsiya

### API Endpoints

- `POST /chat` - Savol yuborish
- `GET /sessions` - Barcha sessionlar
- `POST /sessions/new` - Yangi session
- `GET /sessions/{id}` - Session ma'lumotlari
- `GET /sessions/{id}/history` - Chat tarixi
- `DELETE /sessions/{id}` - Sessionni o'chirish
- `GET /health` - Health check

### Cron Schedule

Default: Har kuni soat 02:00 da

O'zgartirish uchun:
```bash
crontab -e
```

## 🐛 Muammolarni Hal Qilish

### Port band bo'lsa

```bash
# API port (8000)
lsof -ti:8000 | xargs kill -9

# Frontend port (8501)
lsof -ti:8501 | xargs kill -9
```

### Parsing ishlamasa

1. Internet ulanishini tekshiring
2. Lex.uz saytining ishlashini tekshiring
3. Loglarni ko'ring: `cat logs/scraper.log`

### API qotib qolsa

1. Serverni to'xtating: `Ctrl+C`
2. Port'ni tozalang: `lsof -ti:8000 | xargs kill -9`
3. Qayta ishga tushiring: `python api.py`

## 📊 Monitoring

### Loglar

```bash
# Scraper logs
tail -f logs/scraper.log

# Cron logs
tail -f logs/cron.log

# API errors
tail -f logs/api_errors.log
```

### Cron Job

```bash
# Cron job'larni ko'rish
crontab -l

# Cron log'larini ko'rish
grep CRON /var/log/syslog
```

## 🤝 Contributing

Pull request'lar qabul qilinadi! Katta o'zgarishlar uchun avval issue oching.

## 📝 License

MIT

## 👨‍💻 Muallif

Nozima

## 🙏 Minnatdorchilik

- [AutoGen](https://github.com/microsoft/autogen)
- [Streamlit](https://streamlit.io/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Lex.uz](https://lex.uz/)

---

**Savol yoki muammo bo'lsa, issue oching!** 🚀

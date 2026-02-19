# 🤖 Lex.uz AI Legal Assistant

A professional AI assistant for Uzbekistan legal queries — with automatic law scraping, session management, semantic search, and a modern UI.

## ✨ Features

- 🔄 **Auto Scraping** — Parses 20+ laws from Lex.uz automatically
- 📅 **Daily Updates** — Cron job keeps the legal database current
- 💬 **Session Management** — Multi-user support with chat history
- 🎨 **Modern UI** — Clean Streamlit interface
- ⚡ **Hybrid Search** — JSON-based exact lookup + PostgreSQL vector semantic search
- 🤖 **Multi-Agent System** — AutoGen pipeline with specialized agents

---

## 📋 Supported Laws

| # | Law |
|---|-----|
| 1 | Constitution (Konstitutsiya) |
| 2 | Labour Code (Mehnat Kodeksi) |
| 3 | Civil Code (Fuqarolik Kodeksi) |
| 4 | Criminal Code (Jinoyat Kodeksi) |
| 5 | Family Code (Oila Kodeksi) |
| 6 | Tax Code (Soliq Kodeksi) |
| 7 | Land Code (Yer Kodeksi) |
| 8 | Water Code (Suv Kodeksi) |
| 9 | Housing Code (Uy-Joy Kodeksi) |
| 10 | Administrative Liability Code |
| 11 | Criminal Procedure Code |
| 12 | Civil Procedure Code |
| 13 | Economic Procedure Code |
| 14 | Administrative Court Code |
| 15 | Budget Code |
| 16 | Urban Planning Code |
| 17 | Customs Code |
| 18 | Air Code |
| 19 | Criminal Executive Code |
| 20 | Electoral Code |
| 21 | Cybersecurity Law |

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd lex_uz_project_with_agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Linux / macOS
# or
venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
DB_PASSWORD=12345
DB_PORT=5433
```

> **Note:** On this system PostgreSQL runs on port **5433** (not the default 5432).  
> Check your actual port with: `pg_lsclusters`

### 5. Set up PostgreSQL + pgvector

```bash
# Check PostgreSQL cluster and port
pg_lsclusters

# Install pgvector (if not installed)
sudo apt-get install postgresql-16-pgvector

# Create the database (if not exists)
createdb -U postgres lexuz_db
```

### 6. Initialize the database (run once)

This creates the table schema and loads all law articles into the vector database:

```bash
python database.py
```

> This takes 5–15 minutes depending on your hardware — it embeds all law articles.

### 7. Scrape laws from Lex.uz (optional — pre-scraped JSONs are included)

```bash
python auto_scraper.py
```

This downloads the latest version of all laws from Lex.uz and saves them to `lex_structured/`.

---

## 🎯 Running the Application

### Start the API server

```bash
python api.py
```

Server runs at `http://localhost:8000`

### Start the frontend (in a new terminal)

```bash
streamlit run frontend.py
```

Open `http://localhost:8501` in your browser.

---

## 📖 Usage

### Web Interface

1. Open `http://localhost:8501`
2. Click **"Yangi Chat"** to start a new session
3. Type your question (in Uzbek)
4. Get AI-powered legal answers

### API Endpoints

```bash
# Health check
curl http://localhost:8000/

# Ask a question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Mehnat kodeksi 131-modda haqida",
    "session_id": "optional-session-id"
  }'

# List sessions
curl http://localhost:8000/sessions

# Create new session
curl -X POST http://localhost:8000/sessions/new

# Get session history
curl http://localhost:8000/sessions/{session_id}/history
```

### Auto Scraper

```bash
# Scrape all laws
python auto_scraper.py

# Then reload the database with fresh data
python database.py
```

---

## 📁 Project Structure

```
lex_uz_project_with_agent/
├── api.py                # FastAPI backend
├── frontend.py           # Streamlit UI
├── agents.py             # AutoGen multi-agent pipeline
├── database.py           # PostgreSQL vector DB (search + ingestion)
├── session_manager.py    # Session/chat history management
├── auto_scraper.py       # Automated law scraping
├── scraper.py            # Core scraper logic
├── knowledge_base.py     # Lex.uz site usage guides
├── setup_cron.sh         # Cron job setup for daily scraping
├── .env                  # Environment variables (not committed)
├── requirements.txt      # Python dependencies
├── lex_structured/       # Parsed law JSON files (21 laws)
├── lex_data/             # Raw scraped text files
├── sessions/             # Session storage
├── static/               # Static assets (images)
└── logs/                 # Application logs
```

---

## 🔧 Configuration

### API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send a question |
| `GET` | `/sessions` | List all sessions |
| `POST` | `/sessions/new` | Create new session |
| `GET` | `/sessions/{id}/history` | Get chat history |
| `DELETE` | `/sessions/{id}` | Delete session |
| `GET` | `/` | Health check |

### Cron Schedule for Auto-Scraping

Default: every day at 02:00 AM.

```bash
# Setup cron job
chmod +x setup_cron.sh
./setup_cron.sh

# View scheduled jobs
crontab -l

# Edit schedule
crontab -e
```

---

## 🐛 Troubleshooting

### Port already in use

```bash
# Kill API server (port 8000)
lsof -ti:8000 | xargs kill -9

# Kill frontend (port 8501)
lsof -ti:8501 | xargs kill -9
```

### PostgreSQL connection refused

```bash
# Find actual PostgreSQL port
pg_lsclusters

# Start PostgreSQL cluster if stopped
sudo pg_ctlcluster 16 main start

# Update .env file with correct port
echo "DB_PORT=5433" >> .env
```

### Database table doesn't exist

```bash
# Initialize database (run once)
python database.py
```

### Scraping fails

1. Check internet connectivity
2. Verify Lex.uz is accessible: `curl -I https://lex.uz`
3. Check logs: `cat logs/scraper.log`

### API hangs / not responding

1. Stop the server: `Ctrl+C`
2. Clean up: `lsof -ti:8000 | xargs kill -9`
3. Restart: `python api.py`

---

## 📊 Monitoring

```bash
# Scraper logs
tail -f logs/scraper.log

# Cron execution log
tail -f logs/cron.log

# API error log
tail -f logs/api_errors.log

# Last scraping run summary
cat logs/last_run.json
```

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

## 📝 License

MIT

## � Author

Nozima Abduazizova

## 🙏 Acknowledgements

- [AutoGen](https://github.com/microsoft/autogen) — Multi-agent framework
- [Streamlit](https://streamlit.io/) — Frontend UI
- [FastAPI](https://fastapi.tiangolo.com/) — Backend API
- [pgvector](https://github.com/pgvector/pgvector) — Vector similarity search
- [Lex.uz](https://lex.uz/) — Official Uzbekistan legal portal

---

*Questions or issues? Open a GitHub issue.* 🚀

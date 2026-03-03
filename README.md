# LexAI Professional

AI-powered legal assistant for Uzbekistan — answers questions about laws, codes, and statutes sourced directly from [Lex.uz](https://lex.uz).

It runs as a **FastAPI** web service with a built-in **Telegram bot**, backed by a **PostgreSQL + pgvector** database for semantic search.

---

## Run with Docker

```bash
# 1. Copy and fill in credentials
cp .env.example .env

# 2. Start all services (PostgreSQL + app)
docker compose -f docker/docker-compose.yml up -d --build

# 3. Bootstrap the database (first run only)
docker exec lexai_app python3 database.py

# 4. View logs
docker compose -f docker/docker-compose.yml logs -f app

# 5. Stop
docker compose -f docker/docker-compose.yml down
```

The app will be available at **http://localhost:8000**

---

## Run Locally

```bash
# 1. Copy and fill in credentials
cp .env.example .env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Bootstrap the database (first run only)
python3 database.py

# 4. Start
python3 main.py
```

---

## Ingest / Update Legal Data

```bash
# Scrape all laws from Lex.uz and save to lex_structured/
python3 -c "from app.services.scraper_service import ScraperService; ScraperService().scrape_all()"

# Upload scraped data into PostgreSQL
python3 database.py
```

---

## API

```bash
# Ask a legal question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Konstitutsiyaning 20-moddasi nima?"}'

# Health check
curl http://localhost:8000/health
```

Interactive docs: **http://localhost:8000/docs**

---

## Telegram Bot Commands

| Command | Action |
|---------|--------|
| `/start` | Start a new session |
| `/new` | Reset the conversation |
| `/help` | Show help |

---

## Environment Variables

Copy `.env.example` → `.env`:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI secret key |
| `OPENAI_MODEL` | Model name (default: `gpt-4o-mini`) |
| `TELEGRAM_BOT_TOKEN` | Token from [@BotFather](https://t.me/botfather) — optional |
| `DB_NAME` | PostgreSQL database name |
| `DB_USER` | PostgreSQL user |
| `DB_PASSWORD` | PostgreSQL password |
| `DB_HOST` | `localhost` locally, `postgres` inside Docker |
| `DB_PORT` | `5433` locally, `5432` inside Docker |

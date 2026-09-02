# LexAI — Uzbek Legal Assistant

> AI-powered legal Q&A system for Uzbekistan law, backed by [Lex.uz](https://lex.uz)

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-blue?logo=postgresql)](https://github.com/pgvector/pgvector)
[![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)](https://docker.com)

---

## Overview

LexAI is a Retrieval-Augmented Generation (RAG) system that answers legal questions in Uzbek and Russian using laws, codes, and statutes scraped directly from the official Uzbekistan legal database (Lex.uz).

**Key features:**
- Semantic search over 25,000+ legal documents via PostgreSQL + pgvector
- Multi-turn conversation with session memory (per Telegram user or API client)
- Telegram bot interface + REST API
- Scraper to keep legal data up to date

**Tech stack:** FastAPI · OpenAI GPT-4o-mini · PostgreSQL + pgvector · Docker · Aiogram

---

## Architecture

```
User (Telegram / REST)
        │
        ▼
   FastAPI App
        │
   ┌────┴────┐
   │  Agent  │  ← OpenAI GPT-4o-mini
   └────┬────┘
        │  semantic search
        ▼
 PostgreSQL + pgvector
  (25K+ law documents)
```

---

## Quickstart (Docker)

```bash
git clone https://github.com/AbduazizovaNozima/lex_uz_project_with_agent
cd lex_uz_project_with_agent

# 1. Set credentials
cp .env.example .env
# Edit .env — add OPENAI_API_KEY and DB_PASSWORD

# 2. Start services
docker compose -f docker/docker-compose.yml up -d --build

# 3. Bootstrap the database (first run only)
docker exec lexai_app python3 database.py

# 4. Open docs
open http://localhost:8000/docs
```

---

## Quickstart (Local)

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your credentials

python3 database.py    # first run only
python3 main.py
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

## Telegram Bot

| Command | Description |
|---------|-------------|
| `/start` | Start a new session |
| `/new` | Reset conversation |
| `/help` | Show help |

Enable the bot by setting `TELEGRAM_BOT_TOKEN` and `TELEGRAM_BOT_ENABLED=true` in `.env`.

---

## Data Pipeline

```bash
# Scrape updated laws from Lex.uz
python3 scraper.py

# Re-index into PostgreSQL
python3 database.py
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI secret key | ✅ |
| `OPENAI_MODEL` | Model name | default: `gpt-4o-mini` |
| `TELEGRAM_BOT_TOKEN` | Token from [@BotFather](https://t.me/botfather) | optional |
| `TELEGRAM_BOT_ENABLED` | Enable Telegram bot | default: `false` |
| `DB_NAME` | PostgreSQL database name | default: `lexuz_db` |
| `DB_USER` | PostgreSQL user | default: `postgres` |
| `DB_PASSWORD` | PostgreSQL password | ✅ |
| `DB_HOST` | DB host (`localhost` or `postgres` in Docker) | ✅ |
| `DB_PORT` | DB port | default: `5433` |

---

## License

MIT

#!/bin/bash

# Lex.uz Scraper - Cron Job Setup
# Har kuni soat 02:00 da avtomatik parsing

echo "🔧 Lex.uz Scraper - Cron Job O'rnatish"
echo "========================================"

# Current directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_DIR/venv"
PYTHON_PATH="$VENV_PATH/bin/python"
SCRAPER_SCRIPT="$PROJECT_DIR/scraper.py"
LOG_FILE="$PROJECT_DIR/logs/cron.log"

echo "📁 Project: $PROJECT_DIR"
echo "🐍 Python: $PYTHON_PATH"
echo "📜 Script: $SCRAPER_SCRIPT"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment topilmadi: $VENV_PATH"
    echo "Iltimos, avval virtual environment yarating:"
    echo "  python -m venv venv"
    exit 1
fi

# Check if scraper script exists
if [ ! -f "$SCRAPER_SCRIPT" ]; then
    echo "❌ Scraper script topilmadi: $SCRAPER_SCRIPT"
    exit 1
fi

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

# Cron job command
CRON_CMD="0 2 * * * cd $PROJECT_DIR && $PYTHON_PATH $SCRAPER_SCRIPT >> $LOG_FILE 2>&1"

echo ""
echo "� Cron job:"
echo "   $CRON_CMD"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$SCRAPER_SCRIPT"; then
    echo "⚠️  Cron job allaqachon mavjud!"
    echo ""
    read -p "Yangilashni xohlaysizmi? (y/n): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Bekor qilindi"
        exit 0
    fi
    
    # Remove old cron job
    crontab -l 2>/dev/null | grep -v "$SCRAPER_SCRIPT" | crontab -
    echo "🗑️  Eski cron job o'chirildi"
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "✅ Cron job muvaffaqiyatli o'rnatildi!"
echo ""
echo "📅 Jadval: Har kuni soat 02:00 da"
echo "� Loglar: $LOG_FILE"
echo ""
echo "Cron job'larni ko'rish: crontab -l"
echo "Cron job'ni o'chirish: crontab -e"
echo ""

# Test run (optional)
read -p "Test run qilishni xohlaysizmi? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧪 Test run boshlanmoqda..."
    cd "$PROJECT_DIR"
    $PYTHON_PATH $SCRAPER_SCRIPT
    echo ""
    echo "✅ Test run tugadi!"
fi

echo ""
echo "🎉 Setup yakunlandi!"

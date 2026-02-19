#!/bin/bash

# PostgreSQL parolini sozlash va bazani yaratish

echo "🔧 PostgreSQL konfiguratsiya..."

# 1. Postgres foydalanuvchisi uchun parol o'rnatish
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '12345';"

# 2. lexuz_db bazasini yaratish
sudo -u postgres psql -c "CREATE DATABASE lexuz_db;"

# 3. pgvector kengaytmasini o'rnatish
sudo -u postgres psql -d lexuz_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "✅ Database sozlandi!"

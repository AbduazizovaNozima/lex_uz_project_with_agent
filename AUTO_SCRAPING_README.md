# Automated Scraping System

## Overview
This system automatically scrapes lex.uz daily to keep the legal database up-to-date.

## Components

### 1. `auto_scraper.py`
Main automation script that:
- Runs `scraper.py` to fetch latest legal documents
- Updates the PostgreSQL database
- Generates detailed logs
- Creates summary reports

### 2. `setup_cron.sh`
Setup script to configure daily automated scraping:
- Adds cron job to run at 2:00 AM daily
- Configures logging
- Provides management commands

### 3. Logs Directory
All scraping activities are logged in `logs/`:
- `scraping_YYYY-MM-DD.log` - Daily scraping logs
- `cron.log` - Cron job execution log
- `last_run.json` - Latest run summary

## Setup Instructions

### 1. Install the Cron Job
```bash
cd /home/nozima/langchain_first_project
./setup_cron.sh
```

### 2. Verify Installation
```bash
crontab -l
```

You should see:
```
0 2 * * * cd /home/nozima/langchain_first_project && /home/nozima/langchain_first_project/venv/bin/python auto_scraper.py >> /home/nozima/langchain_first_project/logs/cron.log 2>&1
```

### 3. Test Manual Run
```bash
cd /home/nozima/langchain_first_project
source venv/bin/activate
python auto_scraper.py
```

## Schedule
- **Frequency**: Daily
- **Time**: 2:00 AM (low traffic period)
- **Duration**: ~10-30 minutes (depending on network)

## Monitoring

### Check Last Run Status
```bash
cat logs/last_run.json
```

### View Today's Log
```bash
tail -f logs/scraping_$(date +%Y-%m-%d).log
```

### View Cron Log
```bash
tail -f logs/cron.log
```

## Troubleshooting

### Cron Job Not Running
1. Check cron service is running:
   ```bash
   sudo systemctl status cron
   ```

2. Check cron logs:
   ```bash
   grep CRON /var/log/syslog
   ```

### Scraping Failures
1. Check scraping log for errors
2. Verify internet connection
3. Check lex.uz website is accessible
4. Ensure database credentials are correct

### Database Update Failures
1. Check PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql
   ```

2. Verify database credentials in `.env` file
3. Check database connection in logs

## Disabling Auto-Scraping

### Temporary Disable
```bash
crontab -e
# Comment out the line with '#'
```

### Permanent Removal
```bash
crontab -e
# Delete the line containing 'auto_scraper.py'
```

## Manual Operations

### Run Scraper Only
```bash
python scraper.py
```

### Update Database Only
```bash
python -c "from database import setup_database, insert_documents_from_json; setup_database(); insert_documents_from_json()"
```

### Full Manual Update
```bash
python auto_scraper.py
```

## Notifications (Optional)

To receive email notifications on completion, you can modify `auto_scraper.py` to send emails using:
- SMTP (Gmail, etc.)
- Telegram Bot
- Slack Webhook

## Best Practices

1. **Monitor logs regularly** - Check for failures
2. **Backup database** - Before major updates
3. **Test changes** - Run manually before deploying
4. **Keep logs** - Rotate old logs to save space

## Log Rotation (Optional)

To prevent logs from growing too large, setup log rotation:

```bash
sudo nano /etc/logrotate.d/lex-scraper
```

Add:
```
/home/nozima/langchain_first_project/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 nozima nozima
}
```

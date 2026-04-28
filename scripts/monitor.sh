#!/bin/bash
# Health check script for monitoring

# Check if bot is running
if pgrep -f "python.*bot/main.py" > /dev/null; then
    echo "Bot is running"
else
    echo "Bot is not running - attempting restart"
    sudo systemctl restart trading-bot
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo " Disk usage at ${DISK_USAGE}%"
fi

# Check for error log size
if [ -f logs/ethusdt_errors.txt ]; then
    ERROR_COUNT=$(wc -l < logs/ethusdt_errors.txt)
    if [ $ERROR_COUNT -gt 100 ]; then
        echo " High error count: $ERROR_COUNT"
    fi
fi
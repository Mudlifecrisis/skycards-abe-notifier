#!/bin/bash
echo "Starting Skycards Bot on Synology NAS"
echo "======================================"

# Set permissions
chmod +x start.sh

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "Running in Docker container"
    
    # Create health check file
    mkdir -p /app/logs
    touch /app/logs/bot_healthy
    
    # Start the bot
    python bot.py
else
    echo "Running directly on NAS (not recommended)"
    echo "Please use Docker deployment for better reliability"
    python3 bot.py
fi

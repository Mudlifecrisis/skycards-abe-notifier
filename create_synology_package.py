#!/usr/bin/env python3
"""
Create a deployment package for Synology NAS
"""
import os
import shutil
import tarfile
from pathlib import Path

def create_deployment_package():
    """Create a complete deployment package"""
    
    print("Creating Synology Deployment Package")
    print("=" * 50)
    
    # Create deployment directory
    deploy_dir = Path("synology-deploy")
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir()
    
    # Essential Python files
    python_files = [
        "bot.py",
        "rare_hunter.py", 
        "alert_window.py",
        "rarity.py",
        "alerts_sources.py",
        "mission_finder.py",
        "user_airports.py", 
        "airport_llm.py",
        "alert_tracker.py",
        "requirements.txt",
        ".env",
        "rarity.json",
        "ftea.json"
    ]
    
    copied_files = 0
    missing_files = 0
    
    # Copy Python files
    for file in python_files:
        if os.path.exists(file):
            shutil.copy2(file, deploy_dir)
            print(f"  Copied {file}")
            copied_files += 1
        else:
            print(f"  Missing {file}")
            missing_files += 1
    
    # Copy aircraft data directory
    if os.path.exists("aircraft_data"):
        shutil.copytree("aircraft_data", deploy_dir / "aircraft_data")
        data_files = len(os.listdir("aircraft_data"))
        print(f"  Copied aircraft_data/ ({data_files} files)")
        copied_files += data_files
    else:
        print("  Missing aircraft_data directory!")
        missing_files += 1
    
    # Create Dockerfile
    dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p logs aircraft_data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=America/New_York

# Health check
HEALTHCHECK --interval=5m --timeout=3s --start-period=10s --retries=3 \\
  CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=3)" || exit 1

# Run the bot
CMD ["python", "bot.py"]
'''
    
    with open(deploy_dir / "Dockerfile", "w") as f:
        f.write(dockerfile_content)
    print("  Created Dockerfile")
    
    # Create docker-compose.yml
    compose_content = '''version: '3.8'

services:
  skycards-bot:
    build: .
    container_name: skycards-bot
    restart: unless-stopped
    environment:
      - TZ=America/New_York
      - LOG_LEVEL=INFO
    volumes:
      - ./aircraft_data:/app/aircraft_data
      - ./logs:/app/logs
      - ./data:/app/data
    ports:
      - "8080:8080"  # For health checks
    networks:
      - skycards-network
    healthcheck:
      test: ["CMD", "python", "-c", "import os; exit(0 if os.path.exists('/app/logs/bot_healthy') else 1)"]
      interval: 5m
      timeout: 10s
      retries: 3
      start_period: 30s

networks:
  skycards-network:
    driver: bridge

volumes:
  bot-data:
    driver: local
'''
    
    with open(deploy_dir / "docker-compose.yml", "w") as f:
        f.write(compose_content)
    print("  Created docker-compose.yml")
    
    # Create startup script
    startup_script = '''#!/bin/bash
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
'''
    
    with open(deploy_dir / "start.sh", "w") as f:
        f.write(startup_script)
    os.chmod(deploy_dir / "start.sh", 0o755)
    print("  Created start.sh")
    
    # Create deployment instructions
    instructions = '''# Skycards Bot - Synology NAS Deployment

## Quick Start

1. Upload this package to your Synology NAS
2. Extract: `tar -xzf skycards-bot-synology.tar.gz`
3. Navigate: `cd skycards-bot`
4. Deploy: `docker-compose up -d`
5. Monitor: `docker logs skycards-bot -f`

## Commands

### Start Bot
```bash
docker-compose up -d
```

### Stop Bot
```bash
docker-compose down
```

### View Logs
```bash
docker logs skycards-bot -f
```

### Restart Bot
```bash
docker-compose restart
```

### Update Bot
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Monitoring

### Check Status
```bash
docker ps | grep skycards-bot
```

### Health Check
```bash
docker exec skycards-bot python -c "print('Bot is running!')"
```

### View Resource Usage
```bash
docker stats skycards-bot
```

## Troubleshooting

### Bot Not Starting
1. Check logs: `docker logs skycards-bot`
2. Verify .env file has correct Discord token
3. Ensure all required files are present

### Bot Disconnecting
1. Check Discord API status
2. Verify internet connection on NAS
3. Check bot token hasn't expired

### High Memory Usage
1. Restart container: `docker-compose restart`
2. Monitor aircraft database size
3. Check for memory leaks in logs

## File Locations

- Bot files: `/volume1/docker/skycards-bot/`
- Logs: `/volume1/docker/skycards-bot/logs/`
- Aircraft data: `/volume1/docker/skycards-bot/aircraft_data/`

## Support

The bot monitors for rare aircraft types:
- AB18: Aero Boero AB-180
- VUT1: Evektor Cobra  
- KFIR: IAI Kfir
- Plus other military aircraft (C17, F16, A10)

Your Discord channel will receive alerts when these aircraft are detected globally.
'''
    
    with open(deploy_dir / "README.md", "w") as f:
        f.write(instructions)
    print("  Created README.md")
    
    # Create tar.gz package
    print(f"\nCreating compressed package...")
    with tarfile.open("skycards-bot-synology.tar.gz", "w:gz") as tar:
        tar.add(deploy_dir, arcname="skycards-bot")
    
    package_size = os.path.getsize("skycards-bot-synology.tar.gz") / 1024 / 1024
    
    print(f"\n" + "=" * 50)
    print(f"DEPLOYMENT PACKAGE READY!")
    print(f"=" * 50)
    print(f"Files copied: {copied_files}")
    print(f"Missing files: {missing_files}")
    print(f"Package: skycards-bot-synology.tar.gz")
    print(f"Package size: {package_size:.1f} MB")
    
    if missing_files > 0:
        print(f"\n⚠ WARNING: {missing_files} files missing!")
        print(f"Please ensure all required files exist before deployment.")
    
    print(f"\nNEXT STEPS:")
    print(f"1. Upload 'skycards-bot-synology.tar.gz' to your Synology NAS")
    print(f"2. SSH to NAS or use Terminal")
    print(f"3. Extract: tar -xzf skycards-bot-synology.tar.gz")
    print(f"4. Deploy: cd skycards-bot && docker-compose up -d")
    print(f"5. Monitor: docker logs skycards-bot -f")
    print(f"\nYour bot will then run 24/7 monitoring for rare aircraft!")

if __name__ == "__main__":
    create_deployment_package()
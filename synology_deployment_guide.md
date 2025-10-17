# Deploy Skycards Bot to Synology NAS for 24/7 Operation

## Overview
This guide will help you deploy your Discord bot to your Synology NAS so it runs 24/7 without needing your main computer.

## Prerequisites
- Synology NAS with DSM 7.0+
- SSH access enabled on your NAS
- Python 3.9+ support (Container Manager or Python Package)

## Deployment Options

### Option 1: Docker Container (Recommended)
The easiest and most reliable method.

### Option 2: Python Package on DSM
Direct installation using Synology's Python package.

---

## Option 1: Docker Container Deployment

### Step 1: Create Dockerfile
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create data directory
RUN mkdir -p aircraft_data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=America/New_York

# Run the bot
CMD ["python", "bot.py"]
```

### Step 2: Create docker-compose.yml
```yaml
version: '3.8'

services:
  skycards-bot:
    build: .
    container_name: skycards-bot
    restart: unless-stopped
    environment:
      - TZ=America/New_York
    volumes:
      - ./aircraft_data:/app/aircraft_data
      - ./logs:/app/logs
    networks:
      - skycards-network

networks:
  skycards-network:
    driver: bridge
```

### Step 3: Deployment Script
```bash
#!/bin/bash
# deploy_to_synology.sh

echo "Deploying Skycards Bot to Synology NAS"
echo "======================================"

# Configuration
NAS_IP="192.168.1.XXX"  # Replace with your NAS IP
NAS_USER="your-username"  # Replace with your username
DEPLOY_PATH="/volume1/docker/skycards-bot"

echo "1. Creating deployment package..."
# Create deployment directory
mkdir -p synology-deploy

# Copy essential files
cp bot.py synology-deploy/
cp rare_hunter.py synology-deploy/
cp alert_window.py synology-deploy/
cp rarity.py synology-deploy/
cp alerts_sources.py synology-deploy/
cp mission_finder.py synology-deploy/
cp user_airports.py synology-deploy/
cp airport_llm.py synology-deploy/
cp alert_tracker.py synology-deploy/
cp requirements.txt synology-deploy/
cp .env synology-deploy/
cp rarity.json synology-deploy/
cp ftea.json synology-deploy/

# Copy aircraft data (this is the big one)
cp -r aircraft_data synology-deploy/

# Copy Docker files
cat > synology-deploy/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p aircraft_data logs

ENV PYTHONUNBUFFERED=1
ENV TZ=America/New_York

CMD ["python", "bot.py"]
EOF

cat > synology-deploy/docker-compose.yml << 'EOF'
version: '3.8'

services:
  skycards-bot:
    build: .
    container_name: skycards-bot
    restart: unless-stopped
    environment:
      - TZ=America/New_York
    volumes:
      - ./aircraft_data:/app/aircraft_data
      - ./logs:/app/logs
    networks:
      - skycards-network

networks:
  skycards-network:
    driver: bridge
EOF

echo "2. Package created in synology-deploy/"
echo "3. Upload to NAS manually or use the commands below:"
echo
echo "Manual upload steps:"
echo "a. Compress: tar -czf skycards-bot.tar.gz synology-deploy/"
echo "b. Upload to NAS via File Station or SCP"
echo "c. Extract on NAS and run docker-compose up -d"
echo
echo "Automated upload (if SSH enabled):"
echo "scp -r synology-deploy/ ${NAS_USER}@${NAS_IP}:${DEPLOY_PATH}"
echo
echo "Then SSH to NAS and run:"
echo "cd ${DEPLOY_PATH}"
echo "docker-compose up -d"
```

---

## Option 2: Python Package Deployment

### Step 1: Install Python on Synology
1. Open **Package Center** on your Synology DSM
2. Search for and install **Python 3.9** or newer
3. Enable SSH in **Control Panel > Terminal & SNMP**

### Step 2: Upload Files to NAS
```bash
# Create directory structure on NAS
ssh your-username@your-nas-ip
mkdir -p /volume1/docker/skycards-bot
exit

# Upload files
scp -r C:\Projects\GitHub-Repos\Skycards-Project your-username@your-nas-ip:/volume1/docker/skycards-bot/
```

### Step 3: Install Dependencies on NAS
```bash
# SSH to NAS
ssh your-username@your-nas-ip

# Navigate to bot directory
cd /volume1/docker/skycards-bot

# Install Python dependencies
python3 -m pip install --user -r requirements.txt
```

### Step 4: Create Systemd Service (Advanced)
```bash
# Create service file
sudo nano /etc/systemd/system/skycards-bot.service
```

```ini
[Unit]
Description=Skycards Discord Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/volume1/docker/skycards-bot
ExecStart=/usr/bin/python3 bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable skycards-bot
sudo systemctl start skycards-bot
sudo systemctl status skycards-bot
```

---

## Quick Setup Script

### create_synology_package.py
```python
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
    
    # Copy Python files
    for file in python_files:
        if os.path.exists(file):
            shutil.copy2(file, deploy_dir)
            print(f"✓ Copied {file}")
        else:
            print(f"⚠ Missing {file}")
    
    # Copy aircraft data directory
    if os.path.exists("aircraft_data"):
        shutil.copytree("aircraft_data", deploy_dir / "aircraft_data")
        print(f"✓ Copied aircraft_data/ ({len(os.listdir('aircraft_data'))} files)")
    
    # Create Dockerfile
    dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p logs

ENV PYTHONUNBUFFERED=1
ENV TZ=America/New_York

CMD ["python", "bot.py"]
'''
    
    with open(deploy_dir / "Dockerfile", "w") as f:
        f.write(dockerfile_content)
    print("✓ Created Dockerfile")
    
    # Create docker-compose.yml
    compose_content = '''version: '3.8'

services:
  skycards-bot:
    build: .
    container_name: skycards-bot
    restart: unless-stopped
    environment:
      - TZ=America/New_York
    volumes:
      - ./aircraft_data:/app/aircraft_data
      - ./logs:/app/logs
    networks:
      - skycards-network

networks:
  skycards-network:
    driver: bridge
'''
    
    with open(deploy_dir / "docker-compose.yml", "w") as f:
        f.write(compose_content)
    print("✓ Created docker-compose.yml")
    
    # Create startup script
    startup_script = '''#!/bin/bash
echo "Starting Skycards Bot on Synology NAS"
echo "======================================"

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "Running in Docker container"
    python bot.py
else
    echo "Running directly on NAS"
    python3 bot.py
fi
'''
    
    with open(deploy_dir / "start.sh", "w") as f:
        f.write(startup_script)
    os.chmod(deploy_dir / "start.sh", 0o755)
    print("✓ Created start.sh")
    
    # Create tar.gz package
    print(f"\nCreating compressed package...")
    with tarfile.open("skycards-bot-synology.tar.gz", "w:gz") as tar:
        tar.add(deploy_dir, arcname="skycards-bot")
    
    print(f"✓ Created skycards-bot-synology.tar.gz")
    print(f"\nDeployment package ready!")
    print(f"Package size: {os.path.getsize('skycards-bot-synology.tar.gz') / 1024 / 1024:.1f} MB")
    
    print(f"\nNext steps:")
    print(f"1. Upload skycards-bot-synology.tar.gz to your NAS")
    print(f"2. Extract: tar -xzf skycards-bot-synology.tar.gz")
    print(f"3. Run: cd skycards-bot && docker-compose up -d")
    print(f"4. Check logs: docker logs skycards-bot")

if __name__ == "__main__":
    create_deployment_package()
```

---

## Deployment Instructions

### Step 1: Create Package
```bash
cd "C:\Projects\GitHub-Repos\Skycards-Project"
python create_synology_package.py
```

### Step 2: Upload to NAS
1. Upload `skycards-bot-synology.tar.gz` to your NAS via File Station
2. SSH to your NAS or use Terminal in DSM

### Step 3: Deploy
```bash
# Extract package
tar -xzf skycards-bot-synology.tar.gz
cd skycards-bot

# Start with Docker (recommended)
docker-compose up -d

# Or start directly
python3 bot.py
```

### Step 4: Monitor
```bash
# Check container status
docker ps

# View logs
docker logs skycards-bot -f

# Restart if needed
docker-compose restart
```

---

## Configuration for NAS

### Update .env for NAS deployment
```bash
# Add to .env file for better logging on NAS
LOG_LEVEL=INFO
LOG_FILE=/app/logs/skycards-bot.log
RESTART_ON_ERROR=true
```

### Monitor Bot Health
Create a simple health check script:

```python
#!/usr/bin/env python3
# health_check.py
import docker
import requests
import time

def check_bot_health():
    """Check if bot container is running and healthy"""
    try:
        client = docker.from_env()
        container = client.containers.get("skycards-bot")
        
        if container.status != "running":
            print(f"⚠ Container not running: {container.status}")
            container.restart()
            print("✓ Restarted container")
        else:
            print("✓ Bot container healthy")
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    check_bot_health()
```

## Summary

**Recommended approach:**
1. Use **Docker deployment** for reliability
2. Set up **automatic restarts** with docker-compose
3. Monitor logs via `docker logs skycards-bot`
4. Your bot will run 24/7 and monitor for rare aircraft globally

Once deployed, your Discord bot will continuously scan for AB18, VUT1, KFIR, and other rare aircraft even when your main computer is off!
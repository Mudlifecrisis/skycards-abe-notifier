# 🖥️ Synology Container Manager GUI Deployment

Since your Synology NAS uses Docker through the GUI (which is standard), here's a simpler approach that works with Synology's Container Manager.

## 🎯 **GUI-Based Deployment Strategy**

Instead of command-line Docker, we'll use Synology's Container Manager GUI with file sync for updates.

### **Step 1: Set Up File Sync Deployment**

1. **Create project directory on NAS:**
   ```bash
   ssh TheDrizzle@192.168.4.75 "mkdir -p /volume1/docker/skycards-project"
   ```

2. **Copy your files to NAS:**
   ```bash
   scp -r * TheDrizzle@192.168.4.75:/volume1/docker/skycards-project/
   ```

### **Step 2: Set Up Container in GUI**

1. **Open Synology DSM Web Interface**
   - Go to http://192.168.4.75:5000
   - Login with your admin account

2. **Open Container Manager**
   - Package Center → Container Manager
   - Go to "Project" tab

3. **Create New Project**
   - Click "Create"
   - Name: `skycards-bot`
   - Path: `/docker/skycards-project`
   - Source: `Create docker-compose.yml`

### **Step 3: Use This Simplified docker-compose.yml**

```yaml
version: '3.8'
services:
  skycards-bot:
    image: python:3.12-slim
    container_name: skycards-bot
    working_dir: /app
    command: >
      sh -c "pip install --no-cache-dir -r requirements.txt &&
             python -u bot.py"
    volumes:
      - ./:/app
    env_file:
      - .env
    restart: unless-stopped
```

### **Step 4: Create .env File**

Create `/volume1/docker/skycards-project/.env` with your tokens:
```
DISCORD_BOT_TOKEN=your_bot_token_here
OPENSKY_API={"clientId":"porkchopexpress-api-client","clientSecret":"your_secret"}
RARE_CH_ID=your_channel_id
```

### **Step 5: Deploy Through GUI**

1. **In Container Manager:**
   - Select your `skycards-bot` project
   - Click "Action" → "Build"
   - Wait for build to complete
   - Click "Action" → "Up" to start

2. **Monitor Logs:**
   - Click on your container
   - Go to "Log" tab
   - Watch startup logs

## 🔄 **Simple Update Workflow**

### **Method 1: File Sync Update (Recommended)**

```batch
@echo off
echo === SYNOLOGY GUI DEPLOY ===
echo Uploading files to NAS...

scp bot.py TheDrizzle@192.168.4.75:/volume1/docker/skycards-project/
scp rare_hunter.py TheDrizzle@192.168.4.75:/volume1/docker/skycards-project/
scp requirements.txt TheDrizzle@192.168.4.75:/volume1/docker/skycards-project/

echo Files uploaded. Now restart container in Container Manager GUI.
echo 1. Open Container Manager at http://192.168.4.75:5000
echo 2. Select skycards-bot project  
echo 3. Click Action → Down (stop)
echo 4. Click Action → Up (start with new files)

pause
```

### **Method 2: Synology Drive Sync (Advanced)**

1. **Install Synology Drive on your PC**
2. **Sync your project folder** to `/docker/skycards-project`
3. **Auto-restart container** when files change

## 📋 **Container Manager Troubleshooting**

### **View Logs:**
- Container Manager → Containers
- Click your container → Log tab

### **Restart Container:**
- Container Manager → Projects  
- Select `skycards-bot`
- Action → Down → Up

### **Update Container:**
- Update your local files
- Run the file sync script above
- Restart container in GUI

## ✅ **Benefits of GUI Approach:**

- ✅ **No sudo issues** - GUI handles permissions
- ✅ **Visual monitoring** - See logs, stats, health in GUI
- ✅ **Synology integration** - Works with existing DSM setup
- ✅ **File sync updates** - Simple file copy + restart
- ✅ **Backup integration** - Synology can backup your project

## 🎯 **Recommended Next Steps:**

1. Run `CHECK_SYNOLOGY_DOCKER.bat` to confirm Docker setup
2. Create project directory: `mkdir -p /volume1/docker/skycards-project`
3. Upload files: `scp -r * TheDrizzle@192.168.4.75:/volume1/docker/skycards-project/`
4. Set up container in Container Manager GUI
5. Test with simple file update workflow

This approach works perfectly with Synology's design philosophy and avoids all the command-line Docker permission issues!
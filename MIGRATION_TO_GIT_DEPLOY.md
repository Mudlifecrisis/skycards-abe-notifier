# 🚀 Migration to Git-Push-to-Deploy System

This guide will upgrade your deployment from manual SCP/SSH to a modern Git-based system with zero-password automation.

## 📋 **Migration Steps (15 minutes)**

### **Step 1: Set Up SSH Keys**
```bash
SETUP_SSH_KEYS.bat
```
- Generates SSH keys if needed
- Copies to NAS (last password entry ever!)
- Tests passwordless connection

### **Step 2: Configure Git Deployment**
```bash
SETUP_GIT_DEPLOY.bat
```
- Creates bare Git repo on NAS
- Installs automatic deployment hooks
- Moves secrets to shared directory
- Sets up git remote

### **Step 3: Test New System**
```bash
DEPLOY.bat
```
- Commits your changes
- Pushes to NAS (triggers auto-deploy)
- Shows deployment logs

---

## 🎯 **What Changes**

### **Before (Manual & Painful):**
```bash
# Old workflow - multiple password prompts
scp bot.py TheDrizzle@192.168.4.75:/volume1/docker/...
ssh TheDrizzle@192.168.4.75 "sudo docker-compose restart"
# Hope it works, no rollback plan
```

### **After (Automated & Safe):**
```bash
# New workflow - zero passwords
git add .
git commit -m "Update bot"
git push nas main
# Automatic deployment + health checks + rollback ready
```

---

## 📁 **New Directory Structure**

### **On NAS:**
```
/volume1/docker/skycards/
├── repo/                    # Bare Git repository
├── shared/                  # Secrets & data (never in git)
│   ├── .env                 # Discord tokens, API keys
│   ├── aircraft_data/       # 515K aircraft database
│   └── watchlist.json       # User search terms
├── releases/                # Timestamped deployments
│   ├── 20251017-143022/     # Each deployment
│   └── 20251017-162233/
└── deploy/
    └── current -> releases/20251017-162233/  # Active version
```

### **On Your PC (Git Repository):**
```
C:\Projects\GitHub-Repos\Skycards-Project\
├── bot.py                   # Discord bot code
├── rare_hunter.py          # Aircraft hunting logic
├── docker-compose.yml      # Container definition
├── requirements.txt        # Python dependencies
├── quick_test.sh          # Deployment verification
├── DEPLOY.bat             # One-click deployment
└── ROLLBACK.bat           # Emergency recovery
```

---

## 🔄 **New Deployment Workflow**

### **1. Make Changes**
```bash
# Edit bot.py, rare_hunter.py, etc.
```

### **2. Deploy**
```bash
DEPLOY.bat
# OR manually:
git add .
git commit -m "Add new feature"
git push nas main
```

### **3. Automatic Process**
- ✅ Code checks out to timestamped release
- ✅ Shared files (.env, database) linked in
- ✅ Quick tests run (syntax, imports)
- ✅ Symlink flips to new version
- ✅ Container restarts
- ✅ Old releases cleaned up (keeps 5)

### **4. If Something Breaks**
```bash
ROLLBACK.bat 20251017-143022
# Instant recovery to previous version
```

---

## ⚡ **Key Benefits**

### **Zero Password Prompts**
- SSH keys eliminate all authentication
- CLI and LLMs can deploy automatically

### **Atomic Deployments**
- Symlink flips ensure zero-downtime
- No partial deployments or broken states

### **Instant Rollbacks**
- One command to switch back
- Keep 5 previous versions ready

### **Proper Testing**
- Syntax checks before deployment
- Health checks after restart

### **Clean Separation**
- Code in Git, secrets stay on NAS
- No more accidentally committing .env files

---

## 🔧 **Available Commands**

| Command | Purpose |
|---------|---------|
| `SETUP_SSH_KEYS.bat` | One-time SSH key setup |
| `SETUP_GIT_DEPLOY.bat` | One-time Git deployment setup |
| `DEPLOY.bat` | Deploy current changes |
| `ROLLBACK.bat [timestamp]` | Emergency rollback |
| `git push nas main` | Direct deployment trigger |

---

## 🧪 **Testing Your Migration**

### **1. Verify SSH Keys Work**
```bash
ssh TheDrizzle@192.168.4.75 "echo 'No password required!'"
```

### **2. Test Deployment**
```bash
# Make a small change
echo "# Test deployment" >> README.md
DEPLOY.bat
```

### **3. Test Rollback**
```bash
# List available versions
ROLLBACK.bat

# Rollback to previous version
ROLLBACK.bat 20251017-143022
```

### **4. Test Bot Health**
```bash
ssh TheDrizzle@192.168.4.75 "docker logs skycards-bot --since 5m"
```

---

## 🚨 **Troubleshooting**

### **SSH Key Issues**
```bash
# Regenerate keys
SETUP_SSH_KEYS.bat

# Manual key copy
ssh-copy-id TheDrizzle@192.168.4.75
```

### **Deployment Failures**
```bash
# Check post-receive hook logs
ssh TheDrizzle@192.168.4.75 "cat /volume1/docker/skycards/repo/hooks/post-receive"

# Manual deployment
ssh TheDrizzle@192.168.4.75
cd /volume1/docker/skycards/deploy/current
docker compose up -d
```

### **Missing Shared Files**
```bash
# Restore from old location
ssh TheDrizzle@192.168.4.75 "
cd /volume1/docker/skycards
cp skycards-bot/.env shared/
cp -r skycards-bot/aircraft_data shared/
"
```

---

## 🎯 **Next Steps**

### **Optional Enhancements:**

1. **Discord Webhook Notifications**
   - Uncomment webhook in post-receive hook
   - Get notified of successful deployments

2. **GitHub Actions**
   - Auto-deploy on push to main branch
   - Full CI/CD pipeline

3. **Health Monitoring**
   - Automated health checks
   - Alert on bot failures

4. **Development Mode**
   - Hot-reload during development
   - No container restarts needed

---

## ✅ **Migration Checklist**

- [ ] Run `SETUP_SSH_KEYS.bat`
- [ ] Run `SETUP_GIT_DEPLOY.bat`  
- [ ] Test with `DEPLOY.bat`
- [ ] Verify bot working in Discord
- [ ] Test rollback capability
- [ ] Remove old deployment scripts
- [ ] Update documentation

**Estimated Time:** 15 minutes  
**Risk Level:** Low (automatic backups, instant rollback)

---

*After migration, you'll have enterprise-grade deployment with zero-password automation, atomic deployments, and instant rollbacks. Perfect for both manual updates and LLM automation.*
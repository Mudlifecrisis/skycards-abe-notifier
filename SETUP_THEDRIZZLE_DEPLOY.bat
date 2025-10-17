@echo off
echo ===============================================
echo THEDRIZZLE ADMIN GIT DEPLOY SETUP
echo ===============================================
echo.
echo This sets up Git push-to-deploy using TheDrizzle as admin user.
echo Since TheDrizzle is your admin, they should have Docker access.
echo.
pause

set ADMIN_HOST=TheDrizzle@192.168.4.75
set BASE=/volume1/docker/skycards

echo [1/6] Using existing SSH keys for TheDrizzle...
echo (SSH keys should already be set up from earlier)

echo.
echo [2/6] Testing TheDrizzle SSH connection...
ssh %ADMIN_HOST% "echo 'TheDrizzle SSH working!' && whoami" || (
    echo ❌ SSH failed. Make sure SSH keys are set up.
    echo Run: ssh-copy-id %ADMIN_HOST%
    pause
    exit /b 1
)
echo ✅ TheDrizzle SSH working

echo.
echo [3/6] Testing Docker access for TheDrizzle admin...
ssh %ADMIN_HOST% "docker --version 2>/dev/null || /usr/local/bin/docker --version 2>/dev/null || sudo docker --version" && (
    echo ✅ TheDrizzle can run Docker
) || (
    echo ❌ Docker access issue - will use sudo in deployment
    echo This is OK, we'll handle it in the hook
)

echo.
echo [4/6] Creating deployment directories...
ssh %ADMIN_HOST% "mkdir -p %BASE%/repo %BASE%/releases %BASE%/deploy %BASE%/shared"

echo.
echo [5/6] Setting up Git repository and hook...
ssh %ADMIN_HOST% "
cd %BASE%/repo && git init --bare &&
cat > hooks/post-receive << 'HOOK_EOF'
#!/bin/bash
set -euo pipefail

APP_DIR='%BASE%'
REPO_DIR='\$APP_DIR/repo'
DEPLOY_DIR='\$APP_DIR/deploy'
RELEASES_DIR='\$APP_DIR/releases'
SHARED_DIR='\$APP_DIR/shared'

TS=\$(date +%%Y%%m%%d-%%H%%M%%S)
NEW_RELEASE='\$RELEASES_DIR/\$TS'

echo '[HOOK] Starting deployment: \$TS'

# Checkout to new release
mkdir -p '\$NEW_RELEASE'
git --work-tree='\$NEW_RELEASE' --git-dir='\$REPO_DIR' checkout -f

# Link shared assets
ln -sfn '\$SHARED_DIR/.env' '\$NEW_RELEASE/.env'
ln -sfn '\$SHARED_DIR/aircraft_data' '\$NEW_RELEASE/aircraft_data'
ln -sfn '\$SHARED_DIR/watchlist.json' '\$NEW_RELEASE/watchlist.json'

# Quick tests (if present)
if [ -f '\$NEW_RELEASE/quick_test.sh' ]; then
    bash '\$NEW_RELEASE/quick_test.sh' || { 
        echo '[HOOK] Tests failed'; 
        exit 1; 
    }
fi

# Atomic symlink flip
ln -sfn '\$NEW_RELEASE' '\$DEPLOY_DIR/current'

# Restart container (try multiple Docker paths with and without sudo)
cd '\$DEPLOY_DIR/current'
echo '[HOOK] Restarting container...'

if docker compose up -d 2>/dev/null; then
    echo '[HOOK] ✅ Container restarted with docker compose'
elif /usr/local/bin/docker compose up -d 2>/dev/null; then
    echo '[HOOK] ✅ Container restarted with /usr/local/bin/docker compose'
elif docker-compose up -d 2>/dev/null; then
    echo '[HOOK] ✅ Container restarted with docker-compose'
elif sudo /usr/local/bin/docker compose up -d 2>/dev/null; then
    echo '[HOOK] ✅ Container restarted with sudo /usr/local/bin/docker compose'
elif sudo docker-compose up -d 2>/dev/null; then
    echo '[HOOK] ✅ Container restarted with sudo docker-compose'
else
    echo '[HOOK] ❌ All Docker restart attempts failed'
    echo '[HOOK] Tried: docker compose, /usr/local/bin/docker compose, docker-compose, sudo variants'
    exit 1
fi

# Cleanup old releases (keep 5)
ls -1dt '\$RELEASES_DIR'/* | tail -n +6 | xargs -r rm -rf

echo '[HOOK] ✅ Deployed \$TS'
HOOK_EOF
chmod +x hooks/post-receive
echo 'Post-receive hook created and made executable'
"

echo.
echo [6/6] Updating git remote to use TheDrizzle...
git remote remove nas 2>nul || echo (no existing nas remote)
git remote add nas ssh://%ADMIN_HOST%%BASE%/repo

echo.
echo ===============================================
echo ✅ THEDRIZZLE ADMIN DEPLOYMENT SETUP COMPLETE!
echo.
echo Your deployment is now:
echo   git add . && git commit -m "update" && git push nas main
echo.
echo Next steps:
echo   1. Copy shared files: COPY_SHARED_FILES_THEDRIZZLE.bat
echo   2. First deploy: DEPLOY_THEDRIZZLE.bat "initial deploy" 
echo   3. Test: /status in Discord
echo.
echo Rollback format:
echo   ROLLBACK_THEDRIZZLE.bat YYYYMMDD-HHMMSS
echo ===============================================
pause
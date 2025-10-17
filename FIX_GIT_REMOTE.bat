@echo off
echo ===============================================
echo FIXING GIT REMOTE SETUP
echo ===============================================
echo.

set ADMIN_HOST=TheDrizzle@192.168.4.75
set BASE=/volume1/docker/skycards

echo [1/4] Testing SSH connection...
ssh %ADMIN_HOST% "echo 'SSH working' && whoami" || (
    echo ❌ SSH connection failed
    echo Make sure SSH keys are set up: ssh-copy-id %ADMIN_HOST%
    pause
    exit /b 1
)
echo ✅ SSH connection working

echo.
echo [2/4] Creating Git bare repository on NAS...
ssh %ADMIN_HOST% "
mkdir -p %BASE%/repo %BASE%/releases %BASE%/deploy %BASE%/shared &&
cd %BASE%/repo &&
git init --bare &&
echo 'Bare repository created'
" || (
    echo ❌ Failed to create Git repository
    pause
    exit /b 1
)
echo ✅ Git repository created

echo.
echo [3/4] Installing post-receive hook...
ssh %ADMIN_HOST% "cat > %BASE%/repo/hooks/post-receive << 'HOOK_EOF'
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

# Restart container (try multiple Docker paths)
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
    exit 1
fi

# Cleanup old releases (keep 5)
ls -1dt '\$RELEASES_DIR'/* | tail -n +6 | xargs -r rm -rf

echo '[HOOK] ✅ Deployed \$TS'
HOOK_EOF
chmod +x %BASE%/repo/hooks/post-receive &&
echo 'Post-receive hook installed and made executable'
" || (
    echo ❌ Failed to install hook
    pause
    exit /b 1
)
echo ✅ Post-receive hook installed

echo.
echo [4/4] Adding NAS remote to local Git...
git remote remove nas 2>nul || echo (no existing nas remote)
git remote add nas ssh://%ADMIN_HOST%%BASE%/repo
git remote -v

echo.
echo ===============================================
echo ✅ GIT REMOTE SETUP COMPLETE!
echo.
echo Test deployment with:
echo   DEPLOY_THEDRIZZLE.bat "test deploy"
echo.
echo Don't forget to copy shared files first:
echo   COPY_SHARED_FILES_THEDRIZZLE.bat
echo ===============================================
pause
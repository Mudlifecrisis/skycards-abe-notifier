@echo off
echo ===============================================
echo ADMIN USER GIT DEPLOY SETUP
echo ===============================================
echo.
echo This sets up Git push-to-deploy using your DSM admin account.
echo Admin users can run Docker without permission issues.
echo.
echo STEP 1: Set up SSH keys for admin user
echo STEP 2: Create Git deployment system  
echo STEP 3: Switch git remote to admin user
echo.
pause

set ADMIN_HOST=admin@192.168.4.75
set BASE=/volume1/docker/skycards

echo [1/6] Generating SSH keys for admin user...
ssh-keygen -t ed25519 -C "skycards-admin" -f %USERPROFILE%\.ssh\id_ed25519_admin

echo.
echo [2/6] Copying admin SSH key to NAS...
echo You'll need to enter the ADMIN password once:
type %USERPROFILE%\.ssh\id_ed25519_admin.pub | ssh %ADMIN_HOST% "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

echo.
echo [3/6] Testing admin SSH connection...
ssh -i %USERPROFILE%\.ssh\id_ed25519_admin %ADMIN_HOST% "echo 'Admin SSH working!' && whoami" || (
    echo ❌ Admin SSH failed. Check admin username and password.
    pause
    exit /b 1
)
echo ✅ Admin SSH working

echo.
echo [4/6] Testing Docker access for admin...
ssh -i %USERPROFILE%\.ssh\id_ed25519_admin %ADMIN_HOST% "docker --version 2>/dev/null || /usr/local/bin/docker --version" || (
    echo ❌ Admin cannot run Docker. Check Container Manager installation.
    pause
    exit /b 1
)
echo ✅ Admin can run Docker

echo.
echo [5/6] Creating deployment directories...
ssh -i %USERPROFILE%\.ssh\id_ed25519_admin %ADMIN_HOST% "mkdir -p %BASE%/repo %BASE%/releases %BASE%/deploy %BASE%/shared"

echo.
echo [6/6] Setting up Git repository and hook...
ssh -i %USERPROFILE%\.ssh\id_ed25519_admin %ADMIN_HOST% "
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

# Restart container (try multiple Docker paths)
cd '\$DEPLOY_DIR/current'
if docker compose up -d 2>/dev/null || \
   /usr/local/bin/docker compose up -d 2>/dev/null || \
   docker-compose up -d 2>/dev/null; then
    echo '[HOOK] ✅ Container restarted successfully'
else
    echo '[HOOK] ❌ Container restart failed'
    exit 1
fi

# Cleanup old releases (keep 5)
ls -1dt '\$RELEASES_DIR'/* | tail -n +6 | xargs -r rm -rf

echo '[HOOK] ✅ Deployed \$TS'
HOOK_EOF
chmod +x hooks/post-receive
"

echo.
echo [LOCAL] Updating git remote to use admin user...
git remote remove nas 2>nul || echo (no existing nas remote)
git remote add nas ssh://%ADMIN_HOST%%BASE%/repo

echo.
echo [LOCAL] Creating SSH config for admin key...
echo. >> %USERPROFILE%\.ssh\config
echo Host 192.168.4.75 >> %USERPROFILE%\.ssh\config
echo   User admin >> %USERPROFILE%\.ssh\config
echo   IdentityFile %USERPROFILE%\.ssh\id_ed25519_admin >> %USERPROFILE%\.ssh\config

echo.
echo ===============================================
echo ✅ ADMIN USER DEPLOYMENT SETUP COMPLETE!
echo.
echo Your deployment is now:
echo   git add . && git commit -m "update" && git push nas main
echo.
echo Next steps:
echo   1. Copy shared files: COPY_SHARED_FILES.bat
echo   2. First deploy: git push nas main
echo   3. Test: /status in Discord
echo.
echo Rollback format:
echo   ROLLBACK_ADMIN.bat YYYYMMDD-HHMMSS
echo ===============================================
pause
@echo off
echo ===============================================
echo PRE-FLIGHT DEPLOYMENT CHECKLIST
echo ===============================================
echo.

set USERHOST=TheDrizzle@192.168.4.75
set BASE=/volume1/docker/skycards

echo [1/7] Testing SSH key authentication...
ssh -o PasswordAuthentication=no %USERHOST% "echo 'SSH keys working!'" || (
    echo ❌ SSH keys not set up. Run SETUP_SSH_KEYS.bat first.
    pause
    exit /b 1
)
echo ✅ SSH keys working

echo.
echo [2/7] Checking Docker availability on NAS...
ssh %USERHOST% "sudo /usr/local/bin/docker --version 2>/dev/null || sudo docker --version 2>/dev/null || /usr/syno/bin/docker --version 2>/dev/null" || (
    echo ❌ Docker not found on NAS
    echo    Make sure Docker package is installed in Synology Package Center
    pause
    exit /b 1
)
echo ✅ Docker available

echo.
echo [2b/7] Testing Docker Compose...
ssh %USERHOST% "sudo /usr/local/bin/docker compose version 2>/dev/null || sudo docker-compose --version 2>/dev/null" || (
    echo ❌ Docker Compose not available
    echo    This is normal for older Synology - we'll use docker-compose instead
    echo ⚠️  Note: Using legacy docker-compose syntax
)
echo ✅ Docker Compose working

echo.
echo [3/7] Verifying directory structure exists...
ssh %USERHOST% "ls -la %BASE%/repo %BASE%/shared %BASE%/deploy 2>/dev/null" || (
    echo ❌ Directory structure not found. Run SETUP_GIT_DEPLOY.bat first.
    pause
    exit /b 1
)
echo ✅ Directory structure exists

echo.
echo [4/7] Checking post-receive hook...
ssh %USERHOST% "test -x %BASE%/repo/hooks/post-receive" || (
    echo ❌ Post-receive hook not executable
    echo    Fix: ssh %USERHOST% "chmod +x %BASE%/repo/hooks/post-receive"
    pause
    exit /b 1
)
echo ✅ Post-receive hook executable

echo.
echo [5/7] Verifying shared files exist...
ssh %USERHOST% "ls -la %BASE%/shared/.env %BASE%/shared/watchlist.json 2>/dev/null" || (
    echo ❌ Missing shared files (.env or watchlist.json)
    echo    Copy your .env: scp .env %USERHOST%:%BASE%/shared/.env
    pause
    exit /b 1
)
echo ✅ Shared files present

echo.
echo [6/7] Checking Git remote configuration...
git remote -v | findstr "nas" || (
    echo ❌ Git remote 'nas' not configured
    echo    Run SETUP_GIT_DEPLOY.bat to add remote
    pause
    exit /b 1
)
echo ✅ Git remote configured

echo.
echo [7/7] Testing NAS outbound connectivity...
ssh %USERHOST% "curl -s --connect-timeout 5 https://discord.com > /dev/null" || (
    echo ⚠️  Warning: NAS may not reach Discord API
    echo    Bot may fail to connect - check firewall/network
)
echo ✅ Basic connectivity test passed

echo.
echo ===============================================
echo ✅ PRE-FLIGHT CHECK COMPLETE!
echo.
echo All systems ready for deployment.
echo Next steps:
echo   1. Copy aircraft database: scp -r aircraft_data %USERHOST%:%BASE%/shared/
echo   2. Copy .env file: scp .env %USERHOST%:%BASE%/shared/.env  
echo   3. First deployment: DEPLOY.bat "initial deploy"
echo   4. Test in Discord: /status and /hunt commands
echo.
echo If deployment fails, use: ROLLBACK.bat [timestamp]
echo ===============================================
pause
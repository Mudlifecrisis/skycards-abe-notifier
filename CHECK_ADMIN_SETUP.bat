@echo off
echo ===============================================
echo CHECKING ADMIN DEPLOYMENT SETUP
echo ===============================================
echo.

set ADMIN_HOST=admin@192.168.4.75
set BASE=/volume1/docker/skycards

echo [1/5] Testing admin SSH key...
ssh -i %USERPROFILE%\.ssh\id_ed25519_admin %ADMIN_HOST% "echo 'Admin SSH working' && whoami" && (
    echo ✅ Admin SSH key working
) || (
    echo ❌ Admin SSH key not working
    echo Keys may not have been copied properly
    goto troubleshoot
)

echo.
echo [2/5] Testing Docker access...
ssh -i %USERPROFILE%\.ssh\id_ed25519_admin %ADMIN_HOST% "docker --version 2>/dev/null || /usr/local/bin/docker --version" && (
    echo ✅ Admin can run Docker
) || (
    echo ❌ Admin cannot run Docker
    goto troubleshoot
)

echo.
echo [3/5] Checking directory structure...
ssh -i %USERPROFILE%\.ssh\id_ed25519_admin %ADMIN_HOST% "ls -la %BASE%/" && (
    echo ✅ Directory structure exists
) || (
    echo ❌ Directory structure missing
    goto troubleshoot
)

echo.
echo [4/5] Checking Git repository...
ssh -i %USERPROFILE%\.ssh\id_ed25519_admin %ADMIN_HOST% "ls -la %BASE%/repo/hooks/post-receive" && (
    echo ✅ Git repo and hook exist
) || (
    echo ❌ Git repo or hook missing
    goto troubleshoot
)

echo.
echo [5/5] Checking Git remote...
git remote -v | findstr "nas" && (
    echo ✅ Git remote configured
) || (
    echo ❌ Git remote not configured
    goto troubleshoot
)

echo.
echo ===============================================
echo ✅ SETUP LOOKS GOOD!
echo.
echo Next steps:
echo 1. Copy shared files: COPY_SHARED_FILES.bat
echo 2. First deployment: DEPLOY_ADMIN.bat "initial deploy"
echo ===============================================
pause
goto end

:troubleshoot
echo.
echo ===============================================
echo 🔧 TROUBLESHOOTING NEEDED
echo.
echo The setup didn't complete properly. Let's fix it:
echo.
echo 1. Re-run setup with more time: SETUP_ADMIN_DEPLOY.bat
echo 2. Check admin password is correct
echo 3. Make sure admin user exists on NAS
echo 4. Verify NAS IP is 192.168.4.75
echo.
echo Manual setup commands:
echo ssh-keygen -t ed25519 -C "skycards-admin" -f %USERPROFILE%\.ssh\id_ed25519_admin
echo ssh-copy-id -i %USERPROFILE%\.ssh\id_ed25519_admin.pub admin@192.168.4.75
echo ===============================================
pause

:end
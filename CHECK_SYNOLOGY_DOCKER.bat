@echo off
echo ===============================================
echo SYNOLOGY DOCKER ACCESS CHECK
echo ===============================================
echo.

set USERHOST=TheDrizzle@192.168.4.75

echo [1/3] Testing basic SSH connection...
ssh %USERHOST% "whoami && pwd" || (
    echo ❌ SSH connection failed
    pause
    exit /b 1
)
echo ✅ SSH connection working

echo.
echo [2/3] Checking Docker without sudo...
ssh %USERHOST% "docker --version 2>/dev/null" && (
    echo ✅ Docker accessible without sudo
    goto compose_check
) || echo ❌ Docker requires sudo or not in PATH

echo.
echo [3/3] Checking if user is in docker group...
ssh %USERHOST% "groups | grep -q docker && echo 'User in docker group' || echo 'User NOT in docker group'"

echo.
echo [4/3] Testing Docker GUI management approach...
ssh %USERHOST% "ls -la /var/packages/Docker/target/usr/bin/docker* 2>/dev/null || echo 'Docker GUI binaries not found'"

:compose_check
echo.
echo ===============================================
echo ANALYSIS & SOLUTIONS:
echo.
echo Your Synology NAS uses Docker through the Package Center GUI.
echo This is normal and expected for Synology systems.
echo.
echo RECOMMENDED APPROACH:
echo 1. Use Synology Task Scheduler instead of SSH deploy
echo 2. Or add your user to docker group: 
echo    - SSH as admin: ssh admin@192.168.4.75
echo    - Run: sudo usermod -aG docker TheDrizzle
echo 3. Or use Container Manager GUI for deployments
echo.
echo ALTERNATIVE: Switch to Container Manager GUI approach
echo - Upload your docker-compose.yml through web interface
echo - Use GUI for container management
echo - Skip command-line deployment entirely
echo ===============================================
pause
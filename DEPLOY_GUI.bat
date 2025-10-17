@echo off
echo ===============================================
echo SYNOLOGY GUI DEPLOYMENT
echo ===============================================
echo.
echo This uploads your files to NAS for Container Manager GUI
echo You'll need to restart the container in the web interface

set USERHOST=TheDrizzle@192.168.4.75
set PROJECT_DIR=/volume1/docker/skycards-project

set MSG=%*
if "%MSG%"=="" set MSG=GUI deploy update

echo [1/4] Adding changes to git (for tracking)...
git add -A
git commit -m "%MSG%" 2>nul || echo (no changes to commit)

echo.
echo [2/4] Uploading core files to NAS...
scp bot.py %USERHOST%:%PROJECT_DIR%/ || goto error
scp rare_hunter.py %USERHOST%:%PROJECT_DIR%/ || goto error  
scp requirements.txt %USERHOST%:%PROJECT_DIR%/ || goto error
scp docker-compose.yml %USERHOST%:%PROJECT_DIR%/ || goto error

echo.
echo [3/4] Uploading configuration files...
scp aliases.json %USERHOST%:%PROJECT_DIR%/ || goto error
scp watchlist.json %USERHOST%:%PROJECT_DIR%/ 2>nul || echo (watchlist.json not found locally - ok)

echo.
echo [4/4] Checking if aircraft_data exists...
if exist "aircraft_data" (
    echo Found aircraft_data directory, uploading...
    scp -r aircraft_data %USERHOST%:%PROJECT_DIR%/ || goto error
) else (
    echo aircraft_data not found locally - assuming it's already on NAS
)

echo.
echo ===============================================
echo ✅ FILES UPLOADED SUCCESSFULLY!
echo.
echo Next steps:
echo 1. Open Container Manager: http://192.168.4.75:5000
echo 2. Go to Container → skycards-bot
echo 3. Click "Stop" then "Start" to restart with new files
echo.
echo OR using Container Manager Project:
echo 1. Go to Project tab
echo 2. Select skycards-bot project  
echo 3. Action → Down (stop)
echo 4. Action → Up (start with new files)
echo.
echo The container will automatically install requirements.txt
echo and run the new bot.py when it starts up.
echo ===============================================
pause
goto end

:error
echo.
echo ❌ Upload failed! Check:
echo 1. SSH keys are working: ssh %USERHOST%
echo 2. Directory exists: ssh %USERHOST% "ls -la %PROJECT_DIR%"
echo 3. Network connection to NAS
pause

:end
@echo off
echo ===============================================
echo RESCUE DEPLOYMENT - Simple and Fast
echo ===============================================
echo.
echo This will:
echo 1. Copy the RESCUE version to your NAS
echo 2. Restart the container 
echo 3. Check if it's working
echo.
pause

echo [1/3] Copying rescue files...
scp synology-deploy/rare_hunter_RESCUE.py TheDrizzle@192.168.4.75:/volume1/docker/skycards/skycards-bot/rare_hunter.py
if errorlevel 1 goto error

echo.
echo [2/3] Restarting container...
ssh TheDrizzle@192.168.4.75 "cd /volume1/docker/skycards/skycards-bot && sudo docker-compose restart"
if errorlevel 1 goto error

echo.
echo [3/3] Waiting for startup and checking logs...
timeout /t 15 > nul
ssh TheDrizzle@192.168.4.75 "sudo docker logs skycards-bot --since 2m | grep -E 'RESCUE|states_pulled|resolved|matched|alerts_sent'"

echo.
echo ===============================================
echo RESCUE DEPLOYMENT COMPLETE!
echo Look for lines showing states_pulled=XXXX (should be thousands)
echo If you see states_pulled=0, there's still an API issue
echo ===============================================
pause
goto end

:error
echo.
echo ===============================================  
echo DEPLOYMENT FAILED!
echo Check your SSH connection and try again
echo ===============================================
pause

:end
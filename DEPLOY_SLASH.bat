@echo off
echo ===============================================
echo SLASH COMMAND BOT DEPLOYMENT
echo ===============================================
echo.
echo This will deploy the new slash command bot:
echo - Modern /hunt /watchlist /airports commands
echo - Autocomplete for aircraft types
echo - Clean alias system (globemaster -> C17)
echo - No OAuth complexity, just works
echo.
echo IMPORTANT: You need to re-invite your bot with
echo applications.commands scope BEFORE deploying!
echo.
pause

echo [1/4] Backing up current bot...
ssh TheDrizzle@192.168.4.75 "cd /volume1/docker/skycards/skycards-bot && cp bot.py bot_OLD.py"
if errorlevel 1 goto error

echo.
echo [2/4] Deploying slash command bot...
scp synology-deploy/bot_SLASH.py TheDrizzle@192.168.4.75:/volume1/docker/skycards/skycards-bot/bot.py
if errorlevel 1 goto error

echo.
echo [3/4] Deploying rescue rare hunter...
scp synology-deploy/rare_hunter_RESCUE.py TheDrizzle@192.168.4.75:/volume1/docker/skycards/skycards-bot/rare_hunter.py
if errorlevel 1 goto error

echo.
echo [4/4] Restarting container...
ssh TheDrizzle@192.168.4.75 "cd /volume1/docker/skycards/skycards-bot && sudo docker-compose restart"
if errorlevel 1 goto error

echo.
echo [CHECK] Waiting for startup and checking logs...
timeout /t 20 > nul
ssh TheDrizzle@192.168.4.75 "sudo docker logs skycards-bot --since 3m | grep -E 'SETUP|slash|commands|ready'"

echo.
echo ===============================================
echo SLASH COMMAND DEPLOYMENT COMPLETE!
echo.
echo Your new commands:
echo   /hunt type:globemaster     - Find C-17s
echo   /hunt type:chinook         - Find CH-47s
echo   /watchlist add aircraft C17 - Add to watchlist
echo   /watchlist list            - Show watchlist
echo   /airports add KABE         - Monitor airport
echo   /stats                     - Show statistics
echo.
echo Look for "Synced commands" in the output above
echo If bot fails to start, restore with: bot_OLD.py
echo ===============================================
pause
goto end

:error
echo.
echo ===============================================
echo DEPLOYMENT FAILED!
echo.
echo If this failed, restore the old bot:
echo ssh TheDrizzle@192.168.4.75
echo cd /volume1/docker/skycards/skycards-bot
echo cp bot_OLD.py bot.py
echo sudo docker-compose restart
echo ===============================================
pause

:end
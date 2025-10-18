@echo off
echo 🧪 TESTING SLASH COMMAND SYSTEM
echo.

echo 📊 Checking container status...
ssh TheDrizzle@192.168.4.75 "cd /volume1/docker/skycards && ls -la bot.py rare_hunter.py docker-compose.yml"
echo.

echo 📋 Checking if new code is running (looking for version banner)...
ssh TheDrizzle@192.168.4.75 "cd /volume1/docker/skycards && (/usr/local/bin/docker logs skycards-bot --since=5m | grep 'Skycards.*Starting version' || echo 'Version banner not found - container may not have restarted')"
echo.

echo 🔧 Testing HTTP sync server...
curl -v -X POST http://192.168.4.75:8765/admin/sync -H "x-token: sync-token-12345" 2>&1 | findstr /C:"200 OK" /C:"synced" /C:"Connection refused" /C:"timeout"
echo.

echo 📱 DISCORD SLASH COMMAND CHECK:
echo Expected commands (7 total):
echo 1. /watch
echo 2. /rarity_min  
echo 3. /add_search
echo 4. /remove_search
echo 5. /list_search
echo 6. /hunt_stats
echo 7. /clear_search ⭐ NEW
echo.

echo 💡 If /clear_search is missing:
echo 1. Try the HTTP sync: curl -X POST http://192.168.4.75:8765/admin/sync -H "x-token: sync-token-12345"
echo 2. Check Discord in 30 seconds
echo 3. If still missing, container isn't running new code
echo.

pause
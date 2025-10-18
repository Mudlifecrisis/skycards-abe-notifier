@echo off
echo 🔧 MANUAL CONTAINER RESTART (Docker Permissions Workaround)
echo.
echo This script works around Docker permission issues by using Synology GUI restart
echo.

echo ✅ 1. Files normalized - bind-mount compose is now the official version
echo ✅ 2. Latest bot.py with version banner copied to main directory  
echo ✅ 3. Post-receive hook updated for reliable deployment
echo.

echo 🚨 NEXT STEPS FOR YOU:
echo.
echo 1. Go to Synology DSM → Container Manager
echo 2. Find "skycards-bot" container
echo 3. Click Action → Restart
echo 4. Wait 30 seconds for startup
echo 5. Run: TEST_SLASH_COMMANDS.bat
echo.

echo 📋 Expected Results:
echo - Bot logs should show: "🤖 [Skycards] Starting version=YYYYMMDD-HHMMSS"
echo - Discord should have 7 slash commands including /clear_search
echo - HTTP sync server should be available on port 8765
echo.

echo 🔧 If /clear_search still missing after restart:
echo - Run: curl -X POST http://192.168.4.75:8765/admin/sync -H "x-token: sync-token-12345"
echo.

pause
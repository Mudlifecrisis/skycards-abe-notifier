@echo off
echo 🔄 Restarting Skycards Bot Container with New Bind-Mount Configuration...

REM Set version for tracking
set SC_VERSION=%date:~6,4%%date:~3,2%%date:~0,2%-%time:~0,2%%time:~3,2%

echo Setting SC_VERSION=%SC_VERSION%

REM Restart container with portable Docker commands
ssh TheDrizzle@192.168.4.75 "cd /volume1/docker/skycards && export SC_VERSION=%SC_VERSION% && (docker compose down || /usr/local/bin/docker compose down || docker-compose down) && (docker compose up -d || /usr/local/bin/docker compose up -d || docker-compose up -d)"

echo ✅ Container restart initiated. 
echo 📋 Check logs for version banner with: ssh TheDrizzle@192.168.4.75 "docker logs skycards-bot | tail -10"
echo 🔧 Test sync with: curl -X POST http://192.168.4.75:8765/admin/sync -H "x-token: sync-token-12345"

pause
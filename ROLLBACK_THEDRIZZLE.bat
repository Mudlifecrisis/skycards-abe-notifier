@echo off
set ADMIN_HOST=TheDrizzle@192.168.4.75
set BASE=/volume1/docker/skycards

if "%~1"=="" (
  echo === Available releases ===
  ssh %ADMIN_HOST% "ls -1t %BASE%/releases"
  echo.
  echo Usage: ROLLBACK_THEDRIZZLE.bat YYYYMMDD-HHMMSS
  echo Example: ROLLBACK_THEDRIZZLE.bat 20251017-162233
  pause
  exit /b 0
)

set TS=%1
echo === Rolling back to %TS% ===

ssh %ADMIN_HOST% "
cd %BASE% && 
ln -sfn releases/%TS% deploy/current && 
cd deploy/current && 
(docker compose up -d 2>/dev/null || /usr/local/bin/docker compose up -d 2>/dev/null || sudo docker-compose up -d)
" || (
  echo ❌ Rollback failed
  pause
  exit /b 1
)

echo ✅ Rolled back to %TS%
echo Watching logs...
timeout /t 3 > nul
ssh %ADMIN_HOST% "cd %BASE%/deploy/current && (docker compose logs --since=1m 2>/dev/null || /usr/local/bin/docker compose logs --since=1m 2>/dev/null || sudo docker-compose logs --since=1m)"
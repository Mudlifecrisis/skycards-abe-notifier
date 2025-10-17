@echo off
set USERHOST=TheDrizzle@192.168.4.75
set BASE=/volume1/docker/skycards

if "%~1"=="" (
  echo === Available releases on NAS ===
  ssh %USERHOST% "ls -1 %BASE%/releases"
  echo.
  echo Usage: ROLLBACK.bat YYYYMMDD-HHMMSS
  pause
  exit /b 0
)

set TS=%1
ssh %USERHOST% "cd %BASE% && ln -sfn releases/%TS% deploy/current && cd deploy/current && (sudo /usr/local/bin/docker compose up -d 2>/dev/null || sudo docker-compose up -d)" || (
  echo ❌ Rollback failed. Check timestamp.
  pause
  exit /b 1
)
echo ✅ Rolled back to %TS%.
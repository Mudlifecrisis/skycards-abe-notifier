@echo off
set ADMIN_HOST=admin@192.168.4.75
set BASE=/volume1/docker/skycards

if "%~1"=="" (
  echo === Available releases ===
  ssh -i %USERPROFILE%\.ssh\id_ed25519_admin %ADMIN_HOST% "ls -1t %BASE%/releases"
  echo.
  echo Usage: ROLLBACK_ADMIN.bat YYYYMMDD-HHMMSS
  echo Example: ROLLBACK_ADMIN.bat 20251017-162233
  pause
  exit /b 0
)

set TS=%1
echo === Rolling back to %TS% ===

ssh -i %USERPROFILE%\.ssh\id_ed25519_admin %ADMIN_HOST% "
cd %BASE% && 
ln -sfn releases/%TS% deploy/current && 
cd deploy/current && 
docker compose up -d
" || (
  echo ❌ Rollback failed
  pause
  exit /b 1
)

echo ✅ Rolled back to %TS%
echo Watching logs...
timeout /t 3 > nul
ssh -i %USERPROFILE%\.ssh\id_ed25519_admin %ADMIN_HOST% "cd %BASE%/deploy/current && docker compose logs --since=1m"
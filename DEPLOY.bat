@echo off
echo === MODERN DEPLOY: git push nas main ===
where git >nul 2>&1 || (echo Git not found.& pause & exit /b 1)

set MSG=%*
if "%MSG%"=="" set MSG=deploy

git add -A
git commit -m "%MSG%" || echo (no changes to commit)
git push nas main || (echo ❌ Push failed.& pause & exit /b 1)

echo.
echo Watching logs (Ctrl+C to stop)...
ssh TheDrizzle@192.168.4.75 "cd /volume1/docker/skycards/deploy/current && (sudo /usr/local/bin/docker compose logs -f --since=1m 2>/dev/null || sudo docker-compose logs -f --since=1m)"
@echo off
echo === GIT PUSH-TO-DEPLOY ===

set MSG=%*
if "%MSG%"=="" set MSG=deploy update

echo Deploying: %MSG%

git add -A
git commit -m "%MSG%" || echo (no changes to commit)
git push nas main || (
    echo ❌ Push failed. Check git remote and SSH keys.
    pause
    exit /b 1
)

echo.
echo ✅ Push successful! Watching deployment logs...
timeout /t 5 > nul

echo.
ssh -i %USERPROFILE%\.ssh\id_ed25519_admin admin@192.168.4.75 "cd /volume1/docker/skycards/deploy/current && docker compose logs -f --since=2m"
@echo off
echo === SSH KEY SETUP ===
where ssh >nul 2>&1 || (echo OpenSSH not found. Install "OpenSSH Client" in Windows Optional Features.& pause & exit /b 1)

set USERHOST=TheDrizzle@192.168.4.75

echo.
echo 1) Generate key (press Enter for defaults if prompted)...
ssh-keygen -t ed25519 -C "skycards" -N "" -f %USERPROFILE%\.ssh\id_ed25519

echo.
echo 2) Copy key to NAS authorized_keys...
where ssh-copy-id >nul 2>&1
if %errorlevel%==0 (
  ssh-copy-id %USERHOST%
) else (
  type %USERPROFILE%\.ssh\id_ed25519.pub | ssh %USERHOST% "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
)

echo.
echo Done. Test: ssh %USERHOST%
pause
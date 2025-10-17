@echo off
echo ===============================================
echo SIMPLE OAUTH2 CHECK
echo ===============================================
echo.
echo You'll get an SSH prompt. Once connected, copy and paste this command:
echo.
echo sudo docker logs skycards-bot --since 5m | grep -E "OAuth|token|Scanning"
echo.
echo ===============================================
pause

ssh TheDrizzle@192.168.4.75

pause
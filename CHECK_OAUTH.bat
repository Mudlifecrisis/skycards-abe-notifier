@echo off
echo ===============================================
echo CHECKING OAUTH2 STATUS
echo ===============================================
echo.

ssh TheDrizzle@192.168.4.75 "sudo docker logs skycards-bot --since 5m | grep -E 'OAuth|token|Scanning|authentication' && echo '' && echo 'OAuth2 check complete!'"

echo.
echo ===============================================
echo Done! Check output above for OAuth2 status
echo ===============================================
pause
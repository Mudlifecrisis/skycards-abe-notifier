@echo off
echo ===============================================
echo SKYCARDS OAUTH2 FIX - ONE CLICK SOLUTION
echo ===============================================
echo.
echo This will check and fix OAuth2 authentication
echo You only need to enter your password ONCE
echo.
pause

ssh TheDrizzle@192.168.4.75 "
echo 'Checking OAuth2 status...'
sudo docker logs skycards-bot --since 5m | grep -E 'OAuth|token|Scanning|authentication'
echo ''
echo 'Restarting container to apply OAuth2 fix...'
cd /volume1/docker/skycards/skycards-bot && sudo docker-compose restart
echo ''
echo 'Waiting for startup...'
sleep 10
echo ''
echo 'Checking if OAuth2 is now working...'
sudo docker logs skycards-bot --since 2m | grep -E 'OAuth|token|Scanning'
echo ''
echo 'OAuth2 fix complete!'
"

echo.
echo ===============================================
echo Done! Check output above to see if OAuth2 is working
echo If you see 'OAuth token obtained successfully' - it worked!
echo If you still see 'authentication failed' - we need plan B
echo ===============================================
pause
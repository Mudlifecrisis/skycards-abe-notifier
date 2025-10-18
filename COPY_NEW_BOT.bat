@echo off
echo Copying new slash command bot to container directory...

scp bot.py TheDrizzle@192.168.4.75:/volume1/docker/skycards/skycards-bot/bot.py
scp rare_hunter.py TheDrizzle@192.168.4.75:/volume1/docker/skycards/skycards-bot/rare_hunter.py
scp requirements.txt TheDrizzle@192.168.4.75:/volume1/docker/skycards/skycards-bot/requirements.txt
scp docker-compose.yml TheDrizzle@192.168.4.75:/volume1/docker/skycards/skycards-bot/docker-compose.yml
scp aliases.json TheDrizzle@192.168.4.75:/volume1/docker/skycards/skycards-bot/aliases.json

echo Files copied. Now restart the container in Container Manager.
pause
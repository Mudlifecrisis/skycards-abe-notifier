# Skycards Bot - Synology NAS Deployment

## Quick Start

1. Upload this package to your Synology NAS
2. Extract: `tar -xzf skycards-bot-synology.tar.gz`
3. Navigate: `cd skycards-bot`
4. Deploy: `docker-compose up -d`
5. Monitor: `docker logs skycards-bot -f`

## Commands

### Start Bot
```bash
docker-compose up -d
```

### Stop Bot
```bash
docker-compose down
```

### View Logs
```bash
docker logs skycards-bot -f
```

### Restart Bot
```bash
docker-compose restart
```

### Update Bot
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Monitoring

### Check Status
```bash
docker ps | grep skycards-bot
```

### Health Check
```bash
docker exec skycards-bot python -c "print('Bot is running!')"
```

### View Resource Usage
```bash
docker stats skycards-bot
```

## Troubleshooting

### Bot Not Starting
1. Check logs: `docker logs skycards-bot`
2. Verify .env file has correct Discord token
3. Ensure all required files are present

### Bot Disconnecting
1. Check Discord API status
2. Verify internet connection on NAS
3. Check bot token hasn't expired

### High Memory Usage
1. Restart container: `docker-compose restart`
2. Monitor aircraft database size
3. Check for memory leaks in logs

## File Locations

- Bot files: `/volume1/docker/skycards-bot/`
- Logs: `/volume1/docker/skycards-bot/logs/`
- Aircraft data: `/volume1/docker/skycards-bot/aircraft_data/`

## Support

The bot monitors for rare aircraft types:
- AB18: Aero Boero AB-180
- VUT1: Evektor Cobra  
- KFIR: IAI Kfir
- Plus other military aircraft (C17, F16, A10)

Your Discord channel will receive alerts when these aircraft are detected globally.

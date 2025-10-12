# Skycards ABE Notifier

A Discord bot that monitors aircraft arrivals to help you get high scores in Skycards by alerting you about:

- 🛬 Planes landing at your chosen airports (configurable, defaults to ABE)
- 💎 Rare aircraft notifications with rarity scoring
- ✨ Glowing planes and event items
- 🔄 Mirrored Discord signals from Skycards announcement channels

## Features

- **Real-time Flight Monitoring**: Uses AviationStack API to monitor active flights
- **Smart Alert Window**: Only alerts 10-30 minutes before arrival (configurable)
- **Rarity System**: Shows aircraft rarity using Season-1 formula (rarity = 7.5 - ln(FTEA))
- **De-duplication**: Won't spam you with the same flight multiple times per day
- **Skycards Integration**: Mirrors rare/glow/mission announcements from official channels
- **Quiet Hours**: Optional quiet periods when no alerts are sent
- **Slash Commands**: `/watch` and `/rarity_min` for real-time adjustments

## Setup Guide

### 1. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and bot
3. Copy the bot token for your `.env` file
4. Invite bot to your server with these permissions:
   - Send Messages
   - Use Slash Commands
   - Embed Links

### 2. Get AviationStack API Key

1. Sign up at [AviationStack](https://aviationstack.com/)
2. Get your free API key (1000 requests/month)

### 3. Install and Configure

```bash
# Clone the repository
git clone https://github.com/Mudlifecrisis/skycards-abe-notifier.git
cd skycards-abe-notifier

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.template .env
# Edit .env with your tokens and channel IDs
```

### 4. Configure .env File

Copy `.env.template` to `.env` and fill in:

- `DISCORD_BOT_TOKEN`: Your Discord bot token
- `AVIATIONSTACK_API_KEY`: Your AviationStack API key  
- `DISCORD_CHANNEL_ID`: Channel where alerts will be posted
- `TARGET_AIRPORT_IATA`: Airport to monitor (ABE, JFK, LAX, etc.)

### 5. Run the Bot

```bash
python bot.py
```

## Advanced Configuration

### Rarity System
- The bot includes pre-generated `rarity.json` and `ftea.json` from the Skycards aircraft list
- Rarity formula: `7.5 - ln(FTEA)` where FTEA = observed aircraft count
- Tiers: Ultra-rare (7.0+), Rare (5.0+), Uncommon (3.0+), Common

### Skycards Discord Integration
To get enhanced notifications from official Skycards channels:

1. Follow Skycards announcement channels into your server
2. Add the mirrored channel IDs to your `.env`:
   - `RARE_CH_ID`: Channel receiving rare aircraft posts
   - `GLOW_CH_ID`: Channel receiving glow aircraft posts  
   - `MISSION_CH_ID`: Channel receiving daily mission posts

### Alert Tuning
- `ALERT_MINUTES_MIN/MAX`: Adjust alert window (default: 10-30 minutes)
- `MIN_RARITY`: Filter out common aircraft (0.0 = all, 5.0 = rare+, 7.0 = ultra only)
- `QUIET_START/END`: Set quiet hours (24-hour format)

## Files

- `bot.py`: Main bot with Discord integration and flight monitoring
- `alert_window.py`: ETA calculations and deduplication logic
- `rarity.py`: Aircraft rarity lookup and tier classification
- `alerts_sources.py`: Parses mirrored Skycards Discord posts
- `build_rarity_json.py`: Converts aircraft CSV to JSON (one-time setup)
- `rarity.json`/`ftea.json`: Pre-generated aircraft rarity data

## Slash Commands

- `/watch <min> <max>`: Adjust alert window in minutes
- `/rarity_min <value>`: Set minimum rarity threshold

## Troubleshooting

- **No alerts**: Check your AviationStack API key and make sure flights are active to your airport
- **Bot offline**: Verify Discord bot token and permissions
- **Wrong airport**: Update `TARGET_AIRPORT_IATA` in `.env`
- **Too many alerts**: Increase `MIN_RARITY` or adjust alert window

## Contributing

Feel free to submit issues and pull requests to improve the bot!

## License

MIT License - feel free to modify and distribute.
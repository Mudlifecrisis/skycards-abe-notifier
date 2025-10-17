# 🤖 Bot Re-invite Guide for Slash Commands

Your bot needs to be re-invited with the `applications.commands` scope to enable slash commands.

## 📋 Quick Steps

### 1. Get Your Bot's Application ID
- Go to [Discord Developer Portal](https://discord.com/developers/applications)
- Click on your "Skycards Notifier" application  
- Copy the **Application ID** from the General Information tab

### 2. Generate New Invite URL
Replace `YOUR_APPLICATION_ID` with your actual Application ID:

```
https://discord.com/oauth2/authorize?client_id=YOUR_APPLICATION_ID&scope=bot+applications.commands&permissions=2147485696
```

**Example:**
```
https://discord.com/oauth2/authorize?client_id=1426997138038198285&scope=bot+applications.commands&permissions=2147485696
```

### 3. Re-invite the Bot
- Paste the URL in your browser
- Select your Discord server
- Click "Authorize"
- ✅ The bot now has slash command permissions

## 🔐 Permissions Included

The permission number `2147485696` includes:
- ✅ Send Messages
- ✅ Use Slash Commands  
- ✅ Embed Links
- ✅ Attach Files
- ✅ Read Message History
- ✅ Use External Emojis
- ✅ Add Reactions

## 🧪 Test After Re-invite

1. Deploy the new bot: `DEPLOY_SLASH.bat`
2. In Discord, type `/` and you should see your bot's commands
3. Try `/hunt type:globemaster` to test
4. If it works, you're all set! 

## 🚨 Troubleshooting

**"Slash commands not showing up"**
- Make sure you used the correct Application ID
- Wait 5-10 minutes for Discord to sync
- Try reloading Discord (Ctrl+R)

**"Bot offline after deployment"**
- Check logs: `sudo docker logs skycards-bot --since 5m`
- Look for "Synced commands" in startup logs
- If broken, restore old bot: `cp bot_OLD.py bot.py`

**"Commands show but don't work"**
- Check if `DISCORD_BOT_TOKEN` is correct in `.env`
- Verify bot has access to your channels
- Test with `/stats` first (simpler command)

## ✨ New Command Preview

After successful deployment, you'll have:

### 🎯 Hunting Commands
- `/hunt type:globemaster` - Find C-17 Globemasters
- `/hunt type:chinook` - Find CH-47 Chinooks  
- `/hunt type:f16` - Find F-16 Fighting Falcons
- `/hunt type:AB18` - Find your rare Aero Boero AB-180s

### 📋 Watchlist Management
- `/watchlist add aircraft globemaster` - Add to permanent watchlist
- `/watchlist list` - Show what you're watching
- `/watchlist remove aircraft chinook` - Stop watching

### ✈️ Airport Monitoring  
- `/airports add KABE` - Monitor Lehigh Valley airport
- `/airports list` - Show monitored airports

### 📊 Status Commands
- `/stats` - Hunting statistics with real counters
- `/status` - API connectivity check
- `/help` - Command help with examples

---

**Ready to deploy?** Run `DEPLOY_SLASH.bat` after re-inviting!
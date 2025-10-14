# bot.py
import os
import aiohttp
import asyncio
from datetime import datetime
import pytz

import discord
from discord.ext import tasks
from dotenv import load_dotenv

from alert_window import should_alert_window, pick_eta, minutes_until
from rarity import RarityLookup, rarity_tier
from alerts_sources import LiveSignal
from rare_hunter import RareAircraftHunter

load_dotenv()

# Config
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
AERODATABOX_API_KEY = os.getenv("AERODATABOX_API_KEY")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
DST_IATA = os.getenv("TARGET_AIRPORT_IATA", "ABE").upper()

WIN_MIN = int(os.getenv("ALERT_MINUTES_MIN", "10"))
WIN_MAX = int(os.getenv("ALERT_MINUTES_MAX", "30"))

SHOW_RARITY = os.getenv("SHOW_RARITY", "1") == "1"
MIN_RARITY = float(os.getenv("MIN_RARITY", "0"))

RARE_CH_ID = int(os.getenv("RARE_CH_ID", "0"))
GLOW_CH_ID = int(os.getenv("GLOW_CH_ID", "0"))
MISSION_CH_ID = int(os.getenv("MISSION_CH_ID", "0"))
RARE_ROLE_ID = int(os.getenv("RARE_ROLE_ID", "0"))
GLOW_ROLE_ID = int(os.getenv("GLOW_ROLE_ID", "0"))

QUIET_START = int(os.getenv("QUIET_START", "0"))  # 0 disables if both 0
QUIET_END = int(os.getenv("QUIET_END", "0"))

# Objects
intents = discord.Intents.default()
intents.message_content = True  # Re-enable for full functionality
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

RARITY = RarityLookup()
SIGNAL = LiveSignal()
HUNTER = RareAircraftHunter()

AERODATABOX_BASE = "https://aerodatabox.p.rapidapi.com"

async def fetch_arrivals(dst_iata: str) -> list[dict]:
    # Use FIDS endpoint for airport arrivals and departures
    url = f"{AERODATABOX_BASE}/flights/airports/iata/{dst_iata}"
    headers = {
        "X-RapidAPI-Key": AERODATABOX_API_KEY,
        "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=20) as r:
            r.raise_for_status()
            data = await r.json()
            
            # Extract arrivals from FIDS response
            arrivals = data.get("arrivals", [])
            
            # Convert AeroDataBox format to our expected format
            converted_flights = []
            for flight in arrivals:
                converted_flight = {
                    "flight": {
                        "iata": flight.get("number", ""),
                        "number": flight.get("number", "")
                    },
                    "airline": {
                        "name": flight.get("airline", {}).get("name", "Unknown Airline")
                    },
                    "departure": {
                        "iata": flight.get("departure", {}).get("airport", {}).get("iata", "")
                    },
                    "arrival": {
                        "iata": flight.get("arrival", {}).get("airport", {}).get("iata", ""),
                        "scheduled": flight.get("arrival", {}).get("scheduledTimeLocal"),
                        "estimated": flight.get("arrival", {}).get("estimatedTimeLocal")
                    },
                    "aircraft": {
                        "registration": flight.get("aircraft", {}).get("reg", ""),
                        "icao": flight.get("aircraft", {}).get("model", ""),
                        "iata": flight.get("aircraft", {}).get("model", "")
                    }
                }
                converted_flights.append(converted_flight)
            
            return converted_flights

def in_quiet_hours(now_local_hour: int) -> bool:
    if QUIET_START == QUIET_END == 0:
        return False
    if QUIET_START < QUIET_END:
        return QUIET_START <= now_local_hour < QUIET_END
    # wraps midnight
    return now_local_hour >= QUIET_START or now_local_hour < QUIET_END

def priority_for(ac_icao: str | None, rarity_value: float | None) -> int:
    ac_icao = (ac_icao or "").upper()
    if ac_icao in SIGNAL.glow_types:
        return 0
    if rarity_value is not None and rarity_value >= 7.0:
        return 1
    if ac_icao in SIGNAL.rare_types or (rarity_value or 0) >= 5.0:
        return 2
    return 3

async def post_alert(channel: discord.TextChannel, flight: dict, rarity_value: float | None, prio: int):
    airline = (flight.get("airline") or {}).get("name") or "Unknown Airline"
    f = flight.get("flight") or {}
    fnum = f.get("iata") or f.get("number") or "Unknown"
    dep = (flight.get("departure") or {}).get("iata") or "???"
    arr = (flight.get("arrival") or {}).get("iata") or "???"
    ac = flight.get("aircraft") or {}
    reg = ac.get("registration") or "?"
    ac_icao = (ac.get("icao") or "").upper()
    ac_iata = (ac.get("iata") or "").upper()

    eta_iso = pick_eta(flight.get("arrival") or {})
    mins = minutes_until(eta_iso) or 0

    # Labels/tags/mentions
    tag = ""
    mention = None
    if ac_icao in SIGNAL.glow_types:
        tag = "✨ GLOW"
        if GLOW_ROLE_ID:
            mention = f"<@&{GLOW_ROLE_ID}>"
    elif rarity_value is not None and rarity_value >= 7.0:
        tag = "💎 ULTRA"
        if RARE_ROLE_ID:
            mention = f"<@&{RARE_ROLE_ID}>"
    elif ac_icao in SIGNAL.rare_types or (rarity_value or 0) >= 5.0:
        tag = "🟣 RARE"

    title = f"{tag} {airline} {fnum} → {arr}".strip()
    embed = discord.Embed(
        title=title,
        description=f"From **{dep}** | ETA ~ **{mins:.0f} min**"
    )
    if reg != "?":
        embed.add_field(name="Registration", value=reg, inline=True)
    if ac_icao or ac_iata:
        embed.add_field(name="Aircraft", value=(ac_iata or ac_icao), inline=True)
    if SHOW_RARITY and rarity_value is not None:
        emoji, tier = rarity_tier(rarity_value)
        embed.add_field(name="Rarity", value=f"{rarity_value:.2f} {emoji} {tier}", inline=True)
    if eta_iso:
        embed.add_field(name="ETA (ISO)", value=eta_iso, inline=False)

    await channel.send(content=mention, embed=embed)

@tasks.loop(seconds=120)
async def abe_watch():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    local_hour = datetime.now().hour
    if in_quiet_hours(local_hour):
        return

    try:
        flights = await fetch_arrivals(DST_IATA)
    except Exception:
        return

    enriched: list[tuple[int, float | None, dict]] = []
    for fl in flights:
        ok, eta_iso, mins = should_alert_window(fl, DST_IATA, WIN_MIN, WIN_MAX)
        if not ok:
            continue
        ac = fl.get("aircraft") or {}
        ac_icao = (ac.get("icao") or "").upper()
        ac_iata = (ac.get("iata") or "").upper()
        rscore = RARITY.get(ac_icao, ac_iata)

        if rscore is not None and rscore < MIN_RARITY:
            continue

        prio = priority_for(ac_icao, rscore)
        enriched.append((prio, rscore, fl))

    enriched.sort(key=lambda t: t[0])
    for prio, rscore, fl in enriched:
        try:
            await post_alert(channel, fl, rscore, prio)
            await asyncio.sleep(0.5)
        except Exception:
            pass

async def post_rare_alert(channel: discord.TextChannel, aircraft: dict):
    """Post rare aircraft alert to Discord"""
    callsign = aircraft.get('callsign', 'Unknown')
    country = aircraft.get('origin_country', 'Unknown')
    matched_term = aircraft.get('matched_term', '')
    
    # Format location
    lat = aircraft.get('latitude', 0)
    lon = aircraft.get('longitude', 0)
    
    # Format altitude and speed
    alt_text = ""
    if aircraft.get('altitude_ft'):
        alt_text = f"{aircraft['altitude_ft']:,} ft"
        
    speed_text = ""
    if aircraft.get('velocity_kts'):
        speed_text = f"{aircraft['velocity_kts']} kts"
    
    title = f"🎯 **RARE AIRCRAFT FOUND** - {matched_term}"
    
    embed = discord.Embed(
        title=title,
        description=f"**{callsign}** from {country}",
        color=0xFF6B35  # Orange color for rare alerts
    )
    
    if lat and lon:
        embed.add_field(name="Location", value=f"{lat:.4f}, {lon:.4f}", inline=True)
        # Add Google Maps link
        maps_url = f"https://maps.google.com/?q={lat},{lon}"
        embed.add_field(name="Maps Link", value=f"[View on Map]({maps_url})", inline=True)
    
    if alt_text:
        embed.add_field(name="Altitude", value=alt_text, inline=True)
        
    if speed_text:
        embed.add_field(name="Speed", value=speed_text, inline=True)
        
    embed.add_field(name="ICAO24", value=aircraft.get('icao24', 'Unknown'), inline=True)
    embed.add_field(name="Detected", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
    
    # Add Skycards context
    embed.set_footer(text="💡 Use 'Catch Anywhere' item in Skycards to catch this aircraft!")
    
    await channel.send(embed=embed)

@tasks.loop(seconds=180)  # Check every 3 minutes
async def rare_hunt():
    """Global rare aircraft hunting loop"""
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return
        
    try:
        rare_aircraft = await HUNTER.find_rare_aircraft()
        
        for aircraft in rare_aircraft:
            try:
                await post_rare_alert(channel, aircraft)
                await asyncio.sleep(1)  # Brief pause between alerts
            except Exception as e:
                print(f"Error posting rare alert: {e}")
                
    except Exception as e:
        print(f"Rare hunting error: {e}")

@bot.event
async def on_message(msg: discord.Message):
    print(f"Message received: '{msg.content}' from {msg.author.name} in #{msg.channel.name}")
    
    # Skip bot messages for mirroring
    if msg.author.bot:
        if msg.channel.id == RARE_CH_ID:
            SIGNAL.handle_rare_post(msg.content)
        elif msg.channel.id == GLOW_CH_ID:
            SIGNAL.handle_glow_post(msg.content)
        elif msg.channel.id == MISSION_CH_ID:
            SIGNAL.handle_mission_post(msg.content)
        return
    
    print(f"Processing user message: {msg.content}")
    
    # Simple text commands for testing
    if msg.content.startswith("!add "):
        print("Adding search term...")
        term = msg.content[5:].strip()
        HUNTER.add_search_term(term)
        await msg.reply(f"✅ Added **{term.upper()}** to rare aircraft search!")
        
    elif msg.content == "!list":
        print("Listing search terms...")
        terms = HUNTER.get_search_terms()
        if terms:
            await msg.reply(f"🔍 Searching for: {', '.join(terms)}")
        else:
            await msg.reply("No search terms. Use `!add chinook` to add some!")
            
    elif msg.content == "!stats":
        print("Showing stats...")
        terms = HUNTER.get_search_terms()
        await msg.reply(f"📊 **Rare Hunter Stats**\n• {len(terms)} search terms active\n• Scanning every 3 minutes globally\n• Airport monitoring: ABE")
        
    elif msg.content == "!hunt" or msg.content == "!force" or msg.content == "!search":
        print("Force hunting for rare aircraft...")
        await msg.reply("🔍 **Force searching globally for rare aircraft...**")
        
        try:
            rare_aircraft = await HUNTER.find_rare_aircraft()
            
            if rare_aircraft:
                await msg.reply(f"✅ Found **{len(rare_aircraft)}** rare aircraft! Posting alerts...")
                
                for aircraft in rare_aircraft:
                    try:
                        await post_rare_alert(msg.channel, aircraft)
                        await asyncio.sleep(1)  # Brief pause between alerts
                    except Exception as e:
                        print(f"Error posting force alert: {e}")
            else:
                await msg.reply("❌ No rare aircraft found matching your search terms right now.")
                
        except Exception as e:
            print(f"Force hunt error: {e}")
            await msg.reply(f"❌ Error during force search: {str(e)}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id: {bot.user.id})")
    try:
        # Get your Discord server (guild) for instant command sync
        guild_id = CHANNEL_ID  # We'll derive guild from channel
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            guild = channel.guild
            synced = await tree.sync(guild=guild)
            print(f"✅ Synced {len(synced)} commands to {guild.name} (instant)")
        else:
            synced = await tree.sync()
            print(f"✅ Synced {len(synced)} global commands (slow)")
            
        for cmd in synced:
            print(f"  - /{cmd.name}")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    
    # Send test message to confirm bot works
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("✅ **Skycards Bot Online!** Ready for flight alerts.")
        print(f"Test message sent to #{channel.name}")
    else:
        print(f"Channel ID {CHANNEL_ID} not found!")
    
    # Start loops with error handling
    try:
        if not abe_watch.is_running():
            abe_watch.start()
            print("✅ Airport monitoring started")
    except Exception as e:
        print(f"❌ Failed to start airport monitoring: {e}")
        
    try:
        if not rare_hunt.is_running():
            rare_hunt.start()
            print("✅ Rare aircraft hunting started")
    except Exception as e:
        print(f"❌ Failed to start rare hunting: {e}")

# Slash commands (QoL)
@tree.command(name="watch", description="Set alert window (minutes)")
async def _watch(inter: discord.Interaction, min: int, max: int):
    global WIN_MIN, WIN_MAX
    WIN_MIN, WIN_MAX = min, max
    await inter.response.send_message(f"Window set to {min}–{max} minutes.", ephemeral=True)

@tree.command(name="rarity_min", description="Set minimum rarity threshold")
async def _rarity_min(inter: discord.Interaction, value: float):
    global MIN_RARITY
    MIN_RARITY = value
    await inter.response.send_message(f"Minimum rarity set to {value:.2f}.", ephemeral=True)

# Rare Aircraft Search Commands
@tree.command(name="add_search", description="Add aircraft search term with AI suggestions")
async def _add_search(inter: discord.Interaction, term: str):
    try:
        # Add the main term
        HUNTER.add_search_term(term)
        
        # Send immediate response
        await inter.response.send_message(f"✅ Added '{term.upper()}' to rare aircraft search. Getting AI suggestions...", ephemeral=False)
        
        # Get AI suggestions (this might take a few seconds)
        suggestions = await HUNTER.get_aircraft_suggestions(term)
        
        if suggestions:
            suggestion_text = ", ".join(suggestions)
            embed = discord.Embed(
                title=f"🤖 DeepSeek suggests for '{term.upper()}':",
                description=suggestion_text,
                color=0x00FF00
            )
            embed.set_footer(text="Use /add_search to add any of these terms individually")
            
            # Send as follow-up message
            await inter.followup.send(embed=embed)
            
    except Exception as e:
        print(f"Error in add_search: {e}")
        try:
            await inter.response.send_message(f"❌ Error adding search term: {str(e)}", ephemeral=True)
        except:
            await inter.followup.send(f"❌ Error adding search term: {str(e)}", ephemeral=True)

@tree.command(name="remove_search", description="Remove aircraft search term")
async def _remove_search(inter: discord.Interaction, term: str):
    try:
        HUNTER.remove_search_term(term)
        await inter.response.send_message(f"❌ Removed '{term.upper()}' from search.", ephemeral=True)
    except Exception as e:
        print(f"Error in remove_search: {e}")
        await inter.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@tree.command(name="list_search", description="List all aircraft search terms")
async def _list_search(inter: discord.Interaction):
    try:
        terms = HUNTER.get_search_terms()
        
        if terms:
            term_list = ", ".join(terms)
            embed = discord.Embed(
                title="🔍 Current Aircraft Search Terms",
                description=term_list,
                color=0x0099FF
            )
            embed.set_footer(text=f"Searching for {len(terms)} terms globally")
            await inter.response.send_message(embed=embed, ephemeral=False)
        else:
            await inter.response.send_message("No search terms configured. Use `/add_search` to add some!", ephemeral=True)
    except Exception as e:
        print(f"Error in list_search: {e}")
        await inter.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@tree.command(name="hunt_stats", description="Show rare aircraft hunting statistics")
async def _hunt_stats(inter: discord.Interaction):
    terms = HUNTER.get_search_terms()
    
    embed = discord.Embed(
        title="📊 Rare Aircraft Hunter Stats",
        color=0xFF6B35
    )
    embed.add_field(name="Search Terms", value=f"{len(terms)} active", inline=True)
    embed.add_field(name="Scan Frequency", value="Every 3 minutes", inline=True)
    embed.add_field(name="Coverage", value="Global", inline=True)
    embed.add_field(name="Active Hours", value="6 AM - 11 PM", inline=True)
    embed.add_field(name="Data Source", value="OpenSky Network", inline=True)
    embed.add_field(name="AI Assistant", value="DeepSeek", inline=True)
    
    if terms:
        embed.add_field(name="Current Searches", value=", ".join(terms[:10]), inline=False)
        
    await inter.response.send_message(embed=embed, ephemeral=False)

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
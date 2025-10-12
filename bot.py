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

load_dotenv()

# Config
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
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
intents.message_content = True
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

RARITY = RarityLookup()
SIGNAL = LiveSignal()

AVIATIONSTACK_BASE = "http://api.aviationstack.com/v1/flights"

async def fetch_arrivals(dst_iata: str) -> list[dict]:
    params = {
        "access_key": AVIATIONSTACK_API_KEY,
        "limit": 100,
        "arr_iata": dst_iata,
        "flight_status": "active"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(AVIATIONSTACK_BASE, params=params, timeout=20) as r:
            r.raise_for_status()
            data = await r.json()
            return data.get("data") or []

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

@bot.event
async def on_message(msg: discord.Message):
    # Listen for mirrored announcements in our own server.
    if msg.author.bot:
        if msg.channel.id == RARE_CH_ID:
            SIGNAL.handle_rare_post(msg.content)
        elif msg.channel.id == GLOW_CH_ID:
            SIGNAL.handle_glow_post(msg.content)
        elif msg.channel.id == MISSION_CH_ID:
            SIGNAL.handle_mission_post(msg.content)
    await bot.process_commands(msg)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id: {bot.user.id})")
    try:
        await tree.sync()
    except Exception:
        pass
    if not abe_watch.is_running():
        abe_watch.start()

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

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
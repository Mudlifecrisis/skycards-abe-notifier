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
from mission_finder import MissionFinder, parse_mission_command
from user_airports import UserAirportManager
from airport_llm import AirportLLMAssistant
from alert_tracker import AlertTracker

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
MISSION_FINDER = MissionFinder()
AIRPORT_MANAGER = UserAirportManager()
ALERT_TRACKER = AlertTracker()
AIRPORT_LLM = AirportLLMAssistant()

# Multi-user airport management (replaces old PA_AIRPORTS)
# Now handled by AIRPORT_MANAGER

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

async def post_alert(channel: discord.TextChannel, flight: dict, rarity_value: float | None, prio: int, dest_airport: str = "ABE", username: str = None):
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

    title = f"{tag} {airline} {fnum} → {dest_airport}".strip()
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

    # Track alert for reminders
    aircraft_data = {
        'callsign': fnum,
        'icao24': flight.get('icao24', 'unknown'),
        'registration': reg,
        'aircraft_type': ac_icao or ac_iata,
        'airline': airline,
        'departure': dep,
        'arrival': arr,
        'eta': eta_iso,
        'rarity': rarity_value,
        'tag': tag
    }
    
    alert_id = ALERT_TRACKER.create_alert_id(aircraft_data)
    
    # Add alert ID to embed footer for acknowledgment tracking
    embed.set_footer(text=f"React with ✅ to acknowledge • Alert ID: {alert_id[:8]}")
    
    # Send alert and add reaction for acknowledgment
    message = await channel.send(content=mention, embed=embed)
    await message.add_reaction("✅")
    
    ALERT_TRACKER.add_alert(alert_id, aircraft_data, channel.id, username)
    
    return message

@tasks.loop(seconds=300)  # 5 minutes - optimized for API limits
async def multi_user_airports_watch():
    await bot.wait_until_ready()
    
    local_hour = datetime.now().hour
    if in_quiet_hours(local_hour):
        return

    # Monitor all user airports
    all_user_airports = AIRPORT_MANAGER.get_all_airports()
    
    for username, airport_codes in all_user_airports.items():
        if not airport_codes:  # Skip users with no airports
            continue
            
        # Get user's channel
        user_channel_id = AIRPORT_MANAGER.get_channel_for_user(username)
        if not user_channel_id:
            print(f"No channel found for user {username}")
            continue
            
        channel = bot.get_channel(user_channel_id)
        if not channel:
            print(f"Channel {user_channel_id} not found for user {username}")
            continue
        
        # Monitor each airport for this user
        for airport_code in airport_codes:
            try:
                flights = await fetch_arrivals(airport_code)
                
                enriched: list[tuple[int, float | None, dict, str]] = []
                for fl in flights:
                    ok, eta_iso, mins = should_alert_window(fl, airport_code, WIN_MIN, WIN_MAX)
                    if not ok:
                        continue
                    ac = fl.get("aircraft") or {}
                    ac_icao = (ac.get("icao") or "").upper()
                    ac_iata = (ac.get("iata") or "").upper()
                    rscore = RARITY.get(ac_icao, ac_iata)

                    if rscore is not None and rscore < MIN_RARITY:
                        continue

                    prio = priority_for(ac_icao, rscore)
                    enriched.append((prio, rscore, fl, airport_code))

                enriched.sort(key=lambda t: t[0])
                for prio, rscore, fl, dest_airport in enriched:
                    try:
                        await post_alert(channel, fl, rscore, prio, dest_airport, username)
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        print(f"Error posting alert for {username}/{dest_airport}: {e}")
                        
            except Exception as e:
                print(f"Error monitoring {airport_code} for {username}: {e}")
                continue

@tasks.loop(minutes=5)  # Check for reminder alerts every 5 minutes
async def alert_reminder_loop():
    """Check for alerts that need reminders and send them"""
    await bot.wait_until_ready()
    
    try:
        # Clean up old alerts first (older than 6 hours)
        ALERT_TRACKER.cleanup_old_alerts(max_age_hours=6)
        
        # Get alerts that need reminders
        reminders_needed = ALERT_TRACKER.get_alerts_needing_reminder()
        
        for alert_id, alert_info in reminders_needed:
            try:
                channel = bot.get_channel(alert_info['channel_id'])
                if not channel:
                    print(f"Channel {alert_info['channel_id']} not found for reminder {alert_id}")
                    continue
                
                # Create reminder embed
                embed_data = ALERT_TRACKER.create_reminder_embed(alert_id, alert_info)
                embed = discord.Embed(**embed_data)
                
                # Send reminder
                message = await channel.send(embed=embed)
                await message.add_reaction("✅")
                
                # Mark as reminded
                ALERT_TRACKER.mark_reminded(alert_id)
                
                print(f"Sent reminder for alert {alert_id[:8]} to {alert_info.get('user', 'unknown')}")
                
            except Exception as e:
                print(f"Error sending reminder for {alert_id}: {e}")
                
    except Exception as e:
        print(f"Error in alert reminder loop: {e}")

async def post_rare_alert(channel: discord.TextChannel, aircraft: dict):
    """Post condensed rare aircraft alert to Discord"""
    callsign = aircraft.get('callsign', 'Unknown')
    matched_term = aircraft.get('matched_term', '')
    
    # Format altitude and speed compactly
    altitude = aircraft.get('altitude_ft', 0)
    speed = aircraft.get('velocity_kts', 0)
    
    alt_text = f"{altitude//1000}K ft" if altitude > 0 else "?? ft"
    speed_text = f"{speed}kts" if speed > 0 else "??kts"
    
    # Create tracking link - use proper FlightRadar24 format
    track_link = "N/A"
    if callsign and callsign != 'Unknown':
        # FlightRadar24 direct flight URL format
        fr24_url = f"https://www.flightradar24.com/{callsign}"
        flightaware_url = f"https://flightaware.com/live/flight/{callsign}"
        track_link = f"[FR24]({fr24_url})|[FA]({flightaware_url})"
    
    # Single line format: 🎯 RCH817 (Military) - 17K ft, 318kts - [Track](link) - 5min ago
    alert_text = f"🎯 **{callsign}** ({matched_term}) - {alt_text}, {speed_text} - {track_link} - <t:{int(datetime.now().timestamp())}:R>"
    
    # Suppress embeds to prevent link previews
    await channel.send(alert_text, suppress_embeds=True)

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
    
    # Help command - show all available commands
    if msg.content == "!":
        help_text = """🤖 **Skycards Bot Commands**

**🔍 Mission Search:**
• `!find speed >400 ABE` - Find flights >400kts near ABE
• `!find altitude >35000 PHL` - Find high-altitude flights
• `!find manufacturer boeing JFK` - Find Boeing aircraft
• `!find route transpacific LAX` - Find transpacific routes

**✈️ Rare Aircraft Hunting:**
• `!add chinook` - Add search term (with AI suggestions)
• `!list` - Show current search terms
• `!stats` - Show hunting statistics
• `!hunt` - Force search for rare aircraft now
• `!alerts` - Show alert acknowledgment status

**🏢 Airport Management:**
• `!airports list` - Show your monitored airports
• `!airports add PHL` - Add airport to your list (max 3)
• `!airports remove LAX` - Remove airport from list
• `!airports clear` - Clear all your airports

**🤖 Airport Assistant:**
• `!airports_llm find dubai airport` - Ask AI about airports
• `!airports_llm best cargo hub europe` - Natural language queries

**⚙️ System:**
• `!` - Show this help menu
• React with ✅ to acknowledge aircraft alerts

**💡 Tips:**
• Aircraft alerts auto-remind after 30 minutes if not acknowledged
• Max 3 airports per user, 5-minute monitoring intervals
• Active hours: 6am-midnight, quiet: midnight-6am"""

        await msg.reply(help_text)
        return
    
    # Mission search command
    if msg.content.startswith("!find "):
        print("Mission search command received...")
        query_text = msg.content[6:].strip()  # Remove "!find "
        
        if not query_text:
            await msg.reply("❌ **Mission Search Usage:**\n" +
                          "• `!find speed >400 ABE` - Find flights >400kts near ABE\n" +
                          "• `!find altitude >35000 PHL` - Find high-altitude flights\n" +
                          "• `!find manufacturer boeing JFK` - Find Boeing aircraft\n" +
                          "• `!find route transpacific LAX` - Find transpacific routes")
            return
        
        try:
            # Parse the mission search command
            criteria, airport_code = parse_mission_command(query_text)
            if not criteria or not airport_code:
                await msg.reply("❌ Invalid format. Use: `!find [criteria] [airport]`\nExample: `!find speed >400 ABE`")
                return
            
            await msg.reply(f"🔍 **Searching for {query_text}...**")
            
            # Execute the search
            results = await MISSION_FINDER.find_flights_by_criteria(airport_code, criteria)
            
            if not results:
                await msg.reply(f"❌ No flights found matching: **{query_text}**")
                return
            
            # Format results
            result_text = f"✅ **Found {len(results)} flights matching:** {query_text}\n\n"
            for i, flight in enumerate(results[:5], 1):  # Limit to 5 results
                callsign = flight.get('callsign', 'Unknown')
                altitude = flight.get('altitude_ft', 0)
                speed = flight.get('velocity_kts', 0)
                distance = flight.get('distance_km', 0)
                
                alt_text = f"{altitude//1000}K ft" if altitude > 0 else "??"
                speed_text = f"{speed}kts" if speed > 0 else "??"
                dist_text = f"{distance:.0f}km" if distance > 0 else "??"
                
                result_text += f"**{i}.** {callsign} | {alt_text} | {speed_text} | {dist_text} away\n"
            
            if len(results) > 5:
                result_text += f"\n*...and {len(results)-5} more flights*"
            
            await msg.reply(result_text, suppress_embeds=True)
            
        except Exception as e:
            print(f"Mission search error: {e}")
            await msg.reply(f"❌ Error searching: {str(e)}")
            
    # Simple text commands for testing
    elif msg.content.startswith("!add "):
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
    
    elif msg.content == "!alerts":
        print("Showing alert status...")
        status = ALERT_TRACKER.get_alert_status()
        await msg.reply(f"🔔 **Alert Status**\n" + 
                       f"• Total alerts: {status['total']}\n" +
                       f"• Acknowledged: {status['acknowledged']}\n" +
                       f"• Reminded: {status['reminded']}\n" +
                       f"• Pending: {status['pending']}")
        
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
            
    elif msg.content.startswith("!find "):
        print("Mission search command received...")
        try:
            criteria_type, criteria, airport_code = parse_mission_command(msg.content)
            
            if not criteria or not airport_code:
                await msg.reply("❌ **Invalid search format!**\n" +
                              "Examples:\n" +
                              "• `!find speed >400 ABE` - Flights over 400kts near ABE\n" +
                              "• `!find altitude >35000 PHL` - Flights above 35K ft near PHL\n" +
                              "• `!find transpacific JFK` - Transpacific flights near JFK\n" +
                              "• `!find manufacturer bombardier LAX` - Bombardier aircraft near LAX")
                return
                
            # Check if airport is valid
            if not MISSION_FINDER.get_airport_coordinates(airport_code):
                await msg.reply(f"❌ Airport **{airport_code}** not found in database.")
                return
                
            await msg.reply(f"🔍 **Searching for {criteria_type} flights near {airport_code}...**")
            
            # Perform the search
            flights = await MISSION_FINDER.find_flights_by_criteria(airport_code, criteria)
            
            if flights:
                # Format results
                result_lines = [f"🎯 **Found {len(flights)} flights matching criteria near {airport_code}:**"]
                
                for flight in flights:
                    callsign = flight['callsign']
                    distance = flight['distance_from_target']
                    
                    # Include relevant stats based on search type
                    stats = []
                    if 'min_speed' in criteria or 'max_speed' in criteria:
                        stats.append(f"{flight['velocity_kts']}kts")
                    if 'min_altitude' in criteria or 'max_altitude' in criteria:
                        stats.append(f"{flight['altitude_ft']//1000}K ft")
                    if 'route_type' in criteria:
                        stats.append(f"{flight['origin_country']}")
                        
                    stats_text = ", ".join(stats) if stats else ""
                    fr24_url = f"https://www.flightradar24.com/{callsign}"
                    
                    result_lines.append(f"• **{callsign}** - {stats_text} - {distance}km away - [Track]({fr24_url})")
                
                # Send results (suppress embeds to avoid previews)
                result_text = "\n".join(result_lines)
                await msg.reply(result_text, suppress_embeds=True)
                
            else:
                await msg.reply(f"❌ No flights found matching **{criteria_type}** criteria near **{airport_code}**.")
                
        except Exception as e:
            print(f"Mission search error: {e}")
            await msg.reply(f"❌ Error during mission search: {str(e)}")
            
    elif msg.content.startswith("!airports "):
        print("Airport management command received...")
        parts = msg.content.split()
        
        if len(parts) < 2:
            await msg.reply("❌ **Airport Commands:**\n" +
                          "• `!airports list` - Show your airports\n" +
                          "• `!airports add PHL` - Add airport to your list\n" +
                          "• `!airports remove UKT` - Remove airport from your list\n" +
                          "• `!airports clear` - Remove all your airports")
            return
            
        command = parts[1].lower()
        
        # Determine username from channel
        username = AIRPORT_MANAGER.get_user_from_channel(msg.channel.id)
        if not username:
            await msg.reply("❌ This command only works in user airport channels.")
            return
        
        try:
            if command == "list":
                airports = AIRPORT_MANAGER.get_user_airports(username)
                if airports:
                    airports_text = ", ".join(airports)
                    await msg.reply(f"🛫 **{username.title()}'s airports:** {airports_text}")
                else:
                    await msg.reply(f"📭 **{username.title()}** has no airports configured.\nUse `!airports add PHL` to add some!")
                    
            elif command == "add":
                if len(parts) < 3:
                    await msg.reply("❌ Usage: `!airports add PHL`")
                    return
                    
                airport_code = parts[2].upper()
                success, message = AIRPORT_MANAGER.add_airport(username, airport_code)
                await msg.reply(message)
                
            elif command == "remove":
                if len(parts) < 3:
                    await msg.reply("❌ Usage: `!airports remove PHL`")
                    return
                    
                airport_code = parts[2].upper()
                success, message = AIRPORT_MANAGER.remove_airport(username, airport_code)
                await msg.reply(message)
                
            elif command == "clear":
                success, message = AIRPORT_MANAGER.clear_airports(username)
                await msg.reply(message)
                
            else:
                await msg.reply("❌ Unknown command. Use: list, add, remove, or clear")
                
        except Exception as e:
            print(f"Airport management error: {e}")
            await msg.reply(f"❌ Error: {str(e)}")
            
    elif msg.content.startswith("!airports_llm "):
        print("Airport LLM command received...")
        query = msg.content[14:].strip()  # Remove "!airports_llm "
        
        if not query:
            await msg.reply("❌ **Airport LLM Assistant**\n" +
                          "Ask me about airports in natural language!\n\n" +
                          "**Examples:**\n" +
                          "• `!airports_llm find dubai airport with highest traffic`\n" +
                          "• `!airports_llm best european airport for boeing 777s`\n" +
                          "• `!airports_llm airport near london with international flights`\n" +
                          "• `!airports_llm what's the code for paris airport`")
            return
        
        try:
            await msg.reply("🤖 **Asking DeepSeek about airports...**")
            
            # Query the LLM
            response = await AIRPORT_LLM.ask_deepseek(query)
            
            # Format the response nicely
            llm_response = f"🤖 **DeepSeek Airport Assistant:**\n\n{response}\n\n" + \
                          "💡 *Use `!airports add CODE` to add any of these airports to your list!*"
            
            await msg.reply(llm_response, suppress_embeds=True)
            
        except Exception as e:
            print(f"Airport LLM error: {e}")
            await msg.reply(f"❌ Error querying airport assistant: {str(e)}")

@bot.event
async def on_reaction_add(reaction, user):
    """Handle alert acknowledgment reactions"""
    if user.bot:
        return
    
    # Check if this is an acknowledgment reaction (✅) on an alert message
    if str(reaction.emoji) == "✅":
        try:
            # Try to find this alert in our tracker by looking at message embeds
            message = reaction.message
            if message.embeds:
                embed = message.embeds[0]
                
                # Look for alert ID in footer or check if it's a reminder
                footer_text = embed.footer.text if embed.footer else ""
                if "Alert ID:" in footer_text:
                    # Extract alert ID from footer
                    alert_id_part = footer_text.split("Alert ID:")[-1].strip()
                    
                    # Find matching alert (search by partial ID)
                    for full_alert_id in ALERT_TRACKER.pending_alerts.keys():
                        if full_alert_id.startswith(alert_id_part):
                            ALERT_TRACKER.acknowledge_alert(full_alert_id)
                            print(f"Alert {full_alert_id[:8]} acknowledged by {user.name}")
                            break
        except Exception as e:
            print(f"Error handling reaction acknowledgment: {e}")

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
        if not multi_user_airports_watch.is_running():
            multi_user_airports_watch.start()
            print("Multi-user airport monitoring started")
    except Exception as e:
        print(f"❌ Failed to start airport monitoring: {e}")
        
    try:
        if not rare_hunt.is_running():
            rare_hunt.start()
            print("✅ Rare aircraft hunting started")
    except Exception as e:
        print(f"❌ Failed to start rare hunting: {e}")
        
    try:
        if not alert_reminder_loop.is_running():
            alert_reminder_loop.start()
            print("✅ Alert reminder system started")
    except Exception as e:
        print(f"❌ Failed to start alert reminders: {e}")

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
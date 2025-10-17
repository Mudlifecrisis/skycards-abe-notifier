#!/usr/bin/env python3
"""
SLASH COMMAND VERSION - Modern Discord bot with /commands
Clean, exact type matching, no OAuth complexity
"""

import os
import json
import discord
from discord import app_commands
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timezone
from rare_hunter import RareAircraftHunter
from user_airports import UserAirportManager

load_dotenv()

# Config
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("DEV_GUILD_ID", "0"))  # Set for dev server for instant updates
RARE_CH_ID = int(os.getenv("RARE_CH_ID", "0"))

# Alias system for human-readable terms → type codes
ALIASES = {
    "globemaster": {"C17"},
    "chinook": {"H47"},
    "f16": {"F16"},
    "viper": {"F16"}, 
    "fighting falcon": {"F16"},
    "stratolifter": {"C135"},
    "ab-180": {"AB18"},
    "aero boero": {"AB18"},
    "evektor cobra": {"VUT1"},
    "cobra": {"VUT1"},
    "kfir": {"KFIR"},
    "warthog": {"A10"},
    "thunderbolt": {"A10"},
    "a-10": {"A10"},
    "f-16": {"F16"},
    "c-17": {"C17"},
    "ch-47": {"H47"},
    "kc-135": {"C135"}
}

def translate_alias(query: str) -> set[str]:
    """Convert human terms to aircraft type codes"""
    qn = query.strip().lower()
    return ALIASES.get(qn, {query.strip().upper()})

def load_watchlist() -> dict:
    """Load user watchlist from JSON"""
    if os.path.exists("watchlist.json"):
        with open("watchlist.json", 'r') as f:
            return json.load(f)
    return {"aircraft": [], "registrations": [], "airports": []}

def save_watchlist(data: dict):
    """Save watchlist to JSON"""
    with open("watchlist.json", 'w') as f:
        json.dump(data, f, indent=2)

class SkycardsBotSlash(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        
        self.tree = app_commands.CommandTree(self)
        self.hunter = RareAircraftHunter()
        self.airport_manager = UserAirportManager()
        
        # Stats tracking
        self.last_stats = {
            'states_pulled': 0,
            'resolved': 0, 
            'matched': 0,
            'alerts_sent': 0,
            'last_run': None
        }

    async def setup_hook(self):
        """Register slash commands"""
        print("[SETUP] Registering slash commands...")
        
        if GUILD_ID:
            # Dev mode - register to guild for instant updates
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"[SETUP] Synced commands to guild {GUILD_ID}")
        else:
            # Production mode - register globally (takes ~1 hour)
            await self.tree.sync()
            print("[SETUP] Synced commands globally")

    async def on_ready(self):
        print(f"[BOT] {self.user} is ready with slash commands!")
        print(f"[BOT] Servers: {len(self.guilds)}")
        
        # Start background hunting task
        if not hasattr(self, '_hunting_started'):
            self._hunting_started = True
            self.loop.create_task(self.background_hunting())

    async def background_hunting(self):
        """Background task to hunt for rare aircraft"""
        await self.wait_until_ready()
        
        while not self.is_closed():
            try:
                print("[HUNT] Background hunting cycle starting...")
                rare_aircraft = await self.hunter.find_rare_aircraft()
                
                # Update stats
                stats = self.hunter.get_statistics()
                self.last_stats.update({
                    'states_pulled': getattr(self.hunter, '_last_states_pulled', 0),
                    'resolved': getattr(self.hunter, '_last_resolved', 0),
                    'matched': len(rare_aircraft),
                    'alerts_sent': len(rare_aircraft),
                    'last_run': datetime.now(timezone.utc).isoformat()
                })
                
                # Send alerts if any found
                if rare_aircraft and RARE_CH_ID:
                    channel = self.get_channel(RARE_CH_ID)
                    if channel:
                        await self.send_rare_alerts(channel, rare_aircraft)
                
                print(f"[HUNT] Cycle complete: {len(rare_aircraft)} alerts sent")
                
            except Exception as e:
                print(f"[ERROR] Background hunting failed: {e}")
            
            # Wait 3 minutes between cycles
            await asyncio.sleep(180)

    async def send_rare_alerts(self, channel, rare_aircraft):
        """Send rare aircraft alerts to Discord channel"""
        for aircraft in rare_aircraft:
            embed = discord.Embed(
                title=f"🚨 {aircraft['matched_term']} Detected",
                color=discord.Color.red() if aircraft.get('is_user_target') else discord.Color.orange()
            )
            
            embed.add_field(name="Callsign", value=aircraft.get('callsign', 'Unknown'), inline=True)
            embed.add_field(name="Registration", value=aircraft.get('registration', 'Unknown'), inline=True)
            embed.add_field(name="Type", value=aircraft['matched_term'], inline=True)
            
            if aircraft.get('altitude_ft'):
                embed.add_field(name="Altitude", value=f"{aircraft['altitude_ft']:,} ft", inline=True)
            if aircraft.get('velocity_kts'):
                embed.add_field(name="Speed", value=f"{aircraft['velocity_kts']} kts", inline=True)
            
            embed.add_field(
                name="Location", 
                value=f"{aircraft.get('latitude', 0):.3f}, {aircraft.get('longitude', 0):.3f}", 
                inline=True
            )
            
            embed.add_field(name="Reason", value=aircraft.get('search_reason', 'Match'), inline=False)
            embed.timestamp = datetime.now(timezone.utc)
            
            try:
                await channel.send(embed=embed)
            except Exception as e:
                print(f"[ERROR] Failed to send alert: {e}")

# Create bot instance
bot = SkycardsBotSlash()

# SLASH COMMANDS IMPLEMENTATION

@bot.tree.command(name="hunt", description="Find live aircraft by exact type or registration")
@app_commands.describe(
    type="Aircraft type (globemaster, chinook, f16) or exact code (C17, H47)",
    near="Airport code (KABE) or lat,lon (40.7,-75.4) - optional",
    within="Search radius like 120nm or 200km - optional"
)
async def hunt(interaction: discord.Interaction, type: str, near: str = None, within: str = None):
    await interaction.response.defer()
    
    try:
        # Convert aliases to type codes
        type_codes = translate_alias(type)
        print(f"[HUNT] Searching for types: {type_codes}")
        
        # Add to hunter search terms temporarily
        original_terms = self.hunter.search_terms.copy()
        self.hunter.search_terms.update(type_codes)
        
        # Perform hunt
        results = await bot.hunter.find_rare_aircraft()
        
        # Restore original search terms
        bot.hunter.search_terms = original_terms
        
        # Filter results to only requested types
        filtered_results = [r for r in results if r.get('matched_term') in type_codes]
        
        if not filtered_results:
            embed = discord.Embed(
                title="🔍 Hunt Results", 
                description=f"No live matches found for **{', '.join(type_codes)}**",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Search Info",
                value=f"States scanned: {getattr(bot.hunter, '_last_states_pulled', 0)}\nAircraft resolved: {getattr(bot.hunter, '_last_resolved', 0)}",
                inline=False
            )
        else:
            embed = discord.Embed(
                title=f"🎯 Found {len(filtered_results)} Aircraft", 
                color=discord.Color.green()
            )
            
            for aircraft in filtered_results[:5]:  # Limit to 5 results
                location = f"{aircraft.get('latitude', 0):.3f}, {aircraft.get('longitude', 0):.3f}"
                altitude = f"{aircraft['altitude_ft']:,} ft" if aircraft.get('altitude_ft') else "Unknown"
                speed = f"{aircraft['velocity_kts']} kts" if aircraft.get('velocity_kts') else "Unknown"
                
                embed.add_field(
                    name=f"{aircraft['matched_term']} • {aircraft.get('callsign', 'No callsign')}",
                    value=f"**Reg:** {aircraft.get('registration', 'Unknown')}\n**Alt:** {altitude} **Speed:** {speed}\n**Pos:** {location}",
                    inline=False
                )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        print(f"[ERROR] Hunt command failed: {e}")
        await interaction.followup.send("❌ Hunt failed. Check logs for details.")

# WATCHLIST COMMANDS
watchlist_group = app_commands.Group(name="watchlist", description="Manage aircraft watchlists")

@watchlist_group.command(name="list", description="Show your current watchlists")
async def watchlist_list(interaction: discord.Interaction):
    data = load_watchlist()
    
    embed = discord.Embed(title="📋 Your Watchlists", color=discord.Color.blue())
    
    aircraft_list = data.get('aircraft', [])
    reg_list = data.get('registrations', [])
    airport_list = data.get('airports', [])
    
    embed.add_field(
        name="🛩️ Aircraft Types", 
        value=', '.join(aircraft_list) if aircraft_list else 'None',
        inline=False
    )
    embed.add_field(
        name="🏷️ Registrations", 
        value=', '.join(reg_list) if reg_list else 'None', 
        inline=False
    )
    embed.add_field(
        name="✈️ Airports", 
        value=', '.join(airport_list) if airport_list else 'None',
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

@watchlist_group.command(name="add", description="Add aircraft type, registration, or airport to watchlist")
@app_commands.describe(
    kind="What to add to watchlist",
    value="The aircraft type, registration, or airport code"
)
@app_commands.choices(kind=[
    app_commands.Choice(name="Aircraft Type", value="aircraft"),
    app_commands.Choice(name="Registration", value="registrations"),
    app_commands.Choice(name="Airport", value="airports")
])
async def watchlist_add(interaction: discord.Interaction, kind: str, value: str):
    data = load_watchlist()
    
    # Convert aircraft types through alias system
    if kind == "aircraft":
        type_codes = translate_alias(value)
        added = []
        for code in type_codes:
            if code not in data[kind]:
                data[kind].append(code)
                added.append(code)
        
        if added:
            save_watchlist(data)
            # Also add to live hunter
            bot.hunter.search_terms.update(added)
            bot.hunter.save_search_terms()
            await interaction.response.send_message(f"✅ Added **{', '.join(added)}** to aircraft watchlist")
        else:
            await interaction.response.send_message(f"Already watching: **{', '.join(type_codes)}**")
    else:
        val = value.upper()
        if val not in data[kind]:
            data[kind].append(val)
            save_watchlist(data)
            await interaction.response.send_message(f"✅ Added **{val}** to {kind} watchlist")
        else:
            await interaction.response.send_message(f"Already watching: **{val}**")

@watchlist_group.command(name="remove", description="Remove item from watchlist")
@app_commands.describe(
    kind="What to remove from watchlist",
    value="The value to remove"
)
@app_commands.choices(kind=[
    app_commands.Choice(name="Aircraft Type", value="aircraft"),
    app_commands.Choice(name="Registration", value="registrations"), 
    app_commands.Choice(name="Airport", value="airports")
])
async def watchlist_remove(interaction: discord.Interaction, kind: str, value: str):
    data = load_watchlist()
    
    if kind == "aircraft":
        type_codes = translate_alias(value)
        removed = []
        for code in type_codes:
            if code in data[kind]:
                data[kind].remove(code)
                removed.append(code)
        
        if removed:
            save_watchlist(data)
            # Remove from live hunter
            for code in removed:
                bot.hunter.search_terms.discard(code)
            bot.hunter.save_search_terms()
            await interaction.response.send_message(f"❌ Removed **{', '.join(removed)}** from aircraft watchlist")
        else:
            await interaction.response.send_message(f"Not found: **{', '.join(type_codes)}**")
    else:
        val = value.upper()
        if val in data[kind]:
            data[kind].remove(val)
            save_watchlist(data)
            await interaction.response.send_message(f"❌ Removed **{val}** from {kind} watchlist")
        else:
            await interaction.response.send_message(f"Not found: **{val}**")

@watchlist_group.command(name="clear", description="Clear specific watchlist or all")
@app_commands.describe(category="Which watchlist to clear")
@app_commands.choices(category=[
    app_commands.Choice(name="Aircraft Types Only", value="aircraft"),
    app_commands.Choice(name="Registrations Only", value="registrations"),
    app_commands.Choice(name="Airports Only", value="airports"),
    app_commands.Choice(name="Everything", value="all")
])
async def watchlist_clear(interaction: discord.Interaction, category: str):
    data = load_watchlist()
    
    if category == "all":
        save_watchlist({"aircraft": [], "registrations": [], "airports": []})
        # Clear from live hunter too
        bot.hunter.search_terms = {"AB18", "VUT1", "KFIR"}  # Keep core targets
        bot.hunter.save_search_terms()
        await interaction.response.send_message("🧹 **All watchlists cleared**")
    
    elif category == "aircraft":
        data["aircraft"] = []
        save_watchlist(data)
        # Reset hunter to core targets only
        bot.hunter.search_terms = {"AB18", "VUT1", "KFIR"}
        bot.hunter.save_search_terms()
        await interaction.response.send_message("🧹 **Aircraft watchlist cleared** (kept AB18, VUT1, KFIR)")
    
    elif category == "registrations":
        data["registrations"] = []
        save_watchlist(data)
        await interaction.response.send_message("🧹 **Registration watchlist cleared**")
    
    elif category == "airports":
        data["airports"] = []
        save_watchlist(data)
        await interaction.response.send_message("🧹 **Airport watchlist cleared**")

bot.tree.add_command(watchlist_group)

# AIRPORT COMMANDS
airports_group = app_commands.Group(name="airports", description="Manage airport monitoring")

@airports_group.command(name="add", description="Add airport to monitoring list")
@app_commands.describe(code="IATA (JFK) or ICAO (KJFK) airport code")
async def airports_add(interaction: discord.Interaction, code: str):
    code = code.upper()
    try:
        success = bot.airport_manager.add_airport(interaction.user.id, code)
        if success:
            await interaction.response.send_message(f"✅ Added **{code}** to your monitored airports")
        else:
            await interaction.response.send_message(f"Already monitoring: **{code}**")
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to add airport: {e}")

@airports_group.command(name="remove", description="Remove airport from monitoring")
@app_commands.describe(code="Airport code to stop monitoring")
async def airports_remove(interaction: discord.Interaction, code: str):
    code = code.upper()
    try:
        success = bot.airport_manager.remove_airport(interaction.user.id, code)
        if success:
            await interaction.response.send_message(f"❌ Removed **{code}** from monitored airports")
        else:
            await interaction.response.send_message(f"Not found: **{code}**")
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to remove airport: {e}")

@airports_group.command(name="list", description="Show your monitored airports")
async def airports_list(interaction: discord.Interaction):
    try:
        airports = bot.airport_manager.get_user_airports(interaction.user.id)
        if airports:
            embed = discord.Embed(title="✈️ Your Monitored Airports", color=discord.Color.blue())
            embed.description = ', '.join(sorted(airports))
        else:
            embed = discord.Embed(
                title="✈️ No Airports Monitored", 
                description="Use `/airports add <code>` to start monitoring airports",
                color=discord.Color.gray()
            )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to get airports: {e}")

@airports_group.command(name="clear", description="Clear all your monitored airports")
async def airports_clear(interaction: discord.Interaction):
    try:
        # Clear all airports for this user
        airports = bot.airport_manager.get_user_airports(interaction.user.id)
        if airports:
            for airport in list(airports):
                bot.airport_manager.remove_airport(interaction.user.id, airport)
            await interaction.response.send_message(f"🧹 **Cleared {len(airports)} monitored airports**")
        else:
            await interaction.response.send_message("✨ **No airports to clear** - you're not monitoring any airports")
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to clear airports: {e}")

bot.tree.add_command(airports_group)

# STATUS COMMANDS
@bot.tree.command(name="stats", description="Show bot hunting statistics")
async def stats(interaction: discord.Interaction):
    stats = bot.last_stats
    hunter_stats = bot.hunter.get_statistics()
    
    embed = discord.Embed(title="📊 Bot Statistics", color=discord.Color.green())
    
    embed.add_field(
        name="🔍 Last Hunt Cycle",
        value=f"States pulled: **{stats['states_pulled']:,}**\nResolved: **{stats['resolved']:,}**\nMatched: **{stats['matched']}**\nAlerts sent: **{stats['alerts_sent']}**",
        inline=True
    )
    
    embed.add_field(
        name="💾 Database",
        value=f"Aircraft: **{hunter_stats['database_aircraft']:,}**\nSearch terms: **{hunter_stats['search_terms']}**\nSeen cache: **{hunter_stats['seen_aircraft']}**",
        inline=True
    )
    
    if stats['last_run']:
        last_run = datetime.fromisoformat(stats['last_run'].replace('Z', '+00:00'))
        embed.timestamp = last_run
        embed.set_footer(text="Last hunt cycle")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="status", description="Check API connectivity and system status")
async def status(interaction: discord.Interaction):
    embed = discord.Embed(title="🟢 System Status", color=discord.Color.green())
    
    # Test OpenSky connectivity
    try:
        test_aircraft = await bot.hunter.fetch_global_aircraft()
        opensky_status = f"✅ OK ({len(test_aircraft)} aircraft)"
    except Exception as e:
        opensky_status = f"❌ Failed: {str(e)[:50]}"
    
    embed.add_field(name="OpenSky API", value=opensky_status, inline=True)
    embed.add_field(name="ADS-B Exchange", value="⚫ Offline", inline=True)
    embed.add_field(name="Cache Size", value=f"{len(bot.hunter.aircraft_db):,} rows", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="deploy", description="[ADMIN] Show deployment status and trigger updates")
async def deploy_status(interaction: discord.Interaction):
    # Check if user has admin permissions (adjust role/user check as needed)
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ This command requires administrator permissions.", ephemeral=True)
        return
    
    try:
        # Get current deployment info via SSH
        import subprocess
        
        # Get current release timestamp
        result = subprocess.run([
            "ssh", "TheDrizzle@192.168.4.75", 
            "readlink /volume1/docker/skycards/deploy/current | xargs basename"
        ], capture_output=True, text=True, timeout=10)
        
        current_release = result.stdout.strip() if result.returncode == 0 else "Unknown"
        
        # Get container health
        result = subprocess.run([
            "ssh", "TheDrizzle@192.168.4.75",
            "docker inspect --format='{{.State.Health.Status}}' skycards-bot 2>/dev/null || echo 'no_health'"
        ], capture_output=True, text=True, timeout=10)
        
        health_status = result.stdout.strip()
        health_emoji = "✅" if health_status == "healthy" else "⚠️" if health_status == "starting" else "❌"
        
        # Get last few releases
        result = subprocess.run([
            "ssh", "TheDrizzle@192.168.4.75",
            "ls -1t /volume1/docker/skycards/releases | head -5"
        ], capture_output=True, text=True, timeout=10)
        
        recent_releases = result.stdout.strip().split('\n')[:5] if result.returncode == 0 else []
        
        # Build response
        embed = discord.Embed(title="🚀 Deployment Status", color=discord.Color.green())
        
        embed.add_field(
            name="Current Release",
            value=f"`{current_release}`",
            inline=True
        )
        
        embed.add_field(
            name="Container Health", 
            value=f"{health_emoji} {health_status}",
            inline=True
        )
        
        embed.add_field(
            name="Location",
            value=f"`deploy/current -> releases/{current_release}`",
            inline=False
        )
        
        if recent_releases:
            releases_list = '\n'.join([f"{'→ ' if r == current_release else '  '}`{r}`" for r in recent_releases])
            embed.add_field(
                name="Recent Releases",
                value=releases_list,
                inline=False
            )
        
        embed.add_field(
            name="Quick Actions",
            value="• `git push nas main` - Deploy latest code\n• `ROLLBACK.bat <timestamp>` - Rollback to previous version",
            inline=False
        )
        
        embed.timestamp = datetime.now(timezone.utc)
        embed.set_footer(text="Use git push nas main to deploy updates")
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to get deployment status: {str(e)[:100]}", ephemeral=True)

@bot.tree.command(name="help", description="Show available commands and usage examples")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="🆘 Skycards Bot Commands", color=discord.Color.blue())
    
    embed.add_field(
        name="🎯 Hunting",
        value="**/hunt type:** `globemaster` `chinook` `f16`\n**/watchlist add** aircraft `C17`\n**/watchlist list**\n**/watchlist clear** aircraft",
        inline=False
    )
    
    embed.add_field(
        name="✈️ Airports", 
        value="**/airports add** `KABE`\n**/airports list**\n**/airports remove** `JFK`\n**/airports clear**",
        inline=False
    )
    
    embed.add_field(
        name="📊 Status",
        value="**/stats** - Hunt statistics\n**/status** - API connectivity\n**/deploy** - [Admin] Deployment status\n**/help** - This message",
        inline=False
    )
    
    embed.add_field(
        name="💡 Aliases",
        value="**globemaster** → C17\n**chinook** → H47\n**f16/viper** → F16\n**warthog** → A10",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

# AUTOCOMPLETE for aircraft types
@hunt.autocomplete('type')
async def hunt_type_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Provide autocomplete suggestions for aircraft types"""
    current_lower = current.lower()
    
    # Get alias suggestions
    alias_matches = [alias for alias in ALIASES.keys() if current_lower in alias.lower()]
    
    # Get direct type code matches from hunter
    type_matches = [term for term in bot.hunter.get_search_terms() if current_lower in term.lower()]
    
    # Combine and limit to 25 (Discord limit)
    all_matches = alias_matches[:15] + type_matches[:10]
    
    return [app_commands.Choice(name=match.title(), value=match) for match in all_matches[:25]]

if __name__ == "__main__":
    if not TOKEN:
        print("[ERROR] DISCORD_BOT_TOKEN not found in environment")
        exit(1)
        
    print("[START] Starting Skycards Bot with slash commands...")
    bot.run(TOKEN)
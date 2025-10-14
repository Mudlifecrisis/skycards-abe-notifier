# clear_commands.py - Clear all slash commands
import os
import discord
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        # Clear global commands
        tree.clear_commands(guild=None)
        synced = await tree.sync()
        print(f"✅ Cleared all global commands. {len(synced)} commands remaining.")
        await bot.close()
    except Exception as e:
        print(f"❌ Error: {e}")
        await bot.close()

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
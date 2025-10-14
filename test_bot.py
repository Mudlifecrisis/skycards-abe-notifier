# test_bot.py - Minimal bot to test slash commands
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

@tree.command(name="test", description="Simple test command")
async def test_command(interaction: discord.Interaction):
    await interaction.response.send_message("✅ Bot is working!", ephemeral=False)

@tree.command(name="ping", description="Test bot response")
async def ping_command(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!", ephemeral=False)

@bot.event
async def on_ready():
    print(f"Test bot logged in as {bot.user}")
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
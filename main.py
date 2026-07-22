import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Load cogs/extensions
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"✅ Loaded {filename}")

@bot.event
async def on_ready():
    print(f"✨ Bot logged in as {bot.user}")
    print(f"🤖 Bot is ready to serve {len(bot.guilds)} guilds!")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)

# Run the bot
async def main():
    async with bot:
        await load_cogs()
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            raise ValueError("❌ DISCORD_TOKEN not found in .env file!")
        await bot.start(token)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

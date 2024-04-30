import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import logging
import aiosqlite
import asyncio
import aiofiles
import aiohttp
import json

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OLLAMA_URL = os.getenv('OLLAMA_IP')

CONFIG = {
    'default_model': 'dolphin-mistral',
    'max_response_length': 2048
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='/', intents=intents)
bot.available_models = []

async def load_models():
    """
    Fetch the list of available models from the Ollama server.
    If an error occurs, return the default model specified in the CONFIG.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{OLLAMA_URL}/api/tags') as response:
                if response.status == 200:
                    data = await response.json()
                    #print("Response from Ollama server:")
                    #print(data)
                    if 'models' in data:
                        models = [model['name'] for model in data['models']]
                        return models
                    else:
                        logger.error("Unexpected response format from the Ollama server")
                else:
                    logger.error(f"Error fetching models: HTTP {response.status}")
                    logger.error(f"Response from Ollama server: {await response.text()}")
    except aiohttp.ClientError as e:
        logger.exception(f"Error fetching models: {str(e)}")

    return [CONFIG['default_model']]

async def save_models(models):
    """
    Save the list of available models to the 'available_models.txt' file.
    """
    async with aiofiles.open('available_models.txt', 'w') as file:
        await file.write('\n'.join(models))

@bot.event
async def on_ready():
    """
    Event handler for when the bot is ready.
    Loads the available models, syncs the application commands, and creates the database table if it doesn't exist.
    """
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    global AVAILABLE_MODELS
    bot.available_models = await load_models()
    await bot.tree.sync()

    async with aiosqlite.connect('conversation_history.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS history (
                model TEXT,
                user_id INTEGER,
                message TEXT,
                timestamp INTEGER
            )
        ''')
        await db.commit()

async def main():
    await bot.load_extension('cogs.llm-cogs.chat_cog')
    await bot.load_extension('cogs.llm-cogs.history_cog')
    await bot.load_extension('cogs.llm-cogs.utility_cog')
    await bot.load_extension('cogs.llm-cogs.model_cog')
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

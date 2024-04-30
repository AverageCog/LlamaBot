import discord
from discord.ext import commands
from discord import app_commands
import re
import logging
import aiohttp
import aiosqlite
import time
import os
from dotenv import load_dotenv
import aiofiles
from .utils import split_into_chunks

logger = logging.getLogger(__name__)

load_dotenv()
OLLAMA_URL = os.getenv('OLLAMA_IP')

CONFIG = {
    'default_model': 'dolphin-mistral',
    'max_response_length': 2048
}

async def get_last_used_model(user_id):
    async with aiosqlite.connect('conversation_history.db') as db:
        async with db.execute("SELECT DISTINCT model FROM history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                return result[0]
    return CONFIG['default_model']

async def save_models(models):
    """
    Save the list of available models to the 'available_models.txt' file.
    """
    async with aiofiles.open('available_models.txt', 'w') as file:
        await file.write('\n'.join(models))

async def generate_response(model, user_id, message, regenerate=False):
    async with aiosqlite.connect('conversation_history.db') as db:
        if regenerate:
            async with db.execute("SELECT rowid FROM history WHERE model = ? AND user_id = ? ORDER BY timestamp DESC LIMIT 2", (model, user_id)) as cursor:
                rows = await cursor.fetchall()
                if rows:
                    message_ids = [row[0] for row in rows]
                    placeholders = ','.join('?' for _ in message_ids)
                    await db.execute(f"DELETE FROM history WHERE rowid IN ({placeholders})", message_ids)
                    await db.commit()

        async with db.execute("SELECT message FROM history WHERE model = ? AND user_id = ? ORDER BY timestamp", (model, user_id)) as cursor:
            history = [row[0] for row in await cursor.fetchall()]

        messages = [
            *[{"role": "user" if i % 2 == 0 else "assistant", "content": msg} for i, msg in enumerate(history)],
            {"role": "user", "content": message}
        ]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'{OLLAMA_URL}/api/chat', json={
                    'model': model,
                    'messages': messages,
                    'stream': False,
                    'keep_alive': '24h',
                    'options': {
                        'num_ctx': 16384
                    }
                }) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_message = data['message']['content']
                        await db.execute("INSERT INTO history (model, user_id, message, timestamp) VALUES (?, ?, ?, ?)", (model, user_id, message, int(time.time())))
                        await db.execute("INSERT INTO history (model, user_id, message, timestamp) VALUES (?, ?, ?, ?)", (model, user_id, response_message, int(time.time())))
                        await db.commit()
                        return response_message
                    else:
                        logger.error(f"Error generating response: HTTP {response.status}")
                        return "An error occurred while generating the response."
        except aiohttp.ClientError as e:
            logger.exception(f"Error generating response: {str(e)}")
            return "An error occurred while generating the response."

async def model_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """
    Autocomplete function for the 'model' parameter in the '/chat' and '/clear_history' commands.
    Returns a list of available models that match the current input.
    """
    return [
        app_commands.Choice(name=model, value=model)
        for model in interaction.client.available_models if current.lower() in model.lower()
    ]

async def delete_model_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """
    Autocomplete function for the 'name' parameter in the '/delete_model' command.
    Returns a list of available models that match the current input.
    """
    return [
        app_commands.Choice(name=model, value=model)
        for model in interaction.client.available_models if current.lower() in model.lower()
    ]

def format_response(response):
    formatted_response = response.replace('**', '*').replace('__', '_')
    formatted_response = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'[\1](\2)', formatted_response)
    formatted_response = formatted_response.replace('<br>', '\n')
    return formatted_response

class Paginator:
    def __init__(self, interaction: discord.Interaction, embeds: list[discord.Embed], model: str, user_id: int, message: str):
        self.interaction = interaction
        self.embeds = embeds
        self.current_page = 0
        self.model = model
        self.user_id = user_id
        self.message_content = message.content if isinstance(message, discord.Message) else message

    async def start(self):
        self.message = await self.interaction.followup.send(embed=self.embeds[0], view=PaginatorView(self))

    async def update(self):
        await self.message.edit(embed=self.embeds[self.current_page], view=PaginatorView(self))

    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.delete_original_response()
        confirmation_embed = discord.Embed(
            title="Regenerating Response",
            description="Please wait while the response is being regenerated...",
            color=discord.Color.blue()
        )
        confirmation_message = await interaction.followup.send(embed=confirmation_embed)
        response = await generate_response(self.model, self.user_id, self.message_content, regenerate=True)
        response = format_response(response)

        max_length = CONFIG['max_response_length']
        if len(response) > max_length:
            chunks = split_into_chunks(response, max_length)
            self.embeds = [discord.Embed(title=f"AI Response (Part {i+1})", description=chunk, color=discord.Color.green()) for i, chunk in enumerate(chunks)]
        else:
            self.embeds = [discord.Embed(title="AI Response", description=response, color=discord.Color.green())]

        self.current_page = 0
        await confirmation_message.delete()
        await self.start()

class PaginatorView(discord.ui.View):
    def __init__(self, paginator: Paginator):
        super().__init__(timeout=None)
        self.paginator = paginator

        self.update_button_states()

    def update_button_states(self):
        if len(self.paginator.embeds) == 1:
            self.previous_page.disabled = True
            self.next_page.disabled = True
        else:
            if self.paginator.current_page == 0:
                self.previous_page.disabled = True
            else:
                self.previous_page.disabled = False

            if self.paginator.current_page == len(self.paginator.embeds) - 1:
                self.next_page.disabled = True
            else:
                self.next_page.disabled = False

    @discord.ui.button(label='⬅️ ', style=discord.ButtonStyle.blurple)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.paginator.current_page > 0:
            self.paginator.current_page -= 1
            self.update_button_states()
            await self.paginator.update()
        await interaction.response.defer()

    @discord.ui.button(label='➡️', style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.paginator.current_page < len(self.paginator.embeds) - 1:
            self.paginator.current_page += 1
            self.update_button_states()
            await self.paginator.update()
        await interaction.response.defer()

    @discord.ui.button(label='♻️', style=discord.ButtonStyle.green)
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.paginator.regenerate(interaction, button)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.paginator.message.edit(view=self)

class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(UtilityCog(bot))

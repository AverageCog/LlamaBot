import discord
from discord.ext import commands
from discord import app_commands

import aiosqlite
import logging

from .utility_cog import model_autocomplete

logger = logging.getLogger(__name__)

class HistoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='clear_history')
    @app_commands.describe(model="The model to clear history for (optional)")
    @app_commands.autocomplete(model=model_autocomplete)
    async def clear_history(self, interaction: discord.Interaction, model: str = None):
        await interaction.response.defer()

        try:
            user_id = interaction.user.id

            async with aiosqlite.connect('conversation_history.db', isolation_level=None) as db:
                if model:
                    await db.execute("DELETE FROM history WHERE user_id = ? AND model = ?", (user_id, model))
                    embed = discord.Embed(title="History Cleared", description=f"Your conversation history with the model '{model}' has been cleared.", color=discord.Color.green())
                else:
                    await db.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
                    embed = discord.Embed(title="History Cleared", description="Your entire conversation history has been cleared.", color=discord.Color.green())

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.exception(f"Error in '/clear_history' command: {str(e)}")
            embed = discord.Embed(title="Error", description="An error occurred while clearing your history.", color=discord.Color.red())
            embed.add_field(name="Details", value=str(e), inline=False)
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HistoryCog(bot))

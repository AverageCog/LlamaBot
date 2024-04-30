import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import logging
from .utility_cog import model_autocomplete, delete_model_autocomplete, CONFIG, save_models
import os

logger = logging.getLogger(__name__)
OLLAMA_URL = os.getenv('OLLAMA_IP')

class ModelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='create_model')
    @app_commands.describe(name="Name of the model to create")
    @app_commands.describe(system_prompt="System prompt for the model")
    @app_commands.describe(base_model="Base model to use")
    @app_commands.describe(modelfile="Optional detailed modelfile content")
    @app_commands.describe(temperature="Temperature setting for the model creation")
    @app_commands.autocomplete(base_model=model_autocomplete)
    async def create_model(self, interaction: discord.Interaction, name: str, system_prompt: str, base_model: str, modelfile: str = "", temperature: float = 0.5):
        await interaction.response.defer()

        try:
            if not name:
                raise ValueError("Model name cannot be empty.")

            # Replace spaces with underscores in the model name
            name = name.replace(" ", "_")

            if name in interaction.client.available_models:
                raise ValueError(f"A model with the name '{name}' already exists.")

            if not modelfile and base_model:
                modelfile = f"FROM {base_model}\nSYSTEM {system_prompt}\nTEMPERATURE {temperature}"
            elif not modelfile:
                modelfile = f"SYSTEM {system_prompt}\nTEMPERATURE {temperature}"

            api_url = f'{OLLAMA_URL}/api/create'
            data = {
                "name": name,
                "modelfile": modelfile,
                "stream": False
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=data) as response:
                    creation_response = await response.json()
                    if response.status == 200:
                        if 'status' in creation_response and creation_response['status'] == 'success':
                            interaction.client.available_models.append(name)
                            await save_models(interaction.client.available_models)
                            embed = discord.Embed(title="Model Created", description=f"Model '{name}' created successfully and added to available models!", color=discord.Color.green())
                            await interaction.followup.send(embed=embed)
                        else:
                            raise ValueError("Model created, but the response format was not as expected.")
                    else:
                        error_message = f"Failed to create the model due to HTTP {response.status}."
                        error_details = await response.text()
                        raise ValueError(f"{error_message} Details: {error_details}")
        except Exception as e:
            logger.exception(f"Error in '/create_model' command: {str(e)}")
            embed = discord.Embed(title="Error", description="An error occurred while creating the model.", color=discord.Color.red())
            embed.add_field(name="Details", value=str(e), inline=False)
            await interaction.followup.send(embed=embed)

    @app_commands.command(name='list_models')
    async def list_models(self, interaction: discord.Interaction):
        """
        Command handler for the '/list_models' command.
        Lists all available models.
        """
        models = '\n'.join(interaction.client.available_models)
        embed = discord.Embed(title="Available Models", description=models, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='delete_model')
    @app_commands.describe(name="Name of the model to delete")
    @app_commands.autocomplete(name=delete_model_autocomplete)
    async def delete_model(self, interaction: discord.Interaction, name: str):
        """
        Command handler for the '/delete_model' command.
        Deletes the specified model.
        """
        await interaction.response.defer()

        try:
            # Replace spaces with underscores in the model name
            name = name.replace(" ", "_")

            if name not in interaction.client.available_models:
                raise ValueError(f"Model '{name}' not found.")
            else:
                api_url = f'{OLLAMA_URL}/api/delete'
                data = {"name": name}

                async with aiohttp.ClientSession() as session:
                    async with session.delete(api_url, json=data) as response:
                        if response.status == 200:
                            interaction.client.available_models.remove(name)
                            await save_models(interaction.client.available_models)
                            embed = discord.Embed(title="Model Deleted", description=f"Model '{name}' deleted successfully.", color=discord.Color.green())
                            await interaction.followup.send(embed=embed)
                        elif response.status == 404:
                            raise ValueError(f"Model '{name}' not found on the Ollama server.")
                        else:
                            error_message = f"Failed to delete the model due to HTTP {response.status}."
                            error_details = await response.text()
                            raise ValueError(f"{error_message} Details: {error_details}")
        except Exception as e:
            logger.exception(f"Error in '/delete_model' command: {str(e)}")
            embed = discord.Embed(title="Error", description="An error occurred while deleting the model.", color=discord.Color.red())
            embed.add_field(name="Details", value=str(e), inline=False)
            await interaction.followup.send(embed=embed)

    @app_commands.command(name='refresh_models')
    async def refresh_models(self, interaction: discord.Interaction):
        """
        Command handler for the '/refresh_models' command.
        Refreshes the list of available models from the Ollama server.
        """
        await interaction.response.defer()

        try:
            api_url = f'{OLLAMA_URL}/api/tags'

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'models' in data:
                            models = [model['name'] for model in data['models']]
                            interaction.client.available_models = models
                            await save_models(interaction.client.available_models)
                            embed = discord.Embed(title="Models Refreshed", description="Available models have been refreshed from the Ollama server.", color=discord.Color.green())
                            await interaction.followup.send(embed=embed)
                        else:
                            raise ValueError("Unexpected response format from the Ollama server.")
                    else:
                        error_message = f"Failed to refresh models due to HTTP {response.status}."
                        error_details = await response.text()
                        raise ValueError(f"{error_message} Details: {error_details}")
        except Exception as e:
            logger.exception(f"Error in '/refresh_models' command: {str(e)}")
            embed = discord.Embed(title="Error", description="An error occurred while refreshing the list of available models.", color=discord.Color.red())
            embed.add_field(name="Details", value=str(e), inline=False)
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModelCog(bot))

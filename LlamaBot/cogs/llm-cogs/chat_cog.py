import discord
from discord import app_commands
from discord.ext import commands
import logging
from .utility_cog import format_response, model_autocomplete, Paginator, CONFIG, generate_response, get_last_used_model
from .utils import split_into_chunks
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import re

logger = logging.getLogger(__name__)

def format_code(code, language):
    try:
        lexer = get_lexer_by_name(language, stripall=True)
        formatter = HtmlFormatter(style='colorful')
        formatted_code = highlight(code, lexer, formatter)
        return formatted_code
    except ValueError:
        return code

def split_into_chunks(text, max_length):
    chunks = []
    current_chunk = ""

    sentences = re.findall(r'(?s)(.*?(?<=[.!?])\s+)', text)

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def truncate_field(value, max_length=1024):
    if len(value) > max_length:
        return value[:max_length - 3] + "..."
    return value

def get_user_input_embed(message):
    embed = discord.Embed(color=discord.Color.blurple())
    embed.add_field(name="", value=message, inline=False)
    return embed

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='chat', description='Generate a response based on the input message using AI')
    @app_commands.describe(message="The message to process with the AI model")
    @app_commands.describe(model="The AI model to use for generating the response")
    @app_commands.describe(system_prompt="Custom system prompt for the model (optional)")
    @app_commands.describe(temperature="Temperature setting for the model (optional)")
    @app_commands.autocomplete(model=model_autocomplete)
    async def chat(self, interaction: discord.Interaction, message: str, model: str = None, system_prompt: str = None, temperature: float = 0.5):
        await interaction.response.defer()

        if model is None:
            model = await get_last_used_model(interaction.user.id)

        try:
            user_id = interaction.user.id

            user_input_embed = get_user_input_embed(message)
            await interaction.followup.send(embed=user_input_embed)

            loading_embed = discord.Embed(title="Processing...", description="Your request is being processed. Please wait.", color=discord.Color.blurple())
            loading_message = await interaction.followup.send(embed=loading_embed)

            response = await generate_response(model, user_id, message)
            response = format_response(response)

            code_blocks = re.findall(r'```(\w+)?\n([\s\S]*?)\n```', response)
            code_embeds = []

            for language, code in code_blocks:
                formatted_code = format_code(code, language)
                code_embed = discord.Embed(title=f"Code Block ({language})", color=discord.Color.blue())
                code_embed.description = formatted_code
                code_embeds.append(code_embed)

            response = re.sub(r'```(\w+)?\n([\s\S]*?)\n```', '', response)

            await loading_message.delete()  # Delete the loading message

            max_length = CONFIG['max_response_length']
            if len(response) > max_length:
                chunks = split_into_chunks(response, max_length)
                embeds = [discord.Embed(title=f"AI Response (Part {i+1})", description=chunk, color=discord.Color.green()) for i, chunk in enumerate(chunks)]
            else:
                embeds = [discord.Embed(title="AI Response", description=response, color=discord.Color.green())]

            embeds.extend(code_embeds)

            paginator = Paginator(interaction, embeds, model, user_id, message)
            await paginator.start()

        except Exception as e:
            logger.exception(f"Error in '/chat' command: {str(e)}")
            embed = discord.Embed(title="Error", description="An error occurred while processing the request.", color=discord.Color.red())
            embed.add_field(name="Details", value=str(e), inline=False)
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ChatCog(bot))

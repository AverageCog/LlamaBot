# A Discord Bot for AI-Driven Conversations

This Discord bot leverages the Ollama AI platform to deliver a powerful conversational AI experience directly in Discord. It includes various cogs to manage interactions, such as generating responses, maintaining conversation history, and managing AI models.


## Features

### AI Conversations
- **Dynamic Interaction**: The bot uses the Ollama AI platform to generate context-aware responses based on user input, enabling natural and engaging conversations directly within Discord.
- **Contextual Awareness**: By maintaining a conversation history in a local database, the bot can provide more relevant and coherent responses, simulating a more human-like interaction.

### Model Management
- **Create Models**: Users can create custom AI models by specifying parameters such as the base model, system prompts, and other settings directly through Discord commands.
- **List and Delete Models**: Easily manage AI models with commands to list all currently available models and delete any as needed, facilitating flexible model management.
- **Autocompletion**: When using model-related commands, the bot provides autocompletion suggestions based on the existing models, improving user experience and accuracy in model selection.

### Persistent History
- **Database Integration**: Utilizes `aiosqlite` for asynchronous database interactions to store conversation logs, ensuring that each user's interaction history is preserved for future context.
- **History Management**: Users can access and manage their conversation history through specific commands, allowing for transparency and control over their data.

### Utility Commands
- **Rich Interaction**: Besides AI conversation capabilities, the bot includes utility commands for additional functionalities such as clearing histories, refreshing model lists, and more.
- **Accessibility Features**: Commands are designed to be accessible and easy to use, with detailed descriptions and structured command options available through Discord's slash command interface.

### Code Formatting
- **Embedded Code Responses**: For AI-generated responses that include code, the bot formats these using Pygments for syntax highlighting, displaying them in Discord embeds for enhanced readability.
- **Support for Multiple Languages**: The bot can recognize and appropriately format code snippets in multiple programming languages, making it useful for coding-related discussions.

### Advanced Features
- **Model Autocompletion**: Enhances user experience by providing autocomplete suggestions when interacting with model-related commands, reducing errors and streamlining workflow.
- **Paginator**: Implement a custom paginator for messages that exceed Discord's embed limit, allowing users to navigate through lengthy AI responses conveniently.

## Installation

### Prerequisites

- Python 3.8 or newer
- Discord bot token (obtain it from the [Discord Developer Portal](https://discord.com/developers/applications))
- Access to an Ollama AI server

### Dependencies

Install the required Python libraries with pip:

```bash
pip install discord.py aiohttp aiosqlite python-dotenv pygments
```

### Environment Setup

Create a `.env` file in the project root and add the following environment variables:

```plaintext
DISCORD_TOKEN=your_discord_token_here
OLLAMA_IP=your_ollama_server_ip_here
```

### Running the Bot

Navigate to the bot directory and run:

```bash
python bot.py
```

## Usage

Once the bot is running and connected to your Discord server, you can use the following slash commands:

### General Commands

- `/chat`: Generate a response from the AI based on the provided message.
- `/list_models`: List all available AI models.
- `/create_model`: Create a new AI model.
- `/delete_model`: Delete an existing AI model.
- `/refresh_models`: Refresh the list of available models from the Ollama server.

### Advanced Features

- Persistent conversation history for context-aware AI responses.
- Model management through Discord commands.

## Contributing

Contributions to this project are welcome! Please fork the repository and submit a pull request with your changes. For major changes, please open an issue first to discuss what you would like to change.

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Acknowledgments

- [Discord.py](https://github.com/Rapptz/discord.py) for the API wrapper that facilitates bot interactions.
- [Ollama AI](https://ollama.ai) for the conversational AI platform.
- [Pygments](http://pygments.org/) for code syntax highlighting.


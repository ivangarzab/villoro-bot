"""
Core VilloroBot class
"""
import os
import random
import logging
import discord
from datetime import datetime
from discord.ext import commands

from config import BotConfig
from services.brains_service import BrainsService
from utils.constants import GENERIC_ERRORS
from utils.interaction_logger import InteractionLogger
from events.message_handler import setup_message_handlers


class VilloroBot(commands.Bot):
    """Main bot class"""

    def __init__(self):
        print("[DEBUG] ~~~~~~~~~~~~ Initializing VilloroBot... ~~~~~~~~~~~~")
        intents = discord.Intents.default()
        intents.message_content = True  # Privileged — enable in Discord Developer Portal
        super().__init__(command_prefix='!', intents=intents)

        self.setup_logging()
        self.logger.info("VilloroBot initialization started")

        self.config = BotConfig()

        self.brains_service = BrainsService(
            self.config.BRAINS_SUPABASE_URL,
            self.config.BRAINS_SUPABASE_KEY,
            self.config.KEY_OPENAI
        )

        self.interaction_logger = InteractionLogger()

        self.load_cogs()
        setup_message_handlers(self)

    async def setup_hook(self):
        """Called when the bot is preparing to connect"""
        await self.tree.sync()
        self.tree.on_error = self.on_command_error
        self.logger.info("Slash commands synced")

    async def print_nickname(self):
        """Print nickname once bot is ready"""
        await self.wait_until_ready()
        for guild in self.guilds:
            nickname = guild.me.nick or guild.me.name
            print(f"[DEBUG] ~~~~~~~~~~~~ Instance initialized as '{nickname}' ~~~~~~~~~~~~")

    def load_cogs(self):
        """Load all command cogs"""
        from cogs.general_commands import setup_general_commands
        from cogs.brains_commands import setup_brains_commands

        setup_general_commands(self)
        setup_brains_commands(self)

        print("All commands loaded")

    def setup_logging(self):
        """Set up logging with daily log files"""
        os.makedirs('logs', exist_ok=True)

        logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        current_date = datetime.now().strftime('%Y-%m-%d')
        log_filename = f"logs/bot_{current_date}.log"

        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(logging.Formatter(logging_format))

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(logging_format))

        logger = logging.getLogger('villoro_bot')
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Route kluvs_brain logs (engine iterations, relevance scores, etc.) to same handlers
        kluvs_brain_logger = logging.getLogger('kluvs_brain')
        kluvs_brain_logger.setLevel(logging.INFO)
        kluvs_brain_logger.addHandler(file_handler)
        kluvs_brain_logger.addHandler(console_handler)

        self.logger = logger
        self.logger.info("Logging system initialized")

    async def on_command_error(self, interaction, error):
        """Handle errors in application commands gracefully"""
        self.logger.error(
            f"Error in command {interaction.command.name if interaction.command else 'unknown'}: {error}"
        )
        error_message = random.choice(GENERIC_ERRORS)

        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(error_message, ephemeral=True)
            else:
                await interaction.followup.send(error_message, ephemeral=True)
        except Exception as e:
            self.logger.error(f"Couldn't respond to interaction error: {e}")

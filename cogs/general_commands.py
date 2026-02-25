"""
General commands (help, usage)
"""
import discord
from discord import app_commands

from utils.constants import BOOK_TITLE


def setup_general_commands(bot):
    """
    Setup general commands for VilloroBot.

    Args:
        bot: The bot instance
    """

    @bot.tree.command(name="help", description="Show getting started guide")
    async def help_command(interaction: discord.Interaction):
        message = (
            f"**VilloroBot — Your guide to *{BOOK_TITLE}***\n\n"
            "I'm an AI-powered expert on this book. Ask me anything about its themes, "
            "arguments, or key concepts — I'll guide you with hints and page references "
            "rather than just giving you the answer.\n\n"
            "Use `/usage` to see all available commands."
        )
        await interaction.response.send_message(message)
        print("Sent help command response.")

    @bot.tree.command(name="usage", description="Show all available commands")
    async def usage_command(interaction: discord.Interaction):
        message = (
            "**VilloroBot — Available Commands**\n\n"
            "• `/ask <question>` — Ask the Villoro expert a question about the book\n"
            "• `/help` — Show getting started guide\n"
            "• `/usage` — Show this list"
        )
        await interaction.response.send_message(message)
        print("Sent usage command response.")

"""
Brains commands - RAG-powered interactions via kluvs-brain
"""
import discord
from discord import app_commands

from kluvs_brain import BrainError, RetrievalError, ReasoningError


def setup_brains_commands(bot):
    """
    Setup AI-powered commands using the brains service.

    Args:
        bot: The bot instance with brains_service initialized
    """

    @bot.tree.command(name="ask", description="Ask the Villoro expert a question about the book")
    @app_commands.describe(question="What would you like to know?")
    async def ask_command(interaction: discord.Interaction, question: str):
        """
        Ask the RAG brain a question about the book.

        Uses kluvs-brain's SocraticEngine to search relevant excerpts and
        return a Socratic response with hints and page citations.
        """
        if not interaction.guild_id:
            await interaction.response.send_message(
                "This command can only be used in a Discord server, not in DMs.",
                ephemeral=True
            )
            return

        # Defer since the AI call may take a moment
        await interaction.response.defer()

        try:
            response = await bot.brains_service.ask(question)
            await interaction.followup.send(response)
            print(f"[SUCCESS] Sent /ask response")

        except RetrievalError:
            await interaction.followup.send(
                "I couldn't find relevant information in the book for that question. "
                "Try rephrasing or asking about a different aspect."
            )

        except ReasoningError:
            await interaction.followup.send(
                "I had trouble generating a response. This may be an OpenAI service issue — "
                "please try again in a moment."
            )

        except BrainError:
            await interaction.followup.send(
                "Something went wrong on my end. Please try again later."
            )

        except Exception as e:
            print(f"[ERROR] Unexpected error in /ask: {str(e)}")
            await interaction.followup.send(
                "An unexpected error occurred. Please try again later."
            )

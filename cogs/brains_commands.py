"""
Brains commands — RAG-powered interactions via kluvs-brain.

/ask-privately: ephemeral response visible only to the requesting user.
For public responses, use @mention in a server channel (see events/message_handler.py).

Note: reaction feedback (👍/👎) is not applied to ephemeral messages.
"""
import discord
from discord import app_commands

from kluvs_brain import BrainError, RetrievalError, ReasoningError


def setup_brains_commands(bot):
    """
    Setup AI-powered commands using the brains service.

    Args:
        bot: The bot instance with brains_service and interaction_logger initialized
    """

    @bot.tree.command(
        name="ask-privately",
        description="Ask the Villoro expert a question — only you will see the answer"
    )
    @app_commands.describe(question="What would you like to know?")
    async def ask_privately_command(interaction: discord.Interaction, question: str):
        """
        Ask the RAG brain a question with an ephemeral (private) response.

        Uses kluvs-brain's SocraticEngine to search relevant excerpts and
        return a Socratic response with hints and page citations.
        Only the requesting user sees the reply.
        """
        if not interaction.guild_id:
            await interaction.response.send_message(
                "This command can only be used in a Discord server. "
                "For private questions outside a server, you can DM me directly!",
                ephemeral=True
            )
            return

        # Ephemeral defer — response visible only to the user
        await interaction.response.defer(ephemeral=True)

        try:
            result = await bot.brains_service.ask(interaction.user.id, None, question)
            await interaction.followup.send(result.response, ephemeral=True)

            # Log the interaction (no message_id since ephemeral messages aren't retrievable)
            bot.interaction_logger.log_interaction(
                user_id=str(interaction.user.id),
                display_name=interaction.user.display_name,
                guild_id=str(interaction.guild_id),
                mode='private',
                question=question,
                response=result.response,
                error_type='',
                message_id='',
                conversation_id=result.conversation_id,
            )
            print(f"[SUCCESS] Sent /ask-privately response")

        except RetrievalError:
            response = (
                "I couldn't find relevant information in the book for that question. "
                "Try rephrasing or asking about a different aspect."
            )
            await interaction.followup.send(response, ephemeral=True)
            bot.interaction_logger.log_interaction(
                user_id=str(interaction.user.id),
                display_name=interaction.user.display_name,
                guild_id=str(interaction.guild_id),
                mode='private',
                question=question,
                response=response,
                error_type='RetrievalError',
                message_id='',
            )

        except ReasoningError:
            response = (
                "I had trouble generating a response. "
                "This may be an OpenAI service issue — please try again in a moment."
            )
            await interaction.followup.send(response, ephemeral=True)
            bot.interaction_logger.log_interaction(
                user_id=str(interaction.user.id),
                display_name=interaction.user.display_name,
                guild_id=str(interaction.guild_id),
                mode='private',
                question=question,
                response=response,
                error_type='ReasoningError',
                message_id='',
            )

        except BrainError:
            response = "Something went wrong on my end. Please try again later."
            await interaction.followup.send(response, ephemeral=True)
            bot.interaction_logger.log_interaction(
                user_id=str(interaction.user.id),
                display_name=interaction.user.display_name,
                guild_id=str(interaction.guild_id),
                mode='private',
                question=question,
                response=response,
                error_type='BrainError',
                message_id='',
            )

        except Exception as e:
            print(f"[ERROR] Unexpected error in /ask-privately: {str(e)}")
            await interaction.followup.send(
                "An unexpected error occurred. Please try again later.",
                ephemeral=True
            )

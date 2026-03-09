"""
Message event handler — public (@mention) and DM interaction modes.

Public mode:  student @mentions the bot in a server channel → response posted publicly.
DM mode:      student messages the bot directly → response sent in the DM thread.

Button feedback (👍/👎) is attached directly to the response message sporadically
(FEEDBACK_PERCENTAGE). Ephemeral (/ask-privately) responses do not get buttons.
"""
import random
import discord
from kluvs_brain import BrainError, RetrievalError, ReasoningError

from utils.constants import FEEDBACK_PERCENTAGE
from utils.feedback import FeedbackView

MAX_MSG_LEN = 1990


def setup_message_handlers(bot):

    @bot.event
    async def on_message(message: discord.Message):
        # Never respond to other bots
        if message.author.bot:
            return

        # Keep prefix commands (e.g. !version) working
        await bot.process_commands(message)

        # DM mode — any message sent directly to the bot
        if isinstance(message.channel, discord.DMChannel):
            question = message.content.strip()
            if not question:
                return
            await _handle_ask(bot, message, question, mode='dm', guild_id=None)
            return

        # Public mode — @mention in a server channel
        if bot.user in message.mentions:
            question = (
                message.content
                .replace(f'<@{bot.user.id}>', '')
                .replace(f'<@!{bot.user.id}>', '')
                .strip()
            )
            if not question:
                await message.channel.send(
                    "Yes? Ask me something about the book!"
                )
                return
            await _handle_ask(
                bot, message, question,
                mode='public', guild_id=str(message.guild.id)
            )


async def _handle_ask(bot, message: discord.Message, question: str, mode: str, guild_id: str | None):
    """Shared ask logic for public and DM modes."""
    thinking_msg = await message.channel.send("Thinking...")
    try:
        response = await bot.brains_service.ask(message.author.id, question)
        chunks = _split_response(response)
        view = FeedbackView(bot) if random.random() < FEEDBACK_PERCENTAGE else None
        await thinking_msg.edit(content=chunks[0], view=view)
        for chunk in chunks[1:]:
            await message.channel.send(chunk)

        bot.interaction_logger.log_interaction(
            user_id=str(message.author.id),
            display_name=message.author.display_name,
            guild_id=guild_id,
            mode=mode,
            question=question,
            response=response,
            error_type='',
            message_id=str(thinking_msg.id),
        )

    except RetrievalError:
        response = (
            "I couldn't find relevant information in the book for that question. "
            "Try rephrasing or asking about a different aspect."
        )
        await thinking_msg.edit(content=response)
        bot.interaction_logger.log_interaction(
            user_id=str(message.author.id),
            display_name=message.author.display_name,
            guild_id=guild_id,
            mode=mode,
            question=question,
            response=response,
            error_type='RetrievalError',
            message_id=str(thinking_msg.id),
        )

    except ReasoningError:
        response = (
            "I had trouble generating a response. "
            "This may be an OpenAI service issue — please try again in a moment."
        )
        await thinking_msg.edit(content=response)
        bot.interaction_logger.log_interaction(
            user_id=str(message.author.id),
            display_name=message.author.display_name,
            guild_id=guild_id,
            mode=mode,
            question=question,
            response=response,
            error_type='ReasoningError',
            message_id=str(thinking_msg.id),
        )

    except BrainError:
        response = "Something went wrong on my end. Please try again later."
        await thinking_msg.edit(content=response)
        bot.interaction_logger.log_interaction(
            user_id=str(message.author.id),
            display_name=message.author.display_name,
            guild_id=guild_id,
            mode=mode,
            question=question,
            response=response,
            error_type='BrainError',
            message_id=str(thinking_msg.id),
        )

    except Exception as e:
        print(f"[ERROR] Unexpected error in message handler: {str(e)}")
        await thinking_msg.edit(content="An unexpected error occurred. Please try again later.")


def _split_response(text: str) -> list[str]:
    """Split a response into chunks that fit Discord's message limit."""
    if len(text) <= MAX_MSG_LEN:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:MAX_MSG_LEN])
        text = text[MAX_MSG_LEN:]
    return chunks

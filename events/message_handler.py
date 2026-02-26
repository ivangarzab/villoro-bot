"""
Message event handler — public (@mention) and DM interaction modes.

Public mode:  student @mentions the bot in a server channel → response posted publicly.
DM mode:      student messages the bot directly → response sent in the DM thread.

Reaction feedback is applied sporadically (FEEDBACK_PERCENTAGE) to public and DM
responses. Ephemeral (/ask-privately) responses do not support reactions.
"""
import random
import discord
from kluvs_brain import BrainError, RetrievalError, ReasoningError

from utils.constants import FEEDBACK_PERCENTAGE


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

    @bot.event
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
        # Ignore the bot's own reactions
        if payload.user_id == bot.user.id:
            return

        # Only track reactions on messages we flagged for feedback
        if payload.message_id not in bot.feedback_messages:
            return

        emoji = str(payload.emoji)
        if emoji not in ('👍', '👎'):
            return

        # Resolve display name
        display_name = str(payload.user_id)
        if payload.guild_id:
            guild = bot.get_guild(payload.guild_id)
            if guild:
                member = guild.get_member(payload.user_id)
                if member:
                    display_name = member.display_name

        bot.interaction_logger.log_reaction(
            message_id=str(payload.message_id),
            user_id=str(payload.user_id),
            display_name=display_name,
            reaction=emoji,
        )
        print(f"[INFO] Logged reaction {emoji} from {display_name} on message {payload.message_id}")


async def _handle_ask(bot, message: discord.Message, question: str, mode: str, guild_id: str | None):
    """Shared ask logic for public and DM modes."""
    async with message.channel.typing():
        try:
            response = await bot.brains_service.ask(question)
            sent = await message.channel.send(response)

            bot.interaction_logger.log_interaction(
                user_id=str(message.author.id),
                display_name=message.author.display_name,
                guild_id=guild_id,
                mode=mode,
                question=question,
                response=response,
                error_type='',
                message_id=str(sent.id),
            )

            # Sporadic reaction feedback (not on private/ephemeral)
            if random.random() < FEEDBACK_PERCENTAGE:
                await sent.add_reaction('👍')
                await sent.add_reaction('👎')
                bot.feedback_messages.add(sent.id)
                print(f"[INFO] Added feedback reactions to message {sent.id}")

        except RetrievalError:
            response = (
                "I couldn't find relevant information in the book for that question. "
                "Try rephrasing or asking about a different aspect."
            )
            sent = await message.channel.send(response)
            bot.interaction_logger.log_interaction(
                user_id=str(message.author.id),
                display_name=message.author.display_name,
                guild_id=guild_id,
                mode=mode,
                question=question,
                response=response,
                error_type='RetrievalError',
                message_id=str(sent.id),
            )

        except ReasoningError:
            response = (
                "I had trouble generating a response. "
                "This may be an OpenAI service issue — please try again in a moment."
            )
            sent = await message.channel.send(response)
            bot.interaction_logger.log_interaction(
                user_id=str(message.author.id),
                display_name=message.author.display_name,
                guild_id=guild_id,
                mode=mode,
                question=question,
                response=response,
                error_type='ReasoningError',
                message_id=str(sent.id),
            )

        except BrainError:
            response = "Something went wrong on my end. Please try again later."
            sent = await message.channel.send(response)
            bot.interaction_logger.log_interaction(
                user_id=str(message.author.id),
                display_name=message.author.display_name,
                guild_id=guild_id,
                mode=mode,
                question=question,
                response=response,
                error_type='BrainError',
                message_id=str(sent.id),
            )

        except Exception as e:
            print(f"[ERROR] Unexpected error in message handler: {str(e)}")
            await message.channel.send(
                "An unexpected error occurred. Please try again later."
            )

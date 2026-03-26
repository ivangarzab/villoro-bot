"""
Tests for message_handler (public @mention, DM, and thread modes)
"""
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from events.message_handler import setup_message_handlers
from services.brains_service import AskResult
from utils.feedback import FeedbackView


class TestMessageHandler(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.bot = MagicMock()
        self.bot.user = MagicMock()
        self.bot.user.id = 999
        self.bot.brains_service = AsyncMock()
        self.bot.brains_service.has_session = MagicMock(return_value=False)
        self.bot.brains_service.seed_session = MagicMock()
        self.bot.interaction_logger = MagicMock()

        self.events = {}

        def mock_event(func):
            self.events[func.__name__] = func
            return func

        self.bot.event = mock_event
        self.bot.process_commands = AsyncMock()
        setup_message_handlers(self.bot)

    def _make_guild_message(self, content, mentions_bot=True):
        message = AsyncMock(spec=discord.Message)
        message.author = MagicMock()
        message.author.bot = False
        message.author.id = 42
        message.author.display_name = 'Alice'
        message.content = content
        message.channel = AsyncMock(spec=discord.TextChannel)
        message.guild = MagicMock()
        message.guild.id = 100
        message.mentions = [self.bot.user] if mentions_bot else []

        thinking_msg = AsyncMock()
        thinking_msg.id = 555
        message.channel.send = AsyncMock(return_value=thinking_msg)
        return message

    def _make_dm_message(self, content):
        message = AsyncMock(spec=discord.Message)
        message.author = MagicMock()
        message.author.bot = False
        message.author.id = 42
        message.author.display_name = 'Alice'
        message.content = content
        message.channel = AsyncMock(spec=discord.DMChannel)
        message.guild = None
        message.mentions = []

        thinking_msg = AsyncMock()
        thinking_msg.id = 666
        message.channel.send = AsyncMock(return_value=thinking_msg)
        return message

    def _make_thread_message(self, content, mentions_bot=True):
        message = AsyncMock(spec=discord.Message)
        message.author = MagicMock()
        message.author.bot = False
        message.author.id = 42
        message.author.display_name = 'Alice'
        message.content = content
        message.channel = AsyncMock(spec=discord.Thread)
        message.channel.id = 777
        message.guild = MagicMock()
        message.guild.id = 100
        message.mentions = [self.bot.user] if mentions_bot else []

        thinking_msg = AsyncMock()
        thinking_msg.id = 888
        message.channel.send = AsyncMock(return_value=thinking_msg)
        return message

    # ------------------------------------------------------------------
    # on_message — ignore bots
    # ------------------------------------------------------------------

    async def test_ignores_bot_messages(self):
        message = self._make_guild_message(f'<@{self.bot.user.id}> hello')
        message.author.bot = True
        await self.events['on_message'](message)
        self.bot.brains_service.ask.assert_not_called()

    # ------------------------------------------------------------------
    # on_message — public mode
    # ------------------------------------------------------------------

    async def test_public_mention_calls_brains(self):
        self.bot.brains_service.ask.return_value = AskResult(response="A Socratic hint", conversation_id=None)
        message = self._make_guild_message(
            f'<@{self.bot.user.id}> What is freedom?', mentions_bot=True
        )
        await self.events['on_message'](message)
        self.bot.brains_service.ask.assert_called_once()

    async def test_public_mention_passes_none_channel_id(self):
        self.bot.brains_service.ask.return_value = AskResult(response="A hint", conversation_id=None)
        message = self._make_guild_message(
            f'<@{self.bot.user.id}> What is freedom?', mentions_bot=True
        )
        await self.events['on_message'](message)
        args = self.bot.brains_service.ask.call_args[0]
        self.assertIsNone(args[1])  # channel_id is None for public mode

    async def test_public_mention_logs_interaction(self):
        self.bot.brains_service.ask.return_value = AskResult(response="A hint", conversation_id=None)
        message = self._make_guild_message(
            f'<@{self.bot.user.id}> What is freedom?', mentions_bot=True
        )
        await self.events['on_message'](message)
        self.bot.interaction_logger.log_interaction.assert_called_once()
        call_kwargs = self.bot.interaction_logger.log_interaction.call_args[1]
        self.assertEqual(call_kwargs['mode'], 'public')

    async def test_non_mention_ignored(self):
        message = self._make_guild_message('Just chatting', mentions_bot=False)
        await self.events['on_message'](message)
        self.bot.brains_service.ask.assert_not_called()

    async def test_empty_mention_sends_prompt(self):
        message = self._make_guild_message(f'<@{self.bot.user.id}>', mentions_bot=True)
        await self.events['on_message'](message)
        self.bot.brains_service.ask.assert_not_called()
        message.channel.send.assert_called_once()

    # ------------------------------------------------------------------
    # on_message — DM mode
    # ------------------------------------------------------------------

    async def test_dm_calls_brains(self):
        self.bot.brains_service.ask.return_value = AskResult(response="DM response", conversation_id="conv-123")
        message = self._make_dm_message('Who is Villoro?')
        await self.events['on_message'](message)
        self.bot.brains_service.ask.assert_called_once()

    async def test_dm_passes_channel_id(self):
        self.bot.brains_service.ask.return_value = AskResult(response="DM response", conversation_id="conv-123")
        message = self._make_dm_message('Who is Villoro?')
        await self.events['on_message'](message)
        args = self.bot.brains_service.ask.call_args[0]
        self.assertEqual(args[1], message.channel.id)  # channel_id is set for DMs

    async def test_dm_logs_with_dm_mode(self):
        self.bot.brains_service.ask.return_value = AskResult(response="DM response", conversation_id="conv-123")
        message = self._make_dm_message('Who is Villoro?')
        await self.events['on_message'](message)
        call_kwargs = self.bot.interaction_logger.log_interaction.call_args[1]
        self.assertEqual(call_kwargs['mode'], 'dm')
        self.assertIsNone(call_kwargs['guild_id'])

    async def test_dm_logs_conversation_id(self):
        self.bot.brains_service.ask.return_value = AskResult(response="DM response", conversation_id="conv-123")
        message = self._make_dm_message('Who is Villoro?')
        await self.events['on_message'](message)
        call_kwargs = self.bot.interaction_logger.log_interaction.call_args[1]
        self.assertEqual(call_kwargs['conversation_id'], "conv-123")

    async def test_empty_dm_ignored(self):
        message = self._make_dm_message('   ')
        await self.events['on_message'](message)
        self.bot.brains_service.ask.assert_not_called()

    # ------------------------------------------------------------------
    # on_message — thread mode
    # ------------------------------------------------------------------

    async def test_thread_mention_calls_brains(self):
        self.bot.brains_service.ask.return_value = AskResult(response="Thread hint", conversation_id="conv-456")
        message = self._make_thread_message(
            f'<@{self.bot.user.id}> What is knowledge?', mentions_bot=True
        )
        await self.events['on_message'](message)
        self.bot.brains_service.ask.assert_called_once()

    async def test_thread_passes_channel_id(self):
        self.bot.brains_service.ask.return_value = AskResult(response="Thread hint", conversation_id="conv-456")
        message = self._make_thread_message(
            f'<@{self.bot.user.id}> What is knowledge?', mentions_bot=True
        )
        await self.events['on_message'](message)
        args = self.bot.brains_service.ask.call_args[0]
        self.assertEqual(args[1], message.channel.id)  # channel_id is set for threads

    async def test_thread_seeds_session_when_no_existing_session(self):
        self.bot.brains_service.has_session.return_value = False
        self.bot.brains_service.ask.return_value = AskResult(response="Thread hint", conversation_id="conv-456")
        starter = AsyncMock()
        starter.content = "Let's discuss Villoro"
        starter.author = MagicMock()
        starter.author.__eq__ = lambda *_: False  # not the bot
        message = self._make_thread_message(
            f'<@{self.bot.user.id}> What is knowledge?', mentions_bot=True
        )
        message.channel.parent.fetch_message = AsyncMock(return_value=starter)

        await self.events['on_message'](message)

        self.bot.brains_service.seed_session.assert_called_once_with(
            message.channel.id, starter.content, 'user'
        )

    async def test_thread_seeds_with_assistant_role_when_bot_authored(self):
        self.bot.brains_service.has_session.return_value = False
        self.bot.brains_service.ask.return_value = AskResult(response="Thread hint", conversation_id="conv-456")
        starter = AsyncMock()
        starter.content = "Here is a response from the bot"
        starter.author = self.bot.user  # bot authored the starter
        message = self._make_thread_message(
            f'<@{self.bot.user.id}> Follow-up?', mentions_bot=True
        )
        message.channel.parent.fetch_message = AsyncMock(return_value=starter)

        await self.events['on_message'](message)

        self.bot.brains_service.seed_session.assert_called_once_with(
            message.channel.id, starter.content, 'assistant'
        )

    async def test_thread_skips_seeding_when_session_exists(self):
        self.bot.brains_service.has_session.return_value = True
        self.bot.brains_service.ask.return_value = AskResult(response="Thread hint", conversation_id="conv-456")
        message = self._make_thread_message(
            f'<@{self.bot.user.id}> What is knowledge?', mentions_bot=True
        )

        await self.events['on_message'](message)

        self.bot.brains_service.seed_session.assert_not_called()

    async def test_thread_proceeds_if_starter_fetch_fails(self):
        self.bot.brains_service.has_session.return_value = False
        self.bot.brains_service.ask.return_value = AskResult(response="Thread hint", conversation_id="conv-456")
        message = self._make_thread_message(
            f'<@{self.bot.user.id}> What is knowledge?', mentions_bot=True
        )
        message.channel.parent.fetch_message = AsyncMock(side_effect=Exception("not found"))

        await self.events['on_message'](message)

        self.bot.brains_service.seed_session.assert_not_called()
        self.bot.brains_service.ask.assert_called_once()

    # ------------------------------------------------------------------
    # on_message — feedback view
    # ------------------------------------------------------------------

    @patch('events.message_handler.random.random', return_value=0.0)  # always triggers
    async def test_feedback_view_attached_when_triggered(self, _):
        self.bot.brains_service.ask.return_value = AskResult(response="A hint", conversation_id=None)
        message = self._make_guild_message(
            f'<@{self.bot.user.id}> What is freedom?', mentions_bot=True
        )
        await self.events['on_message'](message)
        thinking_msg = message.channel.send.return_value
        _, edit_kwargs = thinking_msg.edit.call_args
        self.assertIsInstance(edit_kwargs.get('view'), FeedbackView)

    @patch('events.message_handler.random.random', return_value=1.0)  # never triggers
    async def test_no_feedback_view_when_not_triggered(self, _):
        self.bot.brains_service.ask.return_value = AskResult(response="A hint", conversation_id=None)
        message = self._make_guild_message(
            f'<@{self.bot.user.id}> What is freedom?', mentions_bot=True
        )
        await self.events['on_message'](message)
        thinking_msg = message.channel.send.return_value
        _, edit_kwargs = thinking_msg.edit.call_args
        self.assertIsNone(edit_kwargs.get('view'))

    # ------------------------------------------------------------------
    # on_message — error paths
    # ------------------------------------------------------------------

    async def test_retrieval_error_logs_error_type(self):
        from kluvs_brain import RetrievalError
        self.bot.brains_service.ask.side_effect = RetrievalError("not found")
        message = self._make_guild_message(
            f'<@{self.bot.user.id}> test', mentions_bot=True
        )
        await self.events['on_message'](message)
        call_kwargs = self.bot.interaction_logger.log_interaction.call_args[1]
        self.assertEqual(call_kwargs['error_type'], 'RetrievalError')


if __name__ == '__main__':
    unittest.main()

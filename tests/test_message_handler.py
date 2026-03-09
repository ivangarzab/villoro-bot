"""
Tests for message_handler (public @mention and DM modes)
"""
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from events.message_handler import setup_message_handlers, _handle_ask
from utils.feedback import FeedbackView


class TestMessageHandler(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.bot = MagicMock()
        self.bot.user = MagicMock()
        self.bot.user.id = 999
        self.bot.brains_service = AsyncMock()
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
        self.bot.brains_service.ask.return_value = "A Socratic hint"
        message = self._make_guild_message(
            f'<@{self.bot.user.id}> What is freedom?', mentions_bot=True
        )
        await self.events['on_message'](message)
        self.bot.brains_service.ask.assert_called_once()

    async def test_public_mention_logs_interaction(self):
        self.bot.brains_service.ask.return_value = "A hint"
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
        self.bot.brains_service.ask.return_value = "DM response"
        message = self._make_dm_message('Who is Villoro?')
        await self.events['on_message'](message)
        self.bot.brains_service.ask.assert_called_once()

    async def test_dm_logs_with_dm_mode(self):
        self.bot.brains_service.ask.return_value = "DM response"
        message = self._make_dm_message('Who is Villoro?')
        await self.events['on_message'](message)
        call_kwargs = self.bot.interaction_logger.log_interaction.call_args[1]
        self.assertEqual(call_kwargs['mode'], 'dm')
        self.assertIsNone(call_kwargs['guild_id'])

    async def test_empty_dm_ignored(self):
        message = self._make_dm_message('   ')
        await self.events['on_message'](message)
        self.bot.brains_service.ask.assert_not_called()

    # ------------------------------------------------------------------
    # on_message — error paths
    # ------------------------------------------------------------------

    @patch('events.message_handler.random.random', return_value=0.0)  # always triggers
    async def test_feedback_view_attached_when_triggered(self, _mock_random):
        self.bot.brains_service.ask.return_value = "A hint"
        message = self._make_guild_message(
            f'<@{self.bot.user.id}> What is freedom?', mentions_bot=True
        )
        await self.events['on_message'](message)
        thinking_msg = message.channel.send.return_value
        _, edit_kwargs = thinking_msg.edit.call_args
        self.assertIsInstance(edit_kwargs.get('view'), FeedbackView)

    @patch('events.message_handler.random.random', return_value=1.0)  # never triggers
    async def test_no_feedback_view_when_not_triggered(self, _mock_random):
        self.bot.brains_service.ask.return_value = "A hint"
        message = self._make_guild_message(
            f'<@{self.bot.user.id}> What is freedom?', mentions_bot=True
        )
        await self.events['on_message'](message)
        thinking_msg = message.channel.send.return_value
        _, edit_kwargs = thinking_msg.edit.call_args
        self.assertIsNone(edit_kwargs.get('view'))

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

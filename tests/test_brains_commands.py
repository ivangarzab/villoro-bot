"""
Tests for brains commands (/ask-privately)
"""
import unittest
from unittest.mock import MagicMock, AsyncMock

from cogs.brains_commands import setup_brains_commands
from services.brains_service import AskResult


class TestBrainsCommands(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.bot = MagicMock()
        self.bot.tree = MagicMock()
        self.bot.brains_service = AsyncMock()
        self.bot.interaction_logger = MagicMock()
        self.commands = {}

        def mock_command(**kwargs):
            def decorator(func):
                self.commands[kwargs.get('name')] = func
                return func
            return decorator

        self.bot.tree.command = mock_command
        setup_brains_commands(self.bot)
        self.assertIn('ask-privately', self.commands)

    def _make_interaction(self, guild_id=12345):
        interaction = AsyncMock()
        interaction.guild_id = guild_id
        interaction.user = MagicMock()
        interaction.user.id = 42
        interaction.user.display_name = 'Alice'
        interaction.response = AsyncMock()
        interaction.followup = AsyncMock()
        return interaction

    async def test_ask_privately_success(self):
        self.bot.brains_service.ask.return_value = AskResult(response="A Socratic hint...", conversation_id=None)
        interaction = self._make_interaction()

        await self.commands['ask-privately'](interaction, question="What is freedom?")

        interaction.response.defer.assert_called_once_with(ephemeral=True)
        interaction.followup.send.assert_called_once_with("A Socratic hint...", ephemeral=True)

    async def test_ask_privately_logs_private_mode(self):
        self.bot.brains_service.ask.return_value = AskResult(response="A hint", conversation_id=None)
        interaction = self._make_interaction()

        await self.commands['ask-privately'](interaction, question="What is freedom?")

        self.bot.interaction_logger.log_interaction.assert_called_once()
        call_kwargs = self.bot.interaction_logger.log_interaction.call_args[1]
        self.assertEqual(call_kwargs['mode'], 'private')

    async def test_ask_privately_logs_null_conversation_id(self):
        self.bot.brains_service.ask.return_value = AskResult(response="A hint", conversation_id=None)
        interaction = self._make_interaction()

        await self.commands['ask-privately'](interaction, question="What is freedom?")

        call_kwargs = self.bot.interaction_logger.log_interaction.call_args[1]
        self.assertIsNone(call_kwargs['conversation_id'])

    async def test_ask_privately_passes_none_channel_id(self):
        self.bot.brains_service.ask.return_value = AskResult(response="A hint", conversation_id=None)
        interaction = self._make_interaction()

        await self.commands['ask-privately'](interaction, question="What is freedom?")

        _, call_kwargs = self.bot.brains_service.ask.call_args
        self.assertIsNone(call_kwargs.get('channel_id') or self.bot.brains_service.ask.call_args[0][1])

    async def test_ask_privately_no_guild(self):
        interaction = self._make_interaction(guild_id=None)

        await self.commands['ask-privately'](interaction, question="What is freedom?")

        interaction.response.send_message.assert_called_once()
        call_kwargs = interaction.response.send_message.call_args[1]
        self.assertTrue(call_kwargs.get('ephemeral'))
        self.bot.brains_service.ask.assert_not_called()

    async def test_ask_privately_retrieval_error(self):
        from kluvs_brain import RetrievalError
        self.bot.brains_service.ask.side_effect = RetrievalError("not found")
        interaction = self._make_interaction()

        await self.commands['ask-privately'](interaction, question="What is knowledge?")

        interaction.followup.send.assert_called_once()
        args, kwargs = interaction.followup.send.call_args
        self.assertTrue(kwargs.get('ephemeral'))
        self.assertIn("couldn't find", args[0])

    async def test_ask_privately_reasoning_error(self):
        from kluvs_brain import ReasoningError
        self.bot.brains_service.ask.side_effect = ReasoningError("ai failed")
        interaction = self._make_interaction()

        await self.commands['ask-privately'](interaction, question="What is knowledge?")

        args, kwargs = interaction.followup.send.call_args
        self.assertTrue(kwargs.get('ephemeral'))
        self.assertIn("trouble generating", args[0])

    async def test_ask_privately_brain_error(self):
        from kluvs_brain import BrainError
        self.bot.brains_service.ask.side_effect = BrainError("unknown")
        interaction = self._make_interaction()

        await self.commands['ask-privately'](interaction, question="What is knowledge?")

        interaction.followup.send.assert_called_once()
        call_kwargs = interaction.followup.send.call_args[1]
        self.assertTrue(call_kwargs.get('ephemeral'))


if __name__ == '__main__':
    unittest.main()

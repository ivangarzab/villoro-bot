"""
Tests for brains commands (/ask)
"""
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

from cogs.brains_commands import setup_brains_commands


class TestBrainsCommands(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.bot = MagicMock()
        self.bot.tree = MagicMock()
        self.bot.brains_service = AsyncMock()
        self.commands = {}

        def mock_command(**kwargs):
            def decorator(func):
                self.commands[kwargs.get('name')] = func
                return func
            # Handle @app_commands.describe chaining
            decorator.describe = lambda **kw: decorator
            return decorator

        def mock_describe(**kwargs):
            def decorator(func):
                return func
            return decorator

        self.bot.tree.command = mock_command
        setup_brains_commands(self.bot)
        self.assertIn('ask', self.commands)

    def _make_interaction(self, guild_id=12345):
        interaction = AsyncMock()
        interaction.guild_id = guild_id
        interaction.response = AsyncMock()
        interaction.followup = AsyncMock()
        return interaction

    async def test_ask_success(self):
        """Successful /ask returns the brain response"""
        self.bot.brains_service.ask.return_value = "Here is a Socratic hint..."
        interaction = self._make_interaction()

        await self.commands['ask'](interaction, question="What is freedom?")

        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once_with("Here is a Socratic hint...")

    async def test_ask_no_guild(self):
        """Command in DMs sends ephemeral error"""
        interaction = self._make_interaction(guild_id=None)

        await self.commands['ask'](interaction, question="What is freedom?")

        interaction.response.send_message.assert_called_once()
        call_kwargs = interaction.response.send_message.call_args[1]
        self.assertTrue(call_kwargs.get('ephemeral'))

    async def test_ask_retrieval_error(self):
        """RetrievalError returns a helpful message"""
        from kluvs_brain import RetrievalError
        self.bot.brains_service.ask.side_effect = RetrievalError("not found")
        interaction = self._make_interaction()

        await self.commands['ask'](interaction, question="What is knowledge?")

        interaction.followup.send.assert_called_once()
        message = interaction.followup.send.call_args[0][0]
        self.assertIn("couldn't find", message)

    async def test_ask_reasoning_error(self):
        """ReasoningError returns a helpful message"""
        from kluvs_brain import ReasoningError
        self.bot.brains_service.ask.side_effect = ReasoningError("ai failed")
        interaction = self._make_interaction()

        await self.commands['ask'](interaction, question="What is knowledge?")

        interaction.followup.send.assert_called_once()
        message = interaction.followup.send.call_args[0][0]
        self.assertIn("trouble generating", message)

    async def test_ask_brain_error(self):
        """Generic BrainError returns fallback message"""
        from kluvs_brain import BrainError
        self.bot.brains_service.ask.side_effect = BrainError("unknown")
        interaction = self._make_interaction()

        await self.commands['ask'](interaction, question="What is knowledge?")

        interaction.followup.send.assert_called_once()


if __name__ == '__main__':
    unittest.main()

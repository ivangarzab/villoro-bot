"""
Tests for general commands (help, usage)
"""
import unittest
from unittest.mock import MagicMock, AsyncMock

from cogs.general_commands import setup_general_commands


class TestGeneralCommands(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.bot = MagicMock()
        self.bot.tree = MagicMock()
        self.commands = {}

        def mock_command(**kwargs):
            def decorator(func):
                self.commands[kwargs.get('name')] = func
                return func
            return decorator

        self.bot.tree.command = mock_command
        setup_general_commands(self.bot)

        self.assertIn('help', self.commands)
        self.assertIn('usage', self.commands)

    async def test_help_command_sends_message(self):
        interaction = AsyncMock()
        await self.commands['help'](interaction)
        interaction.response.send_message.assert_called_once()
        message = interaction.response.send_message.call_args[0][0]
        self.assertIn("VilloroBot", message)

    async def test_usage_command_sends_message(self):
        interaction = AsyncMock()
        await self.commands['usage'](interaction)
        interaction.response.send_message.assert_called_once()
        message = interaction.response.send_message.call_args[0][0]
        self.assertIn("/ask", message)


if __name__ == '__main__':
    unittest.main()

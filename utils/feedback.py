"""
Feedback UI — Discord button view for sporadic response rating.

Attached directly to the bot's response message when FEEDBACK_PERCENTAGE triggers.
Each click logs to the reactions CSV and sends an ephemeral acknowledgment to the clicker.
Buttons stay active for all users (useful for public channel responses) until timeout.
"""
import discord


class FeedbackView(discord.ui.View):
    """
    Two-button view attached to a bot response message.

    Args:
        bot: The bot instance (needs interaction_logger)
        timeout: Seconds before buttons are disabled (default: 10 minutes)
    """

    def __init__(self, bot, timeout: float = 600):
        super().__init__(timeout=timeout)
        self.bot = bot

    @discord.ui.button(label="Helpful", style=discord.ButtonStyle.success, emoji="👍")
    async def helpful(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.interaction_logger.log_reaction(
            message_id=str(interaction.message.id),
            user_id=str(interaction.user.id),
            display_name=interaction.user.display_name,
            reaction='👍',
        )
        await interaction.response.send_message("Thanks for the feedback!", ephemeral=True)

    @discord.ui.button(label="Not helpful", style=discord.ButtonStyle.danger, emoji="👎")
    async def not_helpful(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.interaction_logger.log_reaction(
            message_id=str(interaction.message.id),
            user_id=str(interaction.user.id),
            display_name=interaction.user.display_name,
            reaction='👎',
        )
        await interaction.response.send_message("Thanks for the feedback!", ephemeral=True)

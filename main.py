#!/usr/bin/env python3
"""
Main entry point for VilloroBot
"""
from bot import VilloroBot


def main():
    """Main function to start the bot"""
    bot = VilloroBot()
    bot.run(bot.config.TOKEN)


if __name__ == "__main__":
    main()

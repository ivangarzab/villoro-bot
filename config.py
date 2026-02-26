"""
Configuration module for VilloroBot
"""
import os
from dotenv import load_dotenv


class BotConfig:
    """Configuration class to handle environment variables and settings"""

    def __init__(self):
        load_dotenv(override=True)

        self.ENV = os.getenv("ENV")
        # if self.ENV == "dev":
        #     print("[DEBUG] ~~~~~~~~~~~~ Running in development mode ~~~~~~~~~~~~")
        #     self.TOKEN = os.getenv("DEV_TOKEN")
        # else:
        self.TOKEN = os.getenv("TOKEN")

        # kluvs-brain credentials
        self.BRAINS_SUPABASE_URL = os.getenv("BRAINS_SUPABASE_URL")
        self.BRAINS_SUPABASE_KEY = os.getenv("BRAINS_SUPABASE_KEY")
        self.KEY_OPENAI = os.getenv("KEY_OPEN_AI")

        self._debug_print()
        self._validate()

    def _debug_print(self):
        """Print debug information about configuration"""
        print(f"[DEBUG] TOKEN: {'SET' if self.TOKEN else 'NOT SET'}")
        print(f"[DEBUG] BRAINS_SUPABASE_URL: {'SET' if self.BRAINS_SUPABASE_URL else 'NOT SET'}")
        print(f"[DEBUG] KEY_OPENAI: {'SET' if self.KEY_OPENAI else 'NOT SET'}")

    def _validate(self):
        """Validate that required configuration is present"""
        if not self.TOKEN:
            raise ValueError("[ERROR] TOKEN environment variable is not set.")
        if not self.BRAINS_SUPABASE_URL:
            raise ValueError("[ERROR] BRAINS_SUPABASE_URL environment variable is not set.")
        if not self.BRAINS_SUPABASE_KEY:
            raise ValueError("[ERROR] BRAINS_SUPABASE_KEY environment variable is not set.")
        if not self.KEY_OPENAI:
            raise ValueError("[ERROR] KEY_OPEN_AI environment variable is not set.")

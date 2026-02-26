"""
Interaction logger — writes structured CSV records for research analysis.

Two daily-rotating files:
  logs/interactions_YYYY-MM-DD.csv  — one row per question/response
  logs/reactions_YYYY-MM-DD.csv     — one row per student reaction (👍/👎)

The two files join on `message_id`.
"""
import csv
import os
from datetime import datetime


class InteractionLogger:

    INTERACTION_FIELDS = [
        'timestamp', 'user_id', 'display_name', 'guild_id', 'mode',
        'question', 'response', 'error_type', 'message_id',
        'conversation_id', 'tokens_used',
    ]

    REACTION_FIELDS = [
        'timestamp', 'message_id', 'user_id', 'display_name', 'reaction',
    ]

    def __init__(self, log_dir: str = 'logs'):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _today(self) -> str:
        return datetime.now().strftime('%Y-%m-%d')

    def _interactions_path(self) -> str:
        return os.path.join(self.log_dir, f'interactions_{self._today()}.csv')

    def _reactions_path(self) -> str:
        return os.path.join(self.log_dir, f'reactions_{self._today()}.csv')

    def _write_row(self, filepath: str, fieldnames: list, row: dict):
        file_exists = os.path.exists(filepath)
        with open(filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_interaction(
        self,
        *,
        user_id: str,
        display_name: str,
        guild_id: str | None,
        mode: str,
        question: str,
        response: str,
        error_type: str,
        message_id: str,
        conversation_id: str | None = None,
        tokens_used: int | None = None,
    ):
        """Write one interaction row to today's interactions CSV."""
        self._write_row(
            self._interactions_path(),
            self.INTERACTION_FIELDS,
            {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'display_name': display_name,
                'guild_id': guild_id or '',
                'mode': mode,
                'question': question,
                'response': response,
                'error_type': error_type,
                'message_id': message_id,
                'conversation_id': conversation_id or '',
                'tokens_used': tokens_used if tokens_used is not None else '',
            },
        )

    def log_reaction(
        self,
        *,
        message_id: str,
        user_id: str,
        display_name: str,
        reaction: str,
    ):
        """Write one reaction row to today's reactions CSV."""
        self._write_row(
            self._reactions_path(),
            self.REACTION_FIELDS,
            {
                'timestamp': datetime.now().isoformat(),
                'message_id': message_id,
                'user_id': user_id,
                'display_name': display_name,
                'reaction': reaction,
            },
        )

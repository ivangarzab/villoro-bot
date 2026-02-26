"""
Tests for InteractionLogger
"""
import csv
import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

from utils.interaction_logger import InteractionLogger


class TestInteractionLogger(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.logger = InteractionLogger(log_dir=self.tmp_dir)

    def _interaction_path(self):
        date = datetime.now().strftime('%Y-%m-%d')
        return os.path.join(self.tmp_dir, f'interactions_{date}.csv')

    def _reaction_path(self):
        date = datetime.now().strftime('%Y-%m-%d')
        return os.path.join(self.tmp_dir, f'reactions_{date}.csv')

    def _read_csv(self, filepath):
        with open(filepath, newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    # ------------------------------------------------------------------
    # Interaction logging
    # ------------------------------------------------------------------

    def test_interaction_creates_file_with_headers(self):
        self.logger.log_interaction(
            user_id='123', display_name='Alice', guild_id='999',
            mode='public', question='What is freedom?', response='A hint...',
            error_type='', message_id='msg-1',
        )
        self.assertTrue(os.path.exists(self._interaction_path()))
        rows = self._read_csv(self._interaction_path())
        self.assertEqual(len(rows), 1)
        self.assertIn('timestamp', rows[0])
        self.assertIn('conversation_id', rows[0])
        self.assertIn('tokens_used', rows[0])

    def test_interaction_row_values(self):
        self.logger.log_interaction(
            user_id='42', display_name='Bob', guild_id='777',
            mode='dm', question='Who is Villoro?', response='He is...',
            error_type='', message_id='msg-2',
        )
        rows = self._read_csv(self._interaction_path())
        row = rows[0]
        self.assertEqual(row['user_id'], '42')
        self.assertEqual(row['display_name'], 'Bob')
        self.assertEqual(row['guild_id'], '777')
        self.assertEqual(row['mode'], 'dm')
        self.assertEqual(row['question'], 'Who is Villoro?')
        self.assertEqual(row['error_type'], '')
        self.assertEqual(row['conversation_id'], '')
        self.assertEqual(row['tokens_used'], '')

    def test_multiple_interactions_appended(self):
        for i in range(3):
            self.logger.log_interaction(
                user_id=str(i), display_name=f'User{i}', guild_id='1',
                mode='public', question=f'Q{i}', response=f'R{i}',
                error_type='', message_id=f'msg-{i}',
            )
        rows = self._read_csv(self._interaction_path())
        self.assertEqual(len(rows), 3)

    def test_interaction_with_error_type(self):
        self.logger.log_interaction(
            user_id='99', display_name='Carol', guild_id=None,
            mode='dm', question='Bad question', response='Error msg',
            error_type='RetrievalError', message_id='msg-err',
        )
        rows = self._read_csv(self._interaction_path())
        self.assertEqual(rows[0]['error_type'], 'RetrievalError')
        self.assertEqual(rows[0]['guild_id'], '')

    # ------------------------------------------------------------------
    # Reaction logging
    # ------------------------------------------------------------------

    def test_reaction_creates_file_with_headers(self):
        self.logger.log_reaction(
            message_id='msg-1', user_id='123',
            display_name='Alice', reaction='👍',
        )
        self.assertTrue(os.path.exists(self._reaction_path()))
        rows = self._read_csv(self._reaction_path())
        self.assertEqual(len(rows), 1)
        self.assertIn('timestamp', rows[0])

    def test_reaction_row_values(self):
        self.logger.log_reaction(
            message_id='msg-42', user_id='7',
            display_name='Dave', reaction='👎',
        )
        rows = self._read_csv(self._reaction_path())
        row = rows[0]
        self.assertEqual(row['message_id'], 'msg-42')
        self.assertEqual(row['user_id'], '7')
        self.assertEqual(row['display_name'], 'Dave')
        self.assertEqual(row['reaction'], '👎')

    def test_reactions_and_interactions_are_separate_files(self):
        self.logger.log_interaction(
            user_id='1', display_name='A', guild_id='1',
            mode='public', question='Q', response='R',
            error_type='', message_id='m1',
        )
        self.logger.log_reaction(
            message_id='m1', user_id='2', display_name='B', reaction='👍',
        )
        self.assertTrue(os.path.exists(self._interaction_path()))
        self.assertTrue(os.path.exists(self._reaction_path()))


if __name__ == '__main__':
    unittest.main()

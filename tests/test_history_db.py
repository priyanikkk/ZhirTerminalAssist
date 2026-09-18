import os
import tempfile
import unittest
from pathlib import Path
from zhirterminalassist.storage.history_db import HistoryDB

class TestHistoryDB(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_history.db"
        self.db = HistoryDB(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_conversations_and_messages(self):
        conv_id = self.db.create_conversation("Audio Troubleshooting")
        self.assertIsNotNone(conv_id)

        msg_id1 = self.db.add_message(conv_id, "user", "Почему нет звука?")
        msg_id2 = self.db.add_message(conv_id, "assistant", "Проверь PipeWire", ["pactl info"])

        messages = self.db.get_messages(conv_id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[1]["commands"], ["pactl info"])

    def test_command_executions(self):
        exec_id = self.db.record_execution(
            command="pactl info",
            status="SUCCESS",
            exit_code=0,
            output="Server String: /run/user/1000/pulse/native",
            error="",
            risk_level="SAFE"
        )
        self.assertIsNotNone(exec_id)

        executions = self.db.get_executions(limit=10)
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0]["command"], "pactl info")
        self.assertEqual(executions[0]["status"], "SUCCESS")

        # Search test
        search_res = self.db.get_executions(search="pactl")
        self.assertEqual(len(search_res), 1)
        no_res = self.db.get_executions(search="nonexistentcommandxyz")
        self.assertEqual(len(no_res), 0)

if __name__ == "__main__":
    unittest.main()

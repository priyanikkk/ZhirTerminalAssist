import os
import tempfile
import unittest
from zhirterminalassist.agent import AgentSession
from zhirterminalassist.terminal import TerminalUI

class TestTerminal(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.session = AgentSession(self.tmp_dir.name)
        self.ui = TerminalUI(self.session)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_slash_commands(self):
        # /help
        self.assertTrue(self.ui.handle_slash_command("/help"))
        # /status
        self.assertTrue(self.ui.handle_slash_command("/status"))
        # /commands
        self.assertTrue(self.ui.handle_slash_command("/commands"))
        # /files
        self.assertTrue(self.ui.handle_slash_command("/files"))
        # /diff
        self.assertTrue(self.ui.handle_slash_command("/diff"))
        # /model
        self.assertTrue(self.ui.handle_slash_command("/model"))
        self.assertTrue(self.ui.handle_slash_command("/model google/gemini-2.5-flash"))
        # /language
        self.assertTrue(self.ui.handle_slash_command("/language en"))
        self.assertTrue(self.ui.handle_slash_command("/language ru"))
        # /reset
        self.session.messages.append({"role": "user", "content": "hello"})
        self.assertTrue(self.ui.handle_slash_command("/reset"))
        self.assertEqual(len(self.session.messages), 0)
        # /exit
        self.assertFalse(self.ui.handle_slash_command("/exit"))
        self.assertFalse(self.ui.handle_slash_command("/quit"))

if __name__ == "__main__":
    unittest.main()

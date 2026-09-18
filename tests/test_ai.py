import unittest
from zhirterminalassist.ai import extract_bash_commands, AIClient
from zhirterminalassist.config import AppConfig

class TestAI(unittest.TestCase):
    def test_extract_commands(self):
        text = """
Suggested actions:
```bash
wpctl status
pactl info
```
And restart service:
```sh
systemctl --user restart pipewire
```
        """
        cmds = extract_bash_commands(text)
        self.assertEqual(cmds, [
            "wpctl status",
            "pactl info",
            "systemctl --user restart pipewire"
        ])

    def test_missing_api_key_error(self):
        cfg = AppConfig()
        cfg.data["provider"] = "openrouter"
        cfg.data["api_key"] = ""
        client = AIClient(cfg)
        resp = client.query("test question")
        self.assertFalse(resp.is_success)
        self.assertIn("API Key is not configured", resp.error_message)

if __name__ == "__main__":
    unittest.main()

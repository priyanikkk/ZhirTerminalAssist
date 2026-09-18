import unittest
from zhirterminalassist.ai.providers import extract_bash_commands, PROVIDERS
from zhirterminalassist.ai.client import AIClient
from zhirterminalassist.config import AppConfig

class TestAI(unittest.TestCase):
    def test_command_extraction(self):
        sample_response = """
Here is what you can do to check audio:
```bash
pactl info
systemctl --user status pipewire
```
Also try restarting wireplumber:
```sh
systemctl --user restart wireplumber
```
        """
        commands = extract_bash_commands(sample_response)
        self.assertEqual(commands, [
            "pactl info",
            "systemctl --user status pipewire",
            "systemctl --user restart wireplumber"
        ])

    def test_client_missing_key_graceful(self):
        cfg = AppConfig()
        cfg.data["ai_api_key"] = ""
        cfg.data["ai_provider"] = "openrouter"
        client = AIClient(cfg)
        resp = client.query("test query")
        self.assertFalse(resp.is_success)
        self.assertIn("API Key is missing", resp.error_message)

if __name__ == "__main__":
    unittest.main()

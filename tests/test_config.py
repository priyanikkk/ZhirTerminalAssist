import tempfile
import unittest
from pathlib import Path
from zhirterminalassist.config import AppConfig, mask_api_key

class TestConfig(unittest.TestCase):
    def test_mask_api_key(self):
        self.assertEqual(mask_api_key(""), "<not set>")
        self.assertEqual(mask_api_key("1234"), "****")
        self.assertEqual(mask_api_key("sk-abcdefgh12345678"), "sk-a...5678")

    def test_config_set_get(self):
        cfg = AppConfig()
        cfg.set("model", "custom-test-model")
        self.assertEqual(cfg.get("model"), "custom-test-model")

if __name__ == "__main__":
    unittest.main()

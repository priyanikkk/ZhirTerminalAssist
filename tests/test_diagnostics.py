import unittest
from zhirterminalassist.diagnostics import DiagnosticsRunner

class TestDiagnostics(unittest.TestCase):
    def test_run_all_diagnostics(self):
        results = DiagnosticsRunner.run_all()
        required_categories = [
            "Audio", "Network", "GPU", "Storage",
            "Packages", "Systemd", "Display", "Gaming"
        ]
        for cat in required_categories:
            self.assertIn(cat, results)
            self.assertIsInstance(results[cat], list)
            for item in results[cat]:
                self.assertIn(item.status, ["OK", "WARN", "FAIL"])

    def test_run_category_filter(self):
        res_audio = DiagnosticsRunner.run_category("audio")
        self.assertIn("Audio", res_audio)
        self.assertEqual(len(res_audio), 1)

        res_net = DiagnosticsRunner.run_category("network")
        self.assertIn("Network", res_net)

if __name__ == "__main__":
    unittest.main()

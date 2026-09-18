import unittest
from zhirterminalassist.system.diagnostics import DiagnosticsRunner

class TestDiagnostics(unittest.TestCase):
    def test_run_all_diagnostics(self):
        results = DiagnosticsRunner.run_all()
        required_categories = [
            "Audio", "Network", "GPU", "Storage",
            "Packages", "Services", "Display", "Gaming", "Permissions"
        ]
        for cat in required_categories:
            self.assertIn(cat, results)
            self.assertIsInstance(results[cat], list)
            for item in results[cat]:
                self.assertIn(item.status, ["OK", "WARN", "FAIL"])
                self.assertTrue(len(item.name) > 0)

    def test_format_report_markdown(self):
        report = DiagnosticsRunner.format_report_markdown()
        self.assertIn("# Linux System Diagnostics Report", report)
        self.assertIn("## Audio", report)
        self.assertIn("## Network", report)

if __name__ == "__main__":
    unittest.main()

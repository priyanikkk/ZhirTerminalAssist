import unittest
from zhirterminalassist.system.info import get_system_info, format_system_summary_for_ai, get_uptime_human

class TestSystemInfo(unittest.TestCase):
    def test_get_system_info(self):
        info = get_system_info()
        self.assertIsNotNone(info.os_name)
        self.assertIsNotNone(info.kernel)
        self.assertIsNotNone(info.arch)
        self.assertGreater(info.ram_total_gb, 0)
        self.assertGreater(info.cpu_cores_logical, 0)
        self.assertIsInstance(info.disks, list)
        self.assertIsInstance(info.gpus, list)
        self.assertIn(info.display_server.lower(), ["wayland", "x11", "tty/headless"])

    def test_uptime_human(self):
        self.assertIn("1h", get_uptime_human(3660))
        self.assertIn("1d", get_uptime_human(90000))

    def test_format_system_summary_for_ai(self):
        summary = format_system_summary_for_ai()
        self.assertIn("OS:", summary)
        self.assertIn("Kernel:", summary)
        self.assertIn("RAM:", summary)

if __name__ == "__main__":
    unittest.main()

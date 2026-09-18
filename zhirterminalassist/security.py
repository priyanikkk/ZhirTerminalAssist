import re
import shlex
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

class RiskLevel(str, Enum):
    SAFE = "SAFE"
    CONFIRM = "CONFIRM"
    DANGEROUS = "DANGEROUS"
    BLOCKED = "BLOCKED"

@dataclass
class CommandAnalysis:
    command: str
    risk_level: RiskLevel
    reason: str
    warning_message: str

BLOCKED_PATTERNS = [
    (r"\brm\s+(?:-[a-zA-Z]*[rR]|--recursive)\S*\s+/(?:\s|$|\*)", "Catastrophic: recursive deletion of root filesystem"),
    (r"\brm\s+(?:-[a-zA-Z]*[rR]|--recursive)\S*\s+~(?:\s|$)", "Catastrophic: recursive deletion of user home directory"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb: memory exhaustion crash"),
    (r"\bdd\s+.*of=/dev/(?:sd[a-z]|nvme[0-9]n[0-9]|vd[a-z])(?:\s|$)", "Direct raw whole-disk overwrite destroying partition tables"),
    (r"\bmkfs(?:\.\w+)?\s+/dev/(?:sd[a-z]|nvme[0-9]n[0-9]|vd[a-z])(?:\s|$)", "Formatting entire disk device rather than designated partition"),
    (r">\s*/dev/(?:sd[a-z]|nvme[0-9]n[0-9])(?:\s|$)", "Raw block device truncation"),
]

DANGEROUS_PATTERNS = [
    (r"\bcurl\b.*\|\s*(?:sh|bash|zsh)\b", "Piping remote unverified script directly into shell"),
    (r"\bwget\b.*\|\s*(?:sh|bash|zsh)\b", "Piping remote unverified script directly into shell"),
    (r"\brm\s+-[a-zA-Z]*[rR]", "Recursive file and directory deletion"),
    (r"\brm\b", "File or directory deletion"),
    (r"\brmdir\b", "Directory deletion"),
    (r"\bmkfs\b", "Filesystem formatting"),
    (r"\bdd\b", "Low-level bitstream manipulation"),
    (r"\bfdisk\b", "Disk partition table manipulation"),
    (r"\bparted\b", "Disk partition table manipulation"),
    (r"\bwipefs\b", "Filesystem signature erasing"),
    (r"\bchmod\s+-[a-zA-Z]*R", "Recursive permissions alteration"),
    (r"\bchown\s+-[a-zA-Z]*R", "Recursive ownership alteration"),
    (r"\bsystemctl\s+(?:disable|mask)\b", "Disabling or masking system service"),
    (r"\bpacman\s+-[a-zA-Z]*R", "Removing packages from Arch Linux"),
    (r"\bapt(?:-get)?\s+(?:remove|purge|autoremove)\b", "Removing packages from Debian/Ubuntu"),
    (r"\bdnf\s+(?:remove|erase)\b", "Removing packages from Fedora"),
    (r"\bzypper\s+(?:rm|remove)\b", "Removing packages from openSUSE"),
    (r"\bapk\s+del\b", "Removing packages from Alpine"),
]

CONFIRM_PATTERNS = [
    (r"\bchmod\b", "Modifying file permissions"),
    (r"\bchown\b", "Modifying file ownership"),
    (r"\bsystemctl\s+(?:stop|restart|isolate|poweroff|reboot)\b", "Service state modification or system reboot"),
    (r"\bpacman\s+-[a-zA-Z]*S", "Installing software packages"),
    (r"\bapt(?:-get)?\s+install\b", "Installing software packages"),
    (r"\bdnf\s+install\b", "Installing software packages"),
    (r"\bflatpak\s+install\b", "Installing Flatpak package"),
    (r"\bkill\b", "Process termination"),
    (r"\bkillall\b", "Process termination"),
    (r"\bpkill\b", "Process termination"),
    (r"\bsudo\b", "Command requires superuser privileges"),
]

SAFE_BINARIES = {
    "cat", "head", "tail", "less", "more", "grep", "ls", "dir", "tree", "file", "stat",
    "uname", "uptime", "hostname", "whoami", "id", "groups", "which", "whereis",
    "ps", "top", "htop", "btop", "free", "df", "du",
    "lspci", "lsusb", "lscpu", "lsblk", "inxi", "glxinfo", "vulkaninfo",
    "ip", "ping", "traceroute", "ss", "netstat", "curl -I",
    "systemctl status", "systemctl is-active", "systemctl --failed",
    "journalctl", "dmesg",
    "pactl info", "wpctl status", "pw-top", "alsamixer",
    "pacman -Q", "pacman -Ss", "pacman -Si",
    "apt list", "apt search", "apt show",
    "dnf list", "dnf search", "dnf info",
    "flatpak list", "flatpak search",
}

# Knowledge base for command explanation breakdown
COMMAND_FLAG_EXPLANATIONS: Dict[str, Dict[str, str]] = {
    "pacman": {
        "-S": "Synchronize/install packages from remote repositories",
        "-y": "Refresh package databases against servers",
        "-u": "Upgrade all out-of-date packages on the system",
        "-R": "Remove package",
        "-s": "Remove unneeded dependencies",
        "-n": "Do not save configuration backup files",
        "-Q": "Query local package database",
        "-Si": "Display detailed package information",
        "-Ss": "Search package repositories",
    },
    "apt": {
        "install": "Install one or more packages",
        "remove": "Remove packages",
        "purge": "Remove packages and their configuration files",
        "update": "Download package information from all configured sources",
        "upgrade": "Upgrade all installed packages to their newest versions",
        "autoremove": "Remove packages that were installed as dependencies and are no longer needed",
    },
    "chmod": {
        "-R": "Change files and directories recursively",
        "755": "Owner: read/write/execute (rwx), Group/Others: read/execute (r-x)",
        "644": "Owner: read/write (rw-), Group/Others: read-only (r--)",
        "600": "Owner: read/write (rw-), Group/Others: no access (---)",
        "777": "All users: read/write/execute (DANGEROUS)",
        "+x": "Make file executable for current user",
    },
    "systemctl": {
        "status": "Show terse runtime status information about one or more units",
        "start": "Start (activate) one or more units",
        "stop": "Stop (deactivate) one or more units",
        "restart": "Stop and then start one or more units",
        "enable": "Enable one or more units to start automatically at boot",
        "disable": "Disable one or more units from starting automatically at boot",
        "mask": "Mask one or more units to prevent starting under any circumstances",
        "--user": "Talk to the service manager of the calling user rather than the system",
        "--failed": "Show failed units only",
    },
    "rm": {
        "-r": "Remove directories and their contents recursively",
        "-R": "Remove directories and their contents recursively",
        "-f": "Ignore nonexistent files and arguments, never prompt before removal",
    }
}

class SecurityChecker:
    @staticmethod
    def analyze(command: str) -> CommandAnalysis:
        cleaned = command.strip()
        if not cleaned:
            return CommandAnalysis(command, RiskLevel.SAFE, "Empty command", "")

        # 1. Check BLOCKED
        for pattern, reason in BLOCKED_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                return CommandAnalysis(
                    command=command,
                    risk_level=RiskLevel.BLOCKED,
                    reason=reason,
                    warning_message=f"⛔ BLOCKED: {reason}"
                )

        # 2. Check DANGEROUS
        for pattern, reason in DANGEROUS_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                return CommandAnalysis(
                    command=command,
                    risk_level=RiskLevel.DANGEROUS,
                    reason=reason,
                    warning_message=f"⚠ DANGEROUS COMMAND: {reason}"
                )

        # 3. Check CONFIRM
        for pattern, reason in CONFIRM_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                return CommandAnalysis(
                    command=command,
                    risk_level=RiskLevel.CONFIRM,
                    reason=reason,
                    warning_message=f"Notice: {reason}"
                )

        # 4. Check SAFE
        for safe in SAFE_BINARIES:
            if cleaned.startswith(safe) and ">" not in cleaned and "|" not in cleaned:
                return CommandAnalysis(command, RiskLevel.SAFE, "Read-only inspection", "")

        if ">" in cleaned or "|" in cleaned:
            return CommandAnalysis(command, RiskLevel.CONFIRM, "Pipeline or redirection", "Pipeline requires review")

        return CommandAnalysis(command, RiskLevel.SAFE, "Standard command", "")

    @staticmethod
    def explain_command_local(cmd_str: str) -> Dict[str, Any]:
        """Provides local breakdown of binary, tokens and flags."""
        analysis = SecurityChecker.analyze(cmd_str)
        try:
            tokens = shlex.split(cmd_str)
        except Exception:
            tokens = cmd_str.split()

        breakdown = []
        skip_first = 0
        if tokens and tokens[0] == "sudo":
            breakdown.append(("sudo", "Run command with elevated superuser privileges."))
            skip_first = 1

        active_tokens = tokens[skip_first:]
        main_bin = active_tokens[0] if active_tokens else ""
        
        bin_desc = {
            "pacman": "Arch Linux package manager.",
            "apt": "Debian/Ubuntu Advanced Package Tool.",
            "dnf": "Fedora package manager.",
            "systemctl": "Control the systemd system and service manager.",
            "chmod": "Change file access permissions and modes.",
            "chown": "Change file owner and group.",
            "rm": "Remove files or directories.",
            "pactl": "Control a running PulseAudio/PipeWire sound server.",
            "wpctl": "WirePlumber session manager control tool.",
            "journalctl": "Query the systemd journal log.",
            "cat": "Concatenate files and print on the standard output.",
            "grep": "Print lines that match patterns.",
            "ls": "List directory contents.",
        }.get(main_bin, f"Linux system utility '{main_bin}'.")

        if main_bin:
            breakdown.append((main_bin, bin_desc))

        # Check subcommands & flags
        sub_dict = COMMAND_FLAG_EXPLANATIONS.get(main_bin, {})
        for token in active_tokens[1:]:
            if token in sub_dict:
                breakdown.append((token, sub_dict[token]))
            elif token.startswith("-") and not token.startswith("--") and len(token) > 2:
                # Combined flags e.g. -Syu or -rf
                for char in token[1:]:
                    flag = f"-{char}"
                    if flag in sub_dict:
                        breakdown.append((flag, sub_dict[flag]))
                    else:
                        breakdown.append((flag, f"Flag {flag}"))
            elif token in ("755", "644", "600", "777", "+x") and main_bin == "chmod":
                breakdown.append((token, sub_dict.get(token, "Permission mode argument.")))

        risk_rating = "Low"
        if analysis.risk_level == RiskLevel.BLOCKED:
            risk_rating = "Critical (Blocked)"
        elif analysis.risk_level == RiskLevel.DANGEROUS:
            risk_rating = "High (Dangerous)"
        elif analysis.risk_level == RiskLevel.CONFIRM:
            risk_rating = "Medium"

        return {
            "command": cmd_str,
            "breakdown": breakdown,
            "risk": risk_rating,
            "reason": analysis.reason,
            "analysis": analysis
        }

import re
import shlex
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

class RiskLevel(str, Enum):
    SAFE = "SAFE"
    CONFIRM = "CONFIRM"
    BLOCKED = "BLOCKED"

@dataclass
class CommandAnalysis:
    command: str
    risk_level: RiskLevel
    reason: str
    warning_message: str

# 1. BLOCKED PATTERNS (Catastrophic / Unrecoverable commands)
BLOCKED_PATTERNS = [
    (r"\brm\s+(?:-[a-zA-Z]*[rR]|--recursive)\S*\s+/(?:\s|$|\*)", "Catastrophic command: recursive deletion of root filesystem"),
    (r"\brm\s+(?:-[a-zA-Z]*[rR]|--recursive)\S*\s+~\s*$", "Catastrophic command: recursive deletion of entire user home directory"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb: crashes system memory"),
    (r"\bdd\s+.*of=/dev/(?:sd[a-z]|nvme[0-9]n[0-9]|vd[a-z]|mmcblk[0-9])(?:\s|$)", "Direct raw disk write that will destroy partitioning and file systems"),
    (r"\bmkfs(?:\.\w+)?\s+/dev/(?:sd[a-z]|nvme[0-9]n[0-9]|vd[a-z])(?:\s|$)", "Formatting entire disk device rather than a designated partition"),
    (r">\s*/dev/(?:sd[a-z]|nvme[0-9]n[0-9]|null)\s*$", "Direct raw device truncation"),
    (r"\bchmod\s+-[a-zA-Z]*R\w*\s+777\s+/(?:\s|$)", "Global recursive permission destruction on root"),
]

# 2. SENSITIVE COMMANDS REQUIRING CONFIRMATION
CONFIRM_PATTERNS = [
    # File removals
    (r"\brm\b", "File or directory deletion"),
    (r"\brmdir\b", "Directory deletion"),
    (r"\bunlink\b", "File unlinking"),
    (r"\bshred\b", "Permanent file shredding"),
    
    # Disk & filesystem manipulation
    (r"\bmkfs\b", "Filesystem creation/formatting"),
    (r"\bdd\b", "Low-level data duplication/write"),
    (r"\bfdisk\b", "Disk partition table manipulation"),
    (r"\bparted\b", "Disk partition editing"),
    (r"\bgdisk\b", "GPT partition table editing"),
    (r"\bwipefs\b", "Filesystem signature wiping"),
    (r"\bmkswap\b", "Swap space initialization"),
    
    # Permissions & ownership
    (r"\bchmod\s+-[a-zA-Z]*R", "Recursive permission modification"),
    (r"\bchown\s+-[a-zA-Z]*R", "Recursive ownership modification"),
    (r"\bchmod\b", "File permission modification"),
    (r"\bchown\b", "File ownership modification"),
    
    # Service control
    (r"\bsystemctl\s+(?:disable|mask|stop|restart|poweroff|reboot|isolate)", "System service disruption or shutdown"),
    
    # Package management removals and system upgrades
    (r"\bpacman\s+-[a-zA-Z]*R", "Pacman package removal"),
    (r"\bpacman\s+-[a-zA-Z]*S(?:yu|u|y)?\b", "Pacman package installation or system upgrade"),
    (r"\byay\s+-[a-zA-Z]*[RS]", "AUR package installation/removal"),
    (r"\bparu\s+-[a-zA-Z]*[RS]", "AUR package installation/removal"),
    (r"\bapt\s+(?:remove|purge|autoremove|install|upgrade|dist-upgrade)\b", "APT package installation or removal"),
    (r"\bapt-get\s+(?:remove|purge|autoremove|install|dist-upgrade)\b", "APT package installation or removal"),
    (r"\bdnf\s+(?:remove|erase|install|upgrade)\b", "DNF package installation or removal"),
    (r"\bzypper\s+(?:rm|remove|in|install|dup)\b", "Zypper package installation or removal"),
    (r"\bflatpak\s+(?:uninstall|install|update)\b", "Flatpak application install/removal"),
    (r"\bsnap\s+(?:remove|install|refresh)\b", "Snap package install/removal"),
    
    # Process killing
    (r"\bkill\b", "Process termination signal"),
    (r"\bkillall\b", "Multiple process termination"),
    (r"\bpkill\b", "Process termination by pattern"),
    
    # Kernel, modules, and hardware
    (r"\bmodprobe\s+-[a-zA-Z]*r", "Kernel module removal"),
    (r"\brmmod\b", "Kernel module removal"),
    (r"\binsmod\b", "Kernel module insertion"),
    
    # System power state
    (r"\breboot\b", "System reboot"),
    (r"\bshutdown\b", "System shutdown"),
    (r"\bpoweroff\b", "System power off"),
    (r"\binit\s+[06]\b", "System state change to halt/reboot"),

    # Sudo usage
    (r"\bsudo\b", "Command requires superuser privileges"),
]

# 3. SAFE READ-ONLY COMMAND PREFIXES
SAFE_COMMAND_BINARIES = {
    "cat", "head", "tail", "less", "more", "grep", "egrep", "fgrep",
    "ls", "dir", "tree", "find", "locate", "which", "whereis", "file",
    "stat", "wc", "sort", "uniq", "diff", "echo", "printf",
    "uname", "uptime", "hostname", "whoami", "id", "groups", "w", "who",
    "ps", "pstree", "top", "htop", "btop", "free", "df", "du",
    "lspci", "lsusb", "lscpu", "lsblk", "lshw", "inxi", "glxinfo", "vulkaninfo",
    "ip", "ifconfig", "ping", "traceroute", "mtr", "ss", "netstat",
    "dig", "nslookup", "host", "curl", "wget",
    "systemctl status", "systemctl is-active", "systemctl is-enabled", "systemctl --failed",
    "journalctl", "dmesg",
    "pactl info", "pactl list", "wpctl status", "pw-top", "pw-dump", "alsamixer",
    "pacman -Q", "pacman -Ss", "pacman -Si",
    "apt list", "apt search", "apt show", "apt-cache",
    "dnf list", "dnf search", "dnf info",
    "flatpak list", "flatpak search",
}

class SecurityChecker:
    @staticmethod
    def analyze(cmd: str) -> CommandAnalysis:
        cleaned_cmd = cmd.strip()
        if not cleaned_cmd:
            return CommandAnalysis(
                command=cmd,
                risk_level=RiskLevel.SAFE,
                reason="Empty command",
                warning_message=""
            )

        # 1. Check for BLOCKED patterns
        for pattern, reason in BLOCKED_PATTERNS:
            if re.search(pattern, cleaned_cmd, re.IGNORECASE):
                return CommandAnalysis(
                    command=cmd,
                    risk_level=RiskLevel.BLOCKED,
                    reason=reason,
                    warning_message=f"⛔ BLOCKED: This command was prevented from executing because it can cause catastrophic, unrecoverable data loss or system failure: {reason}"
                )

        # 2. Check for CONFIRM patterns
        for pattern, reason in CONFIRM_PATTERNS:
            if re.search(pattern, cleaned_cmd, re.IGNORECASE):
                return CommandAnalysis(
                    command=cmd,
                    risk_level=RiskLevel.CONFIRM,
                    reason=reason,
                    warning_message=f"⚠ REQUIRES CONFIRMATION: {reason}"
                )

        # 3. Check if safe read-only
        # Tokenize basic command
        try:
            tokens = shlex.split(cleaned_cmd)
        except Exception:
            tokens = cleaned_cmd.split()

        base_bin = tokens[0] if tokens else ""
        if "/" in base_bin:
            base_bin = base_bin.split("/")[-1]

        # Check if safe
        for safe in SAFE_COMMAND_BINARIES:
            if cleaned_cmd.startswith(safe) or base_bin == safe:
                # Make sure there is no output redirection like > or >>
                if ">" not in cleaned_cmd and "|" not in cleaned_cmd:
                    return CommandAnalysis(
                        command=cmd,
                        risk_level=RiskLevel.SAFE,
                        reason="Read-only inspection command",
                        warning_message=""
                    )

        # If it contains pipes or redirections or unknown binary, request confirmation
        if ">" in cleaned_cmd or "|" in cleaned_cmd or base_bin not in SAFE_COMMAND_BINARIES:
            return CommandAnalysis(
                command=cmd,
                risk_level=RiskLevel.CONFIRM,
                reason="Command modifies system state, writes to files, or contains pipelines",
                warning_message="⚠ REQUIRES CONFIRMATION: Modifying command or shell pipeline"
            )

        return CommandAnalysis(
            command=cmd,
            risk_level=RiskLevel.SAFE,
            reason="Standard read-only diagnostic",
            warning_message=""
        )

import os
import shutil
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import psutil

@dataclass
class CheckResult:
    name: str
    status: str  # "OK", "WARN", "FAIL"
    details: str
    command: Optional[str] = None
    suggested_action: Optional[str] = None

def run_cmd(cmd: List[str], timeout: int = 3) -> Tuple[int, str, str]:
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

# Compatibility helper
from typing import Tuple

class DiagnosticsRunner:
    @staticmethod
    def check_audio() -> List[CheckResult]:
        results = []
        
        # Pipewire check
        if shutil.which("pipewire"):
            code, out, _ = run_cmd(["systemctl", "--user", "is-active", "pipewire"])
            if out == "active":
                results.append(CheckResult("PipeWire Server", "OK", "PipeWire daemon is active and running."))
            else:
                results.append(CheckResult("PipeWire Server", "FAIL", f"PipeWire daemon is {out or 'inactive'}", 
                                           command="systemctl --user restart pipewire",
                                           suggested_action="Start PipeWire service"))
        else:
            results.append(CheckResult("PipeWire Binary", "WARN", "PipeWire binary not found in PATH."))

        # WirePlumber check
        if shutil.which("wireplumber"):
            code, out, _ = run_cmd(["systemctl", "--user", "is-active", "wireplumber"])
            if out == "active":
                results.append(CheckResult("WirePlumber Session Manager", "OK", "WirePlumber is active."))
            else:
                results.append(CheckResult("WirePlumber Session Manager", "WARN", f"WirePlumber state: {out or 'inactive'}",
                                           command="systemctl --user restart wireplumber",
                                           suggested_action="Restart WirePlumber session manager"))

        # Audio devices via /proc/asound/cards or pactl
        asound_cards = Path("/proc/asound/cards")
        if asound_cards.exists():
            content = asound_cards.read_text().strip()
            if content:
                card_count = sum(1 for line in content.splitlines() if line.strip() and line[0].isdigit())
                results.append(CheckResult("Sound Cards (ALSA)", "OK", f"Detected {card_count} sound card(s)."))
            else:
                results.append(CheckResult("Sound Cards (ALSA)", "FAIL", "No sound cards listed in /proc/asound/cards",
                                           suggested_action="Check kernel modules for audio (snd_hda_intel, snd_soc_...)"))
        
        # Audio Server Default Sink
        if shutil.which("pactl"):
            code, out, _ = run_cmd(["pactl", "get-default-sink"])
            if code == 0 and out:
                results.append(CheckResult("Default Audio Output", "OK", f"Sink: {out}"))
            else:
                results.append(CheckResult("Default Audio Output", "WARN", "No default audio sink configured.",
                                           command="pactl list sinks short",
                                           suggested_action="Select output device in volume control"))
        return results

    @staticmethod
    def check_network() -> List[CheckResult]:
        results = []
        
        # Default route
        has_gateway = False
        try:
            gateways = psutil.net_if_stats()
            has_up = any(stat.isup for iface, stat in gateways.items() if iface != "lo")
            if has_up:
                has_gateway = True
        except Exception:
            pass

        if has_gateway:
            results.append(CheckResult("Network Interface", "OK", "Active network interfaces found."))
        else:
            results.append(CheckResult("Network Interface", "FAIL", "No active non-loopback network interfaces.",
                                       command="ip link",
                                       suggested_action="Enable WiFi or plug in Ethernet"))

        # DNS Resolution test
        dns_ok = False
        try:
            socket.setdefaulttimeout(3)
            socket.gethostbyname("archlinux.org")
            dns_ok = True
        except Exception:
            pass

        if dns_ok:
            results.append(CheckResult("DNS Resolution", "OK", "Domain names resolve properly (archlinux.org)."))
        else:
            results.append(CheckResult("DNS Resolution", "FAIL", "Failed to resolve DNS queries.",
                                       command="cat /etc/resolv.conf",
                                       suggested_action="Check nameserver in /etc/resolv.conf or restart systemd-resolved"))

        # Internet reachability (ping)
        if shutil.which("ping"):
            code, _, _ = run_cmd(["ping", "-c", "1", "-W", "2", "1.1.1.1"])
            if code == 0:
                results.append(CheckResult("Internet Connectivity", "OK", "Ping to 1.1.1.1 succeeded."))
            else:
                results.append(CheckResult("Internet Connectivity", "WARN", "Could not ping 1.1.1.1. Firewall or offline?"))

        return results

    @staticmethod
    def check_gpu() -> List[CheckResult]:
        results = []
        from zhirterminalassist.system.info import get_gpus
        gpus = get_gpus()
        if gpus and "Generic" not in gpus[0]:
            results.append(CheckResult("GPU Hardware", "OK", "; ".join(gpus)))
        else:
            results.append(CheckResult("GPU Hardware", "WARN", "Could not identify dedicated GPU."))

        # Vulkan check
        if shutil.which("vulkaninfo"):
            code, out, _ = run_cmd(["vulkaninfo", "--summary"])
            if code == 0:
                results.append(CheckResult("Vulkan Support", "OK", "Vulkan loader and devices operational."))
            else:
                results.append(CheckResult("Vulkan Support", "FAIL", "vulkaninfo failed. Missing ICD or driver?",
                                           command="vulkaninfo --summary",
                                           suggested_action="Install vulkan-radeon / vulkan-intel / nvidia-utils"))
        else:
            results.append(CheckResult("Vulkan Loader", "WARN", "vulkaninfo not installed. Check package vulkan-tools."))

        # OpenGL / Mesa
        if shutil.which("glxinfo"):
            code, out, _ = run_cmd(["glxinfo", "-B"])
            if code == 0:
                dev = "Mesa/OpenGL active"
                for line in out.splitlines():
                    if "Device:" in line:
                        dev = line.strip()
                        break
                results.append(CheckResult("OpenGL Acceleration", "OK", dev))
            else:
                results.append(CheckResult("OpenGL Acceleration", "WARN", "glxinfo returned an error."))
        return results

    @staticmethod
    def check_storage() -> List[CheckResult]:
        results = []
        try:
            root_usage = psutil.disk_usage("/")
            if root_usage.percent > 92:
                results.append(CheckResult("Root Partition (/)", "FAIL", 
                                           f"Critical space: {root_usage.percent}% used ({round(root_usage.free/(1024**3), 2)} GB free)",
                                           suggested_action="Clean pacman/apt cache or delete unused files"))
            elif root_usage.percent > 80:
                results.append(CheckResult("Root Partition (/)", "WARN", 
                                           f"High disk usage: {root_usage.percent}% used ({round(root_usage.free/(1024**3), 2)} GB free)"))
            else:
                results.append(CheckResult("Root Partition (/)", "OK", 
                                           f"{root_usage.percent}% used ({round(root_usage.free/(1024**3), 2)} GB free)"))
        except Exception as e:
            results.append(CheckResult("Root Partition (/)", "WARN", str(e)))

        # Inodes check
        try:
            code, out, _ = run_cmd(["df", "-i", "/"])
            if code == 0:
                lines = out.splitlines()
                if len(lines) > 1:
                    parts = lines[1].split()
                    i_use = parts[4]
                    results.append(CheckResult("Inode Allocation", "OK", f"Root inodes used: {i_use}"))
        except Exception:
            pass

        return results

    @staticmethod
    def check_packages() -> List[CheckResult]:
        results = []
        # Check Pacman lock
        pacman_lock = Path("/var/lib/pacman/db.lck")
        if pacman_lock.exists():
            results.append(CheckResult("Pacman Lock", "FAIL", "Lock file /var/lib/pacman/db.lck exists!",
                                       command="sudo rm /var/lib/pacman/db.lck",
                                       suggested_action="Remove lock if no other pacman process is running"))
        elif shutil.which("pacman"):
            results.append(CheckResult("Pacman Lock", "OK", "Database is not locked."))

        # Check for broken dependencies or corrupted pacman DB
        if shutil.which("pacman"):
            results.append(CheckResult("Package Manager (Pacman)", "OK", "Arch pacman available."))
        elif shutil.which("apt"):
            results.append(CheckResult("Package Manager (APT)", "OK", "Debian/Ubuntu apt available."))
        elif shutil.which("dnf"):
            results.append(CheckResult("Package Manager (DNF)", "OK", "Fedora dnf available."))
        return results

    @staticmethod
    def check_services() -> List[CheckResult]:
        results = []
        if shutil.which("systemctl"):
            code, out, _ = run_cmd(["systemctl", "--failed", "--no-legend"])
            if out:
                failed_units = [line.split()[1] for line in out.splitlines() if line.strip()]
                results.append(CheckResult("Systemd System Units", "FAIL", 
                                           f"Failed units: {', '.join(failed_units)}",
                                           command="systemctl --failed",
                                           suggested_action="Inspect logs: journalctl -u <unit> -xe"))
            else:
                results.append(CheckResult("Systemd System Units", "OK", "0 failed system units."))

            code, out, _ = run_cmd(["systemctl", "--user", "--failed", "--no-legend"])
            if out:
                failed_user = [line.split()[1] for line in out.splitlines() if line.strip()]
                results.append(CheckResult("Systemd User Units", "WARN", 
                                           f"Failed user units: {', '.join(failed_user)}",
                                           command="systemctl --user --failed",
                                           suggested_action="Inspect logs: journalctl --user -u <unit> -xe"))
            else:
                results.append(CheckResult("Systemd User Units", "OK", "0 failed user units."))
        else:
            results.append(CheckResult("Init System", "WARN", "systemctl not found."))
        return results

    @staticmethod
    def check_display() -> List[CheckResult]:
        results = []
        sess_type = os.environ.get("XDG_SESSION_TYPE", "unknown")
        de = os.environ.get("XDG_CURRENT_DESKTOP", "unknown")
        results.append(CheckResult("Session Server", "OK", f"Protocol: {sess_type}, Desktop: {de}"))

        if sess_type == "wayland":
            if os.environ.get("WAYLAND_DISPLAY"):
                results.append(CheckResult("Wayland Socket", "OK", f"Socket: {os.environ.get('WAYLAND_DISPLAY')}"))
            else:
                results.append(CheckResult("Wayland Socket", "WARN", "WAYLAND_DISPLAY variable is empty."))
        return results

    @staticmethod
    def check_gaming() -> List[CheckResult]:
        results = []
        # Steam
        if shutil.which("steam"):
            results.append(CheckResult("Steam Client", "OK", "Steam is installed in PATH."))
        else:
            results.append(CheckResult("Steam Client", "WARN", "Steam binary not detected in PATH."))

        # GameMode
        if shutil.which("gamemoded"):
            code, out, _ = run_cmd(["gamemoded", "-s"])
            results.append(CheckResult("Feral GameMode", "OK", f"GameMode daemon is available: {out}"))
        else:
            results.append(CheckResult("Feral GameMode", "WARN", "GameMode not installed (optional performance booster)."))

        # Wine
        if shutil.which("wine"):
            code, out, _ = run_cmd(["wine", "--version"])
            results.append(CheckResult("Wine Compatibility Layer", "OK", f"Version: {out}"))
        else:
            results.append(CheckResult("Wine Compatibility Layer", "WARN", "Wine is not installed."))

        return results

    @staticmethod
    def check_permissions() -> List[CheckResult]:
        results = []
        user = os.environ.get("USER", "unknown")
        results.append(CheckResult("Current User", "OK", f"Running as: {user} (UID: {os.getuid()})"))

        # Check groups
        try:
            import grp
            groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
            key_groups = [g for g in ["wheel", "sudo", "audio", "video", "input", "docker", "storage"] if g in groups]
            results.append(CheckResult("Group Membership", "OK", f"Privilege groups: {', '.join(key_groups) or 'standard user'}"))
        except Exception:
            pass

        return results

    @classmethod
    def run_all(cls) -> Dict[str, List[CheckResult]]:
        return {
            "Audio": cls.check_audio(),
            "Network": cls.check_network(),
            "GPU": cls.check_gpu(),
            "Storage": cls.check_storage(),
            "Packages": cls.check_packages(),
            "Services": cls.check_services(),
            "Display": cls.check_display(),
            "Gaming": cls.check_gaming(),
            "Permissions": cls.check_permissions(),
        }

    @classmethod
    def format_report_markdown(cls, diagnostics: Optional[Dict[str, List[CheckResult]]] = None) -> str:
        if diagnostics is None:
            diagnostics = cls.run_all()
        
        md = ["# Linux System Diagnostics Report\n"]
        for cat, items in diagnostics.items():
            md.append(f"## {cat}")
            for item in items:
                icon = "✓" if item.status == "OK" else ("⚠" if item.status == "WARN" else "✗")
                md.append(f"- **[{icon} {item.status}] {item.name}**: {item.details}")
                if item.suggested_action:
                    md.append(f"  - *Suggestion*: {item.suggested_action}")
                if item.command:
                    md.append(f"  - *Command*: `{item.command}`")
            md.append("")
        return "\n".join(md)

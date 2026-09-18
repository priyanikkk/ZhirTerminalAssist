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
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

class DiagnosticsRunner:
    @staticmethod
    def check_audio() -> List[CheckResult]:
        results = []
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

        if shutil.which("wireplumber"):
            code, out, _ = run_cmd(["systemctl", "--user", "is-active", "wireplumber"])
            if out == "active":
                results.append(CheckResult("WirePlumber Session Manager", "OK", "WirePlumber is active."))
            else:
                results.append(CheckResult("WirePlumber Session Manager", "WARN", f"WirePlumber state: {out or 'inactive'}",
                                           command="systemctl --user restart wireplumber",
                                           suggested_action="Restart WirePlumber session manager"))

        asound_cards = Path("/proc/asound/cards")
        if asound_cards.exists():
            content = asound_cards.read_text().strip()
            if content:
                card_count = sum(1 for line in content.splitlines() if line.strip() and line[0].isdigit())
                results.append(CheckResult("Sound Cards (ALSA)", "OK", f"Detected {card_count} sound card(s)."))
            else:
                results.append(CheckResult("Sound Cards (ALSA)", "FAIL", "No sound cards listed in /proc/asound/cards"))

        if shutil.which("pactl"):
            code, out, _ = run_cmd(["pactl", "get-default-sink"])
            if code == 0 and out:
                results.append(CheckResult("Default Audio Output", "OK", f"Sink: {out}"))
            else:
                results.append(CheckResult("Default Audio Output", "WARN", "No default audio sink configured.",
                                           command="pactl list sinks short"))
        return results

    @staticmethod
    def check_network() -> List[CheckResult]:
        results = []
        has_gateway = False
        try:
            gateways = psutil.net_if_stats()
            has_gateway = any(stat.isup for iface, stat in gateways.items() if iface != "lo")
        except Exception:
            pass

        if has_gateway:
            results.append(CheckResult("Network Interface", "OK", "Active network interfaces found."))
        else:
            results.append(CheckResult("Network Interface", "FAIL", "No active non-loopback network interfaces.",
                                       command="ip link", suggested_action="Enable WiFi or connect Ethernet"))

        dns_ok = False
        try:
            socket.setdefaulttimeout(3)
            socket.gethostbyname("archlinux.org")
            dns_ok = True
        except Exception:
            pass

        if dns_ok:
            results.append(CheckResult("DNS Resolution", "OK", "Domain names resolve properly."))
        else:
            results.append(CheckResult("DNS Resolution", "FAIL", "Failed to resolve DNS queries.",
                                       command="cat /etc/resolv.conf"))

        if shutil.which("ping"):
            code, _, _ = run_cmd(["ping", "-c", "1", "-W", "2", "1.1.1.1"])
            if code == 0:
                results.append(CheckResult("Internet Reachability", "OK", "Ping to 1.1.1.1 succeeded."))
            else:
                results.append(CheckResult("Internet Reachability", "WARN", "Could not ping 1.1.1.1."))
        return results

    @staticmethod
    def check_gpu() -> List[CheckResult]:
        results = []
        from zhirterminalassist.system import get_gpus
        gpus = get_gpus()
        if gpus and "Generic" not in gpus[0]:
            results.append(CheckResult("GPU Hardware", "OK", "; ".join(gpus)))
        else:
            results.append(CheckResult("GPU Hardware", "WARN", "Could not identify dedicated GPU."))

        if shutil.which("vulkaninfo"):
            code, _, _ = run_cmd(["vulkaninfo", "--summary"])
            if code == 0:
                results.append(CheckResult("Vulkan Loader", "OK", "Vulkan operational."))
            else:
                results.append(CheckResult("Vulkan Loader", "FAIL", "vulkaninfo failed. Missing ICD or driver?",
                                           command="vulkaninfo --summary"))
        else:
            results.append(CheckResult("Vulkan Loader", "WARN", "vulkaninfo not found (package: vulkan-tools)."))

        if shutil.which("glxinfo"):
            code, out, _ = run_cmd(["glxinfo", "-B"])
            if code == 0:
                dev = "Mesa / OpenGL active"
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
            root_u = psutil.disk_usage("/")
            free_gb = round(root_u.free / (1024**3), 1)
            if root_u.percent > 92:
                results.append(CheckResult("Root Partition (/)", "FAIL",
                                           f"Critical space: {root_u.percent}% used ({free_gb} GB free)",
                                           suggested_action="Clean pacman/apt cache"))
            elif root_u.percent > 80:
                results.append(CheckResult("Root Partition (/)", "WARN",
                                           f"High disk usage: {root_u.percent}% used ({free_gb} GB free)"))
            else:
                results.append(CheckResult("Root Partition (/)", "OK",
                                           f"{root_u.percent}% used ({free_gb} GB free)"))
        except Exception as e:
            results.append(CheckResult("Root Partition (/)", "WARN", str(e)))
        return results

    @staticmethod
    def check_systemd() -> List[CheckResult]:
        results = []
        if shutil.which("systemctl"):
            code, out, _ = run_cmd(["systemctl", "--failed", "--no-legend"])
            if out:
                failed = [line.split()[1] for line in out.splitlines() if line.strip()]
                results.append(CheckResult("System Units", "FAIL", f"Failed units: {', '.join(failed)}",
                                           command="systemctl --failed",
                                           suggested_action="Inspect logs: journalctl -u <unit> -xe"))
            else:
                results.append(CheckResult("System Units", "OK", "0 failed system units."))

            code, out, _ = run_cmd(["systemctl", "--user", "--failed", "--no-legend"])
            if out:
                failed_u = [line.split()[1] for line in out.splitlines() if line.strip()]
                results.append(CheckResult("User Units", "WARN", f"Failed user units: {', '.join(failed_u)}",
                                           command="systemctl --user --failed"))
            else:
                results.append(CheckResult("User Units", "OK", "0 failed user units."))
        else:
            results.append(CheckResult("Systemd Init", "WARN", "systemctl not found."))
        return results

    @staticmethod
    def check_packages() -> List[CheckResult]:
        results = []
        pacman_lock = Path("/var/lib/pacman/db.lck")
        if pacman_lock.exists():
            results.append(CheckResult("Pacman Lock", "FAIL", "Lock file /var/lib/pacman/db.lck exists!",
                                       command="sudo rm /var/lib/pacman/db.lck",
                                       suggested_action="Remove lock if no other pacman process is running"))
        elif shutil.which("pacman"):
            results.append(CheckResult("Pacman Database", "OK", "Database lock free."))

        for pm in ["pacman", "apt", "dnf", "zypper", "apk", "flatpak"]:
            if shutil.which(pm):
                results.append(CheckResult(f"Package Manager ({pm})", "OK", f"Available: {shutil.which(pm)}"))
                break
        return results

    @staticmethod
    def check_display() -> List[CheckResult]:
        results = []
        sess = os.environ.get("XDG_SESSION_TYPE", "unknown")
        de = os.environ.get("XDG_CURRENT_DESKTOP", "unknown")
        results.append(CheckResult("Display Session", "OK", f"Protocol: {sess}, Desktop: {de}"))
        if sess == "wayland":
            w_disp = os.environ.get("WAYLAND_DISPLAY")
            if w_disp:
                results.append(CheckResult("Wayland Socket", "OK", f"Socket: {w_disp}"))
            else:
                results.append(CheckResult("Wayland Socket", "WARN", "WAYLAND_DISPLAY variable empty."))
        return results

    @staticmethod
    def check_gaming() -> List[CheckResult]:
        results = []
        if shutil.which("steam"):
            results.append(CheckResult("Steam Client", "OK", "Steam binary detected."))
        else:
            results.append(CheckResult("Steam Client", "WARN", "Steam is not installed."))

        if shutil.which("gamemoded"):
            code, out, _ = run_cmd(["gamemoded", "-s"])
            results.append(CheckResult("Feral GameMode", "OK", f"GameMode status: {out}"))
        else:
            results.append(CheckResult("Feral GameMode", "WARN", "GameMode daemon not installed."))

        if shutil.which("wine"):
            code, out, _ = run_cmd(["wine", "--version"])
            results.append(CheckResult("Wine Layer", "OK", f"Wine version: {out}"))
        else:
            results.append(CheckResult("Wine Layer", "WARN", "Wine is not installed."))
        return results

    @classmethod
    def run_category(cls, category: str) -> Dict[str, List[CheckResult]]:
        cat = category.lower().strip()
        if cat in ("1", "audio"):
            return {"Audio": cls.check_audio()}
        elif cat in ("2", "network", "net"):
            return {"Network": cls.check_network()}
        elif cat in ("3", "gpu", "graphics"):
            return {"GPU": cls.check_gpu()}
        elif cat in ("4", "storage", "disk", "disks"):
            return {"Storage": cls.check_storage()}
        elif cat in ("5", "systemd", "services"):
            return {"Systemd": cls.check_systemd()}
        elif cat in ("6", "packages", "pkg"):
            return {"Packages": cls.check_packages()}
        elif cat in ("7", "display", "de"):
            return {"Display": cls.check_display()}
        elif cat in ("8", "gaming", "games"):
            return {"Gaming": cls.check_gaming()}
        else:
            return cls.run_all()

    @classmethod
    def run_all(cls) -> Dict[str, List[CheckResult]]:
        return {
            "Audio": cls.check_audio(),
            "Network": cls.check_network(),
            "GPU": cls.check_gpu(),
            "Storage": cls.check_storage(),
            "Systemd": cls.check_systemd(),
            "Packages": cls.check_packages(),
            "Display": cls.check_display(),
            "Gaming": cls.check_gaming(),
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
                    md.append(f"  - Action: {item.suggested_action}")
                if item.command:
                    md.append(f"  - Command: `{item.command}`")
            md.append("")
        return "\n".join(md)

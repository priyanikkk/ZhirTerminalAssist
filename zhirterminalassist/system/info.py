import os
import platform
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import psutil

@dataclass
class SystemInfo:
    os_name: str
    os_pretty_name: str
    os_id: str
    os_id_like: str
    kernel: str
    arch: str
    hostname: str
    uptime_seconds: float
    uptime_human: str
    cpu_model: str
    cpu_cores_physical: int
    cpu_cores_logical: int
    cpu_usage_percent: float
    ram_total_gb: float
    ram_used_gb: float
    ram_available_gb: float
    ram_percent: float
    swap_total_gb: float
    swap_used_gb: float
    swap_percent: float
    disks: List[Dict[str, Any]]
    gpus: List[str]
    shell: str
    desktop_environment: str
    display_server: str
    available_package_managers: List[str]
    available_tools: Dict[str, bool]

def get_os_release() -> Dict[str, str]:
    info = {
        "NAME": "Linux",
        "PRETTY_NAME": "Linux",
        "ID": "linux",
        "ID_LIKE": ""
    }
    os_release_path = Path("/etc/os-release")
    if not os_release_path.exists():
        os_release_path = Path("/usr/lib/os-release")
        
    if os_release_path.exists():
        try:
            with open(os_release_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    info[k] = v.strip('"\'')
        except Exception:
            pass
    return info

def get_cpu_model() -> str:
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or "Unknown CPU"

def get_gpus() -> List[str]:
    gpus = []
    # 1. Try lspci
    if shutil.which("lspci"):
        try:
            res = subprocess.run(
                ["lspci"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3
            )
            for line in res.stdout.splitlines():
                if "VGA compatible controller" in line or "3D controller" in line:
                    parts = line.split(":", 2)
                    if len(parts) >= 3:
                        gpus.append(parts[2].strip())
                    else:
                        gpus.append(line.strip())
        except Exception:
            pass

    # 2. Try nvidia-smi if nvidia
    if not gpus and shutil.which("nvidia-smi"):
        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3
            )
            for line in res.stdout.splitlines():
                line = line.strip()
                if line and line not in gpus:
                    gpus.append(line)
        except Exception:
            pass

    # 3. Fallback: check /sys/class/drm
    if not gpus:
        drm_path = Path("/sys/class/drm")
        if drm_path.exists():
            for card in drm_path.glob("card[0-9]"):
                device_path = card / "device"
                if device_path.exists():
                    gpus.append(f"DRM Device ({card.name})")

    return gpus or ["Generic Linux Display / GPU"]

def get_uptime_human(seconds: float) -> str:
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)

def get_disks_info() -> List[Dict[str, Any]]:
    disks = []
    seen_mounts = set()
    try:
        for part in psutil.disk_partitions(all=False):
            if part.mountpoint in seen_mounts:
                continue
            # Skip snap, loop, docker mounts
            if any(part.mountpoint.startswith(p) for p in ["/var/lib/docker", "/snap", "/var/lib/flatpak/runtime"]):
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                seen_mounts.add(part.mountpoint)
                disks.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent": usage.percent
                })
            except (PermissionError, FileNotFoundError):
                continue
    except Exception:
        pass
    return disks

def get_system_info(refresh_cpu: bool = False) -> SystemInfo:
    os_info = get_os_release()
    boot_time = psutil.boot_time()
    uptime_sec = time.time() - boot_time

    # Memory
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # Tools check
    tools_to_check = [
        "pacman", "yay", "paru", "apt", "dnf", "zypper", "flatpak", "snap",
        "systemctl", "journalctl", "pactl", "wpctl", "pipewire",
        "vulkaninfo", "glxinfo", "lspci", "ip", "ping", "nmcli"
    ]
    available_tools = {tool: shutil.which(tool) is not None for tool in tools_to_check}

    package_managers = [
        pm for pm in ["pacman", "yay", "paru", "apt", "dnf", "zypper", "flatpak", "snap"]
        if available_tools.get(pm, False)
    ]

    # Display server & Desktop
    display_server = os.environ.get("XDG_SESSION_TYPE", "")
    if not display_server:
        if os.environ.get("WAYLAND_DISPLAY"):
            display_server = "wayland"
        elif os.environ.get("DISPLAY"):
            display_server = "x11"
        else:
            display_server = "tty/headless"

    desktop_env = os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION") or "Unknown"

    cpu_perc = psutil.cpu_percent(interval=0.1 if refresh_cpu else None)

    return SystemInfo(
        os_name=os_info.get("NAME", "Linux"),
        os_pretty_name=os_info.get("PRETTY_NAME", "Linux"),
        os_id=os_info.get("ID", "linux"),
        os_id_like=os_info.get("ID_LIKE", ""),
        kernel=platform.release(),
        arch=platform.machine(),
        hostname=platform.node(),
        uptime_seconds=uptime_sec,
        uptime_human=get_uptime_human(uptime_sec),
        cpu_model=get_cpu_model(),
        cpu_cores_physical=psutil.cpu_count(logical=False) or 1,
        cpu_cores_logical=psutil.cpu_count(logical=True) or 1,
        cpu_usage_percent=cpu_perc,
        ram_total_gb=round(mem.total / (1024**3), 2),
        ram_used_gb=round(mem.used / (1024**3), 2),
        ram_available_gb=round(mem.available / (1024**3), 2),
        ram_percent=mem.percent,
        swap_total_gb=round(swap.total / (1024**3), 2),
        swap_used_gb=round(swap.used / (1024**3), 2),
        swap_percent=swap.percent,
        disks=get_disks_info(),
        gpus=get_gpus(),
        shell=os.environ.get("SHELL", "/bin/bash"),
        desktop_environment=desktop_env,
        display_server=display_server,
        available_package_managers=package_managers,
        available_tools=available_tools
    )

def format_system_summary_for_ai(info: Optional[SystemInfo] = None) -> str:
    if info is None:
        info = get_system_info()
    
    disks_str = ", ".join(f"{d['mountpoint']} ({d['used_gb']}/{d['total_gb']}GB, {d['percent']}%)" for d in info.disks[:3])
    gpus_str = "; ".join(info.gpus)
    pms_str = ", ".join(info.available_package_managers) or "none detected"

    return (
        f"OS: {info.os_pretty_name} (ID: {info.os_id}, Like: {info.os_id_like or 'none'})\n"
        f"Kernel: {info.kernel} ({info.arch})\n"
        f"DE: {info.desktop_environment} | Display Server: {info.display_server} | Shell: {info.shell}\n"
        f"CPU: {info.cpu_model} ({info.cpu_cores_logical} vCPUs, {info.cpu_usage_percent}% load)\n"
        f"RAM: {info.ram_used_gb} / {info.ram_total_gb} GB ({info.ram_percent}%)\n"
        f"Storage: {disks_str}\n"
        f"GPU: {gpus_str}\n"
        f"Package Managers: {pms_str}\n"
        f"Uptime: {info.uptime_human}"
    )

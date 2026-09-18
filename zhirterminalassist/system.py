import os
import platform
import shutil
import subprocess
import time
from dataclasses import dataclass
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
    cpu_cores_logical: int
    cpu_usage_percent: float
    ram_total_gb: float
    ram_used_gb: float
    ram_available_gb: float
    ram_percent: float
    disks: List[Dict[str, Any]]
    gpus: List[str]
    shell: str
    desktop_environment: str
    display_server: str
    package_managers: List[str]

def get_os_release() -> Dict[str, str]:
    info = {"NAME": "Linux", "PRETTY_NAME": "Linux", "ID": "linux", "ID_LIKE": ""}
    for p in [Path("/etc/os-release"), Path("/usr/lib/os-release")]:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            info[k] = v.strip('"\'')
                break
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
    if shutil.which("lspci"):
        try:
            res = subprocess.run(
                ["lspci"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3
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

    if not gpus and shutil.which("nvidia-smi"):
        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3
            )
            for line in res.stdout.splitlines():
                if line.strip():
                    gpus.append(line.strip())
        except Exception:
            pass

    if not gpus:
        drm = Path("/sys/class/drm")
        if drm.exists():
            for card in drm.glob("card[0-9]"):
                if (card / "device").exists():
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
    seen = set()
    try:
        for part in psutil.disk_partitions(all=False):
            if part.mountpoint in seen:
                continue
            if any(part.mountpoint.startswith(p) for p in ["/var/lib/docker", "/snap", "/var/lib/flatpak/runtime"]):
                continue
            try:
                u = psutil.disk_usage(part.mountpoint)
                seen.add(part.mountpoint)
                disks.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "total_gb": round(u.total / (1024**3), 1),
                    "used_gb": round(u.used / (1024**3), 1),
                    "free_gb": round(u.free / (1024**3), 1),
                    "percent": u.percent
                })
            except Exception:
                continue
    except Exception:
        pass
    return disks

def get_system_info(refresh_cpu: bool = False) -> SystemInfo:
    os_info = get_os_release()
    uptime_sec = time.time() - psutil.boot_time()
    mem = psutil.virtual_memory()

    pm_candidates = ["pacman", "yay", "paru", "apt", "dnf", "zypper", "apk", "flatpak", "snap"]
    package_managers = [pm for pm in pm_candidates if shutil.which(pm)]

    sess_type = os.environ.get("XDG_SESSION_TYPE", "")
    if not sess_type:
        if os.environ.get("WAYLAND_DISPLAY"):
            sess_type = "wayland"
        elif os.environ.get("DISPLAY"):
            sess_type = "x11"
        else:
            sess_type = "tty"

    desktop = os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION") or "Unknown"

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
        cpu_cores_logical=psutil.cpu_count(logical=True) or 1,
        cpu_usage_percent=psutil.cpu_percent(interval=0.1 if refresh_cpu else None),
        ram_total_gb=round(mem.total / (1024**3), 1),
        ram_used_gb=round(mem.used / (1024**3), 1),
        ram_available_gb=round(mem.available / (1024**3), 1),
        ram_percent=mem.percent,
        disks=get_disks_info(),
        gpus=get_gpus(),
        shell=os.environ.get("SHELL", "/bin/bash").split("/")[-1],
        desktop_environment=desktop,
        display_server=sess_type,
        package_managers=package_managers
    )

def format_system_summary_for_ai(info: Optional[SystemInfo] = None) -> str:
    if info is None:
        info = get_system_info()
    disks_str = ", ".join(f"{d['mountpoint']} ({d['used_gb']}/{d['total_gb']} GB, {d['percent']}%)" for d in info.disks[:2])
    gpus_str = "; ".join(info.gpus)
    pms_str = ", ".join(info.package_managers) or "none"

    return (
        f"Distribution: {info.os_pretty_name} (ID: {info.os_id})\n"
        f"Kernel: {info.kernel} ({info.arch})\n"
        f"CPU: {info.cpu_model} ({info.cpu_cores_logical} cores, {info.cpu_usage_percent}% load)\n"
        f"GPU: {gpus_str}\n"
        f"RAM: {info.ram_used_gb} / {info.ram_total_gb} GB ({info.ram_percent}%)\n"
        f"Storage: {disks_str}\n"
        f"Shell: {info.shell}\n"
        f"Desktop: {info.desktop_environment}\n"
        f"Session: {info.display_server}\n"
        f"Package Managers: {pms_str}\n"
        f"Uptime: {info.uptime_human}"
    )

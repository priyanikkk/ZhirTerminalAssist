import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class PackageItem:
    name: str
    version: str
    description: str
    installed: bool = False
    source: str = "native"

class PackageManager:
    def __init__(self):
        self.primary_pm = self._detect_primary_pm()

    def _detect_primary_pm(self) -> str:
        # Check AUR helpers first on Arch
        if shutil.which("paru"):
            return "paru"
        if shutil.which("yay"):
            return "yay"
        if shutil.which("pacman"):
            return "pacman"
        if shutil.which("apt"):
            return "apt"
        if shutil.which("dnf"):
            return "dnf"
        if shutil.which("zypper"):
            return "zypper"
        if shutil.which("flatpak"):
            return "flatpak"
        return "unknown"

    def search(self, query: str, limit: int = 30) -> List[PackageItem]:
        query = query.strip()
        if not query:
            return []

        results: List[PackageItem] = []
        pm = self.primary_pm

        try:
            if pm in ("pacman", "yay", "paru"):
                cmd = [pm, "-Ss", query]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
                lines = res.stdout.splitlines()
                # Pacman format:
                # repo/pkgname version [installed]
                #     description
                i = 0
                while i < len(lines) and len(results) < limit:
                    header = lines[i].strip()
                    if "/" in header and not header.startswith(" "):
                        parts = header.split(None, 2)
                        full_name = parts[0]
                        pkg_name = full_name.split("/")[-1]
                        version = parts[1] if len(parts) > 1 else ""
                        is_installed = "[installed]" in header
                        desc = ""
                        if i + 1 < len(lines) and lines[i + 1].startswith("    "):
                            desc = lines[i + 1].strip()
                            i += 1
                        results.append(PackageItem(
                            name=pkg_name,
                            version=version,
                            description=desc,
                            installed=is_installed,
                            source=parts[0].split("/")[0] if "/" in parts[0] else pm
                        ))
                    i += 1

            elif pm == "apt":
                cmd = ["apt-cache", "search", query]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
                for line in res.stdout.splitlines()[:limit]:
                    if " - " in line:
                        name, desc = line.split(" - ", 1)
                        results.append(PackageItem(
                            name=name.strip(),
                            version="",
                            description=desc.strip(),
                            source="apt"
                        ))

            elif pm == "dnf":
                cmd = ["dnf", "repoquery", "--qf", "%{name}|%{version}|%{summary}", f"*{query}*"]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
                for line in res.stdout.splitlines()[:limit]:
                    parts = line.split("|", 2)
                    if len(parts) == 3:
                        results.append(PackageItem(name=parts[0], version=parts[1], description=parts[2], source="dnf"))

            elif pm == "flatpak" or shutil.which("flatpak"):
                cmd = ["flatpak", "search", query]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
                lines = res.stdout.splitlines()
                for line in lines[1:limit+1]:
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        results.append(PackageItem(
                            name=parts[1].strip(),
                            version=parts[2].strip() if len(parts) > 2 else "",
                            description=parts[0].strip(),
                            source="flatpak"
                        ))
        except Exception:
            pass

        return results

    def get_info(self, pkg_name: str) -> str:
        pm = self.primary_pm
        cmd = []
        if pm in ("pacman", "yay", "paru"):
            cmd = [pm, "-Si", pkg_name]
        elif pm == "apt":
            cmd = ["apt-cache", "show", pkg_name]
        elif pm == "dnf":
            cmd = ["dnf", "info", pkg_name]
        elif pm == "flatpak":
            cmd = ["flatpak", "info", pkg_name]

        if not cmd:
            return f"Package manager {pm} not supported for direct info."

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            if res.returncode == 0 and res.stdout:
                return res.stdout
            return res.stderr or "Package info not found."
        except Exception as e:
            return str(e)

    def get_install_command(self, pkg_name: str) -> str:
        pm = self.primary_pm
        if pm in ("yay", "paru"):
            return f"{pm} -S {pkg_name}"
        elif pm == "pacman":
            return f"sudo pacman -S {pkg_name}"
        elif pm == "apt":
            return f"sudo apt install {pkg_name}"
        elif pm == "dnf":
            return f"sudo dnf install {pkg_name}"
        elif pm == "zypper":
            return f"sudo zypper install {pkg_name}"
        elif pm == "flatpak":
            return f"flatpak install {pkg_name}"
        return f"# Cannot install {pkg_name}: unknown package manager"

    def get_remove_command(self, pkg_name: str) -> str:
        pm = self.primary_pm
        if pm in ("yay", "paru"):
            return f"{pm} -R {pkg_name}"
        elif pm == "pacman":
            return f"sudo pacman -R {pkg_name}"
        elif pm == "apt":
            return f"sudo apt remove {pkg_name}"
        elif pm == "dnf":
            return f"sudo dnf remove {pkg_name}"
        elif pm == "zypper":
            return f"sudo zypper rm {pkg_name}"
        elif pm == "flatpak":
            return f"flatpak uninstall {pkg_name}"
        return f"# Cannot remove {pkg_name}: unknown package manager"

    def get_update_command(self) -> str:
        pm = self.primary_pm
        if pm in ("yay", "paru"):
            return f"{pm} -Syu"
        elif pm == "pacman":
            return "sudo pacman -Syu"
        elif pm == "apt":
            return "sudo apt update && sudo apt upgrade"
        elif pm == "dnf":
            return "sudo dnf upgrade"
        elif pm == "zypper":
            return "sudo zypper dup"
        elif pm == "flatpak":
            return "flatpak update"
        return "# Unknown package manager"

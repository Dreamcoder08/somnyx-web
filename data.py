# data.py — Recoleccion de datos SOMNYX Web
import subprocess, os, time, glob
from pathlib import Path
from datetime import datetime

HOME       = Path(os.environ.get("HOME", "/home/dreamcoder08"))
WORKSPACE  = Path(os.environ.get("SOMNYX_WORKSPACE", HOME / "somnyx"))
ARCHIVE    = Path(os.environ.get("SOMNYX_ARCHIVE",   HOME / "archive"))
VAULT      = Path(os.environ.get("SOMNYX_VAULT",     HOME / "vault"))
NOTES      = Path(os.environ.get("SOMNYX_NOTES",     HOME / "notes"))
MEDIA      = Path(os.environ.get("SOMNYX_MEDIA",     HOME / "media"))
INBOX      = Path(os.environ.get("SOMNYX_INBOX",     HOME / "inbox"))

def _run(*cmd) -> str:
    try:
        return subprocess.check_output(cmd, text=True, timeout=5, stderr=subprocess.DEVNULL)
    except Exception:
        return ""

def dir_size(path: Path) -> str:
    out = _run("du", "-sh", "--apparent-size", str(path))
    return out.split()[0] if out.split() else "?"

def _read_proc(path: str) -> str:
    try:
        return Path(path).read_text()
    except Exception:
        return ""

# ── CPU ───────────────────────────────────────────────────────────────────────

_cpu_prev = None

def cpu_percent() -> float:
    global _cpu_prev
    def parse():
        line = _read_proc("/proc/stat").splitlines()[0]
        vals = list(map(int, line.split()[1:]))
        return vals[3] + vals[4], sum(vals)

    curr = parse()
    if _cpu_prev is None:
        _cpu_prev = curr
        time.sleep(0.2)
        curr = parse()

    di = curr[0] - _cpu_prev[0]
    dt = curr[1] - _cpu_prev[1]
    _cpu_prev = curr
    return round((1 - di / dt) * 100, 1) if dt else 0.0

def cpu_temp() -> str:
    for path in sorted(glob.glob("/sys/class/thermal/thermal_zone*/temp")):
        try:
            t = int(Path(path).read_text().strip()) / 1000
            if 10 < t < 120:
                return f"{t:.1f}°C"
        except Exception:
            continue
    # hwmon fallback
    for path in glob.glob("/sys/class/hwmon/hwmon*/temp*_input"):
        try:
            t = int(Path(path).read_text().strip()) / 1000
            if 10 < t < 120:
                return f"{t:.1f}°C"
        except Exception:
            continue
    return "N/A"

# ── Memoria & Swap ────────────────────────────────────────────────────────────

def _meminfo() -> dict:
    info = {}
    for line in _read_proc("/proc/meminfo").splitlines():
        k, *v = line.split()
        info[k.rstrip(":")] = int(v[0]) if v else 0
    return info

def memory_info() -> dict:
    info  = _meminfo()
    total = info.get("MemTotal", 0)
    avail = info.get("MemAvailable", 0)
    used  = total - avail
    gb    = 1024 * 1024
    return {
        "used_gb":  round(used  / gb, 1),
        "total_gb": round(total / gb, 1),
        "percent":  round(used / total * 100, 1) if total else 0,
    }

def swap_info() -> dict:
    info  = _meminfo()
    total = info.get("SwapTotal", 0)
    free  = info.get("SwapFree", 0)
    used  = total - free
    mb    = 1024
    return {
        "used_mb":  round(used  / mb),
        "total_mb": round(total / mb),
        "percent":  round(used / total * 100, 1) if total else 0,
    }

def load_avg() -> dict:
    txt = _read_proc("/proc/loadavg").split()
    return {
        "1m":  float(txt[0]) if txt else 0.0,
        "5m":  float(txt[1]) if len(txt) > 1 else 0.0,
        "15m": float(txt[2]) if len(txt) > 2 else 0.0,
    }

# ── Disco ─────────────────────────────────────────────────────────────────────

def disk_info() -> dict:
    out   = _run("df", "-BG", "/")
    lines = out.splitlines()
    if len(lines) > 1:
        parts = lines[1].split()
        total = float(parts[1].rstrip("G")) if len(parts) > 1 else 0
        used  = float(parts[2].rstrip("G")) if len(parts) > 2 else 0
        return {
            "used_gb":  round(used),
            "total_gb": round(total),
            "percent":  round(used / total * 100, 1) if total else 0,
        }
    return {"used_gb": 0, "total_gb": 0, "percent": 0}

_SKIP_MOUNTS = {"/sys", "/proc", "/dev", "/run", "/boot/efi", "tmpfs",
                "devtmpfs", "cgroup", "pstore", "efivarfs", "bpf", "hugetlbfs"}

def all_partitions() -> list:
    out  = _run("df", "-BG", "--output=target,fstype,size,used,avail,pcent")
    rows = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 6:
            continue
        mount, fstype = parts[0], parts[1]
        if any(mount.startswith(s) for s in _SKIP_MOUNTS):
            continue
        if fstype in ("tmpfs", "devtmpfs", "squashfs", "overlay"):
            continue
        try:
            rows.append({
                "mount":   mount,
                "fstype":  fstype,
                "total_gb": float(parts[2].rstrip("G")),
                "used_gb":  float(parts[3].rstrip("G")),
                "avail_gb": float(parts[4].rstrip("G")),
                "percent":  float(parts[5].rstrip("%")),
            })
        except ValueError:
            continue
    return rows[:6]

# ── Red ───────────────────────────────────────────────────────────────────────

def network_info() -> list:
    out   = _run("ip", "-brief", "addr")
    ifaces = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        name   = parts[0]
        status = parts[1]
        ips    = [p.split("/")[0] for p in parts[2:]
                  if "/" in p and not p.startswith("fe80") and not p.startswith("::")]
        ifaces.append({
            "name":   name,
            "status": status.lower(),
            "ip":     ips[0] if ips else "–",
        })
    return ifaces[:6]

# ── Procesos ──────────────────────────────────────────────────────────────────

def top_processes() -> list:
    out   = _run("ps", "axo", "user,pid,pcpu,pmem,comm", "--sort=-%cpu", "--no-headers")
    procs = []
    for line in out.splitlines()[:8]:
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        try:
            procs.append({
                "user": parts[0],
                "pid":  parts[1],
                "cpu":  float(parts[2]),
                "mem":  float(parts[3]),
                "name": parts[4].strip()[:30],
            })
        except ValueError:
            continue
    return procs

# ── Proyectos ─────────────────────────────────────────────────────────────────

def projects_stats() -> list:
    dev      = WORKSPACE / "dev"
    projects = []
    if not dev.exists():
        return projects

    for category in sorted(dev.iterdir()):
        if not category.is_dir():
            continue
        for proj in sorted(category.iterdir()):
            if not proj.is_dir():
                continue
            info = {
                "name":        proj.name,
                "category":    category.name,
                "has_git":     False,
                "branch":      "–",
                "last_commit": "sin commits",
                "modified":    "–",
            }
            if (proj / ".git").exists():
                info["has_git"]     = True
                info["branch"]      = _run("git", "-C", str(proj), "rev-parse", "--abbrev-ref", "HEAD").strip() or "–"
                info["last_commit"] = (_run("git", "-C", str(proj), "log", "--oneline", "-1").strip() or "sin commits")[:55]
            try:
                mtime = proj.stat().st_mtime
                info["modified"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
            except Exception:
                pass
            projects.append(info)

    return sorted(projects, key=lambda p: (not p["has_git"], p["modified"]), reverse=False)[:10]

# ── Archivos recientes ────────────────────────────────────────────────────────

def recent_files(hours: int = 24) -> list:
    try:
        out = _run(
            "fd", ".", str(HOME), "--type", "f",
            "--newer", f"{hours}h",
            "--exclude", ".git",
            "--exclude", "node_modules",
            "--exclude", "target",
            "--exclude", "__pycache__",
            "--exclude", ".cache",
            "--max-results", "12",
        )
        files = []
        for line in out.splitlines():
            p = Path(line.strip())
            if not line.strip():
                continue
            try:
                rel  = str(p.relative_to(HOME))
                mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%H:%M")
            except Exception:
                rel   = line.strip()
                mtime = "–"
            files.append({"path": rel, "time": mtime})
        return files[:10]
    except Exception:
        return []

# ── Uptime ────────────────────────────────────────────────────────────────────

def uptime() -> str:
    txt  = _read_proc("/proc/uptime")
    secs = int(float(txt.split()[0])) if txt.split() else 0
    d, h, m = secs // 86400, (secs % 86400) // 3600, (secs % 3600) // 60
    return f"{d}d {h}h {m}m" if d else f"{h}h {m}m"

# ── Workspace ─────────────────────────────────────────────────────────────────

def _count_files(path: Path, max_depth: int = 2) -> int:
    out = _run("fd", ".", str(path), "--max-depth", str(max_depth), "--type", "f")
    return len([l for l in out.splitlines() if l])

def _count_old(path: Path, days: int = 7) -> int:
    out = _run("fd", ".", str(path), "--max-depth", "2", "--type", "f", "--older", f"{days}d")
    return len([l for l in out.splitlines() if l])

def _timer_next(name: str) -> str:
    out = _run("systemctl", "--user", "list-timers", "--all", "--no-legend")
    for line in out.splitlines():
        if name in line:
            parts = line.split()
            return parts[3] if len(parts) > 3 else "?"
    return "?"

def workspace_stats() -> dict:
    today        = datetime.now().strftime("%Y-%m-%d")
    journal_file = NOTES / "journal" / f"{today}.md"
    return {
        "workspace_size": dir_size(WORKSPACE),
        "archive_size":   dir_size(ARCHIVE),
        "vault_size":     dir_size(VAULT),
        "notes_size":     dir_size(NOTES),
        "media_size":     dir_size(MEDIA),
        "inbox_size":     dir_size(INBOX),
        "inbox_count":    _count_files(INBOX),
        "inbox_old":      _count_old(INBOX),
        "journal_today":  journal_file.exists(),
        "journal_date":   today,
        "timer_clean":    _timer_next("somnyx-clean"),
        "timer_alert":    _timer_next("somnyx-inbox-alert"),
    }

# ── Full stats ────────────────────────────────────────────────────────────────

def full_stats() -> dict:
    mem  = memory_info()
    disk = disk_info()
    return {
        "system": {
            "cpu_percent":  cpu_percent(),
            "cpu_temp":     cpu_temp(),
            "ram_used_gb":  mem["used_gb"],
            "ram_total_gb": mem["total_gb"],
            "ram_percent":  mem["percent"],
            "disk_used_gb": disk["used_gb"],
            "disk_total_gb":disk["total_gb"],
            "disk_percent": disk["percent"],
            "swap":         swap_info(),
            "load":         load_avg(),
            "uptime":       uptime(),
            "time":         datetime.now().strftime("%Y-%m-%d  %H:%M:%S"),
            "partitions":   all_partitions(),
            "network":      network_info(),
            "processes":    top_processes(),
        },
        "workspace": workspace_stats(),
        "projects":  projects_stats(),
        "recent":    recent_files(24),
    }

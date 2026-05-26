"""Detect available block devices on the host (for the ZFS /code partition choice).

Runs ``lsblk`` on Linux and returns human-readable rows whose first token is the device
path, e.g. ``/dev/sdb  931G  disk``. On non-Linux hosts or if ``lsblk`` is unavailable the
list is empty and the caller falls back to a free-text entry — so DevSysBot can still be
developed/run on Windows.
"""

from __future__ import annotations

import shutil
import subprocess


def list_block_devices() -> list[str]:
    """Return display rows for disks and partitions, or [] if detection is not possible."""
    if not shutil.which("lsblk"):
        return []
    try:
        out = subprocess.run(
            ["lsblk", "-prno", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return []

    rows: list[str] = []
    for line in out.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 3:
            continue
        name, size, dtype = parts[0], parts[1], parts[2]
        if dtype not in ("disk", "part"):
            continue
        fstype = parts[3] if len(parts) > 3 else ""
        mount = parts[4] if len(parts) > 4 else ""
        extra = " ".join(x for x in (fstype, mount) if x)
        rows.append(f"{name}  {size}  {dtype}" + (f"  [{extra}]" if extra else ""))
    return rows


def device_path(display_row: str) -> str:
    """Extract the device path (first token) from a display row."""
    return display_row.split()[0] if display_row else ""

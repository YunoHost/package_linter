"""Apparent directory size without GNU du -b."""

from pathlib import Path


def directory_apparent_bytes(path: Path) -> int:
    total = 0
    for item in Path(path).rglob("*"):
        if not item.is_file():
            continue
        try:
            total += item.stat().st_size
        except OSError:
            continue
    return total

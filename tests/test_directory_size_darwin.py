"""macOS du rejects -b. Screenshot size must still be a byte count."""

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib.directory_size import directory_apparent_bytes


def main() -> None:
    folder = Path(tempfile.mkdtemp())
    (folder / "a.txt").write_text("hello\n")
    red = subprocess.run(["du", "-sb", str(folder)], capture_output=True, text=True)
    if red.returncode == 0:
        raise SystemExit("du -sb unexpectedly succeeded")
    if "invalid option" not in red.stderr and "illegal option" not in red.stderr:
        raise SystemExit(red.stderr)
    size = directory_apparent_bytes(folder)
    if size != 6:
        raise SystemExit(f"expected 6 bytes, got {size}")
    print(f"directory size darwin ok (du -sb exit {red.returncode}, bytes {size})")


if __name__ == "__main__":
    main()

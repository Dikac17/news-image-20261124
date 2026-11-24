#!/usr/bin/env python3
"""THE WORLD — 24 November 2026.

Writes the front page to /output/entry.png. The image is drawn at build
time by draw.py (Pillow + DejaVu fonts, committed beside this file) and
shipped in this repository as entry.png; this program copies it verbatim,
so every run writes exactly the same bytes with no network and no
third-party code at run time.
"""
import hashlib
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "entry.png")
MAX_BYTES = 1048576
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def png_dimensions(path):
    """Read the IHDR chunk of a PNG; raise if it is not a whole PNG."""
    with open(path, "rb") as fh:
        head = fh.read(33)
    if len(head) < 33 or head[:8] != PNG_MAGIC:
        raise ValueError("not a PNG file")
    if head[12:16] != b"IHDR":
        raise ValueError("PNG has no IHDR chunk")
    width, height = struct.unpack(">II", head[16:24])
    return width, height


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "entry.png")
    shutil.copyfile(SOURCE, dest)
    # Gate validation: the written file must be the same image, a whole
    # PNG, exactly 1024x1024 and at most 1 MiB. Fail loudly otherwise.
    if sha256_file(dest) != sha256_file(SOURCE):
        raise SystemExit("entry.png differs from the committed image")
    width, height = png_dimensions(dest)
    if (width, height) != (1024, 1024):
        raise SystemExit(f"entry.png is {width}x{height}, not 1024x1024")
    size = os.path.getsize(dest)
    if size > MAX_BYTES:
        raise SystemExit(f"entry.png is {size} bytes, over the 1 MiB limit")
    print(f"wrote {dest} {size} bytes, {width}x{height} PNG, "
          f"sha256 {sha256_file(dest)[:16]}…")
    sys.exit(0)


if __name__ == "__main__":
    main()

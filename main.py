#!/usr/bin/env python3
"""Entry point: validate the rendered poster and copy it to the output dir.

Stdlib only, no network. Reads entry.png next to this file, checks it is
a whole 1024x1024 PNG, and writes it to $MAKEFUN_OUTPUT_DIR/entry.png
(or /output/entry.png when the variable is unset).
"""

import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def check_png(path):
    with open(path, "rb") as fh:
        head = fh.read(33)
    if len(head) < 33 or head[:8] != PNG_MAGIC:
        raise SystemExit("entry.png is not a PNG file")
    width, height = struct.unpack(">II", head[16:24])
    if (width, height) != (1024, 1024):
        raise SystemExit("entry.png is %dx%d, expected 1024x1024"
                         % (width, height))
    return width, height


def main():
    check_png(SRC)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "entry.png")
    shutil.copyfile(SRC, dest)
    size = os.path.getsize(dest)
    if size > 1048576:
        raise SystemExit("entry.png is %d bytes, over the 1 MiB limit" % size)
    print("wrote %s (%d bytes, 1024x1024 PNG)" % (dest, size))
    return 0


if __name__ == "__main__":
    sys.exit(main())

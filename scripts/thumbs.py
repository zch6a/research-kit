"""site/img/: a small picture of each tool for the site, made from the screenshots in the tools' own repositories
(checked out next to this one). Run by hand when a tool's screenshot changes; the pictures are committed.

    uv run --with pillow python scripts/thumbs.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "img"
# the picture that shows each tool best (its repository's docs/)
PICK = {
    "venue-atlas": "site.png",
    "paper-impact": "site.png",
    "arxiv-diff": "demo.png",
    "gpu-budget": "page.png",
    "exp-tables": "demo.png",
    "fig-check": "diagram.svg",
    "paper-proof": "demo.png",
    "submit-check": "demo.png",
    "iclr-scores": "site.png",
    "paper-page": "example-light.png",
    "scholar-cards": "stats.svg",
    "reading-group": "page.png",
}
WIDTH = 720  # twice the card's width on the page: sharp on high-density screens


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for tool, name in PICK.items():
        src = ROOT.parent / tool / "docs" / name
        if not src.is_file():
            print(f"missing: {src}", file=sys.stderr)
            continue
        if src.suffix == ".svg":
            shutil.copyfile(src, OUT / f"{tool}.svg")
            print(f"{tool}.svg (copied)")
            continue
        im = Image.open(src).convert("RGB")
        if im.width > WIDTH:
            im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
        im = im.crop((0, 0, im.width, min(im.height, round(im.width * 0.62))))  # the top of a long page: what the card shows
        target = OUT / f"{tool}.webp"
        im.save(target, "WEBP", quality=82, method=6)
        print(f"{tool}.webp {target.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Usage: python scripts/main.py --demo  or  python scripts/main.py --login RaVSe"""
from __future__ import annotations
import argparse
from pathlib import Path

from build_gif import save_gif
from fetch_contributions import fetch_calendar, demo_calendar
from render_frames import render_frames, ROOT, FLYING, CASTING, PROJECTILE


def main():
    parser = argparse.ArgumentParser(description="Green mage GitHub activity animation")
    parser.add_argument("--login", default="RaVSe")
    parser.add_argument("--demo", action="store_true", help="Use illustrative activity; never for scheduled updates")
    parser.add_argument("--shots", type=int, default=12, help="Maximum cells destroyed per animation loop")
    parser.add_argument("--gif", type=Path, default=ROOT / "assets/mage-contributions.gif")
    parser.add_argument("--preview", type=Path, default=ROOT / "assets/mage-preview.png")
    args = parser.parse_args()
    if not 0 <= args.shots <= 40:
        parser.error("--shots must be between 0 and 40")
    levels = demo_calendar() if args.demo else fetch_calendar(args.login)
    frames = list(render_frames(levels, shots=args.shots))
    save_gif(frames, args.gif, args.preview, palette_sources=(FLYING, CASTING, PROJECTILE))
    print(f"Built {len(frames)} frames: {args.gif} ({args.gif.stat().st_size/1024/1024:.1f} MiB)"
          + (" [DEMO/SAMPLE DATA]" if args.demo else " [LIVE GITHUB DATA]"))


if __name__ == "__main__":
    main()

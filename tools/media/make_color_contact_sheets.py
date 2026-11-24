#!/usr/bin/env python3
"""Create paired, evenly sampled contact sheets for grey-picture vs locked-cut review."""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageStat


def probe_duration(path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path),
    ], text=True).strip()
    return float(out)


def grab_frame(path: Path, second: float, target: Path) -> Image.Image:
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{second:.3f}",
        "-i", str(path), "-frames:v", "1", "-vf", "scale=180:-2",
        "-q:v", "3", "-y", str(target),
    ], check=True)
    return Image.open(target).convert("RGB")


def mean_rgb(image: Image.Image) -> tuple[float, float, float]:
    return tuple(round(v, 1) for v in ImageStat.Stat(image).mean[:3])


def make_sheet(ep: int, grey: Path, locked: Path, output: Path, samples: int) -> dict:
    dg, dl = probe_duration(grey), probe_duration(locked)
    cell_w, cell_h = 180, 320
    label_h, gap, margin = 34, 8, 20
    width = margin * 2 + samples * cell_w + (samples - 1) * gap
    height = margin * 2 + label_h + cell_h * 2 + gap + 20
    sheet = Image.new("RGB", (width, height), "#15171a")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((margin, 5), f"EP{ep:02d}  |  TOP: GREY PICTURE   BOTTOM: LOCKED CUT / VFX", fill="#eeeeee", font=font)
    stats = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for i in range(samples):
            normalized = (i + 0.5) / samples
            tg, tl = dg * normalized, dl * normalized
            gi = grab_frame(grey, tg, tmp / f"g{i}.jpg")
            li = grab_frame(locked, tl, tmp / f"l{i}.jpg")
            x = margin + i * (cell_w + gap)
            y = margin + label_h
            sheet.paste(gi, (x, y))
            sheet.paste(li, (x, y + cell_h + gap))
            draw.text((x, margin + 15), f"{tg:05.1f}s", fill="#aab0b7", font=font)
            stats.append({"sample": i + 1, "grey_tc_s": round(tg, 2), "locked_tc_s": round(tl, 2), "grey_mean_rgb": mean_rgb(gi), "locked_mean_rgb": mean_rgb(li)})
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=90)
    return {"episode": ep, "grey_duration_s": round(dg, 3), "locked_duration_s": round(dl, 3), "samples": stats}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--grey-dir", type=Path, required=True)
    p.add_argument("--locked-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--samples", type=int, default=12)
    args = p.parse_args()
    all_stats = []
    numbers = sorted(int(p.stem[2:]) for p in args.grey_dir.glob("EP[0-9][0-9].mov"))
    if not numbers or args.samples < 1:
        p.error("need paired EPnn sources and at least one sample")
    for ep in numbers:
        grey = args.grey_dir / f"EP{ep:02d}.mov"
        locked = args.locked_dir / f"EP{ep:02d}.mp4"
        if not grey.exists() or not locked.exists():
            raise FileNotFoundError(f"Missing pair for EP{ep:02d}")
        all_stats.append(make_sheet(ep, grey, locked, args.output_dir / f"EP{ep:02d}.jpg", args.samples))
    (args.output_dir / "sample_metrics.json").write_text(json.dumps(all_stats, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

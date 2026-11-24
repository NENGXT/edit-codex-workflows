#!/usr/bin/env python3
"""Burn a dense, diagonal Sample watermark into selected review episodes.

Original videos are read-only. Each output is encoded in a temporary directory,
validated, then moved into the requested output folder.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


FPS = "30000/1001"


def run(args: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=True, text=True, capture_output=capture)


def probe(path: Path) -> dict:
    result = run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size:stream=index,codec_type,codec_name,profile,level,"
         "width,height,r_frame_rate,bit_rate,nb_frames,pix_fmt,color_primaries,"
         "color_transfer,color_space,sample_rate,channels",
         "-of", "json", str(path)], capture=True
    )
    return json.loads(result.stdout)


def streams(info: dict) -> tuple[dict, dict]:
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    if not video or not audio:
        raise ValueError("Expected one video and at least one audio stream")
    return video, audio


def make_watermark(work: Path) -> Path:
    # Extend the grid beyond the edges so rotated rows leave no bare corners.
    font = Path(run(["fc-match", "Hiragino Sans:style=W5", "-f", "%{file}\n"], capture=True).stdout.strip())
    if not font.is_file():
        raise RuntimeError(f"Hiragino Sans W5 font not found: {font}")
    command = ["magick", "-size", "1080x1920", "xc:none", "-font", str(font),
               "-pointsize", "58", "-fill", "rgba(255,255,255,0.24)"]
    for row, y in enumerate(range(-220, 2180, 190)):
        offset = 135 if row % 2 else 0
        for x in range(-360 + offset, 1450, 295):
            command += ["-draw", f"translate {x},{y} rotate -32 text 0,0 'Sample'"]
    png = work / "sample_watermark.png"
    run(command + ["PNG32:" + str(png)])
    size = run(["magick", "identify", "-format", "%wx%h %[channels]", str(png)], capture=True).stdout
    if not size.startswith("1080x1920") or "a" not in size.lower():
        raise RuntimeError(f"Watermark image is not transparent 1080x1920 RGBA: {size}")
    return png


def audio_hash(path: Path) -> str:
    return run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(path),
         "-map", "0:a:0", "-c", "copy", "-f", "hash", "-hash", "sha256", "-"],
        capture=True,
    ).stdout.strip()


def encode(source: Path, overlay: Path, target: Path, video: dict) -> None:
    source_bitrate = int(video.get("bit_rate") or 20_000_000)
    bitrate = round(source_bitrate * 1.02)
    profile = str(video["profile"]).lower()
    if profile not in {"main", "high", "baseline"}:
        raise ValueError(f"Unsupported H.264 profile: {profile}")
    level = int(video["level"])
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-i", str(source), "-loop", "1", "-framerate", FPS, "-i", str(overlay),
        "-filter_complex", "[0:v:0]format=yuv420p[base];"
        "[1:v:0]format=rgba[wm];[base][wm]overlay=0:0:format=auto:"
        "shortest=1:repeatlast=1[v]",
        "-map", "[v]", "-map", "0:a:0",
        "-c:v", "libx264", "-preset", "faster", "-profile:v", profile,
        "-level:v", f"{level // 10}.{level % 10}", "-pix_fmt", "yuv420p",
        "-r", FPS, "-b:v", str(bitrate), "-minrate", str(bitrate),
        "-maxrate", str(bitrate), "-bufsize", str(bitrate * 2),
        "-x264-params", "nal-hrd=cbr:force-cfr=1", "-c:a", "copy",
        "-movflags", "+faststart",
    ]
    for option, key in (("-color_primaries", "color_primaries"),
                        ("-color_trc", "color_transfer"), ("-colorspace", "color_space")):
        value = video.get(key)
        if value and value not in {"unknown", "reserved"}:
            command += [option, value]
    run(command + [str(target)])


def verify(source: Path, output: Path, original: dict) -> dict:
    current = probe(output)
    src_video, src_audio = streams(original)
    dst_video, dst_audio = streams(current)
    for key in ("codec_name", "profile", "level", "width", "height", "pix_fmt", "r_frame_rate", "nb_frames"):
        if dst_video.get(key) != src_video.get(key):
            raise RuntimeError(f"{output.name}: video {key} changed: {src_video.get(key)} -> {dst_video.get(key)}")
    for key in ("codec_name", "profile", "sample_rate", "channels"):
        if key in src_audio and dst_audio.get(key) != src_audio.get(key):
            raise RuntimeError(f"{output.name}: audio {key} changed")
    duration_delta = float(current["format"]["duration"]) - float(original["format"]["duration"])
    if abs(duration_delta) > 0.05:
        raise RuntimeError(f"{output.name}: duration changed by {duration_delta:.3f}s")
    if audio_hash(source) != audio_hash(output):
        raise RuntimeError(f"{output.name}: source audio packets changed")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(output), "-f", "null", "-"])
    return {"file": output.name, "duration": current["format"]["duration"],
            "frames": dst_video["nb_frames"], "bytes": output.stat().st_size,
            "audio_packets_unchanged": True}


def episode_number(path: Path) -> int:
    match = re.fullmatch(r"EP(\d+)\.mp4", path.name)
    if not match:
        raise ValueError(f"Unexpected episode filename: {path.name}")
    return int(match.group(1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--episodes", type=int, nargs="*")
    args = parser.parse_args()
    for executable in ("ffmpeg", "ffprobe", "magick", "fc-match"):
        if not shutil.which(executable):
            raise RuntimeError(f"Missing required tool: {executable}")
    paths = sorted(args.source.glob("EP*.mp4"), key=episode_number)
    chosen = set(args.episodes) if args.episodes else None
    if chosen is not None:
        paths = [path for path in paths if episode_number(path) in chosen]
        if {episode_number(path) for path in paths} != chosen:
            raise ValueError(f"Missing requested episodes: {sorted(chosen - {episode_number(p) for p in paths})}")
    if not paths:
        raise ValueError("No source episodes selected")
    ready = []
    for path in paths:
        info = probe(path)
        video, _ = streams(info)
        if (video.get("codec_name"), video.get("width"), video.get("height"),
            video.get("r_frame_rate"), video.get("pix_fmt")) != ("h264", 1080, 1920, FPS, "yuv420p"):
            raise ValueError(f"Unexpected source format: {path.name}")
        if not video.get("nb_frames") or not video.get("bit_rate"):
            raise ValueError(f"Missing frame count or bitrate: {path.name}")
        target = args.output / path.name
        if target.exists():
            raise FileExistsError(f"Output already exists: {target}")
        ready.append((path, info, video, target))
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sample_watermark_", dir=args.output) as temp:
        work = Path(temp)
        overlay = make_watermark(work)
        for index, (source, info, video, target) in enumerate(ready, 1):
            partial = work / source.name
            encode(source, overlay, partial, video)
            result = verify(source, partial, info)
            os.replace(partial, target)
            print(json.dumps({"progress": f"{index}/{len(ready)}", **result}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

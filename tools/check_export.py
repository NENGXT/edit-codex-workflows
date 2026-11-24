"""Read-only technical checks on a locally saved sound-and-picture ad."""
import argparse
import json
import re
import subprocess
import sys
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path


def positive(value):
    try:
        number = Decimal(value)
        if number.is_finite() and number > 0:
            return number
    except InvalidOperation:
        pass
    raise argparse.ArgumentTypeError("expected a finite positive number")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--size", help="expected displayed dimensions, e.g. 1080x1920")
    parser.add_argument("--max-seconds", type=positive, help="inclusive full file limit")
    parser.add_argument("--av-tolerance-ms", type=positive,
                        help="review stream boundary differences above this many ms")
    limits = parser.add_mutually_exclusive_group()
    limits.add_argument("--max-mb", type=positive, help="inclusive decimal MB limit")
    limits.add_argument("--under-mb", type=positive, help="strict decimal MB limit")
    args = parser.parse_args()
    if args.size and not re.fullmatch(r"[1-9][0-9]*x[1-9][0-9]*", args.size):
        parser.error("--size must look like 1080x1920")
    path = args.file.resolve(strict=True)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                            "-of", "json", str(path)], check=True, stdout=subprocess.PIPE)
    info = json.loads(probe.stdout)
    videos = [s for s in info["streams"] if s["codec_type"] == "video"
              and not s.get("disposition", {}).get("attached_pic")]
    audios = [s for s in info["streams"] if s["codec_type"] == "audio"]
    if not videos or not audios:
        raise ValueError("expected a video stream and an audio stream")
    video, audio = videos[0], audios[0]
    rotation = next((d["rotation"] for d in video.get("side_data_list", [])
                     if "rotation" in d), video.get("tags", {}).get("rotate", 0))
    width, height = video["width"], video["height"]
    degrees = float(rotation) % 360
    if degrees not in (0, 90, 180, 270) or video.get("sample_aspect_ratio", "1:1") not in ("1:1", "N/A"):
        raise ValueError("verify display geometry manually for rotated or non-square pixels")
    if degrees in (90, 270):
        width, height = height, width
    size = f"{width}x{height}"
    duration = Decimal(info["format"]["duration"])
    if not duration.is_finite() or duration <= 0:
        raise ValueError("missing or invalid container duration")
    byte_count = path.stat().st_size
    failures = []
    if args.size and size != args.size:
        failures.append(f"expected {args.size}, got {size}")
    if args.max_seconds and duration > args.max_seconds:
        failures.append(f"full duration exceeds {args.max_seconds} s")
    if args.max_mb and byte_count > args.max_mb * 1000000:
        failures.append("file exceeds inclusive MB limit")
    if args.under_mb and byte_count >= args.under_mb * 1000000:
        failures.append("file meets or exceeds strict MB limit")
    # Container duration alone can hide a missing picture tail under longer audio.
    spans = {}
    review = []
    for role, stream in (("video", video), ("audio", audio)):
        if stream.get("start_time") in (None, "N/A") or stream.get("duration") in (None, "N/A"):
            review.append(f"{role} stream boundaries unavailable")
            continue
        start = Decimal(stream["start_time"])
        spans[role] = (start, start + Decimal(stream["duration"]))
    if len(spans) == 2:
        rate = video.get("avg_frame_rate", "0/0")
        fps = float(Fraction(rate)) if rate not in ("0/0", "N/A") else 0
        tolerance = float(args.av_tolerance_ms or max(50, 1000 / fps if fps > 0 else 0))
        for index, label in enumerate(("start", "end")):
            delta = float((spans["audio"][index] - spans["video"][index]) * 1000)
            if abs(delta) > tolerance:
                review.append(f"audio {label} minus video {label}: {delta:+.3f} ms (review above {tolerance:g} ms)")
    # Decode the selected streams fully, including damaged packets after the file header.
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-err_detect", "explode",
                    "-i", str(path), "-map", f"0:{video['index']}", "-map", f"0:{audio['index']}",
                    "-f", "null", "-"], check=True)
    print(json.dumps(dict(file=path.name, display=size, seconds=str(duration), bytes=byte_count,
                          video=video["codec_name"], average_fps=video.get("avg_frame_rate"),
                          video_frames=video.get("nb_frames"), audio=audio["codec_name"],
                          sample_rate=audio.get("sample_rate"), channels=audio.get("channels"),
                          stream_spans_seconds={k: list(map(str, v)) for k, v in spans.items()},
                          selected_streams_decoded=True, spec_failures=failures, review=review), ensure_ascii=False))
    return 1 if failures else 2 if review else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError, InvalidOperation) as exc:
        sys.exit(f"Could not verify export: {exc}")

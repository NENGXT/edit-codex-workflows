#!/usr/bin/env python3
"""Burn existing SRT cues into test episodes using the measured EP01 reference style.

Sources are never modified. Each episode is rendered in a temporary directory,
validated, then moved into the output directory.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


FRAME_RATE = "30000/1001"
FONT_SIZE = 64
OUTLINE_WIDTH = 9
BOTTOM_LINE_OFFSET = 499  # ImageMagick center-gravity offset in 1080 x 1920.
TOP_LINE_OFFSET = 409
HORIZONTAL_OFFSET = 1
TIME_RE = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> "
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})$"
)


@dataclass(frozen=True)
class Cue:
    start_ms: int
    end_ms: int
    lines: tuple[str, ...]


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=capture)


def time_ms(values: tuple[str, str, str, str]) -> int:
    hours, minutes, seconds, millis = map(int, values)
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + millis


def parse_srt(path: Path) -> list[Cue]:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").strip()
    cues: list[Cue] = []
    for index, block in enumerate(re.split(r"\n\s*\n", text), 1):
        lines = block.splitlines()
        if len(lines) < 3 or lines[0].strip() != str(index):
            raise ValueError(f"{path.name}: cue {index} has an invalid number or body")
        match = TIME_RE.fullmatch(lines[1].strip())
        if not match:
            raise ValueError(f"{path.name}: cue {index} has an invalid timecode")
        start = time_ms(match.groups()[:4])
        end = time_ms(match.groups()[4:])
        body = tuple(line.strip() for line in lines[2:])
        if not 1 <= len(body) <= 2 or any(not line for line in body):
            raise ValueError(f"{path.name}: cue {index} must have one or two nonempty lines")
        if start >= end or (cues and start < cues[-1].end_ms):
            raise ValueError(f"{path.name}: cue {index} has an invalid or overlapping interval")
        cues.append(Cue(start, end, body))
    if not cues:
        raise ValueError(f"{path.name}: empty subtitle file")
    return cues


def probe(path: Path) -> dict:
    result = run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size:stream=index,codec_type,codec_name,width,height,"
         "r_frame_rate,bit_rate,profile,level,pix_fmt,color_primaries,color_transfer,"
         "color_space,nb_frames", "-of", "json", str(path)],
        capture=True,
    )
    return json.loads(result.stdout)


def media_info(path: Path) -> tuple[dict, dict, float]:
    metadata = probe(path)
    video = next((s for s in metadata["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in metadata["streams"] if s["codec_type"] == "audio"), None)
    if not video or not audio:
        raise ValueError(f"{path.name}: expected a video and an audio stream")
    return video, audio, float(metadata["format"]["duration"])


def japanese_font() -> Path:
    result = run(
        ["fc-match", "Hiragino Sans:style=W5", "-f", "%{file}\n"], capture=True
    )
    font = Path(result.stdout.strip())
    if "W5" not in font.name or not font.is_file():
        raise RuntimeError(f"Could not resolve the reference-style W5 font: {font}")
    return font


def render_cue(path: Path, cue: Cue, font: Path) -> None:
    command = [
        "magick", "-size", "1080x1920", "xc:none", "-gravity", "center",
        "-font", str(font), "-pointsize", str(FONT_SIZE),
    ]
    offsets = [BOTTOM_LINE_OFFSET] if len(cue.lines) == 1 else [TOP_LINE_OFFSET, BOTTOM_LINE_OFFSET]
    for line, vertical in zip(cue.lines, offsets, strict=True):
        position = f"+{HORIZONTAL_OFFSET}+{vertical}"
        command.extend([
            "-fill", "black", "-stroke", "black", "-strokewidth",
            str(OUTLINE_WIDTH), "-annotate", position, line,
            "-fill", "white", "-stroke", "none", "-annotate", position, line,
        ])
    # Keep every event image in the same RGBA pixel format. A palette/monochrome
    # blank PNG can make FFmpeg's concat decoder silently drop later cue images.
    command.append("PNG32:" + str(path))
    run(command)


def image_bounds(path: Path) -> tuple[int, int, int, int]:
    info = run(
        ["magick", str(path), "-trim", "-format", "%w %h %X %Y", "info:"],
        capture=True,
    ).stdout.strip()
    width, height, x, y = map(int, info.split())
    return x, y, width, height


def concat_path(path: Path) -> str:
    if "'" in path.name or "\n" in path.name:
        raise ValueError(f"Unsupported generated filename: {path.name}")
    return f"file '{path.name}'\noption framerate 1000\n"


def write_overlay_timeline(work: Path, cues: list[Cue], duration: float) -> Path:
    blank = work / "blank.png"
    run(["magick", "-size", "1080x1920", "xc:none", "PNG32:" + str(blank)])
    segments: list[tuple[Path, float]] = []
    cursor = 0
    for number, cue in enumerate(cues, 1):
        if cue.start_ms > cursor:
            segments.append((blank, (cue.start_ms - cursor) / 1000))
        segments.append((work / f"cue_{number:04d}.png", (cue.end_ms - cue.start_ms) / 1000))
        cursor = cue.end_ms
    if cursor / 1000 < duration:
        segments.append((blank, duration - cursor / 1000))
    lines = ["ffconcat version 1.0\n"]
    for image, seconds in segments:
        if seconds <= 0:
            raise ValueError(f"Invalid overlay segment duration: {image.name} {seconds}")
        lines.append(concat_path(image))
        lines.append(f"duration {seconds:.6f}\n")
    lines.append(concat_path(blank))  # Final packet fixes the preceding duration.
    path = work / "subtitles.ffconcat"
    path.write_text("".join(lines), encoding="utf-8")
    return path


def encode(source: Path, overlay: Path, output: Path, stream: dict) -> None:
    bitrate = max(8_000_000, round(int(stream.get("bit_rate") or 20_000_000) * 1.02))
    profile = str(stream.get("profile", "High")).lower()
    if profile not in {"high", "main", "baseline"}:
        profile = "high"
    level = int(stream.get("level") or 41)
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-i", str(source), "-f", "concat", "-safe", "0", "-i", str(overlay),
        "-filter_complex",
        "[0:v:0]format=yuv420p[base];"
        "[1:v:0]format=rgba,fps=30000/1001[sub];"
        "[base][sub]overlay=x=0:y=0:format=auto:shortest=0:"
        "repeatlast=1:eof_action=pass[v]",
        "-map", "[v]", "-map", "0:a:0", "-c:v", "libx264",
        "-preset", "faster", "-profile:v", profile,
        "-level:v", f"{level // 10}.{level % 10}", "-pix_fmt", "yuv420p",
        "-r", FRAME_RATE, "-b:v", str(bitrate), "-minrate", str(bitrate),
        "-maxrate", str(bitrate), "-bufsize", str(bitrate * 2),
        "-x264-params", "nal-hrd=cbr:force-cfr=1", "-c:a", "copy",
        "-movflags", "+faststart", str(output),
    ]
    for option, key in (
        ("-color_primaries", "color_primaries"),
        ("-color_trc", "color_transfer"),
        ("-colorspace", "color_space"),
    ):
        value = stream.get(key)
        if value and value not in {"unknown", "reserved"}:
            command[-1:-1] = [option, value]
    run(command)


def verify(source: Path, output: Path) -> dict:
    in_video, in_audio, in_duration = media_info(source)
    out_video, out_audio, out_duration = media_info(output)
    if (out_video.get("codec_name"), out_video.get("width"), out_video.get("height"),
        out_video.get("r_frame_rate")) != ("h264", 1080, 1920, FRAME_RATE):
        raise RuntimeError(f"{output.name}: video format differs from 1080 x 1920 / 29.97 H.264")
    if out_audio.get("codec_name") != in_audio.get("codec_name"):
        raise RuntimeError(f"{output.name}: audio codec changed")
    if abs(out_duration - in_duration) > 0.05:
        raise RuntimeError(f"{output.name}: duration changed by {out_duration - in_duration:.3f}s")
    if (in_video.get("nb_frames") and out_video.get("nb_frames") and
        in_video["nb_frames"] != out_video["nb_frames"]):
        raise RuntimeError(f"{output.name}: video frame count changed")
    def audio_packet_hash(path: Path) -> str:
        return run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
             "-i", str(path), "-map", "0:a:0", "-c", "copy", "-f", "hash",
             "-hash", "sha256", "-"], capture=True,
        ).stdout.strip()
    if audio_packet_hash(source) != audio_packet_hash(output):
        raise RuntimeError(f"{output.name}: original audio packets were changed or trimmed")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-i",
         str(output), "-f", "null", "-"])
    return {
        "file": output.name,
        "source_duration": in_duration,
        "output_duration": out_duration,
        "frames": out_video.get("nb_frames"),
        "bytes": output.stat().st_size,
    }


def subtitle_region(path: Path, time_seconds: float) -> bytes:
    frame = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
         "-i", str(path), "-ss", f"{time_seconds:.3f}", "-frames:v", "1",
         "-vf", "crop=1080:230:0:1320,format=rgb24", "-f", "rawvideo", "-"],
        check=True, capture_output=True,
    ).stdout
    if len(frame) != 1080 * 230 * 3:
        raise RuntimeError(f"Could not read subtitle-region frame from {path.name}")
    return frame


def verify_subtitles(source: Path, output: Path, cues: list[Cue], frame_count: int) -> None:
    checks = {0, len(cues) // 2, len(cues) - 1}
    two_line = next((i for i, cue in enumerate(cues) if len(cue.lines) == 2), None)
    if two_line is not None:
        checks.add(two_line)
    for i in sorted(checks):
        cue = cues[i]
        center = (cue.start_ms + cue.end_ms) / 2000
        # The final cue can extend to the container's end, past the timestamp
        # of its last picture. Seek just before that picture so FFmpeg can
        # still return it while checking the cue at its actual frame time.
        last_picture_time = (frame_count - 1) * 1001 / 30000
        sample_time = min(center, max(0, last_picture_time - 0.001))
        if sample_time + 1001 / 30000 < cue.start_ms / 1000:
            raise RuntimeError(f"{output.name}: cue {i + 1} falls after the last video frame")
        original = subtitle_region(source, sample_time)
        rendered = subtitle_region(output, sample_time)
        changed_channels = sum(
            1 for before, after in zip(original, rendered, strict=True)
            if abs(before - after) > 80
        )
        if changed_channels < 1500:
            raise RuntimeError(
                f"{output.name}: cue {i + 1} is not visible at {sample_time:.3f}s "
                f"({changed_channels} changed channels)"
            )


def episode_number(path: Path) -> int:
    match = re.fullmatch(r"EP(\d+)\.mp4", path.name)
    if not match:
        raise ValueError(f"Unexpected video filename: {path.name}")
    return int(match.group(1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--srt-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--episodes", type=int, nargs="*")
    args = parser.parse_args()

    for executable in ("ffmpeg", "ffprobe", "magick", "fc-match"):
        if not shutil.which(executable):
            raise RuntimeError(f"Required local tool is unavailable: {executable}")
    font = japanese_font()
    sources = sorted(args.input_dir.glob("EP*.mp4"), key=episode_number)
    if args.episodes:
        wanted = set(args.episodes)
        sources = [path for path in sources if episode_number(path) in wanted]
        if len(sources) != len(wanted):
            raise ValueError(f"Missing requested episodes: {sorted(wanted - {episode_number(p) for p in sources})}")
    if not sources:
        raise ValueError("No test videos found")

    ready = []
    for source in sources:
        number = episode_number(source)
        srt = args.srt_dir / f"{number}.srt"
        cues = parse_srt(srt)
        video, _, duration = media_info(source)
        if (video.get("width"), video.get("height"), video.get("r_frame_rate")) != (1080, 1920, FRAME_RATE):
            raise ValueError(f"{source.name}: unexpected video size or frame rate")
        if cues[-1].end_ms / 1000 > duration + 0.05:
            raise ValueError(f"{srt.name}: cue ends after {source.name}")
        target = args.output_dir / source.name
        if target.exists():
            raise FileExistsError(f"Output already exists: {target}")
        ready.append((source, cues, video, duration, target))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for source, cues, video, duration, target in ready:
        work = Path(tempfile.mkdtemp(prefix=f".burn_{source.stem}_", dir=args.output_dir))
        try:
            for number, cue in enumerate(cues, 1):
                image = work / f"cue_{number:04d}.png"
                render_cue(image, cue, font)
                x, y, width, height = image_bounds(image)
                if x < 20 or x + width > 1060 or y < 1280 or y + height > 1510:
                    raise ValueError(f"{source.name} cue {number}: subtitle escapes reference region: {(x, y, width, height)}")
            timeline = write_overlay_timeline(work, cues, duration)
            partial = work / source.name
            encode(source, timeline, partial, video)
            result = verify(source, partial)
            verify_subtitles(source, partial, cues, int(video["nb_frames"]))
            os.replace(partial, target)
            result["cue_count"] = len(cues)
            print(json.dumps(result, ensure_ascii=False), flush=True)
        finally:
            shutil.rmtree(work)


if __name__ == "__main__":
    main()

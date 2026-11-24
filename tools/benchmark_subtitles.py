"""Time a fresh local Whisper process from import through a usable Japanese SRT."""

import argparse
import json
import subprocess
from pathlib import Path
from time import perf_counter


def stamp(milliseconds):
    seconds, millis = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("media", type=Path)
    parser.add_argument("--model", required=True, type=Path, help="Local MLX Whisper model directory")
    parser.add_argument("--out", required=True, type=Path, help="New SRT file")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Choose a new SRT filename.")
    duration = float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(args.media),
            ],
            text=True,
        )
    )
    started = perf_counter()
    import mlx_whisper

    result = mlx_whisper.transcribe(
        str(args.media),
        path_or_hf_repo=str(args.model.resolve()),
        language="ja",
        temperature=0.0,
        condition_on_previous_text=False,
    )
    cues = []
    previous_start = -1
    for s in result["segments"]:
        start = round(1000 * s["start"])
        end = min(round(1000 * s["end"]), round(1000 * duration))
        line = s["text"].strip()
        if not line:
            continue
        if not previous_start <= start < end or start < 0:
            raise ValueError(f"Invalid segment interval {start}..{end}")
        cues.append(f"{len(cues) + 1}\n{stamp(start)} --> {stamp(end)}\n{line}\n")
        previous_start = start
    if not cues:
        raise ValueError("The model returned no subtitle cues.")
    with args.out.open("x", encoding="utf-8") as f:
        f.write("\n".join(cues))
    elapsed = perf_counter() - started
    print(
        json.dumps(
            {"source_seconds": duration, "srt_cues": len(cues), "elapsed_seconds": round(elapsed, 3)}
        )
    )


if __name__ == "__main__":
    main()

"""Test that two PCM auditions preserve every sample after a named edit boundary."""

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import wave


def check(before, after, boundary):
    with wave.open(str(before), "rb") as a, wave.open(str(after), "rb") as b:
        if a.getparams() != b.getparams() or a.getcomptype() != "NONE":
            raise ValueError("Expected PCM WAVs of equal length, sample rate, width and channel count.")
        rate, frames = a.getframerate(), a.getnframes()
        boundary_frame = boundary * rate
        if boundary_frame != boundary_frame.to_integral_value() or not 0 < boundary_frame < frames:
            raise ValueError("Choose an exact sample boundary inside the audio.")
        start = int(boundary_frame)
        changed_opening = a.readframes(start) != b.readframes(start)
        first_hash, second_hash = hashlib.sha256(), hashlib.sha256()
        remaining = frames - start
        frame_bytes = a.getnchannels() * a.getsampwidth()
        while remaining:
            n = min(rate, remaining)
            left, right = a.readframes(n), b.readframes(n)
            if min(len(left), len(right)) != n * frame_bytes:
                raise ValueError("Truncated PCM data.")
            first_hash.update(left)
            second_hash.update(right)
            remaining -= n
        return {
            "duration_seconds": frames / rate,
            "sample_rate_hz": rate,
            "bits_per_sample": 8 * a.getsampwidth(),
            "channels": a.getnchannels(),
            "comparison_from_seconds": float(boundary),
            "tail_seconds": (frames - start) / rate,
            "tail_frames": frames - start,
            "opening_differs": changed_opening,
            "tail_matches": first_hash.digest() == second_hash.digest(),
            "before_tail_sha256": first_hash.hexdigest(),
            "after_tail_sha256": second_hash.hexdigest(),
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--from-seconds", type=Decimal, required=True)
    args = parser.parse_args()
    result = check(args.before, args.after, args.from_seconds)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["tail_matches"] else 1)

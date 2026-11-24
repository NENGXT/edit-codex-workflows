"""Measure one identifiable sound against a local printed mix; files are read-only."""
import argparse
import json
import math
import subprocess
import sys


def mono(path, start, length):
    import numpy as np
    from pathlib import Path
    data = subprocess.check_output([
        "ffmpeg", "-nostdin", "-v", "error", "-ss", str(start), "-i",
        str(Path(path).resolve(strict=True)), "-t", str(length), "-map", "0:a:0",
        "-vn", "-ac", "1", "-ar", "48000", "-f", "f32le", "-"
    ])
    return np.frombuffer(data, dtype="<f4").astype(np.float64)


def main():
    import numpy as np
    from scipy.signal import correlate
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference")
    parser.add_argument("output")
    parser.add_argument("--reference-at", type=float, required=True)
    parser.add_argument("--output-at", type=float, required=True,
                        help="intended timeline time for reference-at, seconds")
    parser.add_argument("--window", type=float, default=.35)
    parser.add_argument("--radius", type=float, default=.15)
    args = parser.parse_args()
    times = [args.reference_at, args.output_at, args.window, args.radius]
    if not all(math.isfinite(t) for t in times) or min(times) < 0 or min(times[2:]) <= 0:
        parser.error("use finite times in seconds and a positive window and radius")
    rate = 48000
    start = max(0, args.output_at - args.radius)
    x = mono(args.reference, args.reference_at, args.window)
    y = mono(args.output, start, args.output_at + args.window + args.radius - start)
    if len(x) < max(2, round(args.window * rate) - 1) or len(y) < len(x) + 2:
        raise ValueError("insufficient audio at the requested positions")
    x -= x.mean()
    energy = x @ x
    if energy / len(x) < 1e-12:
        raise ValueError("reference window is silent; choose an audible onset")
    n = len(x)
    def rolling_sum(z):
        total = np.r_[0., np.cumsum(z)]
        return total[n:] - total[:-n]
    variance = np.maximum(rolling_sum(y*y) - rolling_sum(y)**2 / n, 0)
    valid = np.isfinite(variance) & (variance > n * 1e-12)
    if not valid.any():
        raise ValueError("output search region has no usable signal")
    numerator = correlate(y, x, mode="valid", method="fft")
    scores = np.full(variance.shape, -np.inf)
    scores[valid] = numerator[valid] / np.sqrt(variance[valid] * energy)
    valid &= np.isfinite(scores) & (np.abs(scores) <= 1 + 1e-6)
    scores[~valid] = -np.inf
    scores[valid] = np.clip(scores[valid], -1, 1)
    if not valid.any():
        raise ValueError("no numerically reliable correlation in output")
    best = int(scores.argmax())
    distant = valid & (np.abs(np.arange(len(scores)) - best) > round(.012 * rate))
    if not distant.any():
        raise ValueError("search radius too narrow to judge uniqueness")
    alternative = float(scores[distant].max())
    # A quiet/periodic window or an edge peak is insufficient evidence to shift a track.
    reliable = bool(0 < best < len(scores)-1 and scores[best] >= .70 and scores[best]-alternative >= .08)
    offset = round((start + best/rate - args.output_at)*1000, 3) if reliable else None
    print(json.dumps(dict(offset_ms=offset,
                          correlation=round(float(scores[best]), 3),
                          competing_peak=round(alternative, 3), usable_marker=reliable)))
    return 0 if reliable else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ImportError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        sys.exit(f"Could not measure sync: {exc}")

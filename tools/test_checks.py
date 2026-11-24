"""Offline regressions for delivery checks. Uses only a temporary directory."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
from scipy.io.wavfile import write

SCRIPTS = Path(__file__).resolve().parent
RATE = 48000


class DeliveryChecks(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def check(self, script, status, *args):
        result = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, status, result.stdout + result.stderr)
        return json.loads(result.stdout) if result.stdout else {}

    def audio(self, name, samples):
        path = self.root / name
        write(path, RATE, samples.astype("float32"))
        return path

    def sync(self, reference, mix, t, status, window=.2):
        return self.check("check_sync.py", status, reference, mix,
                          "--reference-at", t, "--output-at", t, "--window", window)

    def test_per_segment_delays(self):
        rng = np.random.default_rng(47)
        x = np.zeros(3 * RATE)
        y = rng.normal(0, .005, len(x))
        markers = [(.5, .093), (1.5, -.047)]
        for t, delay in markers:
            segment = rng.normal(0, .2, RATE // 4)
            a, b = round(t * RATE), round((t + delay) * RATE)
            x[a:a+len(segment)] = segment
            y[b:b+len(segment)] += segment
        ref, mix = self.audio("ref.wav", x), self.audio("mix.wav", y)
        for t, delay in markers:
            self.assertAlmostEqual(self.sync(ref, mix, t, 0)["offset_ms"], delay * 1000, places=1)

    def test_unrelated_and_repeated_sound(self):
        rng = np.random.default_rng(123)
        x = rng.normal(0, .19, 2 * RATE)
        y = rng.normal(0, .19, len(x))
        y[:round(.56 * RATE)] = 0
        ref, mix = self.audio("ref.wav", x), self.audio("mix.wav", y)
        for window in (.1, .15, .2):
            self.assertIsNone(self.sync(ref, mix, .5, 2, window)["offset_ms"])
        tone = self.audio("tone.wav", np.sin(2*np.pi*500*np.arange(RATE*2)/RATE)*.2)
        self.assertIsNone(self.sync(tone, tone, .5, 2)["offset_ms"])

    def test_missing_picture_tail(self):
        path = self.root / "short-picture.mp4"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
                        "testsrc2=size=160x240:rate=25:duration=0.2", "-f", "lavfi", "-i",
                        "sine=duration=2", "-c:v", "libx264", "-c:a", "aac", str(path)], check=True)
        result = self.check("check_export.py", 2, path, "--size", "160x240", "--max-seconds", 2)
        self.assertFalse(result["spec_failures"])
        self.assertTrue(result["review"])
        video_end = float(result["stream_spans_seconds"]["video"][1])
        audio_end = float(result["stream_spans_seconds"]["audio"][1])
        self.assertAlmostEqual(audio_end - video_end, 1.8, places=2)


if __name__ == "__main__":
    unittest.main()

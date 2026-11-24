"""Render the cover and both case films from released extracts and production measurements."""

import argparse
import json
import math
import subprocess
import tempfile
from array import array
from functools import lru_cache
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw, ImageFont

from film_copy import DIALOGUE, EDIT

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "examples/speech/review"
AD = ROOT / "examples/edit"
W, H, FPS, SHOT = 960, 540, 24, 6
INK, WHITE, BLUE, GOLD = "#151c26", "#f3f0e6", "#a8c4ff", "#ffab72"
MUTED, RULE, LIGHT, RUST = "#adb7c6", "#485569", "#ded8c9", "#993f20"
CJK_FONT = None


@lru_cache(maxsize=140)
def face(size, numeric=False):
    paths = (["/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf"] if numeric else []) + [
        CJK_FONT,
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "NotoSansCJK-Regular.ttc",
    ]
    for path in filter(None, paths):
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            continue
    raise RuntimeError("Provide a Chinese/Japanese font with --font.")


def label(d, xy, value, size, color=WHITE, limit=None, numeric=False):
    while limit and size > 12 and d.textlength(value, font=face(size, numeric)) > limit:
        size -= 1
    d.text(xy, value, fill=color, font=face(size, numeric), anchor="lt")


def caption(d, value, color, line_color):
    d.line((36, 417, 924, 417), fill=line_color, width=1)
    # Keep captions above the area covered by native playback controls.
    english = value.isascii() or (" " in value and value[0].isascii() and "。" not in value)
    words = value.split() if english else list(value)
    joiner = " " if english else ""
    lines, line = [], ""
    for word in words:
        candidate = joiner.join(filter(None, [line, word]))
        if line and d.textlength(candidate, font=face(25)) > 885:
            lines.append(line)
            line = word
        else:
            line = candidate
    lines.append(line)
    if len(lines) > 3:
        raise ValueError(f"Caption exceeds frame: {value}")
    for i, row in enumerate(lines):
        label(d, (36, 435 + 33 * i), row, 25, color)


def intro(d, series, title, part, light=False):
    base, accent = (INK, RUST) if light else (WHITE, BLUE)
    label(d, (36, 25), series, 22, accent)
    label(d, (838, 24), f"{part + 1:02} / 06", 21, base, numeric=True)
    label(d, (34, 68), title, 48, base, 887)


def ff(*args):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *map(str, args)], check=True)


@lru_cache(maxsize=4)
def samples(path, width, height, limit):
    data = subprocess.check_output(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-i",
            str(path),
            "-an",
            "-vf",
            f"fps={FPS},scale={width}:{height}",
            "-frames:v",
            str(limit),
            "-pix_fmt",
            "rgb24",
            "-f",
            "rawvideo",
            "-",
        ]
    )
    stride = width * height * 3
    if not data or len(data) % stride:
        raise ValueError(f"Incomplete RGB frames in {path.name}")
    return [
        Image.frombytes("RGB", (width, height), data[i : i + stride]) for i in range(0, len(data), stride)
    ]


@lru_cache(maxsize=3)
def envelope(path):
    data = subprocess.check_output(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-i",
            str(path),
            "-t",
            "4.8",
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "s16le",
            "-",
        ]
    )
    pcm = array("h", data)
    count = 92
    peaks = [
        math.sqrt(
            sum(v * v for v in pcm[i * len(pcm) // count : (i + 1) * len(pcm) // count])
            / (len(pcm) // count)
        )
        for i in range(count)
    ]
    return peaks


def waveform(d, values, x, y, width, height, progress, color):
    for i, v in enumerate(values):
        head = x + i * width / len(values)
        extent = max(1, height * v)
        d.line(
            (head, y - extent, head, y + extent),
            fill=color if i / len(values) <= progress else RULE,
            width=2,
        )


BENCH = json.loads((REVIEW / "benchmark.json").read_text())
PITCH = json.loads((AD / "intonation.json").read_text())
EVENTS = json.loads((AD / "events.json").read_text())
VOICE_TRACKS = [REVIEW / "comparison.mp4", REVIEW / "acopy-voice.m4a", REVIEW / "scene.mp4"]


@lru_cache(maxsize=1)
def listening_peaks():
    tracks = json.loads((REVIEW / "listening.json").read_text())["tracks"]
    rows = [
        [value * 10 ** (track["playback_gain_db"] / 20) for value in envelope(path)]
        for path, track in zip(VOICE_TRACKS, tracks)
    ]
    ceiling = max(max(row) for row in rows)
    return [[value / ceiling for value in row] for row in rows]


def dialogue_frame(second, lang):
    c = DIALOGUE[lang]
    part, local = divmod(second, SHOT)
    i = int(part)
    im = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(im)
    if i < 3:
        label(d, (36, 26), c["series"], 22, BLUE)
        label(d, (36, 102), c["titles"][i], 47, WHITE, 322)
        label(d, (36, 185), ["ACOPY", "BS-RoFormer", "POST / ADR"][i], 28, GOLD if i == 2 else BLUE, 320)
        u = min(1, local / 4.8)
        waveform(d, listening_peaks()[i], 36, 283, 313, 51, u, GOLD if i == 2 else BLUE)
        label(d, (36, 355), c["trace"], 19, MUTED, 172)
        label(d, (226, 354), f"{min(local, 4.8):04.1f} / 4.8 s", 20, MUTED, numeric=True)
        frames = samples(VOICE_TRACKS[0], 406, 360, 116)
        im.paste(frames[min(int(local * FPS), len(frames) - 1)], (496, 47))
        # Original and dub use the same cut; accent is a listening cue.
        for j, name in enumerate(["ACOPY", c["dub"]]):
            x = 496 + 203 * j
            col = (GOLD if i == 2 else BLUE) if j == int(i == 2) else MUTED
            label(d, (x, 16), name, 20, col, 197)
            d.rectangle((x, 402, x + 202, 406), fill=col if j == int(i == 2) else RULE)
    else:
        intro(d, c["series"], c["titles"][i], i)
        if i == 3:
            for x, key, value, col in [
                (36, "duration", BENCH["source_seconds"], WHITE),
                (485, "elapsed", median(BENCH["runs_seconds"]), BLUE),
            ]:
                label(d, (x, 153), c[key], 21, MUTED)
                label(d, (x, 187), f"{value:.2f} s", 62, col, numeric=True)
            d.line((39, 302, 918, 302), fill=RULE, width=1)
            for start, end in BENCH["cue_intervals_seconds"]:
                x = 39 + 879 * start / BENCH["source_seconds"]
                endx = 39 + 879 * end / BENCH["source_seconds"]
                if local / 3.3 >= start / BENCH["source_seconds"]:
                    d.rectangle((x, 285, endx - 1, 319), fill=BLUE)
            label(d, (36, 356), f"{BENCH['cue_count']}  {c['cues']}", 27)
            label(d, (528, 358), c["batch"], 22, BLUE, 394)
        elif i == 4:
            for row, reading in enumerate(["拷問あるか", "ごめんあるから"]):
                y = 167 + row * 107
                label(d, (37, y), c["tracks"][row], 23, MUTED, 262)
                d.line((300, y + 12, 355, y + 12), fill=RULE, width=2)
                label(d, (383, y - 5), reading, 39, BLUE if row else WHITE)
            label(d, (37, 366), "Qwen3-ASR   /   27.0–31.8 s", 22, MUTED)
        else:
            for row, reading in enumerate(["ごめん、やるから", "手を貸せ。ご褒美やるから。"]):
                y = 170 + row * 110
                label(d, (37, y), c["versions"][row], 23, MUTED, 252)
                label(d, (311, y - 4), reading, 44, GOLD if row else MUTED, 600)
            d.line((310, 238, 620, 238), fill=RULE, width=1)
            label(d, (36, 365), "SRT   →   FFmpeg   →   MP4", 22, BLUE)
    caption(d, c["captions"][i], WHITE, RULE)
    return im


def edit_frame(second, lang):
    c = EDIT[lang]
    part, local = divmod(second, SHOT)
    i = int(part)
    im = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(im)
    intro(d, c["series"] if i < 3 else c["pickup"], c["titles"][i], i, True)
    progress = min(1, local / 2.2)
    if i == 0:
        frames = samples(ROOT / "examples/films/comment-comparison.mp4", 960, 540, 96)
        frame = frames[min(int(local * FPS), len(frames) - 1)]
        for version, box, y, height in [
            ("V3", (137, 33, 912, 166), 129, 102),
            ("V4", (137, 301, 912, 514), 239, 164),
        ]:
            label(
                d, (48, y + height // 2 - 18), version, 35, INK if version == "V3" else RUST, numeric=True
            )
            im.paste(frame.crop(box).resize((596, height), Image.Resampling.LANCZOS), (202, y))
    elif i == 1:
        for j, ((when, _), event) in enumerate(zip(EVENTS, c["events"])):
            x = 38 + j * 297
            active = local >= j * 1.5
            col = RUST if active else "#777a78"
            label(d, (x, 179), f"{when} s", 45, col, 279, True)
            d.line((x, 277, x + 274, 277), fill=col, width=4 if active else 1)
            d.ellipse((x, 271, x + 12, 283), fill=col)
            label(d, (x, 312), event, 28, INK, 278)
        label(d, (37, 376), c["eventlog"], 19, RUST)
    elif i == 2:
        for j, (name, ms) in enumerate(zip(c["sync"], [88, 44])):
            y = 178 + j * 102
            label(d, (36, y), name, 24, INK, 190)
            label(d, (255, y - 8), f"+{ms} ms", 43, INK, 221, True)
            d.line((478, y + 19, 736, y + 19), fill="#aba69b", width=3)
            x = 478 + ms * 2.55 * (1 - progress)
            d.ellipse((x - 7, y + 11, x + 8, y + 27), fill=RUST)
            label(d, (783, y - 8), "0 ms" if progress == 1 else "…", 42, RUST, numeric=True)
        label(d, (38, 371), f"36 + 4   /   {c['after']}", 24, RUST)
    elif i in (3, 5):
        labels = c["refs"] if i == 3 else c["pause"]
        values = [7.44, 8.48] if i == 3 else [2.50, 1.88, 1.94]
        scale = 44 if i == 3 else 165
        for j, (name, val) in enumerate(zip(labels, values)):
            y = 164 + (95 if i == 3 else 64) * j
            label(d, (36, y + 2), name, 22, INK, 245)
            d.rectangle(
                (314, y + 9, 314 + scale * val * min(1, max(0, (local - j * 0.17) / 1.45)), y + 20),
                fill=RUST if j == len(labels) - 1 else "#7e827d",
            )
            label(d, (776, y - 4), f"{val:.2f} s", 30, INK, numeric=True)
        label(d, (37, 373), "GPT-SoVITS v5 Turbo" if i == 3 else c["interval"], 22, RUST)
    else:
        for j, key in enumerate(("before", "after")):
            y = 201 + j * 78
            label(d, (36, y - 22), c["pitch"][j], 22, INK, 190)
            d.line((233, y, 906, y), fill=LIGHT, width=1)
            previous = None
            for n, v in enumerate(PITCH[key]):
                if v is None or n * PITCH["window_seconds"] > min(local, 2.16):
                    previous = None
                    continue
                pt = (235 + n * 18, y - v * 2.3)
                if previous:
                    d.line([previous, pt], fill=RUST if j else INK, width=4)
                previous = pt
        d.rectangle((37, 348, 257, 361), fill=RUST)
        d.rectangle((260, 348, 918, 361), fill="#909b95")
        label(d, (37, 373), "2.16 s", 21, RUST, numeric=True)
        label(d, (307, 372), f"6.32 s   /   {c['tail']}", 22, INK)
    caption(d, c["captions"][i], INK, "#aaa598")
    return im


def render(stage, frame, lang, poster):
    proc = subprocess.Popen(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{W}x{H}",
            "-r",
            str(FPS),
            "-i",
            "-",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(stage),
        ],
        stdin=subprocess.PIPE,
    )
    try:
        for n in range(6 * SHOT * FPS):
            im = frame(n / FPS, lang)
            if n == int(2.8 * FPS):
                im.save(poster, quality=92)
            proc.stdin.write(im.tobytes())
    finally:
        proc.stdin.close()
        status = proc.wait()
    if status:
        raise RuntimeError("FFmpeg encoding failed")


def preview(movie, output):
    # Give GitHub readers a short silent preview in their chosen language.
    cuts = "+".join(f"between(t,{start},{end})" for start, end in [(1, 3), (7, 9), (20, 22), (32, 34)])
    graph = (
        f"fps=8,select='{cuts}',setpts=N/(8*TB),scale=576:-2:flags=lanczos,"
        "split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer"
    )
    ff("-i", movie, "-an", "-filter_complex", graph, "-loop", "0", output)


def cover(output):
    im = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(im)
    label(d, (37, 33), "KUMA TSU   /   POST-PRODUCTION", 21, BLUE)
    label(d, (34, 135), "对白与剪辑", 73, WHITE, 440)
    label(d, (37, 241), "DIALOGUE  /  EDIT", 31, BLUE, numeric=True)
    dialogue = samples(VOICE_TRACKS[0], 406, 360, 116)[57]
    label(d, (512, 34), "ACOPY   /   ADR", 20, BLUE, numeric=True)
    im.paste(dialogue.crop((0, 46, 406, 239)), (512, 70))
    comment = samples(ROOT / "examples/films/comment-comparison.mp4", 960, 540, 96)[57]
    label(d, (512, 277), "COMMENT   /   V4", 20, GOLD, numeric=True)
    card = comment.crop((137, 301, 912, 514))
    im.paste(card.resize((406, 112), Image.Resampling.LANCZOS), (512, 310))
    waveform(d, listening_peaks()[0], 38, 367, 410, 47, 0.68, BLUE)
    d.line((37, 451, 920, 451), fill=RULE, width=1)
    label(d, (37, 475), "短剧字幕", 24, WHITE)
    label(d, (510, 475), "游戏广告剪辑与补声", 24, GOLD)
    im.save(output, quality=94)


def main():
    global CJK_FONT
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("output", type=Path)
    p.add_argument("--font")
    p.add_argument("--language", choices=list(DIALOGUE), action="append")
    args = p.parse_args()
    CJK_FONT = args.font
    args.output.mkdir(exist_ok=True, parents=True)
    cover(args.output / "cover.webp")
    with tempfile.TemporaryDirectory() as directory:
        stage = Path(directory) / "silent.mp4"
        for lang in args.language or DIALOGUE:
            suffix = "" if lang == "zh" else "-" + lang
            render(stage, dialogue_frame, lang, args.output / f"dialogue{suffix}.webp")
            levels = json.loads((REVIEW / "listening.json").read_text())["tracks"]
            filters = ";".join(
                f"[{i + 1}:a]aresample=48000,aformat=channel_layouts=stereo,volume={levels[i]['playback_gain_db']}dB,atrim=end=4.8,apad,atrim=end=6,asetpts=PTS-STARTPTS[a{i}]"
                for i in range(3)
            )
            ff(
                "-i",
                stage,
                "-i",
                VOICE_TRACKS[0],
                "-i",
                VOICE_TRACKS[1],
                "-i",
                VOICE_TRACKS[2],
                "-filter_complex",
                filters + ";[a0][a1][a2]concat=n=3:v=0:a=1,apad[a]",
                "-map",
                "0:v",
                "-map",
                "[a]",
                "-t",
                "36",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-movflags",
                "+faststart",
                args.output / f"dialogue{suffix}.mp4",
            )
            preview(args.output / f"dialogue{suffix}.mp4", args.output / f"dialogue-preview{suffix}.gif")
            render(
                args.output / f"edit{suffix}.mp4", edit_frame, lang, args.output / f"edit{suffix}.webp"
            )


if __name__ == "__main__":
    main()

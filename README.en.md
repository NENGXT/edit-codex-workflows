# Dialogue and editing

[中文](README.md) · [日本語](README.ja.md) · English

On a ten-episode Japanese drama, I spent hours rewinding noisy location recordings and typing dialogue onto an empty timeline. I now give the chat assistant a batch of episodes and have local speech models make a first subtitle pass. I watch the cut with those subtitles burned in, then go back to the lines and timings that need a second listen.

| Case | What to look for |
| --- | --- |
| [Subtitling a short drama](docs/dialogue.en.md) | Hear one line as recorded, with the voice isolated, and in the later dub. The 36-second film follows a misheard word through to the subtitle I corrected. |
| [Editing a game ad](docs/edit.en.md) | Compare the same four seconds of the opening comment in V3 and V4. The editing walkthrough also covers reaction timing and a voice pickup for a separate ad. [Play the four-second comparison](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/comment-comparison.mp4) |

The [round-by-round production notes (Chinese)](docs/conversations.md) trace what I asked for in chat, what changed in the next cut, and what I still had to check by ear.

## Run the examples

Install Python and FFmpeg, including ffprobe, then run these commands from the repository root.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python tools/test_checks.py
python tools/draw_plates.py out/plates
python tools/render_workflow.py out/films
```

The first script tests audio offsets, duplicated audio and picture ending early. The other two generate the illustrations and walkthrough films. The film renderer needs a font with Chinese and Japanese glyphs. Pass its path with `--font` if needed.

[Subtitle tools and models](models/README.md) · [Production tools](docs/production.md) · [Example chat requests](prompts/README.md) · [Practice audio credits](examples/speech/CREDITS.md)

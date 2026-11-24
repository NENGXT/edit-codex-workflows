# Getting one line right in the short drama 桜乱

[中文](dialogue.md) · [日本語](dialogue.ja.md) · English | [Home](../README.en.md)

Watch the 36-second walkthrough with [Chinese captions](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/dialogue.mp4) or [Japanese captions](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/dialogue-ja.mp4).

Listen to the first 18 seconds with sound on. The original ACOPY footage is on the left and the later dubbed cut is on the right. The action matches across both frames. You hear the location recording first, then the voice isolated from that recording, then the dub.

To draft subtitles for ten episodes, I specified the batch in chat and used local Whisper transcription. When background noise masked a line, I kept the original audio, isolated the voice and ran a second recognition pass. FFmpeg burned the draft subtitles into a review copy so I could check timing and wording against the performances.

For this excerpt, Qwen3-ASR returned “拷問あるか” on the original and “ごめんあるから” on the isolated voice. Both missed *gohōbi*, meaning “reward.” An earlier production draft had “ごめん、やるから.” After listening in context, I corrected the full line to “手を貸せ。ご褒美やるから。” (“Give me a hand. I’ll reward you.”)

[Hear the isolated voice (4.8 seconds)](../examples/speech/review/acopy-voice.m4a) · [Original audio transcript](../examples/speech/review/acopy-asr.srt) · [Isolated voice transcript](../examples/speech/review/acopy-voice-asr.srt) · [Models and production notes (Chinese)](../models/README.md)

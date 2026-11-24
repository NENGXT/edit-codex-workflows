# Four seconds at the start of a game ad

[中文](edit.md) · [日本語](edit.ja.md) · English | [Home](../README.en.md)

[Play the comment comparison (4 seconds, silent)](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/comment-comparison.mp4) · [Watch the editing walkthrough (36 seconds, Chinese)](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/edit.mp4)

In this vertical *Whiteout Survival* ad, the performer reads a viewer’s question. Watch the comment at the same instant in both exports. In V3, on top, the lines replace one another as he speaks. By the end of the question, the opening line has disappeared. I asked Codex to restore the whole comment card in ChatCut. In V4, below, the viewer can read all three lines as soon as the card appears.

**Timing the reaction.** At 42.83 seconds the player is still stuck. The first item comes out at 47.70, so that’s where I placed “できた！” (“I did it!”). On export, dialogue ran about 88 ms late and the end card about 44 ms late. I corrected the tracks separately and checked 36 dialogue onsets and four end-card cues. The portrait, landscape and 4:5 deliveries each ran 65.87 seconds, including the end card.

**A voice pickup for a separate ad.** A Japanese line was missing from the recording. Using authorized reference audio from the same speaker, I tried two readings with GPT-SoVITS v5 Turbo. The opening delivery produced a 7.44-second take. Using the closing, direct-to-camera delivery as reference produced an 8.48-second take. At 18 seconds in the walkthrough, the pitch traces show a later revision that flattened just the opening 2.16 seconds. The production record ends with audition takes.

[Cut timings](../examples/edit/events.json) · [Pitch comparison data](../examples/edit/intonation.json) · [Round-by-round notes (Chinese)](conversations.md)

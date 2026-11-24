# Game advertising | Finding the frame for a reaction, and the offset in an export

[中文](edit.md) · [日本語](edit.ja.md) · English · [Home](../README.en.md)

[Watch the 36-second English film](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/edit-en.mp4) · [Chinese](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/edit.mp4) · [Japanese](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/edit-ja.mp4)

**Start with the same instant in the opening.** The actor is answering a viewer’s question. In V3, each line replaces the last. In V4, I used Codex to change the comment card in ChatCut: the viewer can read the entire question before hearing the reply. Both images come from the actual portrait exports.

![The V3 comment changes line by line; the V4 comment is visible in full.](../examples/edit/comment-revision.gif)

[Watch the original four-second comparison, silent](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/comment-comparison.mp4)

## Put the reaction on the action

I kept gameplay, performance, dialogue, captions and the end card on separate tracks. At 36.37 s in the *Whiteout Survival* edit, the food finishes cooking: that gets “Whoa!” At 42.83 s the player still cannot push the item through. I held “I did it!” until the first item came out at 47.70 s. [Cut timings](../examples/edit/events.json)

| Revision | What I had checked | Recorded result |
| --- | --- | --- |
| Fix late sound | Measure dialogue and end card separately in the export | About 88 ms and 44 ms late. After separate corrections, 36 dialogue onsets and four end-card points measured 0 ms offset |
| Enlarge one caption at 20.5 s | Compare all 47 caption cards across the revision | The specified card went from size 42 to 74. The other 46 matched |
| Deliver three aspect ratios | Check the gameplay, inset, end card and duration in each | Portrait, landscape and 4:5 delivered at 1,976 frames, 65.87 s each, with the same approved mix |

I also extracted the AAC stream from V3 and all three V4 deliveries. All four streams had the same SHA-256 digest. [Delivery measurements](../examples/edit/deliveries.json)

## A voice pickup for a separate ad

One Japanese line was missing. With permission to clone the speaker’s voice, I selected two reference performances for GPT-SoVITS v5 Turbo. The same line and settings yielded 7.44 s with an opening reference and 8.48 s with a direct-to-camera closing reference. Changing one thing at a time let me hear what the delivery did to the pace.

Next I asked for a flatter opening. The two auditions are both 8.48 s long. The opening 2.16 s changed; **the final 6.32 s match across all 303,360 samples**. The film plots pitch from those takes in 60 ms bins, leaving gaps where pitch could not be measured. [Pitch data](../examples/edit/intonation.json) · [PCM comparison](../examples/edit/pickup-check.json)

Later I preferred the pauses in v5 Dev and the timbre in Qwen. I used the v5 reading to direct a new Qwen audition. The first pause moved from 2.50 s to 1.94 s, close to the 1.88 s reference. The production record ends with the audition export. [Five rounds of listening notes](conversations.en.md#a-voice-pickup-in-a-separate-ad)

To check your own material, use the [audio offset measurement](../tools/check_sync.py), [export check](../tools/check_export.py) or [sample-level comparison](../tools/check_pickup.py).

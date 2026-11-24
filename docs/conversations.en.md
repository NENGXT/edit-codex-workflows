# Inside the edit session

[中文](conversations.md) · [日本語](conversations.ja.md) · English · [Home](../README.en.md)

These are my instructions and decisions, paraphrased from the edit logs. A round ends where I saw or heard something that changed my next instruction.

## Drama subtitles

| What I asked for | What came back | What I did next |
| --- | --- | --- |
| Work through a batch episode by episode. Give me Japanese text with an in and an out for each cue. | Seven source files covering episodes 3–10 had 150 first-draft cues. Episodes 3 and 4 were in one file. | I could open an episode on a timed subtitle track and jump straight to a line. |
| Keep the location sound and extract the voice where the background covers the ending. | I had two readings at the same timecode. In the published scene Qwen heard different words on the two tracks. | I played the picture either side of the line. The character is offering a reward. |
| Join the two cues and keep the spoken “手を貸せ。ご褒美やるから。” | The original draft had “ごめん、やるから”. FFmpeg burned the revised SRT onto a review copy. | I checked the entry against the performance and the following cue. The public comparison includes the later studio dub as a third listening track. |

[Hear the three recordings](dialogue.en.md) · [Episode counts](../examples/speech/review/production.csv) · [Run timings](../examples/speech/review/benchmark.json)

## Game ad

The reaction timings, comment revision and three delivery sizes below belong to *Whiteout Survival*. Earlier work on a *Kingshot* opening was a separate edit.

1. **Keep the gameplay continuous.** I put the game, actor’s inset, recorded dialogue, caption cards and end card on separate tracks. I could move a reaction without changing the game’s speed.
2. **Place the reaction where the player succeeds.** The food finishes cooking at 36.37 s. At 42.83 s the player is still stuck. I held “できた！” until the first item came through at 47.70 s. In a later type-size correction, one card at 20.5 s went from 42 to 74. I compared all 47 cards after the change.
3. **Measure what the export actually plays.** Dialogue was about 88 ms late and the end card about 44 ms late. I had those tracks corrected separately, then checked 36 dialogue and four end-card onsets. All 40 measured on target.
4. **Let the viewer read the question first.** In V3 the opening comment changed one line at a time. I asked for the whole comment to stay on screen while the actor started to reply. You can see the change in the two real exports.
5. **Check the versions going to delivery.** I reviewed the actor’s framing, graphics and inset in portrait, landscape and 4:5. All three final files have 1,976 video frames. Their AAC audio matches the approved V3 stream byte for byte.

[Watch the comment change](edit.en.md) · [Frame and audio checks for the three exports](../examples/edit/deliveries.json)

## A voice pickup in a separate ad

| Round | What I changed | What I listened for |
| --- | --- | --- |
| 1 | A line was missing. With authorization for this voice and use, I chose a continuous reading from the opening as the reference for GPT-SoVITS v5 Turbo. | The first audition of the missing line ran 7.44 s. |
| 2 | I replaced the reference with two connected phrases delivered straight to camera in the closing shot. I kept the text, model, rate and seed fixed. | The new reading took 8.48 s. I could hear how the choice of performance affected the pace. |
| 3 | I asked to flatten the pitch on the opening words only, then auditioned a newly spoken opening as well. | For the local pitch edit, both files were 8.48 s. From 2.16 s to the end their samples match. |
| 4 | I tried Qwen, VoxCPM2 and GPT-SoVITS v5 Dev. I compared listening levels and asked for less harshness in the v5 Dev high end. | I liked the pauses in v5 Dev. Qwen had the cleaner timbre, but waited too long before its first pause. |
| 5 | I gave the selected v5 performance to Qwen as a timing reference. | The first pause moved from 2.50 s to 1.94 s, close to the reference at 1.88 s. The last documented result is an exported audition. |

[Compare the pitch traces](../examples/edit/intonation.json) · [Check the unchanged 6.32 s of audio](../examples/edit/pickup-check.json)

# 《桜乱》的一句台词，现场到底说了什么？

中文 · [日本語](dialogue.ja.md) · [English](dialogue.en.md)

先开声音。左边是飞书制作表「ACOPY」里的 7 月 19 日原片，右边是后来配过音的带水印审片。演员做同一个动作时，两版的声音差多少，听这几秒就知道。

![同一场戏的两版画面并排播放，左边为 ACOPY，右边为配音审片](../examples/films/dialogue-preview.gif)

[中文有声版 · 36 秒](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/dialogue.mp4) · [日本語版 · 36 秒](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/dialogue-ja.mp4)

先听左边的 ACOPY，再听从它分出的人声，最后听右边成片的后期配音。三个镜头里，两边的动作和切镜对齐。第 18 秒进入字幕制作，依次看十集起稿、两份听写结果和我当时改回的一句台词。原片取自旧第 5 集的 27.0–31.8 秒，成片取自新版第 4 集的 32.8–37.6 秒。想单听从原片分离出的人声，可以[播放这段 4.8 秒的音轨](../examples/speech/review/acopy-voice.m4a)。

**为什么我会用这套流程。** 一次拿到十集，让人从头听、倒回去找词，再一句句打时间码，光做出第一版字幕就很费神。我在对话里指定集数，让本机先按集听写；遇到环境声盖过台词，再把原声和单独提取的人声来回听。字幕压进画面后，我能直接看片，把时间留给有疑问的句子。

**有些字，人声分出来也照样会听错。** 这次让同一个 Qwen 模型听前两轨，原片的句尾被写成「拷問あるか」，分离后写成「ごめんあるから」。回看制作时的另一份记录，8 月 25 日版的初稿写的是「ごめん、やるから」。我当时把它改回「手を貸せ。ご褒美やるから。」意思是“帮我一把，我会给你奖励”。两份识别结果见下方字幕文件。

[查看现场声听写](../examples/speech/review/acopy-asr.srt) · [查看分离人声听写](../examples/speech/review/acopy-voice-asr.srt) · [字幕技术手册](../models/README.md) · [当时的改稿对话](conversations.md#短剧字幕)

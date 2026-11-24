# 『桜乱』の一言を字幕にするまで

[中文](dialogue.md) · 日本語 · [English](dialogue.en.md)　｜　[トップ](../README.ja.md)

[日本語解説を再生（36秒）](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/dialogue-ja.mp4)

最初の18秒は音を出して見てほしい。左がACOPYの素材、右が後からアフレコを入れた完成版。同じ動きに合わせて、元の音、そこから分離した声、最後に完成版の声が流れる。

10話分を一から耳で起こす代わりに、まず対話で対象の話数を指定して、Whisperで字幕の下書きを作った。雑音で聞き取りづらいところは元の音を残しつつ、声だけを分離してもう一度認識にかける。FFmpegで字幕を映像に焼き込み、セリフとタイミングを自分で確認する。

この抜粋をQwen3-ASRで聞き直すと、元の音では「拷問あるか」、分離後は「ごめんあるから」と出た。制作時の別の下書きには「ごめん、やるから」とあった。私が前後を聞いて直した字幕は「手を貸せ。ご褒美やるから。」だった。

[分離した声を聴く（4.8秒）](../examples/speech/review/acopy-voice.m4a) · [元の音の認識結果](../examples/speech/review/acopy-asr.srt) · [分離後の認識結果](../examples/speech/review/acopy-voice-asr.srt) · [モデルと制作手順（中国語）](../models/README.md)

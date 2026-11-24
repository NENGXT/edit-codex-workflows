# セリフと編集

[中文](README.md) · 日本語 · [English](README.en.md)

日本語の短編ドラマを10話まとめて扱うとき、一番時間がかかったのは、録音を巻き戻しながら一行ずつ字幕に起こす作業だった。今は対話で素材と範囲を指定し、ローカルの音声認識で下書きを作る。聞きづらい箇所と字幕のタイミングは、映像に戻って自分で確かめている。

| 制作例 | 見どころ |
| --- | --- |
| [短編ドラマの字幕](docs/dialogue.ja.md) | 同じセリフを現場音、分離した声、アフレコで聴き比べる。36秒の解説で、聞き違えた一語を直すところまで見られる。 |
| [ゲーム広告の編集と追加収録](docs/edit.ja.md) | 冒頭4秒のコメントをV3とV4で比較する。編集の解説では、ゲームの動きにリアクションを合わせた箇所と、別案件の追加音声の試作も紹介。 [冒頭4秒の比較を再生](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/comment-comparison.mp4) |

[制作時の対話をたどる（中国語）](docs/conversations.md)では、私がどこを指摘し、次の版に何が反映されたかを順にまとめた。

## 手元で試す

PythonとFFmpeg（ffprobeを含む）を用意し、リポジトリのルートで実行する。

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python tools/test_checks.py
python tools/draw_plates.py out/plates
python tools/render_workflow.py out/films
```

最初のスクリプトは音ズレ、音の重複、映像の早切れをテストする。次の二つは図版と解説映像を生成する。描画には中国語と日本語のフォントが必要で、`--font`で指定できる。

[字幕制作の技術メモ](models/README.md) · [制作ツール一覧](docs/production.md) · [対話の指示例](prompts/README.md) · [練習用音声のクレジット](examples/speech/CREDITS.md)

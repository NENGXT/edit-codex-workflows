# ゲーム広告｜反応を置くフレームと、音が入る瞬間

[中文](edit.md) · 日本語 · [English](edit.en.md) · [トップ](../README.ja.md)

[36秒の日本語版を再生](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/edit-ja.mp4) · [中文](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/edit.mp4) · [English](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/edit-en.mp4)

**まず冒頭の同じ瞬間を見る。** 演者が視聴者のコメントに答える場面。V3では一行ずつ入れ替わり、三行目に来ると最初の一行が消えていた。ChatCutのタイムラインをCodexから直し、V4では最初から全文を読める形にした。

![同じフレームで比べたV3とV4のコメント](../examples/edit/comment-revision.gif)

[書き出した映像の比較・4秒、無音](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/comment-comparison.mp4)

## 反応の編集と、書き出し後の確認

『Whiteout Survival』の映像、演者、セリフ、字幕、エンドカードを別トラックにした。36.37秒で食べ物が焼けたところに「うわ、すげえ！」。42.83秒ではまだ押しても進まない。最初の一つが出る47.70秒まで「できた！」を待った。[カット位置](../examples/edit/events.json)

| 指示 | 確認範囲 | 制作記録の結果 |
| --- | --- | --- |
| セリフの遅れを直す | セリフとエンドカードを別々に測定 | 遅れは約88msと44ms。補正後、セリフ36か所とエンドカード4か所で測定値は0ms |
| 20.5秒の字幕だけ大きくする | 修正前後の字幕47枚を比較 | 指定の1枚が42から74に変わり、残り46枚は一致 |
| 同じ映像を3種類の比率で納品 | 縦、横、4:5の画面と音を確認 | 各1,976フレーム、65.87秒。同じ確認済みミックスを使用 |

V3と3本のV4納品ファイルからAAC音声を取り出して照合した。4本のSHA-256はすべて一致した。[納品ファイルの検証結果](../examples/edit/deliveries.json)

## 別案件の追加音声

日本語の一言が録音素材に足りなかった。許諾済みの本人音声から参照する芝居を選び、GPT-SoVITS v5 Turboで同じセリフを試した。冒頭の読み方を参照した案は7.44秒、カメラ目線の締めを使った案は8.48秒。セリフも設定も同じにして、話し方の違いを聴いた。

次の指示は出だしの抑揚を抑えること。どちらも8.48秒の試作で、変更は最初の2.16秒に収まった。**残り6.32秒、303,360サンプルは一致**した。映像の線は実際の試作の音高。60msずつ集計し、測れない区間は空白にした。[音高データ](../examples/edit/intonation.json) · [波形の照合結果](../examples/edit/pickup-check.json)

その後、v5 Devの間合いとQwenの音色を選び、Qwenにv5の読みを手本として渡した。最初の間までが旧版の2.50秒から1.94秒になり、手本の1.88秒に近づいた。記録は試作音声の書き出しまで。[5回の試聴とその判断](conversations.ja.md#別の広告で不足していた声を補う)

自分のファイルで検証するには、[音ずれの測定](../tools/check_sync.py)、[書き出しの検査](../tools/check_export.py)、[変更範囲の照合](../tools/check_pickup.py)を使える。

# ゲーム広告の冒頭4秒を見比べる

[中文](edit.md) · 日本語 · [English](edit.en.md)　｜　[トップ](../README.ja.md)

[コメント部分の比較を再生（4秒・無音）](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/comment-comparison.mp4) · [編集の解説を見る（36秒・中国語）](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/edit.mp4)

『Whiteout Survival』の縦型広告で、出演者が視聴者のコメントを読み上げる。同じ4秒を上下に並べると、修正した理由がわかる。上のV3では読み上げに合わせて一行ずつ切り替わり、最後には質問の冒頭が消えてしまう。私はChatCut上でコメントを一枚のカードに戻すよう頼んだ。下のV4では、カードが出た時点で質問を三行とも読める。

**リアクションの位置。** 42.83秒では、ゲームの中でまだ先に進めない。最初の一つが出てくるのは47.70秒なので、「できた！」をそこに合わせた。書き出した動画ではセリフが約88ミリ秒、エンドカードの音が約44ミリ秒遅れていた。別々に補正し、セリフ36か所、エンドカード4か所の音の立ち上がりを再確認した。縦、横、4:5の各納品版は、エンドカード込みで65.87秒。

**別案件の追加音声。** 足りない日本語の一節は、使用許諾のある同じ話者の録音を使って試作した。GPT-SoVITS v5 Turboで冒頭の話し方を参照したテイクは7.44秒、カメラに語りかける終盤の話し方を参照したものは8.48秒。解説の18秒からは、冒頭2.16秒だけ抑揚を抑えた修正の前後を音高の線で見比べられる。記録は試聴版まで。

[実際のカット位置](../examples/edit/events.json) · [音高の比較データ](../examples/edit/intonation.json) · [やり取りの記録（中国語）](conversations.md)

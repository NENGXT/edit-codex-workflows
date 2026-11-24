# 我用 Codex 做对白和剪辑

我做日语短剧字幕和游戏广告后期。平时我在 Codex 对话里交代素材和要求，让它调用语音识别、整理时间码、检查导出。遇到一句话有两种解读，或者演员的反应快了半拍，我会回到声音和画面里做决定。

## 日语短剧 · 一句台词怎么定稿

<a href="docs/dialogue.md"><img src="examples/speech/cover.webp" width="480" alt="日语公开样音的声谱，亮色区域为发声段"></a>

**原声听写 → 疑句复听 → 字幕对时**

有一句初稿写成「ごめん、やるから」。连着上句再听，我改成了「ご褒美やるから」。前一句是在道歉，后一句是在说要给对方奖励。时间码能把我带回那几秒，最后用哪个词，还得听演员怎么说。

想看字幕怎么落到声音上，可以听下面这段公开样音「ありがとう」。录音长 1.30 秒，本机生成的字幕从 0.240 秒出现，到 1.120 秒结束。

[听公开样音](examples/speech/thanks.wav) · [看这句字幕](examples/speech/thanks.srt) · [看完整复核过程](docs/dialogue.md)

## 游戏广告 · 一句反应该落在哪一帧

<a href="docs/edit.md"><img src="examples/edit/cover.webp" width="480" alt="按广告剪点重绘的出料分镜"></a>

**标记画面动作 → 对齐演员反应 → 检查导出成片**

游戏里，42.83 秒时东西还推不进去。到 47.70 秒，升级后的第一份成品终于出来，我把演员的「できた！」（做到了！）接在这里。剪完再检查导出文件，发现主对白晚了约 88 毫秒，尾卡晚了约 44 毫秒。分轨校正后，这条片的 40 个起音测点全部对齐。

[看三个剪点和复测结果](docs/edit.md) · [打开剪点数据](examples/edit/events.json)

## 自己跑一次

| 你想做什么 | 从哪儿开始 | 会得到什么 |
| --- | --- | --- |
| 在 Mac 上给样音配字幕 | [本地模型与命令](models/README.md) | 一份 SRT 字幕和带时间的识别结果 |
| 检查自己的成片 | [剪辑记录里的两条检查命令](docs/edit.md) | 声音偏移量、音画时长及解码结果 |
| 用 Codex 做类似的制作任务 | [对话指令](prompts/README.md) · [交接表](templates/handoff.md) | 可以按自己项目改写的指令和交付清单 |

<details>
<summary>运行检查示例、生成演示插图</summary>

安装 Python 和 FFmpeg（含 ffprobe），在仓库目录运行以下命令。

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python tools/test_checks.py
python tools/draw_plates.py out/plates
```

检查脚本会生成临时音视频，测试声音偏移、重复声音和画面提前结束的情况。插图脚本用公开样音和剪点记录生成六张图，写入 `out/plates`。

</details>

字幕压制、配音试听和调色交接的工具收在[制作工具索引](docs/production.md)。公开样音由 Fukujinzuke 录制，出自 Lingua Libre。[样音来源与许可](examples/speech/CREDITS.md)

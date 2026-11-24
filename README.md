# 对白与剪辑

![对白与剪辑，蓝色声波接入橙色剪辑分镜](examples/films/cover.webp)

我在 Codex 对话里做两种后期工作。给短剧做字幕时，我要的是演员实际说出口的那句话。剪游戏广告时，我要观众先看见动作，再听见反应。遇到现有录音里没有的台词，我也会用获准的参考音色补一条试听，一版版调到说话节奏合适为止。

**[读完整的对话复盘](docs/conversations.md)**。从第一份稿、我指出的具体问题，一直写到下一版改了什么，以及哪些地方仍然要回听。

| 子项目 | 动画里可以看到什么 |
| --- | --- |
| [日语短剧字幕 · 18 秒](examples/films/dialogue.mp4) | 一句台词从「抱歉」改成「给你奖励」。最后播放一声公开日语录音，对着声音看字幕什么时候出现。 |
| [广告剪辑与补声 · 36 秒](examples/films/edit.mp4) | 演员那句「做到了」要等游戏出料。另一段追加口播从首版试听、改开头语调，到拿 v5 的节奏给 Qwen 作示范。 |

如果只看一个细节，可以从广告动画的 **第 18 秒**开始。两条音高线取自真实的调整前后录音。我要求「开头平一点」，两版都保留了 2.16 秒之后的原有声音。[查看两版数据](examples/edit/intonation.json)

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
python tools/render_workflow.py out/films
```

检查脚本会生成临时音视频，测试声音偏移、重复声音和画面提前结束的情况。插图脚本用公开样音和剪点记录生成六张图，写入 `out/plates`。最后一个命令用公开样音、音高数据和剪点重绘封面及两段 MP4，需要能显示中文和日文的字体；可以用 `--font` 指定字体文件。

</details>

字幕压制、配音试听和调色交接的工具收在[制作工具索引](docs/production.md)。公开样音由 Fukujinzuke 录制，出自 Lingua Libre。[样音来源与许可](examples/speech/CREDITS.md)

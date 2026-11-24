# 对白与剪辑

![对白与剪辑，蓝色声波接入橙色剪辑分镜](examples/films/cover.webp)

剪十集日语短剧，最耗神的是一边倒带听现场收音，一边把每句对白敲到时间线上。我让对话助手调用本机模型先出字幕，压出样片，自己看片改词。剪游戏广告时，我也在对话里指出具体的镜头、停顿和读法，再看下一版到底改对了没有。

**[读完整的对话复盘](docs/conversations.md)**。从第一份稿、我指出的具体问题，一直写到下一版改了什么，以及哪些地方仍然要回听。

| 子项目 | 动画里可以看到什么 |
| --- | --- |
| [短剧素材与审片字幕 · 36 秒](docs/dialogue.md) | 从五个拍摄日的机位卡找到对应集数，再听同一句后期配音的混音和分离人声。 |
| [广告剪辑与补声 · 36 秒](docs/edit.md) | 同一条开场评论，V3 逐句换，V4 三行一起出现。接着看游戏的反应剪点，以及另一条广告怎样补录日语。 |

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

检查脚本会生成临时音视频，测试声音偏移、重复声音和画面提前结束的情况。插图脚本用公开样音和剪点记录生成六张图，写入 `out/plates`。最后一个命令用样片节选、人声轨、音高数据和剪点生成封面及两段 MP4，需要能显示中文和日文的字体；可以用 `--font` 指定字体文件。

</details>

字幕压制、配音试听和调色交接的工具收在[制作工具索引](docs/production.md)。公开样音由 Fukujinzuke 录制，出自 Lingua Libre。[样音来源与许可](examples/speech/CREDITS.md)

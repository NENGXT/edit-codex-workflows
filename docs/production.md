# 制作工具索引

| 原工作环节 | 公开版 |
| --- | --- |
| 项目笔记、制作对话、剪辑方法 | [对白](dialogue.md)、[剪辑](edit.md)、[对话指令](../prompts/README.md)、[交接表](../templates/handoff.md)。专名、内部批注和私人链接已剥离。 |
| 短剧原声识别、逐句复核、对齐 | [模型与运行方法](../models/README.md)、可重跑的[公开录音和字幕](../examples/speech/)。 |
| 导出检查与音画同步 | [导出检查](../tools/check_export.py)、[起音对照](../tools/check_sync.py)和[离线测试](../tools/test_checks.py)。 |
| 字幕压制、审片拷贝 | [字幕样片](../tools/media/burn_reference_style_subtitles.py)和[Sample 审片水印](../tools/media/burn_sample_watermark.py)。输入、输出目录显式指定，保留工作区竖版 1080×1920、30000/1001 fps 的原始规格检查。另需 ImageMagick、Fontconfig 和可用日文字体。 |
| 画面与调色交接 | [灰片／定剪对照联系表](../tools/media/make_color_contact_sheets.py)。同一集上下两排并列，按各自片长取样。另附[场景交接模板](../templates/color.md)，原文件中的客户故事线、剧照及场景清单不进入公开版。 |
| 追加台词与配音试听 | [语音批处理](../tools/voice/)提供 GPU 环境准备、模型来源与校验、批次推理和空白任务。已有工作涉及 GPT-SoVITS、Qwen3-TTS、VoxCPM2 的试听；声音自然度、念法和情绪由人听。授权单、参考人声和仅对制作团队可见的样片留在原工程。 |
| 广告时间点与公开封面 | [剪点](../examples/edit/events.json)、[插图生成](../tools/draw_plates.py)。橙色分镜按剪辑记录绘制。 |

### 工具入口

```sh
python tools/media/burn_reference_style_subtitles.py --help
python tools/media/burn_sample_watermark.py --help
python tools/media/make_color_contact_sheets.py --help
```

配音目录是原 GPU 批次的可复用部分。任务需在有明确授权的参考音频和指定 T4 环境中执行。通用模型清单用于校验下载内容。账户登录、远程会话与上传下载绑定原私有工作区，公开版不附凭据或会话读取工具。本次公开演示只复跑本地 ASR 和剪辑交付检查。

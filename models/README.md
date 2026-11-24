# 技术手册 · 短剧字幕

| 我碰到的事 | 当时怎么处理 |
| --- | --- |
| 一批日语片源等着听写 | 我在对话里指定集数，调用本地 Whisper large-v3 起稿。每集留一份字幕，难句保留前后几秒，方便回听。 |
| 配乐、脚步和人声挤在一起 | 用 Demucs 或 BS-RoFormer 单独导出人声。遇到贴耳低语，我还会分别听原声左右声道和轻度增强版。分离有时会吃掉辅音，原声始终留着。 |
| 两种听法只差一个词 | 让 Qwen3-ASR-1.7B 再听一遍，对照画面和前后句，最后由我定词。 |
| 字是对的，出现得太早 | 用 Qwen3-ForcedAligner-0.6B 把确定的文字对回声音，输出起止时间。 |
| 逐集审片 | FFmpeg 把 SRT 压进视频副本。我看片，按集号、时间码和改词返修，再看修改位置。 |

以上按制作对话整理。作品集中的 4.8 秒现场声取自飞书 **ACOPY 的 EP5_0719.mp4**。本次用 BS-RoFormer 分离这段现场声，又让 Qwen3-ASR 和对齐器分别处理原声和分离后的人声。第三遍播放同一场戏的后期配音。下方用一条可以公开复跑的日语录音说明命令。

## 在 Mac 上复现日语字幕

这次公开样例使用 Apple Silicon、Python 3.13、mlx-qwen3-asr 0.3.5。两个 8-bit 模型分别负责听写和对齐。可先看仓库里的 WAV、JSON 和 SRT，再自行复跑。权重从模型发布者下载，下载一次后保存在本机。

```sh
python3.13 -m venv .venv-asr
. .venv-asr/bin/activate
python -m pip install 'mlx-qwen3-asr==0.3.5'
mlx-qwen3-asr examples/speech/thanks.wav --language Japanese \
  --model mlx-community/Qwen3-ASR-1.7B-8bit \
  --forced-aligner mlx-community/Qwen3-ForcedAligner-0.6B-8bit \
  --timestamps --output-format all --output-dir out/asr
```

已有完整本地模型时，把两个模型参数替换为各自的目录，可设置 HF_HUB_OFFLINE=1。本次公开录音长 1.301 秒，听写为「ありがとう。」，导出的字幕区间是 0.240–1.120 秒。机器、模型版本或音频变化时，以重新生成的结果为准。

| 制作环节 | 工作区模型与用法 |
| --- | --- |
| 全片日语候选 | [MLX Whisper Large-v3](https://huggingface.co/mlx-community/whisper-large-v3-mlx)，长段按有重叠的窗口识别。也使用过 [faster-whisper large-v3](https://huggingface.co/Systran/faster-whisper-large-v3)。 |
| 难句复核 | [Qwen3-ASR-1.7B 8-bit](https://huggingface.co/mlx-community/Qwen3-ASR-1.7B-8bit)，与 Whisper 分别给候选。 |
| 已知台词落点 | [Qwen3-ForcedAligner-0.6B 8-bit](https://huggingface.co/mlx-community/Qwen3-ForcedAligner-0.6B-8bit)。 |
| 背景很响时 | BS-RoFormer（ep_317_sdr_12.9755）与 Demucs 分离人声，再对照原声。分离可能吃掉气声。 |

工作中也用过 ASR API。本公开示例在本机完成，不需要向云服务提交录音。各模型沿用上游许可。

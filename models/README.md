# 在 Mac 上复现日语字幕

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

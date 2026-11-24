# 游戏广告｜把改片意见对到画面，把声音对回剪点

中文 · [日本語](edit.ja.md) · [English](edit.en.md) · [返回首页](../README.md)

[播放 36 秒中文解说](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/edit.mp4) · [日本語](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/edit-ja.mp4) · [English](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/edit-en.mp4)

**先看开场的同一秒。** 演员正要回应观众的一条评论。V3 跟着说话一行行换，读到第三行时第一行已经没了。我让 Codex 在 ChatCut 里改成 V4 的完整评论卡。观众可以先读问题，再看他怎么回答。下图直接截自两版竖屏导出。

![V3和V4的真实评论卡按同一帧比较](../examples/edit/comment-revision.gif)

[播放原画面对比 · 4 秒，无声](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/comment-comparison.mp4)

## 我给动作定剪点

游戏画面、演员、对白、字幕和尾卡分轨保留。我要改反应时，就能挪动那句声音和表演，保留游戏动作的先后。

| 《Whiteout Survival》成片时间 | 我看到的动作 | 我的剪辑决定 |
| --- | --- | --- |
| 36.37 s | 食物烤好 | 在这一下接「うわ、すげえ！」 |
| 42.83 s | 东西还推不进 | 留住卡顿，观众先看到他遇到什么问题 |
| 47.70 s | 升级后第一次出料 | 这时才接「できた！」 |

[三个原始剪点](../examples/edit/events.json)

## 导出后，我怎么知道改准了

| 改片意见 | 我让工具检查什么 | 制作记录里的结果 |
| --- | --- | --- |
| 对白听起来晚了 | 分别测主对白和尾卡的起音 | 两轨各晚约 88 ms、44 ms。分轨修正后，36 处对白和 4 处尾卡的起音偏移均为 0 ms |
| 20.5 秒这一张字卡太小 | 修改前后比对全部 47 张字幕卡 | 点名的卡片字号从 42 改为 74，其余 46 张一致 |
| 同一支片交三种画幅 | 分别检查竖版、横版、4:5 的游戏画面、小窗、尾卡和时长 | 三个画幅各 1,976 帧，计 65.87 秒，使用同一条确认过的混音 |

我又从 V3 和三个 V4 交付档里单独取出 AAC 音轨，四份数据的 SHA-256 完全相同。[三个画幅的核验记录](../examples/edit/deliveries.json)

40 处是这次导出的测点数。47 张是另一次字号返修的检查范围。两件事都能看出，给一句反馈之后，我怎样控制下一版究竟动了哪里。

## 另一次广告｜现有录音少了一句

我从获准使用的本人录音里选了两个参考片段。同一句日语、同一个 GPT-SoVITS v5 Turbo 设置，看片头说话的方式做出 7.44 秒，换成直视镜头的片尾语气是 8.48 秒。这样可以先试两种表演，判断哪种放进广告比较自然。

下一轮，我想把开头的抑扬收一点。两份 8.48 秒的试听中，**改动落在前 2.16 秒，后 6.32 秒的 303,360 个采样逐个相同**。动画的两条音高线取自试听文件，分段窗长 60 毫秒，测不到可靠音高的位置留空。[实际音高数据](../examples/edit/intonation.json) · [保留段的比对结果](../examples/edit/pickup-check.json)

我后来喜欢上 v5 Dev 的停顿，又更喜欢 Qwen 的音色。把 v5 的读法给 Qwen 作示范后，从开口到第一次明显停顿，旧版是 2.50 秒，示范是 1.88 秒，新版是 1.94 秒。制作记录止于试听导出。[五轮选音与改法](conversations.md#广告追加口播)

## 检查自己的导出

选一个在成片中容易辨认的起音。下例用自己的素材路径和时间替换参数。

```sh
python tools/check_sync.py voice.wav export.mp4 --reference-at 1.2 --output-at 11.2
python tools/check_export.py export.mp4 --size 1080x1920
python tools/check_pickup.py first.wav revised.wav --from-seconds 2.16
```

第一条报告声音相对预期位置的偏移，正值表示晚到。静音和重复节拍难以唯一定位，需换一个测点。第二条检查音画长度和解码。第三条比较两份等长 PCM WAV，打印指定位置之后的采样数和校验值。发行声道和音画偏移仍应在成片上检查。

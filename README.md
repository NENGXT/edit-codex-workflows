# 对白与剪辑

中文 · [日本語](README.ja.md) · [English](README.en.md)

![对白与剪辑。现场声波、短剧的同帧对照，以及游戏广告改过的评论卡。](examples/films/cover.webp)

做日语短剧，十来分钟素材也能拆出上百处对白。最花时间的是来回倒片、找每一句的头尾，再把它放进剪辑时间线。我在 Codex 里把这些动作接了起来。下面两个案例都有实际用过的素材、修改前后和测量记录。

### 短剧｜从一批现场录音，到剪辑师能用的字幕轨

《桜乱》第 3–10 集的 7 份原片，合计 **10 分 46 秒、150 条候选字幕**。我先让本机按集听写、切句、打时间码。遇到收音差的段落，我留下原声，另分一轨人声，再把两份听写放回同一镜头。剪辑师可以点到争议的那一句，直接改词和入点。

**单段测速**取了另一份 43.21 秒的未处理 ACOPY。在 Apple M4 上，三次独立运行都写出相同的 10 条 SRT，中位用时 **10.19 秒**。[看 36 秒有声解说](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/dialogue.mp4) · [按镜头听对比](docs/dialogue.md) · [逐集数量](examples/speech/review/production.csv) · [三次实测](examples/speech/review/benchmark.json)

### 广告｜从「这一句接早了」，到一个可以复查的剪点

《Whiteout Survival》的游戏里，42.83 秒东西还推不进，47.70 秒才第一次出料。我把演员的「できた！」放在出料那一刻。导出后，我又把对白和尾卡拆开量，分别修掉约 **88 ms 和 44 ms** 的延迟，再复测 **40 个起音**。

![同一帧的两张评论卡。V3 只显示演员正在读的一行；V4 在开头就展示完整问题。](examples/edit/comment-revision.gif)

另一个广告缺录了一句日语。我用获准的参考录音做克隆试听，让同一句分别按两种语气来读。后来我只想把开头念平一点。两份 8.48 秒的试听从 2.16 秒起，后面 **6.32 秒逐采样一致**。[看 36 秒剪辑与补声解说](https://github.com/NENGXT/edit-codex-workflows/raw/refs/heads/main/examples/films/edit.mp4) · [看剪点和试听数据](docs/edit.md)

### 看我是怎么一轮轮做的

[制作对话复盘](docs/conversations.md)把一轮请求、产出和下一轮修改放在一起。比如开场的评论卡一开始会逐句消失，我怎么说，改完哪一秒能看到区别。对话按原记录重述，表格和音高数据可以单独核对。

| 想复现哪一步 | 从这里开始 |
| --- | --- |
| 给自己的素材出一份日语字幕，测到落盘要多久 | [模型与实测方法](models/README.md) |
| 检查成片的声音偏移、画面长度和解码 | [剪辑案例里的检查命令](docs/edit.md#检查自己的导出) |
| 按项目改写对话指令、交接下一位剪辑师 | [制作指令](prompts/README.md) · [交接清单](templates/handoff.md) |
| 生成这里的封面和三语动画 | [制作工具与运行方法](docs/production.md) |

练习用的公开日语样音由 Fukujinzuke 录制，来自 Lingua Libre。[录音署名](examples/speech/CREDITS.md)

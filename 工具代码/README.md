# 工具代码（通用库）

Python + OpenCV + PIL 逐帧画画面，用管道送进 ffmpeg 编码；音频用 numpy 按配乐表混音。

## 文件

| 文件 | 作用 |
| --- | --- |
| style3.py | 字体路径、文字渲染、贴纸（emoji 白边）、照片卡片、印章、字幕 |
| own.py | 背景 `bg()`、玻璃徽章 `token()`、纸张卡片、印章、红笔圈/叉、箭头、主播画中画 `pip()`、人像抠图、`blit/put/cover/grab` |
| own2.py | 金属标题 `metal_title`、扫光 `sweep`、微光 `glow`、毛笔标题 `brush_title`、故障 `glitch`、粒子隧道 `tunnel`、网点背景 `halftone_bg`、角色徽章 `char_token`、通用抠图 `cut` |
| mix.py | 按配乐表（cue json）混音：人声分段并统一响度、音乐分段 + 说话时自动压低 + 停顿处抬升、音效按峰值对齐、整片两遍 loudnorm 到 -14 LUFS |
| synthfx.py | 合成小音效：shine / scribble / pop / type |
| setup.sh | 新容器里一键还原运行环境（见下） |

## 每期视频自己写的部分（放在那期的仓库里）

- **时间线**：一个场景列表 `S(口播起, 口播止, 画面函数)`，画面函数输入输出时间、返回一帧。
- **插入表 INSERTS**：`(口播时间, 时长, 类型)`。正数 = 在口播里插入停顿（大标题、梗视频）；负数 = 剪掉一段口播（长停顿、要删的词）。`T(n)` 口播时间→成片时间，`N(t)` 成片时间→口播时间。
- **配乐表**：`cues.py` 生成 json，交给 `mix.py`。
- 渲染：`python3 时间线.py video 输出.mp4 起 止`（成片秒数），两个进程并行；**内存只有 7 GB，最多同时开 2 个渲染进程，混音时不要渲染**。

## setup.sh 做了什么

代码里写死了一些路径（历史原因），`setup.sh` 用软链接把它们指到仓库：

- `/tmp/claude-0/mock`、`/tmp/claude-0/build` → 本文件夹
- `/tmp/claude-0/fonts/...` → `字体/`
- `/tmp/claude-0/music/ts/materials/audio/音乐素材/{音乐,音效}` → `音乐库/`
- 从 GitHub Releases 下载抠图模型到 `/tmp/claude-0/seg/`（u2net_human_seg、isnet-general-use）
- 可选：下载 sherpa-onnx 语音识别（SenseVoice 模型 + silero VAD），用于口播转写和逐字时间戳

每期视频仓库还要把口播和素材链接到 `own.py` 里的 `R`（见那期的 README）。

## 环境注意

- 网络通常只能访问 GitHub；pip、HuggingFace 可能不通。需要的 Python 包：numpy、opencv、pillow、onnxruntime、scipy。
- 系统字体：Noto CJK（思源黑体）和 Noto Color Emoji。
- 音源分离用 sherpa-onnx 的 spleeter-2stems，按 60 秒分段跑，否则内存溢出。

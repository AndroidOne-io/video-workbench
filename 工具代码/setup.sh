#!/usr/bin/env bash
# 在新容器里还原剪辑环境。用法：bash 工具代码/setup.sh [--asr]
set -e
WB="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p /tmp/claude-0
# 代码路径
for d in mock build; do [ -e /tmp/claude-0/$d ] || ln -s "$WB/工具代码" /tmp/claude-0/$d; done
# 字体
F=/tmp/claude-0/fonts; mkdir -p $F/cn $F/smiley $F/gf/ofl/mashanzheng $F/gf/ofl/bebasneue
for f in "$WB"/字体/*.ttf; do ln -sf "$f" $F/cn/; done
ln -sf "$WB/字体/SmileySans-Oblique.ttf" $F/smiley/
ln -sf "$WB/字体/MaShanZheng-Regular.ttf" $F/gf/ofl/mashanzheng/
ln -sf "$WB/字体/BebasNeue-Regular.ttf" $F/gf/ofl/bebasneue/
# 音乐库（两个配乐文件夹合并成一个「音乐」目录）
M=/tmp/claude-0/music/ts/materials/audio/音乐素材; mkdir -p "$M/音乐" "$M/音效"
for f in "$WB"/音乐库/配乐/* "$WB"/音乐库/配乐_科技解说/*; do ln -sf "$f" "$M/音乐/"; done
for f in "$WB"/音乐库/音效/*; do ln -sf "$f" "$M/音效/"; done
# 抠图模型
S=/tmp/claude-0/seg; mkdir -p $S
U=https://github.com/danielgatis/rembg/releases/download/v0.0.0
[ -s $S/u2h.onnx ] || curl -sSL -o $S/u2h.onnx $U/u2net_human_seg.onnx
[ -s $S/isnet.onnx ] || curl -sSL -o $S/isnet.onnx $U/isnet-general-use.onnx
# 语音识别（可选）
if [ "$1" = "--asr" ]; then
  A=/tmp/claude-0/asr; mkdir -p $A; cd $A
  R=https://github.com/k2-fsa/sherpa-onnx/releases/download
  [ -d sherpa-onnx-v1.13.8-linux-x64-static ] || curl -sSL $R/v1.13.8/sherpa-onnx-v1.13.8-linux-x64-static.tar.bz2 | tar xj
  [ -d sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17 ] || curl -sSL $R/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2 | tar xj
  [ -s silero_vad.onnx ] || curl -sSL -o silero_vad.onnx $R/asr-models/silero_vad.onnx
fi
python3 -c "import numpy, cv2, PIL, onnxruntime, scipy" && echo "环境就绪"

#!/usr/bin/env bash
# 04 — 把 PNG 序列编码成带 alpha 的 VP9 WebM。
#
# 用法：bash 04_encode_webm.sh [帧目录] [输出文件]
#   bash 04_encode_webm.sh ../frames ../assets/hair_wave.webm
#
# 参数逐条解释（这几个都不能省）：
#   -c:v libvpx-vp9      VP9 编码器。alpha 只有 vp9/vp8 在 WebM 里能带。
#   -pix_fmt yuva420p    带 alpha 的 4:2:0。必须是 yuva 开头，写 yuv420p 就把透明丢了。
#   -auto-alt-ref 0      ★ 必须关。开 alt-ref 帧时 libvpx 会把 alpha 通道写坏，
#                          播放时表现为"整块变黑"或"边缘一圈硬边"。
#   -b:v 0 -crf 30       恒定质量模式。alpha 边缘对 CRF 很敏感，30 是
#                        体积/锯齿的平衡点；要更干净的边缘用 26（体积约 1.6 倍）。
#   -metadata:s:v:0 alpha_mode=1
#                        告诉容器"这条流带 alpha"。少了这行 Chromium 会当普通视频播，
#                        透明区域变黑底。
#   -row-mt 1            多线程行并行，纯加速，不影响输出。
#
# 验证 alpha 有没有真的写进去（用 libvpx 解码器读，默认解码器不出 alpha）：
#   ffmpeg -c:v libvpx-vp9 -i hair_wave.webm -frames:v 1 -pix_fmt rgba /tmp/chk.png
#   python3 -c "import cv2;a=cv2.imread('/tmp/chk.png',-1)[...,3];print(a.min(),a.max())"
#   输出形如 0 255 才算对；如果 min 也是 255，说明 alpha 丢了。
set -euo pipefail

FRAMES="${1:-../frames}"
OUT="${2:-../assets/hair_wave.webm}"

ffmpeg -y -framerate 30 -i "$FRAMES/f_%04d.png" \
  -c:v libvpx-vp9 \
  -pix_fmt yuva420p \
  -auto-alt-ref 0 \
  -b:v 0 -crf 30 \
  -deadline good -cpu-used 2 \
  -row-mt 1 -threads 4 \
  -metadata:s:v:0 alpha_mode=1 \
  "$OUT"

echo "written: $OUT"
ffprobe -v error -show_entries stream=codec_name,width,height -show_entries format=duration,size \
  -of default=nw=1 "$OUT"

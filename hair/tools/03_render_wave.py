#!/usr/bin/env python3
"""03 — 离线渲染「头发飘动」帧序列（RGBA，带透明通道）。

为什么不是 moderngl / 三角网格
--------------------------------
网格 + 顶点位移的数学，等价于一张「位移场」作用于图像。三角化和光栅化只会
引入接缝（发丝边缘最容易露出来），而这个镜头只有 108 帧 —— CPU 上直接对
位移场做一次重采样（cv2.remap，双线性）大约 0.1 s/帧，全片 30 秒出完，
比配置 GL 上下文（无显示器环境还要 EGL/OSMesa）省事得多，也没有显存上限。

所以这里把「网格」推到无限细：每个像素都是一个顶点，位移量完全由权重图决定。
要换 GPU 版，把 `warp_frame()` 换成 moderngl 的纹理 + warp shader 即可，
位移场公式不用改。

位移公式
--------
    wave(t, w) = A_MAIN * sin(2π f_main t − K·w) + A_LOW * sin(2π f_low t)
    dx = w · wave · sign
    dy = DY_RATIO · dx

  · w        ← 权重图（发根 0，发梢 1），决定幅度从根到梢递增
  · −K·w     ← 相位延迟：发梢比发根晚 K 弧度起摆，波才「传」得出去
  · 第二项   ← 低频整体摆动，避免只剩高频正弦那种机械抖动感
  · sign     ← 主波走正弦，反向摆动时自然回摆，不用额外做回弹

首尾闭合：F_MAIN_CYCLES / F_LOW_CYCLES 取整数倍，t=0 与 t=DURATION 时
位移都等于 0，最后一帧和原图完全重合 —— 所以视频播完停在最后一帧不会跳。

用法：
    python3 03_render_wave.py
输出：
    <OUT_DIR>/f_0000.png ... （RGBA）
"""
import os
from pathlib import Path

import cv2
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

# ============================== 可调常量 ==============================
BASE    = Path(__file__).resolve().parents[2]        # 插件根目录
IMAGE   = BASE / "assets" / "splash.png"
MASK    = BASE / "hair" / "masks" / "hair_mask.png"
WEIGHT  = BASE / "hair" / "masks" / "hair_weight.png"
OUT_DIR = os.environ.get("HAIR_OUT", str(BASE / "hair" / "frames"))

W, H          = 1920, 1080     # 输出尺寸（要和插件里 cover 的显示尺寸比例一致）
DURATION      = 3.6            # 秒
FPS           = 30

A_MAIN        = 6.0            # 主波幅度，像素（乘在权重 1 的发梢上）
A_LOW         = 2.5            # 低频整体摆动幅度，像素
F_MAIN_CYCLES = 2              # 整段时长内主波走几个完整周期（整数=首尾闭合）
F_LOW_CYCLES  = 1              # 低频摆动周期数
PHASE_DELAY   = 1.60           # 发根→发梢的相位延迟，弧度（0=整片一起动，2.5=波浪明显）
DY_RATIO      = 0.35           # 纵向位移占横向的比例（头发主要横着飘）

DILATE_PX     = 12             # alpha 膨胀像素，必须 >= A_MAIN+A_LOW，否则位移会露出缺口
FEATHER_SIGMA = 2.0            # alpha 羽化 sigma
PREVIEW_ON_IMAGE = True        # 顺带合成一张「叠在底图上」的检查图到 OUT_DIR/preview
# =====================================================================


def load_assets():
    img = cv2.imread(IMAGE, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"读不到图: {IMAGE}")
    img = cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA)

    mask = cv2.imread(MASK, cv2.IMREAD_GRAYSCALE)
    weight = cv2.imread(WEIGHT, cv2.IMREAD_GRAYSCALE)
    if mask is None or weight is None:
        raise SystemExit(f"读不到 mask / weight: {MASK} {WEIGHT}")
    mask = cv2.resize(mask, (W, H), interpolation=cv2.INTER_LINEAR)
    weight = cv2.resize(weight, (W, H), interpolation=cv2.INTER_LINEAR)

    m = mask > 127
    w = (weight.astype(np.float32) / 255.0) * m       # mask 外权重归零
    w = np.clip(w, 0, 1)

    # alpha：mask 膨胀后羽化。膨胀区内的像素不位移，所以和底图像素一致，
    # 叠上去看不出来；但能兜住位移后边缘的缺口。
    alpha = cv2.dilate(m.astype(np.uint8),
                       cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                                 (DILATE_PX * 2 + 1, DILATE_PX * 2 + 1)))
    alpha = gaussian_filter(alpha.astype(np.float32), FEATHER_SIGMA)
    return img, m, w, np.clip(alpha, 0, 1)


def bbox_of(m, pad=20):
    ys, xs = np.where(m)
    return (max(ys.min() - pad, 0), min(ys.max() + pad, H),
            max(xs.min() - pad, 0), min(xs.max() + pad, W))


def warp_frame(img, w, t, y0, y1, x0, x1):
    """返回 bbox 区域的变形结果（BGR, uint8）。"""
    f_main = F_MAIN_CYCLES / DURATION
    f_low = F_LOW_CYCLES / DURATION
    # 减去 t=0 时刻的相位偏置：否则整片头发一开始就偏着，首帧和原图对不上。
    # 减掉之后 t=0 与 t=DURATION（整数周期）位移都严格等于 0。
    phase0 = np.sin(-PHASE_DELAY * w)
    wave = (A_MAIN * (np.sin(2 * np.pi * f_main * t - PHASE_DELAY * w) - phase0)
            + A_LOW * np.sin(2 * np.pi * f_low * t))
    dx = w * wave
    dy = DY_RATIO * dx

    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    map_x = (xx - dx[y0:y1, x0:x1]).astype(np.float32)
    map_y = (yy - dy[y0:y1, x0:x1]).astype(np.float32)
    return cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_REPLICATE)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    img, m, w, alpha = load_assets()
    y0, y1, x0, x1 = bbox_of(m)
    total = int(round(DURATION * FPS))
    print(f"渲染 {total} 帧 {W}x{H}，bbox=({x0},{y0})-({x1},{y1})")

    for f in range(total):
        t = f / FPS
        warped = warp_frame(img, w, t, y0, y1, x0, x1)

        frame = np.zeros((H, W, 4), np.uint8)
        frame[y0:y1, x0:x1, :3] = warped
        frame[y0:y1, x0:x1, 3] = (alpha[y0:y1, x0:x1] * 255).astype(np.uint8)
        cv2.imwrite(os.path.join(OUT_DIR, f"f_{f:04d}.png"), frame)

        if PREVIEW_ON_IMAGE and f in (0, total // 4, total // 2, 3 * total // 4):
            a = frame[..., 3:4].astype(np.float32) / 255.0
            comp = (frame[..., :3].astype(np.float32) * a + img.astype(np.float32) * (1 - a))
            cv2.imwrite(os.path.join(OUT_DIR, f"preview_{f:04d}.jpg"), comp.astype(np.uint8))

        if f % 20 == 0:
            print(f"  {f}/{total}")

    print("done")


if __name__ == "__main__":
    main()

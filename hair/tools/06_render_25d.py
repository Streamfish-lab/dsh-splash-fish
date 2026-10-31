#!/usr/bin/env python3
"""06 — 深度驱动的全图 2.5D 网格渲染（输出整帧序列）。

为什么不是 moderngl
-------------------
网格顶点位移在数学上就是一张位移场作用于图像。网格推到足够细之后，
GPU 光栅化和 CPU 双线性重采样的结果几乎一样，而这个镜头只有 108 帧，
CPU 上 cv2.remap 跑完不到 20 秒——省掉无显示器环境配 EGL/OSMesa 的麻烦。
真要 GPU 版：把 warp_frame 里的 cv2.remap 换成 moderngl 的纹理 warp shader，
位移场那几个函数一行都不用改。

它和上一版的区别（也是"纸片感"的处方）
--------------------------------------
上一版：位移只在头发 mask 内非零，mask 内每个像素位移量完全相同
        -> 一块贴纸在滑动，其余全图静止。
这一版四个改动：
  1. 驱动源是深度图，全图每个像素都有幅度，没有一块是死的；
  2. 幅度按深度分层：近处（飘在前面的发丝）大、远处（背景）小 -> 视差；
  3. 相位随空间位置变化 phase = 2π(PU·u + PV·v)，波横扫过去而不是整片齐动；
  4. 再叠一层高频湍流，同一区域内部相邻像素的位移也不一致
     -> 这一条是消灭"刚性平移"的关键，形变发生在区域内部而不是边界。

首尾闭合：所有正弦项周期数取整数，并各自减掉 t=0 的相位偏置。
于是 t=0 与 t=DURATION 时位移严格为 0，首帧 == 原图，末帧 == 原图。

用法：
    python3 06_render_25d.py
输出：
    <OUT_DIR>/f_0000.png ...   整帧（全图都在动）
"""
import os
from pathlib import Path

import cv2
import numpy as np

# ============================== 可调常量 ==============================
BASE    = Path(__file__).resolve().parents[2]
IMAGE   = BASE / "assets" / "splash.png"
DEPTH   = BASE / "hair" / "masks" / "depth.png"        # 05_depth.py 的输出
MASK    = BASE / "hair" / "masks" / "hair_mask.png"    # 头发范围（只用来加成幅度）
WEIGHT  = BASE / "hair" / "masks" / "hair_weight.png"  # 发根 0 / 发梢 1
OUT_DIR = os.environ.get("WALL_OUT", str(BASE / "hair" / "frames25d"))

W, H          = 1600, 900      # 按实际窗口尺寸给，别超过显示尺寸太多
DURATION      = 3.6
FPS           = 30
MESH_N        = 160            # 网格密度：位移场先降到 N×N 再插值回来，等效 N² 个顶点

A_BASE        = 1.2            # 全局基线幅度：最远的地方也动，保证没有"死区"
A_DEPTH       = 3.6            # 深度视差幅度（像素，depth=1 处）
A_HAIR        = 5.4            # 头发附加幅度（像素，hairWeight=1 处）
A_TURB        = 2.2            # 湍流幅度（像素）：给区域内部制造形变
A_BREATH      = 0.0027         # 全局呼吸缩放（0.45%），整图活着的最低基线

PHASE_U       = 1.6            # 相位沿横向扫过的强度
PHASE_V       = 0.9            # 相位沿纵向的强度
CYCLES        = (1, 2, 3)      # 三个波的周期数（必须整数，保证首尾闭合）
# =====================================================================


def load(path, flags=cv2.IMREAD_GRAYSCALE):
    img = cv2.imread(str(path), flags)
    if img is None:
        raise SystemExit(f"读不到: {path}")
    return img


def normalize(a):
    a = a.astype(np.float32)
    a -= a.min()
    a /= max(a.max(), 1e-6)
    return a


def smooth_noise(h, w, scale, rng):
    """低频随机场，返回大致 -1..1，用来做湍流。"""
    small = rng.random((max(h // scale, 2), max(w // scale, 2))).astype(np.float32)
    n = cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)
    n = cv2.GaussianBlur(n, (0, 0), sigmaX=scale * 0.5)
    n -= n.mean()
    n /= max(np.abs(n).max(), 1e-6)
    return n


def to_mesh(field, n):
    """把全分辨率位移场压到 n×n 网格，再插值回来 —— 这就是"顶点位移"。"""
    small = cv2.resize(field, (n, n), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (field.shape[1], field.shape[0]), interpolation=cv2.INTER_LINEAR)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    img = cv2.resize(cv2.imread(str(IMAGE), cv2.IMREAD_COLOR), (W, H), interpolation=cv2.INTER_AREA)
    depth = normalize(cv2.resize(load(DEPTH), (W, H), interpolation=cv2.INTER_CUBIC))
    mask = (cv2.resize(load(MASK), (W, H), interpolation=cv2.INTER_LINEAR) > 127).astype(np.float32)
    weight = normalize(cv2.resize(load(WEIGHT), (W, H), interpolation=cv2.INTER_LINEAR)) * mask
    weight = cv2.GaussianBlur(weight, (0, 0), 6)

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u = xx / W
    v = yy / H
    phase = 2.0 * np.pi * (PHASE_U * u + PHASE_V * v)

    rng = np.random.default_rng(7)
    turb_x = smooth_noise(H, W, 26, rng)
    turb_y = smooth_noise(H, W, 26, rng)

    # 基线 + 深度 + 头发：基线保证最远处也在动，深度给出视差，头发给出发丝额外的甩动
    amp = A_BASE + A_DEPTH * depth + A_HAIR * weight
    print(f"幅度场 min/mean/max = {amp.min():.2f}/{amp.mean():.2f}/{amp.max():.2f} px")

    f = [c / DURATION for c in CYCLES]

    def wave_terms(t):
        """三个波，各自减掉 t=0 的相位偏置 -> t=0 与 t=DURATION 都严格为 0。"""
        a = np.sin(2 * np.pi * f[0] * t + phase) - np.sin(phase)
        b = np.sin(2 * np.pi * f[1] * t - 0.7 * phase) - np.sin(-0.7 * phase)
        c = np.sin(2 * np.pi * f[2] * t + 2.1 * phase) - np.sin(2.1 * phase)
        return a, b, c

    total = int(round(DURATION * FPS))
    for i in range(total):
        t = i / FPS
        a, b, c = wave_terms(t)

        dx = amp * (0.62 * a + 0.38 * b) + A_TURB * turb_x * c
        dy = amp * (0.30 * a - 0.22 * b) * 0.9 + A_TURB * 0.7 * turb_y * c

        # 主波走网格（低频大范围）；湍流保留全分辨率（高频、内部形变）
        dx = to_mesh(dx, MESH_N) + (dx - to_mesh(dx, MESH_N))
        dy = to_mesh(dy, MESH_N) + (dy - to_mesh(dy, MESH_N))

        # 全局呼吸：坐标按画面中心整体缩放
        s = 1.0 + A_BREATH * np.sin(2 * np.pi * f[0] * t)
        cx, cy = W * 0.5, H * 0.5
        map_x = ((xx - cx) / s + cx - dx).astype(np.float32)
        map_y = ((yy - cy) / s + cy - dy).astype(np.float32)

        out = cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_REFLECT)
        cv2.imwrite(os.path.join(OUT_DIR, f"f_{i:04d}.png"), out)
        if i % 20 == 0:
            print(f"  {i}/{total}")

    print("done", OUT_DIR)


if __name__ == "__main__":
    main()

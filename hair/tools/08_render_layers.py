#!/usr/bin/env python3
"""08 — 分层渲染（配合 07 使用）：每层独立位移，前层快、后层慢。

只在跑过 07_split_layers.py、拿到 hair/layers/*.png + layers.json 之后才有用。
参数与 06 一致，区别是位移幅度按层缩放（layers.json 里的 amp），
并且在层与层之间加一点相位差，避免所有层同频同步（那样又会变回"整体平移"）。

用法：
    python3 08_render_layers.py
输出：
    <OUT_DIR>/f_0000.png ...
"""
import json
import os
from pathlib import Path

import cv2
import numpy as np

BASE = Path(__file__).resolve().parents[2]
LAYERS_DIR = BASE / "hair" / "layers"
OUT_DIR = os.environ.get("WALL_OUT", str(BASE / "hair" / "frames_layers"))

W, H = 1600, 900
DURATION, FPS = 3.6, 30
A_BASE = 2.0
PHASE_U, PHASE_V = 1.6, 0.9
CYCLES = (1, 2, 3)


def load_layer(path):
    rgba = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    rgba = cv2.resize(rgba, (W, H), interpolation=cv2.INTER_AREA)
    rgb = rgba[..., :3].astype(np.float32)
    a = rgba[..., 3:4].astype(np.float32) / 255.0
    return rgb * a, a                      # 预乘，方便直接相加


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    meta = json.loads((LAYERS_DIR / "layers.json").read_text(encoding="utf-8"))
    layers = []
    for i, layer in enumerate(meta):       # 远 -> 近
        pre, a = load_layer(LAYERS_DIR / f"{layer['name']}.png")
        layers.append({"pre": pre, "a": a, "amp": layer["amp"], "z": layer["z"],
                       "shift": i * 0.55})  # 每层错开一点相位

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    phase = 2.0 * np.pi * (PHASE_U * xx / W + PHASE_V * yy / H)
    f = [c / DURATION for c in CYCLES]

    total = int(round(DURATION * FPS))
    for i in range(total):
        t = i / FPS
        canvas = np.zeros((H, W, 3), np.float32)
        for L in layers:
            ph = phase + L["shift"]
            a = np.sin(2 * np.pi * f[0] * t + ph) - np.sin(ph)
            b = np.sin(2 * np.pi * f[1] * t - 0.7 * ph) - np.sin(-0.7 * ph)
            k = A_BASE + 6.0 * L["z"]
            k *= L["amp"]
            dx = (k * (0.62 * a + 0.38 * b)).astype(np.float32)
            dy = (k * 0.35 * (0.62 * a - 0.22 * b)).astype(np.float32)
            warped = cv2.remap(L["pre"], xx - dx, yy - dy,
                               interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            canvas += warped
        cv2.imwrite(os.path.join(OUT_DIR, f"f_{i:04d}.png"), np.clip(canvas, 0, 255).astype(np.uint8))
    print("done", OUT_DIR)


if __name__ == "__main__":
    main()

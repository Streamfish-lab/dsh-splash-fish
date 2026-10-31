#!/usr/bin/env python3
"""05 — 为插画生成深度图（Depth Anything V2 优先，MiDaS 兜底）。

为什么需要深度图：视差要让"近的东西动得快、远的动得慢"。没有深度，
所有像素只能一刀切给同一个幅度，那就必然回到"整块平移 = 纸片"。

三条路径，按可用性自动选：
  1) depth-anything-v2（推荐）—— 对插画/动漫泛化最好，small 版只有 ~100MB
  2) MiDaS DPT_Hybrid —— 备选，对扁平二次元图偏软
  3) --pseudo —— 完全离线，用亮度+位置凑一张近似深度，只用来跑通管线

安装（任选其一即可）：
    pip install torch torchvision
    pip install transformers          # Depth Anything V2 走 HF hub
  或
    pip install timm                  # MiDaS 走 torch.hub

用法：
    python3 05_depth.py --image ../../assets/splash.png --out ../masks/depth.png
    python3 05_depth.py --image ../../assets/splash.png --out ../masks/depth.png --pseudo

输出是灰度 PNG：
    255 = 最近（人物前面飘的头发）
      0 = 最远（背景）

注意两点：
  · 深度是"相对"的，不是真实尺度。渲染脚本里会再归一化一次。
  · Depth Anything 输出的是"逆深度"（越大越近），MiDaS 也是。不用翻转。
    只有当你换成某些输出"距离"的模型时，才需要 --invert。
"""
import argparse
from pathlib import Path

import cv2
import numpy as np


def pseudo_depth(rgb: np.ndarray) -> np.ndarray:
    """离线兜底：亮度越低越近 + 画面中心偏下略微更近。

    这个近似对"背景浅、人物深"的图成立，够验证管线，但不要拿它当正式深度：
    它分不清"深色的后发"和"深色的前发"。
    """
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    d = 1.0 - gray                              # 暗 -> 近
    d = cv2.GaussianBlur(d, (0, 0), sigmaX=max(rgb.shape[:2]) * 0.010)
    # 拉对比：背景（浅）压到 0 附近，暗发丝拉到 1 附近
    lo, hi = np.percentile(d, 15), np.percentile(d, 92)
    d = np.clip((d - lo) / max(hi - lo, 1e-6), 0, 1)
    d = cv2.GaussianBlur(d, (0, 0), sigmaX=max(rgb.shape[:2]) * 0.008)
    return (d * 255).astype(np.uint8)


def depth_anything(rgb: np.ndarray):
    from transformers import pipeline
    import torch

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    pipe = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf", device=0 if dev == "cuda" else -1)
    out = pipe(rgb)
    d = np.array(out["depth"], dtype=np.float32)
    if d.shape[:2] != rgb.shape[:2]:
        d = cv2.resize(d, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_CUBIC)
    return d


def midas(rgb: np.ndarray):
    import torch

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = torch.hub.load("intel-isl/MiDaS", "DPT_Hybrid", trust_repo=True).to(dev).eval()
    tf = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True).dpt_transform
    with torch.no_grad():
        inp = tf(rgb).to(dev)
        d = model(inp)
        d = torch.nn.functional.interpolate(d.unsqueeze(1), size=rgb.shape[:2],
                                            mode="bicubic", align_corners=False).squeeze()
    return d.cpu().numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--method", choices=["auto", "da2", "midas", "pseudo"], default="auto")
    ap.add_argument("--invert", action="store_true", help="模型输出的是距离而非逆深度时才加")
    args = ap.parse_args()

    bgr = cv2.imread(args.image, cv2.IMREAD_COLOR)
    if bgr is None:
        raise SystemExit(f"读不到图: {args.image}")
    # 深度不需要原始分辨率：缩到 1600 宽再算，快几十倍，也是渲染的工作分辨率
    if bgr.shape[1] > 1600:
        nh = round(bgr.shape[0] * 1600 / bgr.shape[1])
        bgr = cv2.resize(bgr, (1600, nh), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    method = args.method
    depth = None
    if method in ("auto", "da2"):
        try:
            depth = depth_anything(rgb)
            method = "depth-anything-v2"
        except Exception as e:                      # noqa: BLE001
            print(f"[da2 不可用] {type(e).__name__}: {e}")
            if args.method == "da2":
                raise
    if depth is None and method in ("auto", "midas"):
        try:
            depth = midas(rgb)
            method = "midas"
        except Exception as e:                      # noqa: BLE001
            print(f"[midas 不可用] {type(e).__name__}: {e}")
            if args.method == "midas":
                raise
    if depth is None:
        depth = pseudo_depth(rgb)
        method = "pseudo"

    depth = depth.astype(np.float32)
    if args.invert:
        depth = depth.max() - depth
    depth -= depth.min()
    depth /= max(depth.max(), 1e-6)
    # 轻度平滑：深度图的锯齿会在网格位移里被放大成"台阶"
    depth = cv2.GaussianBlur(depth, (0, 0), sigmaX=max(depth.shape) * 0.004)
    cv2.imwrite(args.out, (depth * 255).astype(np.uint8))
    print(f"depth ({method}) -> {args.out}  {depth.shape[1]}x{depth.shape[0]}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""02 — 从头发 mask 生成「发根 0 / 发梢 1」的渐变权重图。

权重图的作用：让位移幅度从发根到发梢递增。发根是长在头皮上的，
幅度必须是 0，否则整束头发会连根平移，看着像被人拽。

做法：把 mask 顶部一条横带当作「发根种子」，对整个画面做欧氏距离变换，
再在 mask 内归一化到 0-1。这样发梢（离根部最远）自然拿到最大值，
不需要手工描一根根发丝的走向。

用法：
    python3 02_make_weight.py --mask ../masks/hair_mask.png --out ../masks/hair_weight.png

参数：
    --root-y     发根种子带的底边（相对高度，默认 0.15，即画面顶部 15% 以内算发根）
    --blur       羽化 sigma（像素），让权重过渡连续，避免网格出现折痕
    --gamma      权重曲线指数。<1 让中段更快变大，>1 让幅度更集中在发梢
"""
import argparse
import cv2
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mask", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--root-y", type=float, default=0.15)
    ap.add_argument("--blur", type=float, default=9.0)
    ap.add_argument("--gamma", type=float, default=0.85)
    args = ap.parse_args()

    mask = cv2.imread(args.mask, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise SystemExit(f"读不到 mask: {args.mask}")
    H, W = mask.shape
    m = mask > 127

    # 发根种子：mask 内最上面那条带
    root = np.zeros_like(m)
    root[: int(H * args.root_y)] = True
    root &= m
    if not root.any():                      # 兜底：没有顶部种子就取最高的一行
        ys = np.where(m.any(1))[0]
        root[ys[0] : ys[0] + 3] = True

    dist = distance_transform_edt(~root)     # 每个像素到最近发根种子的距离
    w = dist.astype(np.float32)
    w /= max(w[m].max(), 1e-6)
    w = np.clip(w, 0.0, 1.0) ** args.gamma
    w = gaussian_filter(w, args.blur)        # 空间平滑，防止网格折痕
    w[~m] = 0.0
    w /= max(w[m].max(), 1e-6)

    cv2.imwrite(args.out, (w * 255).astype(np.uint8))
    inside = w[m]
    print(f"weight: {args.out}  ({W}x{H})  发根均值 {inside[inside < 0.15].mean():.3f}  "
          f"发梢均值 {inside[inside > 0.85].mean():.3f}")


if __name__ == "__main__":
    main()

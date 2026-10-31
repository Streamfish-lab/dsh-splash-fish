#!/usr/bin/env python3
"""07 — 备选方案：自动拆层 + 补全（只有 2.5D 效果不够时才走这条）。

为什么默认不走它
----------------
这套流程能给出真正的"前层快、后层慢"和逐层遮挡，是 Live2D 的路子。
但它有两个硬成本：

  1. 分割精度。逐根发丝之间的镂空，SAM2 在 1–3 px 的发丝上会糊成一片，
     必须手工修边。这张图头发层数多，修边会吃掉几个小时。
  2. 补全质量。刘海压在额头、长发压在肩和衣领，拆开后要补画被遮住的部分。
     LaMa 在动漫平涂上补出来的是"抹布"——而且补全区域只有静止时才看不出，
     一动就露。SD Inpaint 能好一些，但需要写 prompt 逐块重绘，风格很难统一。

2.5D 一个像素都不用补，失败模式也温和得多。所以先用 06。

它什么时候值得用：你愿意花半天到一天修 mask、调补全，并且要做真正的
"发丝前后穿插"。启动动画 3–4 秒、看一眼就过，投入产出不划算。

依赖：
    pip install torch torchvision
    pip install git+https://github.com/facebookresearch/sam2.git
    pip install simple-lama-inpainting        # LaMa 补全，CPU 也能跑
权重：checkpoints/sam2.1_hiera_large.pt

用法：
    python3 07_split_layers.py --image ../../assets/splash.png --out ../../hair/layers
输出：
    layers/<name>.png        每层 RGBA（含 alpha）
    layers/<name>_base.jpg   该层被移除后、补全出来的背景（调试用）
    layers/preview.png       叠回原样的检查图（应该和原图几乎一致）
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np

# ---------------------------------------------------------------- 图层定义
# 从远到近排。pos/neg 是相对坐标点，z 是视差深度，amp 是该层的位移放大系数。
LAYERS = [
    {"name": "hair_back", "z": 0.25, "amp": 0.45,
     "pos": [(0.62, 0.14), (0.58, 0.20), (0.66, 0.22)], "neg": [(0.56, 0.42), (0.20, 0.30)]},
    {"name": "body", "z": 0.45, "amp": 0.20,
     "pos": [(0.55, 0.72), (0.60, 0.80), (0.45, 0.90)], "neg": [(0.62, 0.20), (0.20, 0.30)]},
    {"name": "face", "z": 0.60, "amp": 0.06,
     "pos": [(0.56, 0.40), (0.58, 0.44), (0.54, 0.38)], "neg": [(0.70, 0.12), (0.20, 0.30)]},
    {"name": "hair_side", "z": 0.80, "amp": 0.75,
     "pos": [(0.86, 0.30), (0.90, 0.24), (0.78, 0.36)], "neg": [(0.56, 0.42), (0.20, 0.30)]},
    {"name": "hair_bang", "z": 1.00, "amp": 1.05,
     "pos": [(0.62, 0.22), (0.55, 0.14), (0.70, 0.10)], "neg": [(0.56, 0.44), (0.20, 0.30)]},
    {"name": "accessory", "z": 1.10, "amp": 0.85,
     "pos": [(0.78, 0.18), (0.52, 0.21)], "neg": [(0.62, 0.30), (0.20, 0.30)]},
]


def sam2_predictor(ckpt, config, device):
    import torch
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    model = build_sam2(config, ckpt, device=device)
    return SAM2ImagePredictor(model), device


def segment(predictor, rgb, layer):
    H, W = rgb.shape[:2]
    pts = np.array([[x * W, y * H] for x, y in layer["pos"] + layer["neg"]], np.float32)
    labels = np.array([1] * len(layer["pos"]) + [0] * len(layer["neg"]), np.int32)
    masks, scores, _ = predictor.predict(point_coords=pts, point_labels=labels, multimask_output=True)
    m = (masks[int(np.argmax(scores))] > 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 1:                                        # 只保留最大连通域
        keep = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        m = (lab == keep).astype(np.uint8)
    # 向上取整一点，避免层与层之间出现缝隙
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    return m


def inpaint(bgr, mask):
    """LaMa 补全。没有装 simple-lama 时退回 cv2.inpaint（质量差，仅兜底）。"""
    try:
        from simple_lama_inpainting import SimpleLama
        from PIL import Image

        lama = SimpleLama()
        out = lama(Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)),
                   Image.fromarray(mask * 255))
        return cv2.cvtColor(np.array(out), cv2.COLOR_RGB2BGR)
    except Exception as e:                            # noqa: BLE001
        print(f"  [LaMa 不可用，退回 cv2.inpaint] {type(e).__name__}")
        return cv2.inpaint(bgr, mask, 5, cv2.INPAINT_TELEA)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--checkpoint", default="checkpoints/sam2.1_hiera_large.pt")
    ap.add_argument("--config", default="configs/sam2.1/sam2.1_hiera_l.yaml")
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    bgr = cv2.imread(args.image, cv2.IMREAD_COLOR)
    H, W = bgr.shape[:2]
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    predictor, device = sam2_predictor(args.checkpoint, args.config, args.device)
    predictor.set_image(rgb)
    print(f"device = {device}")

    # 1) 逐层分割
    masks = {}
    for layer in LAYERS:
        m = segment(predictor, rgb, layer)
        masks[layer["name"]] = m
        print(f"  {layer['name']:12s} 面积 {m.mean() * 100:5.2f}%")

    # 2) 补全：每一层的"背景" = 原图把这一层抹掉后补出来的结果
    #    从近到远处理，近层的 mask 会一起被抹掉，所以远层拿到的背景是干净的
    for i in reversed(range(len(LAYERS))):
        layer = LAYERS[i]
        hole = masks[layer["name"]].copy()
        for near in LAYERS[i + 1:]:                   # 更近的层也要一起抹掉
            hole |= masks[near["name"]]
        base = inpaint(bgr, hole)
        cv2.imwrite(str(out / f"{layer['name']}_base.jpg"), base, [cv2.IMWRITE_JPEG_QUALITY, 92])

    # 3) 导出每层 RGBA。边界羽化 1px，避免叠加时出现硬边
    for layer in LAYERS:
        m = masks[layer["name"]]
        alpha = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.0)
        rgba = np.dstack([bgr, (alpha * 255).astype(np.uint8)])
        cv2.imwrite(str(out / f"{layer['name']}.png"), rgba)

    # 4) 叠回检查图：应该和原图几乎一样
    canvas = np.zeros_like(bgr, np.float32)
    for layer in LAYERS:
        rgba = cv2.imread(str(out / f"{layer['name']}.png"), cv2.IMREAD_UNCHANGED)
        a = rgba[..., 3:4].astype(np.float32) / 255.0
        canvas = rgba[..., :3].astype(np.float32) * a + canvas * (1 - a)
    cv2.imwrite(str(out / "preview.png"), canvas.astype(np.uint8))

    (out / "layers.json").write_text(json.dumps(LAYERS, indent=2), encoding="utf-8")
    print(f"written {out}  ({W}x{H})")


if __name__ == "__main__":
    main()

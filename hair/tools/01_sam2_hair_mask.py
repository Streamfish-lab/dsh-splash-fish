#!/usr/bin/env python3
"""01 — 用 SAM2 对插画做交互式点选分割，导出头发黑白 mask（尺寸与原图一致）。

为什么必须用 SAM2：这张图里头发和皮肤只差十几级灰度（头发 ~127，脸 ~145），
而且是冷色调打光，脸被蓝光染过，任何阈值/GrabCut 都会把脸颊并进头发。
SAM2 的第二阶段解码器能靠语义把这个边界分开。

准备（一次性）：
    pip install torch torchvision
    pip install git+https://github.com/facebookresearch/sam2.git
    # 权重放到 checkpoints/ 下
    #   SAM 2.1 Large : sam2.1_hiera_large.pt   (~900 MB, 质量最好)
    #   SAM 2.1 Base+ : sam2.1_hiera_base_plus.pt (~320 MB, 够用且快)
    # 下载地址：https://github.com/facebookresearch/sam2#model-descriptions

用法：
    python3 01_sam2_hair_mask.py \
        --image ../assets/splash.png \
        --out ../masks/hair_mask.png \
        --preview ../masks/hair_mask_preview.jpg

交互方式：脚本里的 POS / NEG 是相对坐标（0-1，左上角为原点）的点列表。
先按下面这组跑，看 --preview 的叠加图，不对就加点：
    POS 至少点：头顶、左右两侧发束、最外侧飘散发梢
    NEG 至少点：脸颊/额头皮肤、背景白点、衣领、肩
每个正点对应的 mask 会取 SAM2 给出的最高分候选。

输出：
    <out>.png          头发 mask，0/255，与原图同尺寸（未羽化，羽化在渲染时做）
    <out>_preview.jpg  叠加预览，用来肉眼核对
"""
import argparse
import cv2
import numpy as np

# ---------------------------------------------------------------- 交互点
# 相对坐标 (x, y)，基于你给的这张图。换图请重新点。
POS = [
    (0.70, 0.10),   # 头顶
    (0.62, 0.22),   # 头发中部
    (0.55, 0.14),   # 前额上方
    (0.88, 0.27),   # 右侧发束
    (0.94, 0.22),   # 最外侧飘散发梢
    (0.50, 0.24),   # 左侧发束
]
NEG = [
    (0.56, 0.40),   # 脸颊
    (0.58, 0.34),   # 眼睛附近
    (0.20, 0.25),   # 左侧背景
    (0.96, 0.06),   # 右上背景
    (0.55, 0.68),   # 衣领 / 肩
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--preview", default=None)
    ap.add_argument("--checkpoint", default="checkpoints/sam2.1_hiera_large.pt")
    ap.add_argument("--config", default="configs/sam2.1/sam2.1_hiera_l.yaml")
    ap.add_argument("--device", default=None, help="cuda / mps / cpu，默认自动")
    args = ap.parse_args()

    import torch
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor

    if args.device:
        device = args.device
    elif torch.cuda.is_available():
        device = "cuda"
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"device = {device}")

    bgr = cv2.imread(args.image, cv2.IMREAD_COLOR)
    if bgr is None:
        raise SystemExit(f"读不到图片: {args.image}")
    H, W = bgr.shape[:2]
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    sam2 = build_sam2(args.config, args.checkpoint, device=device)
    predictor = SAM2ImagePredictor(sam2)
    predictor.set_image(rgb)

    pts = np.array([[x * W, y * H] for x, y in POS] + [[x * W, y * H] for x, y in NEG], np.float32)
    labels = np.array([1] * len(POS) + [0] * len(NEG), np.int32)

    masks, scores, _ = predictor.predict(
        point_coords=pts, point_labels=labels, multimask_output=True
    )
    best = int(np.argmax(scores))
    mask = (masks[best] > 0.0).astype(np.uint8)
    print(f"mask {mask.shape}  score={scores[best]:.4f}  面积 {mask.mean() * 100:.2f}%")

    # 只保留最大的连通域，去掉零碎误检
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask, 8)
    if n > 1:
        keep = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        mask = (lab == keep).astype(np.uint8)
    # 填掉头发高光造成的小洞（不改外轮廓）
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))

    cv2.imwrite(args.out, mask * 255)
    if args.preview:
        vis = bgr.copy()
        sel = mask.astype(bool)
        vis[sel] = (vis[sel] * 0.45 + np.array([0, 140, 255]) * 0.55).astype(np.uint8)
        cv2.imwrite(args.preview, vis)
    print(f"written {args.out}  ({W}x{H})")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build client.js from client.template.js, inlining the artwork and the hair video.

Usage:  python3 build.py [path/to/artwork.png|jpg|webp] [width]

Two assets get inlined as data:
  · the still artwork  -> WebP, embedded in a CSS custom property
  · the hair video     -> WebM, embedded as base64 and turned into a Blob at runtime

The WebM is optional: if assets/hair_wave.webm is missing, the placeholder is
replaced with an empty string and the plugin simply plays without the hair layer.
"""
import base64, io, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "client.template.js"
OUT = ROOT / "client.js"
# 优先用深度驱动的 2.5D 全帧视频；没有就退回上一版的头发层视频
WEBM = ROOT / "assets" / "wall_25d.webm"
if not WEBM.exists():
    WEBM = ROOT / "assets" / "hair_wave.webm"

default_src = ROOT / "assets" / "splash.png"
if not default_src.exists():          # 仓库里不放 15 MB 的原图，回退到压缩版
    default_src = ROOT / "assets" / "splash.webp"
src_img = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else default_src
width = int(sys.argv[2]) if len(sys.argv) > 2 else 1600

try:
    from PIL import Image
    im = Image.open(src_img).convert("RGB")
    if src_img.suffix.lower() == ".webp" and im.width <= width:
        raw = src_img.read_bytes()      # 已经是压好的，别二次压缩
    else:
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=82, method=6)
        raw = buf.getvalue()
        (ROOT / "assets").mkdir(exist_ok=True)
        (ROOT / "assets" / "splash.webp").write_bytes(raw)
    mime = "image/webp"
except ImportError:
    mime = "image/png" if src_img.suffix.lower() == ".png" else "image/jpeg"
    raw = src_img.read_bytes()

data_uri = "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode())

webm_b64 = ""
if WEBM.exists():
    webm_b64 = base64.b64encode(WEBM.read_bytes()).decode()

js = (SRC.read_text(encoding="utf-8")
         .replace("__IMG_DATA_URI__", data_uri)
         .replace("__HAIR_WEBM_B64__", webm_b64))
OUT.write_text(js, encoding="utf-8")
print("client.js  %.0f KB  (artwork %.0f KB, hair video %.0f KB%s)" % (
    len(js) / 1024, len(raw) / 1024, len(webm_b64) * 3 / 4 / 1024,
    "" if webm_b64 else " — 未找到 hair_wave.webm，头发层关闭"))

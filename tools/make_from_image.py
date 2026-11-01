#!/usr/bin/env python3
"""把任意一张图换成开屏插画。

    python3 tools/make_from_image.py 我的图.jpg

它会居中裁成 16:9、缩到 1600×900、重新生成 client.js。
把生成的 client.js 覆盖到插件目录，重启 dsh 就能看到。

不需要深度图，也不需要头发视频。画面里仍然有显影、光晕、光扫、粒子和淡出，
只是没有头发飘动那一层——那一层要用 hair/tools/ 里那套离线渲染流程。
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

if len(sys.argv) < 2:
    print("用法: python3 tools/make_from_image.py 你的图.jpg")
    sys.exit(1)

src = pathlib.Path(sys.argv[1].strip().strip('"').strip("'"))
if not src.exists():
    print("找不到文件:", src)
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("需要 Pillow，先装一下：")
    print("    pip install pillow")
    sys.exit(1)

im = Image.open(src).convert("RGB")
w, h = im.size

# 居中裁成 16:9，比拉伸好——拉伸会把脸压扁
target = 16 / 9
if w / h > target:
    nw = int(round(h * target))
    box = ((w - nw) // 2, 0, (w + nw) // 2, h)
else:
    nh = int(round(w / target))
    box = (0, (h - nh) // 2, w, (h + nh) // 2)
im = im.crop(box).resize((1600, 900), Image.LANCZOS)

assets = ROOT / "assets"
assets.mkdir(exist_ok=True)
out = assets / "splash.webp"
im.save(out, "WEBP", quality=86, method=6)
print("原图 %dx%d -> 裁切 %dx%d -> 1600x900，已写入 assets/splash.webp" % (w, h, box[2] - box[0], box[3] - box[1]))

# 复用 build.py：它会把这张图内联进 client.js
sys.path.insert(0, str(ROOT))
import importlib.util

spec = importlib.util.spec_from_file_location("build", ROOT / "build.py")
build = importlib.util.module_from_spec(spec)
sys.argv = ["build.py", str(out), "1600"]
spec.loader.exec_module(build)

print("")
print("下一步：把 %s 覆盖到插件目录里的 client.js，重启 dsh。" % (ROOT / "client.js"))
print("插件目录一般是 D:\\dsh-plugins\\dsh-splash-fish\\ 这种地方，认 package.json 那一层。")

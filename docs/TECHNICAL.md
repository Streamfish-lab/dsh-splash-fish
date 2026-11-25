# 实现细节

主 README 里没展开的东西都放这儿。不关心实现可以跳过，不影响用。

## 为什么做成视频

一开始是纯 CSS，让头发那块区域平移几个像素。效果很差：单张图里头发和脸是同一批像素，平移就等于连着脸一起拽，看着像有人扯纸片。

后来改成离线渲染。用深度图算每个像素该移动多少，近的动得多、远的动得少；用发根到发梢的权重控制幅度递增；加空间相位让波形扫过去，再加一层高频湍流让区域内部也发生形变。渲染 108 帧，编码成 WebM，运行时当视频层播。

位移公式，参数都在 `hair/tools/06_render_25d.py` 顶部：

```
amp = A_BASE + A_DEPTH·depth + A_HAIR·hairWeight
φ   = 2π(PHASE_U·u + PHASE_V·v)
dx  = amp·(0.62·sin(2πf₁t+φ) + 0.38·sin(2πf₂t−0.7φ)) + A_TURB·turb·sin(2πf₃t+2.1φ)
```

所有波走整数个周期，再减掉 t=0 时的相位偏置，这样首帧和末帧的位移都正好是 0。视频播完直接摘掉，画面不会跳。

## 接入时踩到的三个坑

**视频得跟底图一起缩放。** `.sf-bg` 上有 `sfFocus`（1.14 缩到 1.02）和 `sfDrift`（1.02 到 1.06）两条动画，还有模糊。视频如果作为兄弟节点放进去，4.3 秒时底图已经是 1.06 倍而视频还是 1 倍，头发会飘到脸外面。解决办法是把 `<video>` 塞进 `.sf-bg` 内部，子元素继承父节点的 `transform` 和 `filter`。

**插件没有打包器。** `client.js` 是被 `__ModuleLoader__.load()` 直接执行的，没有 webpack，也没有 `import.meta.url`，包目录里的 webm 根本引用不到。只能把视频转成 base64 内联，运行时 `atob` → `Blob` → `createObjectURL`。不要直接用 `data:` 当 `video.src`，那个有长度限制，而且有些 Chromium 版本对 data URI 的视频不带 alpha。

**视频 3.6 秒，时间轴 4.4 秒。** 播完停在最后一帧，如果那帧头发还飘着，后面 0.8 秒就定格在一个歪掉的位置。所以渲染时必须保证首尾位移是 0，播完摘掉才看不出来。

## 为什么不闪 dsh 自带的启动画面

dsh 自带的启动画面（`[data-dsh-boot]`，HARNESS 加转圈加 Loading plugins）在任何客户端插件被实例化之前就画好了，光靠 client 半边怎么都追不上。

能用的是 `webserver/index-inject`，它收集的注入行会在 index.html 解析阶段就渲染。`lib/index.js` 推了两行：一条样式铺同色封面，一条脚本负责在 client 挂载时把封面摘掉，另外设了 3.5 秒兜底。

几个要注意的地方，都是试出来的：

- 只推 `style` 和 `script` 两种。行类型是闭集，写个不认识的会导致 boot gate reject，桌面端直接进崩溃恢复页。
- `style` 必须排在 `script` 前面。
- 订阅要同步注册，因为注入表只在启动时收集一次。
- `tapIndex` 在桌面端没用，那边走 `dsh-app://` 直接读 index.html，不经过 web 服务器。

## 层级

`shell.overlay` 槽位的包装层 z-index 只有 20，祖先带 `transform` 之类就会创建层叠上下文，后代写多大的数都被锁在里面。所以动画层是自己建节点挂到 `body` 下面的，z-index 用 `2147483600`。

挂到 body 之后要小心不能挡住界面：`.sf-root` 和 React 那个空壳都设了 `pointer-events: none`，挂载前清理残留节点，播完还有一道 1.2 秒的强制清理定时器。

## 自己重算头发飘动

这一层是离线算出来的，需要装齐环境：

```bash
pip install opencv-python numpy scipy
pip install transformers                       # 深度图，可选

python3 hair/tools/05_depth.py --image assets/splash.webp --out hair/masks/depth.png
python3 hair/tools/01_sam2_hair_mask.py --image assets/splash.webp --out hair/masks/hair_mask.png
python3 hair/tools/02_make_weight.py --mask hair/masks/hair_mask.png --out hair/masks/hair_weight.png
python3 hair/tools/06_render_25d.py
bash hair/tools/04_encode_webm.sh hair/frames25d assets/wall_25d.webm
python3 build.py
```

第一步的深度图需要 `transformers`，装不上会自动退回用亮度凑一张。第二步的 SAM2 需要 torch 和权重 `sam2.1_hiera_large.pt`。

说清楚一点：仓库里现在这张 mask 是凑出来的，不是 SAM2 的输出。生成的时候手上没有 GPU 环境，用的是椭圆约束加颜色阈值再挖掉脸和肩膀，发丝之间的空隙是糊的。自己跑一遍 `01_sam2_hair_mask.py` 换掉它，边缘会好很多。

## 编码参数

```bash
ffmpeg -i hair/frames25d/%04d.png \
  -c:v libvpx-vp9 -pix_fmt yuva420p -auto-alt-ref 0 \
  -b:v 1.2M assets/wall_25d.webm
```

`yuva420p` 是带 alpha 的像素格式，`-auto-alt-ref 0` 必须加——交替参考帧会破坏 alpha 通道。Chromium 系能吃这个编码，Safari 不行。

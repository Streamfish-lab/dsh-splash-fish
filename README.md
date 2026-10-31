# dsh-splash-fish

**A depth-driven 2.5D startup animation plugin for [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness).**
Your own illustration develops out of the dark, the hair drifts with parallax, a sheen sweeps across, and the whole layer dissolves into the workspace.

纯客户端 UI 插件，挂在 dsh 的 `shell.overlay` 槽位上，每次页面加载只播一次，播完自行卸载。

| 预览 | 说明 |
|---|---|
| [`preview/splash-25d-preview.mp4`](preview/splash-25d-preview.mp4) | 完整启动动画，5.07 秒，含 2.5D 位移 |
| [`preview/hair_wave_preview.mp4`](preview/hair_wave_preview.mp4) | 上一版：只有头发层叠在原图上（3.6 秒，对照用） |
| `preview.html` | 浏览器直接打开就能看，支持 `?t=2600` 冻结到某一帧 |

---

## 安装

需要 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)（developer preview，`dsh` 命令可用）。

```bash
# 1. 解压到任意目录，路径必须是绝对路径
#    例如 C:\Users\<你>\dsh-plugins\dsh-splash-fish

# 2. 注册到 web profile
dsh plugin --profile web add /你的绝对路径/dsh-splash-fish

#    没全局装 dsh 时：
npx @deepseek-ai/dsh plugin --profile web add /你的绝对路径/dsh-splash-fish

# 部分版本写法是 dsh plugin add <路径>（不带 --profile），
# 以 dsh plugin --help 为准。

# 3. 重启一次（桌面版重启应用，浏览器版刷新页面）
```

卸载：

```bash
dsh plugin --profile web remove dsh-splash-fish
```

装完打开 dsh，应该先看到宿主的启动壳，然后是这张图的显影动画。

---

## 工作原理

### 为什么是一个视频，而不是 CSS 动画

头发要"动起来"，纯 CSS 只能做整块平移——单张图的头发和脸在同一条像素里，没有分层，平移就等于把发丝连着脸一起拽，观感是纸片。

所以头发（现在是整帧）的位移是**离线渲染**的：生成带视差的帧序列，编码成 WebM，运行时作为视频层播放。

### 三个必须解决的接入问题

**1. 视频层要和底图共用同一个变换**

`.sf-bg` 上有 `sfFocus`（1.14 → 1.02 倍）和 `sfDrift`（1.02 → 1.06 倍）两条缩放动画，还有 `blur(28px) → 0`。视频若作为兄弟节点叠上去，会因为缩放不同步而错位（最大 6%，几十像素）。

解法：把 `<video>` 放进 `.sf-bg` **内部**，子元素继承父节点的 `transform` 与 `filter`，两层完全同步。

**2. 插件没有打包器，拿不到外部文件**

`client.js` 由 `window.__ModuleLoader__.load()` 直接执行，没有 webpack/vite，也没有 `import.meta.url`，包目录里的 webm 无法 import。

解法：base64 内联 + 运行时转 Blob。

```js
var bin = atob(HAIR_B64), u8 = new Uint8Array(bin.length);
for (var i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
v.src = URL.createObjectURL(new Blob([u8], { type: "video/webm" }));
```

不用 `data:` URI 直接喂 `<video>`：有长度限制的坑，且部分 Chromium 版本对 data URI 视频不带 alpha。

**3. 视频 3.6 秒，时间轴 4.4 秒**

视频播完停在最后一帧。如果那帧头发是"被吹起来"的状态，后面就会定格在一个歪掉的位置。

解法：让**首尾两帧的位移严格为 0**。位移公式里的相位延迟项在 t=0 就有值（不同区域起摆时间不同），必须减掉这个静态偏置，并让所有波走整数个周期：

```python
wave = A * (sin(2πft − K·w) − sin(−K·w)) + ...
```

首帧差异实测 0.00，末帧 1.19（纯重采样噪声）。播完 `display:none` 摘掉视频层，画面零变化，解码器释放。

### 4. 让宿主启动壳不闪（host 半边）

宿主自带的启动画面（`[data-dsh-boot]`：HARNESS + 转圈 + Loading plugins…）在**任何客户端插件被实例化之前**就画好了。所以只靠 client 半边，无论 `z-index` 多高，都必然先闪一下那张壳。

唯一比它更早的界面，是被服务的文档本身——而 dsh 把它开放出来了：`webserver/index-inject` 收集的「结构化注入行」会在 `index.html` 解析阶段就渲染。

`lib/index.js` 里：

```js
const inject = ["webServer"];
function apply(ctx) {
  ctx.on("webserver/index-inject", (table) => {
    table.push({ kind: "style", text: COVER_CSS });   // 同色封面
    table.push({ kind: "script", placement: "head", text: COVER_JS });  // 立刻铺上 + 提供摘除句柄
  });
}
```

几条纪律，都是踩坑换来的：

- **只推 `style` / `script` 两种行。** 行类型是闭集（`global | script | script-src | script-preload | style | html`），未知 `kind` 会让 boot gate 直接 reject，把桌面端打进崩溃恢复页；`script-src` 会让桌面壳 `await loadScript`，失败即 reject，整个应用起不来。
- **`style` 必须在 `script` 之前。** 行按数组顺序应用。
- **订阅必须同步注册。** 注入表只在宿主启动时收集一次，异步注册会拿不到。
- **不能用 `tapIndex`。** 桌面端主窗口走 `dsh-app://` 协议直读 `index.html`，从不经过 web 服务器的 `renderIndex()`，那条路在桌面端是死代码。
- **封面颜色必须和动画首帧底色一致**（`#05080d`），摘除时才没有接缝。

退场三条路径：client 半边挂载时主动调 `window.__dshSfDrop()`（正常情况几百毫秒内）、3.5 秒硬超时兜底、以及脚本自身 catch 之后不清场也不影响页面。

**改 `lib/index.js` 必须重启应用**，刷新页面不算——注入表只在进程启动时收集一次。

### 5. 为什么动画层必须挂到 `<body>` 下

`shell.overlay` 这个槽位的包装层级 z-index 只有 20。祖先只要带 `transform`、`filter`、`contain` 或 `isolation`，就会创建层叠上下文，把后代的大 z-index **锁死在里面**——你在 `.sf-root` 上写 `2147483600` 也没用，对外等效只有 20。

后果：任何挂在 `body` 下的第三方浮层（余额鲸鱼挂件是 `2147483100`、皮肤类常见 `2147483300`）都会压在启动动画上面。

所以 `mountSplash` 不把节点留在槽位容器里，而是自己建一个 `div` 追加到 `document.body`：

```js
var stage = document.createElement("div");
stage.innerHTML = MARKUP;
document.body.appendChild(stage);      // ← 参与根上下文的排序
```

当前取值：动画层 `2147483600`，注入的启动封面 `2147483601`。

### 层叠顺序（从下到上）

```
.sf-bg            底图 + 缩放/模糊动画
  └ .sf-hair      ← 视频层（在这里，继承变换）
.sf-vignette      四角压暗
.sf-glow          冰蓝光晕（screen）
.sf-sheen         斜向扫光（screen）
.sf-parts         上升微粒
.sf-brand         字标
.sf-flash         结尾白闪
```

视频层必须夹在底图之上、暗角之下，否则扫光和暗角会被它盖住。

---

## 制作管线

四步，脚本在 `hair/tools/`。产物已经放进仓库，**只有想改内容时才需要跑**。

```bash
pip install opencv-python numpy scipy          # 渲染必需
pip install transformers                       # 深度图（可选，装不上会退伪深度）

# 1) 深度图
python3 hair/tools/05_depth.py --image assets/splash.webp --out hair/masks/depth.png

# 2) 头发 mask（SAM2，需要 torch + 权重）
python3 hair/tools/01_sam2_hair_mask.py \
  --image assets/splash.webp --out hair/masks/hair_mask.png

# 3) 发根→发梢权重图
python3 hair/tools/02_make_weight.py \
  --mask hair/masks/hair_mask.png --out hair/masks/hair_weight.png

# 4) 2.5D 渲染（108 帧）
python3 hair/tools/06_render_25d.py

# 5) 编码
bash hair/tools/04_encode_webm.sh hair/frames25d assets/wall_25d.webm

# 6) 内联进 client.js
python3 build.py
```

### 位移公式

```
amp = A_BASE + A_DEPTH·depth + A_HAIR·hairWeight
φ   = 2π(PHASE_U·u + PHASE_V·v)
dx  = amp·(0.62·sin(2πf₁t+φ) + 0.38·sin(2πf₂t−0.7φ)) + A_TURB·turb·sin(2πf₃t+2.1φ)
dy  = amp·(0.30·sin(...) − 0.22·sin(...))·0.9 + A_TURB·0.7·turb·sin(...)
```

- **`A_BASE`** 保证最远处也在动，没有死区
- **`A_DEPTH`** 按深度给视差：近处快、远处慢
- **`A_HAIR`** 发丝额外加成
- **`A_TURB`** 高频湍流，让区域内部也在形变——这一条是消灭"刚性平移"的关键
- **`φ` 随空间位置变化**，波横扫过去而不是整片齐动

参数都在 `06_render_25d.py` 顶部。当前值：`A_BASE=1.2 / A_DEPTH=3.6 / A_HAIR=5.4 / A_TURB=2.2 / A_BREATH=0.0027`，峰值位移 9.1 px。

### 编码参数

```bash
ffmpeg -y -framerate 30 -i hair/frames25d/f_%04d.png \
  -c:v libvpx-vp9 -pix_fmt yuva420p -auto-alt-ref 0 \
  -b:v 0 -crf 30 -row-mt 1 -threads 4 \
  -metadata:s:v:0 alpha_mode=1 \
  assets/wall_25d.webm
```

带 alpha 时四个参数不能省：`yuva420p`、`-auto-alt-ref 0`、`alpha_mode=1`、`libvpx-vp9`。当前版本输出的是不透明全帧（整幅都在动），用 `-pix_fmt yuv420p` 即可。

---

## 换图

1. 把新图放到 `assets/splash.png`（或直接替换 `assets/splash.webp`）
2. 重跑管线 1 → 6（`01_sam2_hair_mask.py` 顶部的 `POS`/`NEG` 点要按新图重新点）
3. `python3 build.py`

图建议横版 16:9、主体偏右、左侧留白——左侧是字标位置。

---

## 已知限制

- **无纹理区域看不出在动。** 皮肤、纯色背景这类平滑区域，位移 9 px 在像素值上只差不到 2 个灰度级。这不是参数问题，是整图位移方案的物理极限。
- **启动壳的覆盖依赖注入行。** host 半边通过 `webserver/index-inject` 推一行 CSS 封面来盖住宿主自带的 `[data-dsh-boot]`。
  这个通道在个别版本上可能被收紧；万一失效，表现只是「先闪一下宿主的启动画面」，不影响动画本身。
- **只播一次**，刷新页面重播。
- **仓库里的 mask 是几何近似。** 生成它的时候没有 GPU 环境跑 SAM2，用的是"椭圆约束 + 蓝度阈值 + 挖掉脸/肩"。发丝之间的镂空是糊的。跑一遍 `01_sam2_hair_mask.py` 换成真 mask 再重渲染，边缘会干净得多。
- **VP9 + alpha 只在 Chromium 系生效**（dsh 桌面版是 Electron，没问题）。Safari 不支持，网页版会看到黑块——除非改用不透明全帧（当前版本就是）。
- dsh 仍是 developer preview，`shell.overlay` / `slots.register` 契约可能随小版本变动。

---

## 拆层方案（备选，未采用）

`07_split_layers.py` + `08_render_layers.py` 实现了"SAM2 逐层分割 + LaMa 补全 + 分层独立动画"，也就是 Live2D 的路子。

没有默认采用的原因：逐根发丝的镂空需要手工修边（几小时起），被遮挡区域要靠补画（LaMa 在动漫平涂上补出来是"抹布"，且只在静止时不露），而 2.5D 一个像素都不用补。启动动画看一眼就过，投入产出不划算。

真要做"发丝前后穿插"时再走这条。

---

## 项目结构

```
dsh-splash-fish/
├── package.json              dsh.bundle.patch + dsh.client.platform=web
├── cordis.patch.yml          roster 里插一行
├── lib/index.js              host 半边：注入启动封面（消除宿主启动壳闪烁）
├── client.js                 构建产物（图 + 视频已内联，勿手改）
├── client.template.js        源码：样式、时间线、video 挂载
├── build.py                  内联静图 + webm → client.js
├── assets/
│   ├── splash.webp           静图（154 KB）
│   ├── wall_25d.webm         2.5D 全帧视频（1.0 MB）
│   └── hair_wave.webm        旧版头发层（303 KB，对照用）
├── hair/
│   ├── tools/                01 SAM2 / 02 权重 / 05 深度 / 06 2.5D 渲染
│   │                         04 编码 / 07 拆层 / 08 分层渲染 / 03 旧渲染
│   └── masks/                hair_mask.png, hair_weight.png, depth.png
├── preview/                  三段预览 mp4
├── preview.html              免安装预览页
└── dev/harness.html          伪宿主自测页（?t= 冻结帧 / ?nohair=1 差分）
```

---

## License

MIT. 插图版权归原作者，仓库内仅供演示，请自行替换 `assets/splash.*`。

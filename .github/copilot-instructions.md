# dsh-splash-fish — Copilot 上下文

给 GitHub Copilot / 任何 AI 助手的项目约定。改代码前先读这一份。

## 这个项目的形态

DeepSeek Harness（dsh）的客户端 UI 插件。运行在 dsh 的 `window.__ModuleLoader__` 沙箱里，
通过 `ctx.slots.register({ name: "shell.overlay" }, Component)` 挂一个铺满整窗的 React 组件，
播放一段约 5 秒的启动动画，然后自行卸载。

## 硬约束（违反任何一条都会让插件在真机上跑不起来）

1. **`client.js` 是构建产物，不要手改。** 改 `client.template.js`，然后 `python3 build.py`。
   `build.py` 做两件事：把静图压成 WebP 内联进 CSS 变量，把 webm 转 base64 内联成字符串。
2. **不能引用外部文件。** 沙箱里没有打包器、没有 `import.meta.url`、不能 `import` 图片或视频。
   所有资源必须内联（base64 → 运行时转 Blob URL）。
3. **不能发网络请求。** 启动动画必须在离线状态下完整播放。
4. **视频必须挂在 `.sf-bg` 内部。** 父节点上有 `transform`（缩放）和 `filter`（模糊），
   子元素继承才能与底图对齐。挂成兄弟节点会错位。
5. **渲染出的视频首帧和末帧位移必须严格为 0。** 视频播完会 `display:none` 摘掉，
   若末帧是"位移中"的状态，画面会跳。这是通过减掉相位偏置 + 周期数取整数做到的。
6. **WebM 编码参数不能省**：`-c:v libvpx-vp9 -pix_fmt yuva420p -auto-alt-ref 0 -metadata:s:v:0 alpha_mode=1`。
   丢了 `auto-alt-ref 0` 或 `alpha_mode=1`，alpha 通道就废了。

## 目录职责

- `client.template.js` — 唯一的样式与时间线来源。CSS 全在顶部的模板字符串里，
  keyframes 命名前缀 `sf`。时间常量：`TOTAL = 4400`（主时间线）、`EXIT = 700`（淡出）。
- `client.js` — 生成物。改了会被 `build.py` 覆盖。
- `hair/tools/` — 离线渲染管线，与运行时无关：
  - `01_sam2_hair_mask.py` 分割头发（顶部 `POS`/`NEG` 是相对坐标点）
  - `02_make_weight.py` 发根 0 / 发梢 1 的权重
  - `05_depth.py` 深度图（Depth Anything V2 → MiDaS → 伪深度三级回退）
  - `06_render_25d.py` 深度驱动的 2.5D 渲染，**所有可调参数在文件顶部常量区**
  - `04_encode_webm.sh` 编码
  - `07`/`08` 备选的拆层方案（一般不用）
- `dev/harness.html` — 用一个极简 React mock + 伪 `__ModuleLoader__` 把 `client.js` 当真加载一遍，
  用来验证挂载、槽位注册、DOM 生成。`?t=毫秒` 冻结到某一帧，`?nohair=1` 摘掉视频层做差分。

## 改行为时看哪里

| 想改 | 改哪里 |
|---|---|
| 动画时长 / 节奏 | `client.template.js` 的 `TOTAL`、`EXIT`，以及各 keyframes 的 delay |
| 字标文案、位置 | `.sf-brand` 相关的 CSS 与 `MARKUP` |
| 飘动幅度 / 频率 | `06_render_25d.py` 顶部的 `A_BASE / A_DEPTH / A_HAIR / A_TURB / A_BREATH / CYCLES` |
| 视差方向 | 同上，`PHASE_U` / `PHASE_V` |
| 分辨率 | `06_render_25d.py` 的 `W / H`（按实际窗口尺寸给，别超太多） |

改完渲染参数的完整流程：`06` 出帧 → `04_encode_webm.sh` 编码 → `build.py` 内联。

## 验证方式

```bash
node --check client.js                       # 语法
python3 build.py                             # 能构建
# 打开 dev/harness.html?t=2600 看冻结帧
# 打开 dev/harness.html?t=2600&nohair=1 做差分，确认视频层生效
```

像素级验证的常用脚本（差分集中在哪个区域）：

```python
import numpy as np
from PIL import Image
a = np.array(Image.open("f_0027.png").convert("L")).astype(int)
b = np.array(Image.open("f_0054.png").convert("L")).astype(int)
d = np.abs(a - b)
print(d.mean(), (d > 6).mean() * 100)
```

## 代码风格

- `client.template.js` 用 ES5 写法（`var`、`function`），不用箭头函数和模板字符串以外的语法糖——
  它要被 loader 直接执行，避免任何 Babel 依赖。
- Python 脚本：参数集中在文件顶部常量区，路径用 `Path(__file__).resolve().parents[n]` 锚定，
  不要写相对 cwd 的路径（用户会从任意目录调用）。
- 注释写"为什么"，不写"是什么"。尤其是那些看起来多余的参数（比如 `-auto-alt-ref 0`），
  必须说明省掉会坏在哪。

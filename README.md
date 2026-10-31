# dsh-splash-fish

**A startup animation plugin for [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness).**

插画从黑场里显影，冰蓝光晕扩散，一道斜光扫过，然后整层溶解进工作区。

纯客户端 UI 插件，挂在 dsh 的 `shell.overlay` 槽位上，每次页面加载只播一次，播完自行卸载。

## 时间线（4.4 秒 + 0.7 秒淡出）

| 时间 | 画面上发生的事 |
|---|---|
| 0 – 1.25 s | 黑场里图片从 `blur(28px) / brightness(.28)` 渐变到清晰，镜头从 1.14 倍缓回 1.02 倍 |
| 0.26 – 2.06 s | 冰蓝光晕扩散（`screen` 混合） |
| 0.42 – 1.32 s | 左下细线从左展开 |
| 0.62 – 1.62 s | `DEEPSEEK HARNESS` 字标淡入 |
| 1.25 – 2.75 s | 一道 104° 斜光扫过 |
| 1.3 – 4.3 s | 镜头极缓推近到 1.06 倍 |
| 1.5 – 4.4 s | 24 颗白色微粒上升 |
| 3.32 – 3.94 s | 轻白闪 |
| 4.4 – 5.1 s | 整层淡出，露出工作区 |

跳过：点击任意处 / 任意键 / 滚轮。

## 安装

```bash
dsh plugin --profile web add /你的绝对路径/dsh-splash-fish
```

桌面版走应用内「设置 → 插件 → 添加插件」，填本地目录绝对路径。

## 换图

把图覆盖到 `assets/splash.png`，然后 `python3 build.py`，重启 dsh。

## 已知限制

- 盖不住宿主自带的启动壳（`[data-dsh-boot]`），启动时会先闪一下。
- 画面里的角色完全静止，只有光效与字标在动。
- dsh 仍是 developer preview，槽位契约可能随小版本变动。

## License

MIT. 插图版权归原作者，仓库内仅供演示，请自行替换 `assets/splash.*`。

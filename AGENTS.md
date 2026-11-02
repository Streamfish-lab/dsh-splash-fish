# 给 AI Agent 的说明

这个仓库是 DeepSeek Harness 的插件，包名 `dsh-splash-fish`。要做的事情只有一件：把它注册进 profile，然后重启宿主。

## 桌面版：优先用应用内安装

**不要手改 `profiles\desktop\package.json`。** 那是 dsh 的启动配置，手改 JSON 只要漏一个逗号、或者 Windows 路径的反斜杠没转义成 `\\`，应用就再也起不来了，报 `Unexpected token ... is not valid JSON`。已经有人因此把 dsh 搞崩过。

正确做法是走应用自带的插件安装界面，让应用自己写配置。

**第一步**，把仓库放到一个长期保留的目录：

```powershell
$dest = "$env:USERPROFILE\.dsh\bundles\dsh-splash-fish"
git clone https://github.com/Streamfish-lab/dsh-splash-fish.git $dest
```

**第二步**，让用户操作界面：

1. 打开 DeepSeek Harness
2. 左侧栏 → 设置（齿轮图标，一般在最下面）→ 插件
3. 右上角 `+ 添加插件`
4. 粘贴 `$dest` 的绝对路径，要指到有 `package.json` 的那一层
5. 装完重启

**第三步**，告诉用户彻底退出应用再打开。托盘图标右键退出，关窗口不算。

这样装完，配置由应用自己写，不会破坏 JSON。

## macOS 怎么装

**先确认机器能不能跑桌面版**：必须是 **Apple 芯片（M 系列）**，系统 macOS 13 以上。Intel Mac 没有官方桌面版，只能走 Web 版，见下一节。

**路径换成 Mac 的写法**（没有 `%USERPROFILE%`，也没有 PowerShell）：

```bash
DEST="$HOME/.dsh/bundles/dsh-splash-fish"
git clone https://github.com/Streamfish-lab/dsh-splash-fish.git "$DEST"
```

**装法跟 Windows 一样走界面**：设置 → 插件 → 添加插件，填展开后的绝对路径 `/Users/<用户名>/.dsh/bundles/dsh-splash-fish`，要指到有 `package.json` 的那一层。

**不要用 `ln -s` 手动建链接，也不要改 `package.json`。** 界面自己会处理。Windows 上那些 `New-Item -ItemType Junction` 的命令在 Mac 上不适用，别照抄。

**`换自己的图.bat` 在 Mac 上用不了**，那是 Windows 批处理。换图改成直接跑命令：

```bash
cd "$HOME/.dsh/bundles/dsh-splash-fish"
python3 tools/make_from_image.py 我的图.jpg
```

跑完不用复制文件——脚本就在插件目录里跑，生成的 `client.js` 原地覆盖，彻底退出 dsh 再打开就生效。

**依赖**：

```bash
python3 -m pip install pillow        # 换图必需
```

**Mac 上有个好处**：插件目录就是运行目录，改完 `client.js` 重启就生效，不像某些装法还要往另一个地方复制。

## Web 版怎么装

```bash
dsh plugin --profile web add /absolute/path/to/dsh-splash-fish
```

本机有 git 和 pnpm 的话也可以直接从仓库装：

```bash
dsh plugin --profile web add github:Streamfish-lab/dsh-splash-fish
```

## 装完怎么确认

重启后应该看到：黑屏，插画从模糊变清晰，光晕扩散，一道光扫过，然后淡出进界面。

没出来的话按这个顺序查：

1. `package.json` 里 `dependencies` 和 `dsh.profile.bundles` 是不是都加了
2. `node_modules\dsh-splash-fish` 这条链接指向的目录里，有没有 `package.json` 和 `client.js`
3. 打开 DevTools（Ctrl+Shift+I）看 Console，如果有 `slots.register` 或 `apply` 的报错，说明宿主版本的槽位接口变了

## 卸载

让用户在应用里操作：设置 → 插件 → 找到 `dsh-splash-fish` → 移除，然后彻底退出再打开。

**不要手改 `package.json` 来卸载。** 删一项时漏掉前面的逗号，照样起不来。

如果界面里移不掉，直接删掉插件目录 `%USERPROFILE%\.dsh\bundles\dsh-splash-fish` 也行——`link:` 的目标没了，插件就加载不了。配置里留个失效条目一般不挡启动。

## 如果要改代码

先看 `.github/copilot-instructions.md`，里面写了哪些东西不能动：`client.js` 是构建产物、资源必须内联、视频要放在 `.sf-bg` 内部、WebM 的编码参数不能省、动画层不能拦截鼠标。

改完跑一遍：

```bash
python3 build.py          # 重新内联图片和视频
node --check client.js
```

改的是 `client.template.js` 就刷新页面，改的是 `lib/index.js` 必须重启进程。

`dev/harness.html` 可以离线自测。它用极简的 React mock 加一个假的 `__ModuleLoader__`，把 `client.js` 真加载一遍。`?t=2600` 冻在某一帧，`?nohair=1` 去掉视频层做对比。

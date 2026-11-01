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

## 兜底：应用内装不了的时候

只有在界面里装不进去时，才走手动路线。桌面版的 `desktop` profile 是 Electron 应用独占的，命令行 `dsh plugin --profile desktop add` 会被直接拒绝。

**第一步**，克隆到一个长期保留的目录。profile 里记的是 `link:` 路径，目录挪走或删掉，插件就失效了。

```powershell
$dest = "$env:USERPROFILE\.dsh\bundles\dsh-splash-fish"
git clone https://github.com/Streamfish-lab/dsh-splash-fish.git $dest
```

**第二步**，改 `%USERPROFILE%\.dsh\profiles\desktop\package.json`。

> ⚠️ **改之前必须复制一份 `package.json.bak`。** 这个文件写坏了 dsh 就起不来。
> 路径一律用**正斜杠** `C:/Users/...`，不要用反斜杠——JSON 里 `\d` 不是合法转义，
> 整个文件会解析失败。改完用任意 JSON 校验工具过一遍再让用户重启。

两处都要动：

```jsonc
{
  "dependencies": {
    "dsh-splash-fish": "link:C:/Users/<用户名>/.dsh/bundles/dsh-splash-fish"
  },
  "dsh": {
    "profile": {
      "bundles": [
        "dsh-splash-fish"
      ]
    }
  }
}
```

只往 `dependencies` 里加是不够的，`dsh.profile.bundles` 里没有这个包名，loader 不会去挂载它。

**第三步**，建目录链接。Windows 上用 Junction 不需要管理员权限，`mklink /D` 需要。

```powershell
New-Item -ItemType Junction -Path "$env:USERPROFILE\.dsh\profiles\desktop\node_modules\dsh-splash-fish" -Target $dest
```

**第四步**，让用户彻底退出应用再打开。托盘图标右键退出，关窗口不算。

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

从 `dependencies` 和 `dsh.profile.bundles` 里删掉 `dsh-splash-fish`，删掉 `node_modules` 下那条链接，重启。

## 如果要改代码

先看 `.github/copilot-instructions.md`，里面写了哪些东西不能动：`client.js` 是构建产物、资源必须内联、视频要放在 `.sf-bg` 内部、WebM 的编码参数不能省、动画层不能拦截鼠标。

改完跑一遍：

```bash
python3 build.py          # 重新内联图片和视频
node --check client.js
```

改的是 `client.template.js` 就刷新页面，改的是 `lib/index.js` 必须重启进程。

`dev/harness.html` 可以离线自测。它用极简的 React mock 加一个假的 `__ModuleLoader__`，把 `client.js` 真加载一遍。`?t=2600` 冻在某一帧，`?nohair=1` 去掉视频层做对比。

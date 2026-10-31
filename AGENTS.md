# 给 AI Agent 的说明

这个仓库是 DeepSeek Harness 的插件，包名 `dsh-splash-fish`。要做的事情只有一件：把它注册进 profile，然后重启宿主。

## 桌面版怎么装

桌面版的 `desktop` profile 是 Electron 应用独占的，命令行 `dsh plugin --profile desktop add` 会被直接拒绝，只能手动链接。

**第一步**，克隆到一个长期保留的目录。profile 里记的是 `link:` 路径，目录挪走或删掉，插件就失效了。

```powershell
$dest = "$env:USERPROFILE\.dsh\bundles\dsh-splash-fish"
git clone https://github.com/Streamfish-lab/dsh-splash-fish.git $dest
```

**第二步**，改 `%USERPROFILE%\.dsh\profiles\desktop\package.json`。改之前先备份一份。两处都要动：

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

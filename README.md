# dsh-splash-fish

给 DeepSeek Harness 换一个 2.5D 深度视差的开屏动画，替掉默认那张加载页。

开屏换成一张插画：从黑场里显影，带一点深度位移，然后淡出，进工作区。纯前端，只播一次，播完自己卸掉，之后跟在没装插件一样。

![license](https://img.shields.io/badge/license-MIT-black?style=flat-square)
![version](https://img.shields.io/badge/version-0.3.0-black?style=flat-square)
![platform](https://img.shields.io/badge/Windows%20%7C%20macOS-black?style=flat-square)



https://github.com/user-attachments/assets/8c18cd8d-3094-4837-91ff-90267f97d4dd



## 安装

最省事的方式：把下面这句发给 dsh 里的 Agent，剩下的它自己搞定。

```
帮我安装这个 DeepSeek Harness 插件：https://github.com/Streamfish-lab/dsh-splash-fish
```

Agent 会去仓库里读 [AGENTS.md](AGENTS.md)，按里面写的步骤装。装完彻底退出 dsh 再打开。

想自己装：**设置 → 插件 → 添加插件**，填仓库目录的绝对路径（要指到有 `package.json` 那一层），重启。

> 别手改 `profiles\desktop\package.json`。那是 dsh 的启动配置，一个逗号错位、或者 Windows 路径反斜杠没转义，dsh 就再也起不来。用应用界面装，让它自己写。

Windows 和 Mac 都能装。Mac 上没有 `.bat` 那套东西，换图用 python 命令，[AGENTS.md](AGENTS.md) 里写了。

装完看了不喜欢，插件列表里点移除就干净了。dsh 自己的配置没被动过，删完跟没装过一样。

## 和常见开屏插件不一样的地方

**先把 dsh 自带的那张加载页压掉。** 不少同类插件在 README 里直说压不住，动画前面总要闪一下。客户端插件被实例化的时候那张图早就画完了，追不上。这里用的是 `webserver/index-inject`，在 index.html 解析阶段就把封面铺上去，比客户端插件早。

**头发是算出来的，不是整块平移。** 单张图里头发和脸是同一批像素，CSS 平移等于连脸一起拽。这里是离线渲染：深度图决定每个像素动多少，发根到发梢权重让幅度递增，再叠相位和湍流。算完 108 帧压成带 alpha 的 WebM。

**启动时不吃 CPU。** 上面那 108 帧早就烘成一个 1MB 视频，运行时只是播一段视频，没有逐帧计算，没有 canvas。

**播完不挡鼠标。** 动画层挂在 `body` 下，`pointer-events: none`，加残留清理和 1.2 秒兜底定时器。等不及可以点一下屏幕、按任意键、滚一下滚轮，立刻进收尾——那一下点击会被吃掉，不会漏到下面的界面。

实现细节、位移公式、接入时踩的坑，在 [docs/TECHNICAL.md](docs/TECHNICAL.md)。

## 换成自己的图（可选）

默认那张插画是别的画师的作品。可以换，但代价说清楚：**换完头发那层飘动就没了**——它是照着这张图单独算的，换图必须重算。

不在乎飘动、只要画面能显影，把图拖到 `换自己的图.bat` 上松手（Mac 上跑 `python3 tools/make_from_image.py 我的图.jpg`）。它会居中裁成 16:9、缩到 1600×900、重新打包。显影、光晕、光扫、粒子、淡出都还在，只是没有发丝飘动。

想要新的飘动，得装 Python、torch、SAM2 权重，跑一遍离线渲染，一小时上下。步骤在 [docs/TECHNICAL.md](docs/TECHNICAL.md)。

## 更新

**不会自动更新。** 装在本地那份就是当时那份，dsh 不会去仓库比对。

git clone 装的：

```bash
cd %USERPROFILE%\.dsh\bundles\dsh-splash-fish
git pull
```

然后彻底退出 dsh 再打开。换过图的人注意：更新会用新的 `client.js` 覆盖，画面回到默认，重新拖一次图就行。

新版看 [Releases](https://github.com/Streamfish-lab/dsh-splash-fish/releases)。

## 版本历史

| 版本 | 改了什么 |
|---|---|
| v0.1.0 | 第一版，纯 CSS 动画 |
| v0.2.0 | 换成深度图驱动的 2.5D 位移，顺便解决启动闪烁 |
| v0.2.1 | 动画层改挂到 body 下面，压住第三方浮层 |
| v0.2.2 | 顶部加压暗带，想盖住 Windows 的窗口按钮 |
| v0.2.3 | 修掉动画层拦截点击的问题，删掉压暗带 |
| v0.3.0 | 收尾时序：视频循环、掐掉 animation 干扰、整层同步淡出，不再露出 dsh 的加载页 |

细节见 [CHANGELOG.md](CHANGELOG.md)。

## 还没解决的问题

- 皮肤、纯色背景这种没纹理的地方，位移 9 像素在数值上只差一两个灰度级，肉眼看不出在动。这是整图位移的上限，调参数解决不了。
- Windows 右上角三个窗口按钮是系统画的，网页盖不住。想彻底解决只能把 dsh 切到 advanced 窗口模式。
- 只播一次，想重播要刷新。
- dsh 还是 developer preview，`shell.overlay` 和 `slots.register` 的接口说不定哪天会变。

<details>
<summary>目录结构</summary>

```
dsh-splash-fish/
├── package.json          插件声明
├── cordis.patch.yml      roster 里插一行
├── lib/index.js          host 半边，负责注入启动封面
├── client.js             构建产物，图和视频都内联在里面，别手改
├── client.template.js    源码，样式、时间线、视频挂载、清理逻辑
├── build.py              把图和视频内联进 client.js
├── tools/make_from_image.py  一张图换图，自动裁 16:9
├── 换自己的图.bat         Windows 双击，把图拖上去就行
├── assets/               splash.webp / wall_25d.webm / hair_wave.webm
├── hair/tools/           01 分割 02 权重 04 编码 05 深度 06 渲染 07 拆层 08 分层
├── hair/masks/           三张图：mask、权重、深度
├── preview/              预览图
├── preview.html          免安装预览
├── dev/harness.html      自测页，?t= 冻结帧，?nohair=1 去掉视频层做对比
├── docs/TECHNICAL.md     实现细节
└── AGENTS.md             给 Agent 看的安装说明
```

</details>

## License

MIT。插画版权属于原作者。

---

如果它让你每次打开 dsh 的时候心情好一点，点个 Star 就行。有问题直接开 Issue。

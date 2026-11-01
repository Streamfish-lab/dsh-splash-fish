/* dsh-splash-fish — host half.
 *
 * 这一半干两件事：
 *   1. 让 loader 为这个包挂一个 fiber（否则 client bundle 不会被下发到页面）
 *   2. 通过 dsh 的「结构化注入行」在 index.html 解析阶段就铺一层同色封面
 *
 * 为什么要第 2 件事
 * -----------------
 * 宿主自带的启动壳（[data-dsh-boot]：HARNESS + 转圈 + Loading plugins…）在任何
 * 客户端插件被实例化之前就已经画出来了。所以只靠 client 半边，无论如何都会先闪
 * 一下那张壳。唯一能比它更早的界面，是被服务的文档本身 —— 而 dsh 把它开放出来了：
 * webserver/index-inject 收集的行会在页面解析时就写进 index.html。
 *
 * 这里只推两种最稳的行：style 和 script，且 style 在前。
 * （行类型是闭集：global | script | script-src | script-preload | style | html。
 *   未知 kind 会让 boot gate 直接 reject，把桌面端打进崩溃恢复页；
 *   script-src 会让桌面壳 await loadScript，失败即 reject。所以都不用。）
 *
 * 封面怎么退场
 * ------------
 * 三条路径，任意一条命中就摘掉：
 *   · client 半边挂载时主动调用 window.__dshSfDrop()   ← 正常情况下几百毫秒内
 *   · 3.5 秒硬超时                                      ← 兜底，client 挂了也不会挡住界面
 * 封面颜色和动画首帧的底色完全一致（#05080d），所以摘掉那一刻看不出接缝。
 *
 * 注意：注入表只在宿主启动时收集一次。改了这个文件必须重启应用才生效，
 * 刷新页面不算。
 */

/** Stable Cordis plugin name; matches cordis.patch.yml's roster id. */
const name = "dsh-splash-fish";

/** 需要宿主的 webServer 服务（注入表由它收集）。 */
const inject = ["webServer"];

/** 与 client 半边 .sf-root 的 background 完全一致，摘除时无接缝。 */
/* 用真实元素而不是 html::before：伪元素依赖根元素的层叠上下文，
   在宿主把启动壳画在很高层级时不一定压得住。真实 div 更可控。 */
const COVER_CSS =
  "#dsh-sf-cover{position:fixed;inset:0;background:#05080d;" +
  "z-index:2147483646;pointer-events:none;transition:opacity .35s ease}" +
  "#dsh-sf-cover.dsh-sf-off{opacity:0}";

/* 只做一件事：立刻盖上，并提供摘下它的把手。没有 DOM 查询、没有轮询，
   出错也只是不盖（catch 兜住），不会影响页面自身。 */
/* head 里执行时 body 还不存在，所以直接挂到 documentElement 上，
   这样第一帧就有黑底。摘除时先淡出再移除，避免硬切。 */
const COVER_JS =
  "(function(){try{" +
  'if(document.getElementById("dsh-sf-cover"))return;' +
  'var c=document.createElement("div");c.id="dsh-sf-cover";' +
  "(document.documentElement||document.body).appendChild(c);" +
  "var gone=false;" +
  "function drop(){if(gone)return;gone=true;" +
  'c.className="dsh-sf-off";' +
  "window.setTimeout(function(){if(c.parentNode)c.parentNode.removeChild(c)},420);}" +
  "window.__dshSfDrop=drop;" +
  "window.setTimeout(drop,3500);" +
  "}catch(e){}})();";

function apply(ctx) {
  ctx.on("webserver/index-inject", (table) => {
    if (!Array.isArray(table)) return;
    table.push({ kind: "style", text: COVER_CSS });
    table.push({ kind: "script", placement: "head", text: COVER_JS });
  });
}

export { apply, name, inject };
export default { name, inject, apply };

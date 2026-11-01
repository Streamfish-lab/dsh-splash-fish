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
  "#dsh-sf-cover{position:fixed;inset:0;pointer-events:none;transition:opacity .9s ease;" +
  /* 别再铺纯黑了：纯黑和动画首帧的暗蓝对不上，衔接处会显得空。
     用一层接近首帧的光晕，封面透下去的时候背景正好接着亮起来。 */
  "background:radial-gradient(ellipse 76% 60% at 50% 46%," +
  "#16304a 0%,#0b1626 40%,#060a10 72%,#04060a 100%);" +
  "z-index:2147483647}" +
  "#dsh-sf-cover.dsh-sf-off{opacity:0}" +
  /* 宿主自带的启动壳（HARNESS + Loading plugins…）层级比插件高，压不住，
     那就别压了，直接让它不可见。选择器挂在 html.dsh-sf-boot 上：
     只有封面脚本真的跑起来了才会加这个 class，脚本失败时不会误伤。
     注意：这个 class 一旦加上就不再摘掉。之前是在撤封面时把它 remove 掉的，
     结果动画淡完的那一瞬间，底下露出宿主启动页，要等主界面渲染完（0.5~1 秒）才走。
     宿主自己会在界面就绪后移除 [data-dsh-boot] 节点，所以这里不需要我们管。 */
  "html.dsh-sf-boot [data-dsh-boot]{opacity:0!important;transition:none!important}";

/* 只做一件事：立刻盖上，并提供摘下它的把手。没有 DOM 查询、没有轮询，
   出错也只是不盖（catch 兜住），不会影响页面自身。 */
/* head 里执行时 body 还不存在，所以直接挂到 documentElement 上，
   这样第一帧就有黑底。摘除时先淡出再移除，避免硬切。 */
const COVER_JS =
  "(function(){try{" +
  'if(document.getElementById("dsh-sf-cover"))return;' +
  'var c=document.createElement("div");c.id="dsh-sf-cover";' +
  "(document.documentElement||document.body).appendChild(c);" +
  'document.documentElement.classList.add("dsh-sf-boot");' +
  "var gone=false;" +
  "function drop(){if(gone)return;gone=true;" +
  'c.className="dsh-sf-off";' +
  "window.setTimeout(function(){if(c.parentNode)c.parentNode.removeChild(c)},420);}" +
  "window.__dshSfDrop=drop;" +
  /* 宿主还有第二张启动画面：界面就绪前的 "DEEPSEEK HARNESS / STARTING WORKSPACE" 加载页。
     它没有稳定的 class/id，只能按文字认。每 250ms 扫一次，认出来就连同它的全屏祖先一起
     压成透明；扫 15 秒后收工，不影响后续。 */
  'var tick=0,tv=setInterval(function(){' +
  'if(++tick>60){clearInterval(tv);return;}' +
  'if(!document.body)return;' +
  'var els=document.body.getElementsByTagName("*"),i,e,txt,p,g,r;' +
  'for(i=0;i<els.length;i++){e=els[i];' +
  'if(e.children.length||!/^(DIV|SPAN|P|LI|H1|H2|H3|SECTION)$/.test(e.tagName))continue;' +
  'txt=e.textContent||"";' +
  'if(txt.indexOf("STARTING WORKSPACE")<0)continue;' +
  'p=e;g=0;' +
  'while(p&&p!==document.body&&g++<12){r=p.getBoundingClientRect();' +
  'if(r.width>innerWidth*0.85&&r.height>innerHeight*0.85)break;p=p.parentElement;}' +
  'if(p&&p!==document.body)p.style.setProperty("opacity","0","important");}' +
  '},250);' +
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

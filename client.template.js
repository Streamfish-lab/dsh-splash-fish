/* dsh-splash-fish — client half (GENERATED from client.template.js by build.py; do not edit by hand).
 *
 * Mounts a one-shot startup film on the `shell.overlay` slot:
 * the artwork develops out of the dark (blur + dim -> sharp), a soft light
 * blooms from the character, a diagonal sheen sweeps across, dust rises,
 * then the whole layer cross-dissolves into the workspace.
 *
 * The hair gets its motion from an offline-rendered VP9+alpha WebM that is
 * inlined as base64, decoded into a Blob at mount time and placed *inside*
 * .sf-bg so it inherits the exact same scale/blur transform as the still.
 * It plays once, then removes itself -- after 3.6 s the layer is gone and the
 * compositor cost drops back to zero.
 *
 * No other part of the figure moves: no drift, no sway, no breathing.
 *
 * Skip: click / any key / wheel. Plays once per page load, then unmounts.
 */
window.__ModuleLoader__.load({
  id: "dsh-splash-fish",
  factory(require) {
    var React = require("react");
    var h = React.createElement;

    var CSS = `
.sf-root{position:fixed;inset:0;z-index:2147483600;overflow:hidden;background:#05080d;
  opacity:1;transform:scale(1);will-change:opacity,transform;cursor:default}
.sf-root.sf-out{animation:sfExit 680ms cubic-bezier(.4,0,.25,1) forwards}
@keyframes sfExit{from{opacity:1;transform:scale(1)}to{opacity:0;transform:scale(1.045)}}

/* ---------- artwork: develop from the dark, then hold ----------------------
   starts at 1.14 and settles at 1.02 over 1.4 s, then only a very slow
   1.02 -> 1.06 drift. The figure inside the image never moves. */
.sf-bg{position:absolute;inset:0;background:var(--sf-img) center/cover no-repeat;
  filter:blur(28px) brightness(.28) saturate(.55);transform:scale(1.14);opacity:0;
  will-change:filter,transform,opacity}
.sf-play .sf-bg{animation:sfFade 1250ms cubic-bezier(.22,.61,.36,1) forwards,
  sfFocus 1400ms cubic-bezier(.22,.61,.36,1) forwards,
  sfDrift 3000ms linear 1300ms forwards}
@keyframes sfFade{from{opacity:0}to{opacity:1}}
@keyframes sfFocus{from{filter:blur(28px) brightness(.28) saturate(.55);transform:scale(1.14)}
  to{filter:blur(0) brightness(.92) saturate(1);transform:scale(1.02)}}
@keyframes sfDrift{from{transform:scale(1.02)}to{transform:scale(1.06)}}

/* ---------- hair video: a sibling of the still, inside .sf-bg ----------
   object-fit:cover must stay in sync with the parent's background-size:cover,
   otherwise the hair layer would be offset by a few pixels. */
.sf-hair{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;
  pointer-events:none;opacity:0;transition:opacity 260ms ease;background:transparent}
.sf-hair.sf-on{opacity:1}

/* ---------- vignette ---------- */
.sf-vignette{position:absolute;inset:0;pointer-events:none;opacity:0;background:
  radial-gradient(120% 90% at 62% 34%,rgba(5,8,13,0) 30%,rgba(5,8,13,.55) 78%,rgba(5,8,13,.86) 100%),
  linear-gradient(90deg,rgba(5,8,13,.72) 0%,rgba(5,8,13,.34) 26%,rgba(5,8,13,0) 52%),
  linear-gradient(0deg,rgba(5,8,13,.55) 0%,rgba(5,8,13,0) 30%)}
.sf-play .sf-vignette{animation:sfIn 1500ms ease 200ms forwards}

/* ---------- bloom + sheen ---------- */
.sf-glow{position:absolute;left:50%;top:50%;width:150vmin;height:150vmin;
  margin:-75vmin 0 0 -75vmin;pointer-events:none;opacity:0;mix-blend-mode:screen;
  background:radial-gradient(circle,rgba(169,214,255,.30) 0%,rgba(169,214,255,.12) 34%,rgba(169,214,255,0) 66%)}
.sf-play .sf-glow{animation:sfGlow 1800ms cubic-bezier(.22,.61,.36,1) 260ms forwards}
@keyframes sfGlow{from{opacity:0;transform:scale(.72)}to{opacity:1;transform:scale(1)}}

.sf-sheen{position:absolute;inset:-20% -30%;pointer-events:none;opacity:0;
  transform:translateX(-60%);mix-blend-mode:screen;
  background:linear-gradient(104deg,rgba(255,255,255,0) 38%,rgba(220,236,255,.10) 46%,
  rgba(220,236,255,.42) 50%,rgba(220,236,255,.10) 54%,rgba(255,255,255,0) 62%)}
.sf-play .sf-sheen{animation:sfSheen 1500ms cubic-bezier(.4,0,.2,1) 1250ms forwards}
@keyframes sfSheen{0%{opacity:0;transform:translateX(-62%)}14%{opacity:1}
  86%{opacity:.9}100%{opacity:0;transform:translateX(62%)}}

/* ---------- wordmark ---------- */
.sf-brand{position:absolute;left:7.2vw;bottom:23vh;max-width:44vw;color:#f4f9ff;
  font-family:system-ui,-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
.sf-rule{width:0;height:1px;margin-bottom:22px;
  background:linear-gradient(90deg,rgba(169,214,255,.95),rgba(169,214,255,0))}
.sf-play .sf-rule{animation:sfRule 900ms cubic-bezier(.22,.61,.36,1) 420ms forwards}
@keyframes sfRule{from{width:0}to{width:min(220px,24vw)}}

.sf-mark{display:flex;align-items:baseline;gap:.42em;opacity:0;transform:translateY(10px);
  font-size:clamp(20px,2.5vw,40px);font-weight:300;letter-spacing:.30em;line-height:1;
  text-shadow:0 0 26px rgba(169,214,255,.35);white-space:nowrap}
.sf-mark b{font-weight:600;letter-spacing:.30em}
.sf-mark i{font-style:normal;font-size:.52em;font-weight:400;letter-spacing:.52em;
  color:rgba(206,230,255,.78)}
.sf-play .sf-mark{animation:sfIn 1000ms cubic-bezier(.22,.61,.36,1) 620ms forwards}

.sf-sub{display:flex;align-items:center;gap:12px;margin-top:16px;opacity:0;
  font-size:clamp(10px,.95vw,13px);letter-spacing:.42em;text-transform:uppercase;
  color:rgba(196,222,255,.62)}
.sf-dot{width:4px;height:4px;border-radius:50%;background:rgba(169,214,255,.85);
  box-shadow:0 0 10px rgba(169,214,255,.9);animation:sfBreathe 1400ms ease-in-out infinite}
@keyframes sfBreathe{0%,100%{opacity:.35}50%{opacity:1}}
.sf-play .sf-sub{animation:sfIn 900ms cubic-bezier(.22,.61,.36,1) 900ms forwards}
@keyframes sfIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}

/* ---------- dust ---------- */
.sf-parts{position:absolute;inset:0;pointer-events:none;overflow:hidden}
.sf-p{position:absolute;border-radius:50%;background:#eaf5ff;opacity:0;
  box-shadow:0 0 8px rgba(200,230,255,.55)}
@keyframes sfRise{0%{opacity:0;transform:translate(0,0) scale(.6)}12%{opacity:.85}
  80%{opacity:.5}100%{opacity:0;transform:translate(var(--sf-dx),-72vh) scale(1)}}

.sf-flash{position:absolute;inset:0;pointer-events:none;opacity:0;background:#eef6ff;
  mix-blend-mode:screen}
.sf-play .sf-flash{animation:sfFlash 620ms ease-out 3320ms forwards}
@keyframes sfFlash{0%{opacity:0}22%{opacity:.42}100%{opacity:0}}
`;

    var MARKUP = '<div class="sf-root">' +
      '<div class="sf-bg"></div>' +
      '<div class="sf-vignette"></div>' +
      '<div class="sf-glow"></div>' +
      '<div class="sf-sheen"></div>' +
      '<div class="sf-parts"></div>' +
      '<div class="sf-brand">' +
        '<div class="sf-rule"></div>' +
        '<div class="sf-mark"><b>DEEPSEEK</b><i>HARNESS</i></div>' +
        '<div class="sf-sub"><span class="sf-dot"></span>starting workspace</div>' +
      '</div>' +
      '<div class="sf-flash"></div>' +
      '</div>';

    /* hair_wave.webm, base64 (VP9 + alpha, 1920x1080, 30 fps, 3.6 s).
       Empty string when build.py could not find the file -> layer is skipped. */
    var HAIR_B64 = "__HAIR_WEBM_B64__";

    function attachHair(root) {
      if (!HAIR_B64) return null;
      var bg = root.querySelector(".sf-bg");
      if (!bg) return null;

      var url;
      try {
        var bin = atob(HAIR_B64), n = bin.length, u8 = new Uint8Array(n);
        for (var i = 0; i < n; i++) u8[i] = bin.charCodeAt(i);
        url = URL.createObjectURL(new Blob([u8], { type: "video/webm" }));
      } catch (e) {
        return null;
      }

      var v = document.createElement("video");
      v.className = "sf-hair";
      v.muted = true;
      v.defaultMuted = true;
      v.playsInline = true;
      v.setAttribute("muted", "");
      v.setAttribute("playsinline", "");
      v.setAttribute("preload", "auto");
      v.setAttribute("aria-hidden", "true");
      v.src = url;

      function drop() {
        v.style.display = "none";
        try { v.pause(); } catch (e) {}
      }
      v.addEventListener("loadeddata", function () { v.classList.add("sf-on"); }, { once: true });
      v.addEventListener("ended", drop);       /* last frame == original art, so no jump */
      v.addEventListener("error", drop);       /* decode unsupported -> stay on the still */

      bg.appendChild(v);
      var pr = v.play();
      if (pr && pr.catch) pr.catch(drop);

      return { el: v, url: url, drop: drop };
    }

    var TOTAL = 4400;   /* main timeline */
    var EXIT = 700;     /* cross-dissolve */

    function mountSplash(anchor, opts) {
      /* 关键：不要留在 shell.overlay 的槽位容器里。
         那个槽位包装元素所在层级的 z-index 只有 20，任何祖先只要带
         transform / filter / contain / isolation 就会创建层叠上下文，
         把后代的大 z-index 锁死在里面——对外等效只有 20，
         于是被 2147483100 的第三方挂件（比如余额鲸鱼）压住。
         挂到 body 下，才在根上下文中真正参与排序。 */
      var stage = document.createElement("div");
      stage.className = "sf-stage-host";
      stage.innerHTML = MARKUP;
      document.body.appendChild(stage);

      var root = stage.firstChild;
      var parts = root.querySelector(".sf-parts");
      var i, el, size, x, drift;
      for (i = 0; i < 24; i++) {
        el = document.createElement("span");
        el.className = "sf-p";
        size = 1.5 + Math.random() * 4.5;
        x = 6 + Math.random() * 88;
        drift = (Math.random() * 2 - 1) * 40;
        el.setAttribute("style",
          "width:" + size + "px;height:" + size + "px;left:" + x + "vw;bottom:-30px;" +
          "--sf-dx:" + drift + "px;animation:sfRise " + (1500 + Math.random() * 1100) +
          "ms linear " + (1500 + Math.random() * 1400) + "ms forwards;");
        parts.appendChild(el);
      }

      var hair = attachHair(root);

      /* 摘掉 host 半边注入的启动封面。此刻 .sf-root 已经铺满整窗、底色与封面完全一致，
         所以摘除的瞬间看不出接缝。没有这个全局函数（比如宿主版本不支持注入行）就跳过。 */
      try { if (window.__dshSfDrop) window.__dshSfDrop(); } catch (e) {}

      /* start on next frame so the first paint is the dark, blurred state */
      requestAnimationFrame(function () { root.classList.add("sf-play"); });

      var done = false;
      var timers = [];
      function finish() {
        if (done) return;
        done = true;
        timers.forEach(clearTimeout);
        if (hair) hair.drop();          /* 跳过时立刻停播，不再解码 */
        root.classList.add("sf-out");
        timers.push(setTimeout(function () { if (opts.onDone) opts.onDone(); }, EXIT));
      }
      timers.push(setTimeout(finish, TOTAL));

      function onKey() { finish(); }
      function onWheel() { finish(); }
      root.addEventListener("pointerdown", finish);
      window.addEventListener("keydown", onKey);
      window.addEventListener("wheel", onWheel, { passive: true });

      return {
        total: TOTAL + EXIT,
        skip: finish,
        destroy: function () {
          done = true;
          timers.forEach(clearTimeout);
          root.removeEventListener("pointerdown", finish);
          window.removeEventListener("keydown", onKey);
          window.removeEventListener("wheel", onWheel);
          if (hair) { hair.drop(); try { URL.revokeObjectURL(hair.url); } catch (e) {} }
          if (stage.parentNode) stage.parentNode.removeChild(stage);
        },
      };
    }

    var playedThisLoad = false;

    function Overlay() {
      var hostRef = React.useRef(null);
      var handleRef = React.useRef(null);
      var state = React.useState(false);
      var gone = state[0];
      var setGone = state[1];

      React.useEffect(function () {
        if (playedThisLoad || !hostRef.current) { setGone(true); return; }
        playedThisLoad = true;
        handleRef.current = mountSplash(hostRef.current, {
          onDone: function () { setGone(true); },
        });
        return function () {
          if (handleRef.current) { handleRef.current.destroy(); handleRef.current = null; }
        };
      }, []);

      if (gone) return null;
      return h("div", { ref: hostRef, className: "dsh-splash-fish", "aria-hidden": "true" });
    }

    return {
      inject: ["slots"],
      apply: function (ctx) {
        ctx.slots.inject("shell.overlay", function () {
          return ctx.slots.register({
            name: "shell.overlay",
            id: "dsh-splash-fish",
            order: -1000,
            label: function () { return "Splash (fish)"; },
          }, Overlay);
        });
        ctx.effect(function () {
          var style = document.createElement("style");
          style.id = "dsh-splash-fish-style";
          style.textContent = CSS +
            ".dsh-splash-fish{position:fixed;inset:0;z-index:2147483600;overflow:hidden;" +
            '--sf-img:url("__IMG_DATA_URI__")}';
          document.head.appendChild(style);
          return function () { style.remove(); };
        });
      },
    };
  },
});

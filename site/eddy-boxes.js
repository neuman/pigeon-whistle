// Eddy boxes on the static site.
//
// Eddy draws the boxes in site/boxes/<id>/box.json (agent.md section 5); nopekit's
// static renderer (page.js, marketing.js) does not, so the GitHub Pages site showed
// none of the pictures Eddy shows. This file is the project's own, loaded by the two
// page shells, and follows Eddy's placement (nopekit server/static/app.js):
//   engineering  choices, implications -> a "Pictures" section after the grounding map
//                (the static page has no choices or implications sections);
//                claims -> inside the board its `about` names, else after the boards
//   marketing    story -> after the story; specs -> after "what it must do"
// A custom box runs in a sandboxed frame (allow-scripts only) with its thumbnail in
// front until it posts {eddy: "ready"}, as on Eddy.
//
// The list of boxes is boxes/index.json, written by the Pages workflow at deploy time
// (.github/scripts/boxes_index.py); a static host cannot list a folder. No list, no
// boxes, no error. Remove this file when nopekit renders boxes (neuman/nopekit#26).
(function () {
  "use strict";
  var VIEW = document.documentElement.dataset.boxview || (location.pathname.indexOf("/marketing") >= 0 ? "marketing" : "engineering");

  var css = [
    ".ybox{margin:16px 0;border:2px solid #c9a400;border-radius:8px;background:var(--panel,#fff);position:relative;overflow:hidden;display:grid;min-width:0}",
    ".ytag{position:absolute;top:0;left:0;z-index:2;font:600 10.5px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.06em;text-transform:uppercase;background:#c9a400;color:#fff;padding:2px 8px;border-radius:0 0 6px 0}",
    ".ybox figcaption{border-top:1px solid var(--line,#ded9d2);padding:8px 12px;font-size:13px;color:var(--muted,#6b7480)}",
    ".ybox img,.ybox video{display:block;width:100%;height:auto}",
    ".boxframe{position:relative;width:100%}",
    ".boxframe iframe{position:absolute;inset:0;width:100%;height:100%;border:0;opacity:0}",
    ".boxframe.ready iframe{opacity:1}.boxframe .thumb{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}",
    ".boxframe.ready .thumb{visibility:hidden}",
    ".boxframe .vnote{position:absolute;left:10px;bottom:8px;right:10px;font-size:12px;color:var(--muted,#6b7480);pointer-events:none}",
    ".board .ybox{margin:14px}",
    "#pictures .ybox,#story .ybox,#asked .ybox{max-width:760px}",
  ].join("\n");

  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "text") n.textContent = attrs[k]; else n.setAttribute(k, attrs[k]);
    });
    (kids || []).forEach(function (c) { if (c) n.appendChild(c); });
    return n;
  }
  function dark() {
    var t = document.documentElement.dataset.theme;
    if (t) return t === "dark";
    return !!(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
  }
  function url(b, file) { return "boxes/" + encodeURIComponent(b.id) + "/" + encodeURIComponent(file); }

  function boxNode(b) {
    var cap = el("figcaption", {}, [b.title ? el("b", { text: b.title + " " }) : null, document.createTextNode(b.caption || "")]);
    var tag, body;
    if (b.kind === "image") {
      tag = "image";
      body = el("img", { src: url(b, b.src), alt: b.title || b.caption || "", loading: "lazy" });
      body.addEventListener("error", function () { if (b.thumbnail && body.getAttribute("src") !== url(b, b.thumbnail)) body.src = url(b, b.thumbnail); }, { once: true });
    } else if (b.kind === "video") {
      tag = "video";
      body = el("video", { controls: "", preload: "metadata", poster: url(b, b.thumbnail), src: url(b, b.src) });
    } else {
      tag = "custom · runs live";
      body = el("div", { class: "boxframe", style: "aspect-ratio:" + String(b.aspect || "4/3").replace("/", " / ") }, [
        el("img", { class: "thumb", src: url(b, b.thumbnail), alt: b.title || "Static thumbnail" }),
        el("iframe", { sandbox: "allow-scripts", loading: "lazy", title: b.title || b.id, src: url(b, b.src) + "#" + (dark() ? "dark" : "light") }),
        el("div", { class: "vnote" }),
      ]);
      setTimeout(function () {
        if (!body.classList.contains("ready")) body.querySelector(".vnote").textContent = "Static thumbnail: this box has not started.";
      }, 10000);
    }
    return el("figure", { class: "ybox", "data-box": b.id }, [el("div", { class: "ytag", text: tag }), body, cap]);
  }

  window.addEventListener("message", function (e) {
    if (!e.data || e.data.eddy !== "ready") return;
    var frames = document.querySelectorAll(".boxframe iframe");
    for (var i = 0; i < frames.length; i++) {
      if (frames[i].contentWindow === e.source) {
        frames[i].parentNode.classList.add("ready");
        frames[i].parentNode.querySelector(".vnote").textContent = "";
      }
    }
  });

  function forView(boxes, section) {
    return boxes.filter(function (b) { return b.section === section && (b.view === "both" || b.view === VIEW); });
  }
  function ready() {
    if (VIEW === "marketing") { var s = document.getElementById("story"); return s && !s.hidden && s.children.length > 0; }
    var b = document.getElementById("boards"); return b && b.children.length > 0;
  }

  function place(boxes) {
    if (document.querySelector("[data-box]")) return; // already placed, and still on the page
    if (VIEW === "marketing") {
      var story = document.getElementById("story"), asked = document.getElementById("asked");
      forView(boxes, "story").forEach(function (b) { story.appendChild(boxNode(b)); });
      var specs = forView(boxes, "specs");
      if (specs.length && asked) specs.forEach(function (b) { asked.appendChild(boxNode(b)); });
      return;
    }
    var pics = forView(boxes, "choices").concat(forView(boxes, "implications"));
    if (pics.length) {
      var sec = el("section", { class: "nk-sec", id: "pictures" }, [el("h2", { text: "Pictures" })]);
      pics.forEach(function (b) { sec.appendChild(boxNode(b)); });
      var map = document.getElementById("map");
      map.parentNode.insertBefore(sec, map.nextSibling);
    }
    var boards = document.getElementById("boards"), rest = [];
    forView(boxes, "claims").forEach(function (b) {
      var home = b.about && document.getElementById("board-" + b.about);
      if (home) home.appendChild(boxNode(b)); else rest.push(b);
    });
    rest.forEach(function (b) { boards.parentNode.insertBefore(boxNode(b), boards.nextSibling); });
  }

  function start(boxes) {
    if (!boxes.length) return;
    document.head.appendChild(el("style", { text: css }));
    var tries = 0;
    (function wait() {
      if (ready()) { place(boxes); setInterval(function () { if (ready()) place(boxes); }, 1500); return; }
      if (++tries < 150) setTimeout(wait, 200);
    })();
  }

  fetch("boxes/index.json", { cache: "no-store" })
    .then(function (r) { return r.ok ? r.json() : { boxes: [] }; })
    .then(function (d) { start((d && d.boxes) || []); })
    .catch(function () { /* no list: a site without boxes */ });
})();

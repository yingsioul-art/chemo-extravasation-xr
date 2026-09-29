/* 使用者後台紀錄（2026-09-30）
 * 各站進出＋每題作答 → Google Apps Script（同前後測 ENDPOINT，payload.type="activity"）→ 試算表工作表 activity
 * 用法：<script src="../assets/js/track.js" data-page="learn"></script>
 *       XRT.track("answer", {item:"Q3", choice:"A", correct:true, attempt:1})
 * 原則：不收姓名、不收病人資料；所有存取 try/catch，失敗不影響頁面。
 */
(function () {
  "use strict";
  var ENDPOINT = "https://script.google.com/macros/s/AKfycby8y3kZ0DrQeeNRm7CpHuokuO8F1g4Q3WRfuE_zmEq8q91G2vdbyC0pp7wX7BEHx6RuVA/exec";
  var CODE_KEY = "xr:code", TEST_CODE_KEY = "xrtest:lastcode", Q_KEY = "xr:actq";
  var CODE_RE = /^[0-9]{4}_(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])$/;
  var MAX_BATCH = 20, FLUSH_MS = 10000, MAX_STORE = 800;

  var me = document.currentScript;
  var PAGE = (me && me.getAttribute("data-page")) || (location.pathname.split("/").filter(Boolean).slice(-1)[0] || "home").replace(/\.html$/, "");
  if (PAGE === "chemo-extravasation-xr" || PAGE === "index" || PAGE === "docs") PAGE = "home";

  function ls(k, v) { try { if (v === undefined) return localStorage.getItem(k); if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) {} return null; }
  function rid(n) { var s = ""; var c = "abcdefghijkmnpqrstuvwxyz23456789"; for (var i = 0; i < n; i++) s += c[Math.floor(Math.random() * c.length)]; return s; }
  function isoLocal(d) { var z = d.getTimezoneOffset(), a = Math.abs(z), p = function (x) { return (x < 10 ? "0" : "") + x; };
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()) + "T" + p(d.getHours()) + ":" + p(d.getMinutes()) + ":" + p(d.getSeconds()) + (z <= 0 ? "+" : "-") + p(Math.floor(a / 60)) + ":" + p(a % 60); }

  var SID = rid(10), t0 = Date.now(), visMs = 0, visFrom = document.visibilityState === "visible" ? Date.now() : null, seq = 0, xrMode = false;
  function getCode() { var c = ls(CODE_KEY) || ls(TEST_CODE_KEY) || ""; return CODE_RE.test(c) ? c : ""; }
  function setCode(c) { c = String(c || "").trim(); if (c && !CODE_RE.test(c)) return false; ls(CODE_KEY, c || null); if (c) ls(TEST_CODE_KEY, c); return true; }
  function device() {
    var w = Math.min(screen.width || innerWidth, screen.height || innerHeight), touch = "ontouchstart" in window || navigator.maxTouchPoints > 0;
    var dev = /iPad|Tablet/i.test(navigator.userAgent) || (touch && w >= 600) ? "tablet" : (touch && w < 600) ? "phone" : "desktop";
    return { dev: dev, orient: innerWidth >= innerHeight ? "landscape" : "portrait" };
  }

  var queue = [];
  function load() { try { var a = JSON.parse(ls(Q_KEY) || "[]"); return Array.isArray(a) ? a : []; } catch (e) { return []; } }
  function store() { try { var a = load().concat(queue).slice(-MAX_STORE); queue = []; ls(Q_KEY, JSON.stringify(a)); } catch (e) {} }

  function track(action, data) {
    try {
      data = data || {}; var d = device();
      var ev = { eid: SID + "-" + (++seq), t: isoLocal(new Date()), code: getCode(), page: data.page || PAGE, action: action,
        item: data.item, choice: data.choice, correct: data.correct, attempt: data.attempt, dwell: data.dwell, value: data.value,
        extra: data.extra, sid: SID, dev: d.dev, orient: d.orient, xr: xrMode || !!data.xr };
      queue.push(ev);
      if (queue.length >= MAX_BATCH) flush(false);
    } catch (e) {}
  }

  function send(events, beacon) {
    var body = JSON.stringify({ type: "activity", events: events });
    try {
      if (beacon && navigator.sendBeacon && navigator.sendBeacon(ENDPOINT, new Blob([body], { type: "text/plain;charset=utf-8" }))) return Promise.resolve(true);
    } catch (e) {}
    try {
      return fetch(ENDPOINT, { method: "POST", mode: "no-cors", keepalive: body.length < 60000, headers: { "Content-Type": "text/plain;charset=utf-8" }, body: body })
        .then(function () { return true; }, function () { return false; });
    } catch (e) { return Promise.resolve(false); }
  }
  var busy = false;
  function flush(beacon) {
    try {
      store(); var all = load(); if (!all.length || (busy && !beacon)) return;
      var batch = all.slice(0, 50); ls(Q_KEY, JSON.stringify(all.slice(50)));   // 先移出；失敗再放回
      busy = true;
      send(batch, beacon).then(function (ok) { busy = false; if (!ok) { try { ls(Q_KEY, JSON.stringify(batch.concat(load()).slice(-MAX_STORE))); } catch (e) {} } else if (load().length && !beacon) flush(false); });
    } catch (e) { busy = false; }
  }

  function dwellSec() { var v = visMs + (visFrom ? Date.now() - visFrom : 0); return Math.round(v / 1000); }
  var left = false;
  function leave() {
    if (left) return; left = true;
    track("leave", { dwell: dwellSec(), value: Math.round((Date.now() - t0) / 1000) });
    flush(true);
  }
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") { if (visFrom) { visMs += Date.now() - visFrom; visFrom = null; } store(); flush(true); }
    else { visFrom = Date.now(); if (left) { left = false; track("return", {}); } }
  });
  window.addEventListener("pagehide", leave);
  /* 點連結離開本頁（到其他站、外部 AI 網站等）自動記錄 */
  document.addEventListener("click", function (e) {
    try {
      var a = e.target.closest && e.target.closest("a[href]"); if (!a || a.dataset.noTrack !== undefined) return;
      var h = a.getAttribute("href"); if (!h || h.charAt(0) === "#" || /^javascript:/i.test(h)) return;
      track("open_link", { item: a.id || (a.textContent || "").trim().slice(0, 40), choice: h.split("?")[0] }); flush(true);
    } catch (x) {}
  }, true);
  setInterval(function () { if (queue.length || load().length) flush(false); }, FLUSH_MS);

  window.XRT = { track: track, getCode: getCode, setCode: setCode, flush: flush, page: PAGE, sid: SID, CODE_RE: CODE_RE,
    setXR: function (on) { xrMode = !!on; }, _endpoint: ENDPOINT };
  track("enter", { extra: { ref: document.referrer ? document.referrer.replace(/^https?:\/\/[^/]+/, "") : "", hash: location.hash || undefined, q: location.search || undefined } });
  setTimeout(function () { flush(false); }, 1500);   // 補送上次沒送出的
})();

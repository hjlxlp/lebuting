(function () {
  "use strict";
  var deg = { eat: 0, cook: 0 };
  var amt = "0";

  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }

  function go(id) {
    $$(".page").forEach(function (p) { p.classList.toggle("on", p.id === "p-" + id); });
    $$(".side-item").forEach(function (b) { b.classList.toggle("on", b.dataset.screen === id); });
  }

  function bind() {
    $$(".side-item").forEach(function (b) {
      b.addEventListener("click", function () { go(b.dataset.screen); });
    });
    document.addEventListener("click", function (e) {
      var row = e.target.closest(".row-tap");
      if (row && !e.target.closest(".row-ops")) {
        var goId = row.dataset.go;
        if (goId) { e.preventDefault(); go(goId); return; }
      }
      var t = e.target.closest("[data-go]");
      if (t) { e.preventDefault(); go(t.dataset.go); }
    });
    $$(".tabs button").forEach(function (b) {
      b.addEventListener("click", function () { if (b.dataset.go) go(b.dataset.go); });
    });
    $$(".mod-card").forEach(function (c) {
      c.addEventListener("click", function () {
        var m = { chat: "chat", eat: "eat-wheel", cook: "cook-wheel", bill: "bill-home" };
        if (m[c.dataset.mod]) go(m[c.dataset.mod]);
      });
    });

    ["eat", "cook"].forEach(function (mod) {
      var btn = document.getElementById(mod + "-go");
      var ndl = document.getElementById(mod + "-ndl");
      var res = document.getElementById(mod + "-res");
      var data = {
        eat: { n: "成都你六姐 · 火锅", m: "本月已吃 3 次" },
        cook: { n: "番茄炒蛋 · 家常菜", m: "本月已做 5 次" }
      };
      if (!btn || !ndl) return;
      btn.addEventListener("click", function () {
        deg[mod] += 720 + Math.floor(Math.random() * 360);
        ndl.style.transform = "translate(-50%, -100%) rotate(" + deg[mod] + "deg)";
        btn.disabled = true;
        setTimeout(function () {
          btn.disabled = false;
          if (!res) return;
          res.hidden = false;
          document.getElementById(mod + "-rn").textContent = data[mod].n;
          document.getElementById(mod + "-rm").textContent = data[mod].m;
        }, 420);
      });
    });

    var inp = document.getElementById("chat-in");
    var send = document.getElementById("chat-go");
    var list = document.getElementById("chat-msgs");
    if (inp && send && list) {
      function esc(s) { return s.replace(/&/g, "&amp;").replace(/</g, "&lt;"); }
      function push(role, text) {
        var d = document.createElement("div");
        d.className = "bubble " + role;
        d.innerHTML = esc(text);
        list.appendChild(d);
        list.scrollTop = list.scrollHeight;
      }
      function submit() {
        var t = inp.value.trim();
        if (!t) return;
        push("me", t);
        inp.value = "";
        setTimeout(function () { push("ai", "收到。正式版将连接 Agent。"); }, 500);
      }
      send.addEventListener("click", submit);
      inp.addEventListener("keydown", function (e) { if (e.key === "Enter") submit(); });
    }

    var disp = document.getElementById("bill-amt");
    if (disp) {
      $$(".pad button").forEach(function (k) {
        k.addEventListener("click", function () {
          var v = k.dataset.k;
          if (v === "clr") amt = "0";
          else if (v === "bk") amt = amt.length <= 1 ? "0" : amt.slice(0, -1);
          else if (v === "ok") { go("bill-home"); return; }
          else if (v === ".") { if (amt.indexOf(".") < 0) amt += "."; }
          else amt = amt === "0" ? v : amt + v;
          disp.textContent = amt;
        });
      });
    }

    $$(".cats .cat").forEach(function (c) {
      c.addEventListener("click", function () {
        if (c.dataset.go) return;
        $$(".cats .cat").forEach(function (x) { x.classList.remove("on"); });
        c.classList.add("on");
      });
    });

    $$(".type-row, .switch-row, .seg, .tag-row").forEach(function (g) {
      $$("button", g).forEach(function (b) {
        b.addEventListener("click", function (e) {
          e.stopPropagation();
          $$("button", g).forEach(function (x) { x.classList.remove("on"); });
          b.classList.add("on");
        });
      });
    });

    go("home");
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bind);
  else bind();
})();

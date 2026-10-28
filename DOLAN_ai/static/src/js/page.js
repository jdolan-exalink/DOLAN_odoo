/** DOLAN AI — pagina de conexion ChatGPT (vanilla, sin dependencias). */
(function () {
  "use strict";
  function rpc(path, params) {
    return fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: params || {} }),
      credentials: "same-origin",
    }).then(function (r) { return r.json(); }).then(function (j) { return j.result || j.error || { error: "rpc" }; });
  }
  var el = function (id) { return document.getElementById(id); };
  var pollTimer = null;
  function setStatus(txt, cls) {
    var s = el("dolan-ai-status");
    if (s) { s.textContent = txt; s.className = "badge " + (cls || "bg-secondary"); }
  }
  function showCode(data) {
    var box = el("dolan-ai-device");
    if (!box) return;
    if (data && data.user_code) {
      box.style.display = "block";
      el("dolan-ai-code").textContent = data.user_code;
      el("dolan-ai-uri").textContent = data.verification_uri;
      el("dolan-ai-uri").href = data.verification_uri;
      setStatus("Esperando autorizacion…", "bg-warning text-dark");
      var every = Math.max(3, Math.min(15, data.interval || 5)) * 1000;
      if (pollTimer) clearInterval(pollTimer);
      var tries = 0;
      pollTimer = setInterval(function () {
        tries += 1;
        if (tries > 180) { clearInterval(pollTimer); setStatus("Tiempo agotado", "bg-danger"); return; }
        rpc("/dolan_ai/poll").then(function (res) {
          if (res.status === "connected") {
            clearInterval(pollTimer);
            box.style.display = "none";
            setStatus("Conectado" + (res.account_id ? " (" + res.account_id.slice(0, 8) + "…)" : ""), "bg-success");
          } else if (res.status === "failed") {
            clearInterval(pollTimer);
            setStatus("Fallo: " + (res.error || "desconocido"), "bg-danger");
          } else if (res.status === "slow_down") {
            clearInterval(pollTimer);
            setTimeout(function () { pollTimer = setInterval(arguments.callee, every + 2000); }, every);
          }
        });
      }, every);
    }
  }
  document.addEventListener("DOMContentLoaded", function () {
    var bStart = el("dolan-ai-connect");
    if (bStart) bStart.addEventListener("click", function () {
      setStatus("Solicitando codigo…", "bg-info text-dark");
      rpc("/dolan_ai/start").then(function (res) {
        if (res.error) { setStatus("Error: " + res.error, "bg-danger"); return; }
        showCode(res);
      });
    });
    var bTest = el("dolan-ai-test");
    if (bTest) bTest.addEventListener("click", function () {
      setStatus("Probando…", "bg-info text-dark");
      rpc("/dolan_ai/test").then(function (res) {
        if (res.ok) {
          setStatus("Prueba OK: " + (res.text || "").slice(0, 60), "bg-success");
        } else {
          setStatus("Prueba fallo: " + res.error, "bg-danger");
        }
      });
    });
    var bOut = el("dolan-ai-logout");
    if (bOut) bOut.addEventListener("click", function () {
      rpc("/dolan_ai/logout").then(function () { setStatus("Desconectado", "bg-secondary"); });
    });
    // estado inicial
    rpc("/dolan_ai/status").then(function (res) {
      if (res.connected) setStatus("Conectado" + (res.account_id ? " (" + String(res.account_id).slice(0, 8) + "…)" : ""), "bg-success");
      else if (res.needs_reconnect) setStatus("Token vencido — reconectar", "bg-warning text-dark");
      else if (res.device_pending) setStatus("Pendiente de autorizar", "bg-warning text-dark");
      else setStatus("Sin conexion", "bg-secondary");
    });
  });
})();

/* ===== Agentes (v1 tool-loop) ===== */
(function () {
  "use strict";
  function rpcA(path, params) {
    return fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: params }),
      credentials: "same-origin",
    }).then(function (r) { return r.json(); }).then(function (j) { return j.result || j.error || { error: "rpc" }; });
  }
  document.addEventListener("DOMContentLoaded", function () {
    var sel = document.getElementById("dolan-ai-agente");
    var input = document.getElementById("dolan-ai-agente-text");
    var btn = document.getElementById("dolan-ai-agente-run");
    var out = document.getElementById("dolan-ai-agente-out");
    if (!sel) return;
    rpcA("/dolan_ai/agentes").then(function (res) {
      (res.agentes || []).forEach(function (a) {
        var o = document.createElement("option");
        o.value = a.id; o.textContent = a.name;
        sel.appendChild(o);
      });
    });
    if (btn) btn.addEventListener("click", function () {
      var text = (input.value || "").trim();
      if (!text) return;
      out.innerHTML = "<i>Pensando…</i>";
      rpcA("/dolan_ai/agente/run", { agente_id: sel.value, text: text }).then(function (res) {
        if (res.error) { out.innerHTML = '<span style="color:#dc2626">Error: ' + res.error + "</span>"; return; }
        out.innerHTML = "<b>Agente:</b> " + (res.reply || JSON.stringify(res.tool_result || {}).slice(0, 300));
      });
    });
  });
})();

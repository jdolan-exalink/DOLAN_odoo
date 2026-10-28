/** DOLAN AI — página de conexión ChatGPT + Agentes v2 (conversaciones). */
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
  var convActual = null;

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
      setStatus("Esperando autorización…", "bg-warning");
      var every = Math.max(3, Math.min(15, data.interval || 5)) * 1000;
      if (pollTimer) clearInterval(pollTimer);
      var tries = 0;
      pollTimer = setInterval(function () {
        tries += 1;
        if (tries > 180) { clearInterval(pollTimer); setStatus("Tiempo agotado", "bg-danger"); return; }
        rpc("/dolan_ai/poll").then(function (res) {
          if (res.status === "connected") {
            clearInterval(pollTimer);
            el("dolan-ai-device").style.display = "none";
            setStatus("Conectado" + (res.account_id ? " (" + String(res.account_id).slice(0, 8) + "…)" : ""), "bg-success");
          } else if (res.status === "failed") {
            clearInterval(pollTimer);
            setStatus("Fallo: " + (res.error || "desconocido"), "bg-danger");
          }
        });
      }, every);
    }
  }

  function cargarMensajes(cid) {
    convActual = cid;
    return rpc("/dolan_ai/conv/messages", { conversacion_id: cid }).then(function (res) {
      var hilo = el("dolan-ai-hilo");
      if (!hilo) return;
      hilo.innerHTML = "";
      (res.mensajes || []).forEach(function (m) {
        var div = document.createElement("div");
        div.style.margin = "6px 0";
        var who = m.rol === "user" ? "Vos" : (m.rol === "tool" ? "🔧 herramienta" : "Agente");
        var color = m.rol === "user" ? "#714b67" : (m.rol === "tool" ? "#6b7280" : "#1f2937");
        div.innerHTML = '<div style="font-size:11px;color:#94a3b8;font-weight:700">' + who + '</div>' +
          '<div style="color:' + color + ';white-space:pre-wrap">' + String(m.content).replace(/</g, "&lt;") + '</div>';
        hilo.appendChild(div);
      });
      hilo.scrollTop = hilo.scrollHeight;
    });
  }

  function cargarConversaciones(agenteId) {
    return rpc("/dolan_ai/conv/list", { agente_id: agenteId }).then(function (res) {
      var sel = el("dolan-ai-conv");
      if (!sel) return;
      sel.innerHTML = "";
      (res.conversaciones || []).forEach(function (c) {
        var o = document.createElement("option");
        o.value = c.id;
        o.textContent = c.name + " · " + (c.user_id && c.user_id[1] ? c.user_id[1] : "");
        sel.appendChild(o);
      });
      if (sel.options.length) {
        sel.value = sel.options[0].value;
        cargarMensajes(sel.options[0].value);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var bStart = el("dolan-ai-connect");
    if (bStart) bStart.addEventListener("click", function () {
      setStatus("Solicitando código…", "bg-info");
      rpc("/dolan_ai/start").then(function (res) {
        if (res.error) { setStatus("Error: " + res.error, "bg-danger"); return; }
        showCode(res);
      });
    });
    var bTest = el("dolan-ai-test");
    if (bTest) bTest.addEventListener("click", function () {
      setStatus("Probando…", "bg-info");
      rpc("/dolan_ai/test").then(function (res) {
        setStatus(res.ok ? "Prueba OK: " + (res.text || "").slice(0, 50) : "Prueba falló: " + res.error,
                  res.ok ? "bg-success" : "bg-danger");
      });
    });
    var bOut = el("dolan-ai-logout");
    if (bOut) bOut.addEventListener("click", function () {
      rpc("/dolan_ai/logout").then(function () { setStatus("Desconectado", "bg-secondary"); });
    });
    // estado inicial
    rpc("/dolan_ai/status").then(function (res) {
      if (res.connected) setStatus("Conectado" + (res.account_id ? " (" + String(res.account_id).slice(0, 8) + "…)" : ""), "bg-success");
      else if (res.needs_reconnect) setStatus("Token vencido — reconectar", "bg-warning");
      else if (res.device_pending) setStatus("Pendiente de autorizar", "bg-warning");
      else setStatus("Sin conexión", "bg-secondary");
    });
    // Agentes v2
    var selAg = el("dolan-ai-agente");
    if (selAg) {
      rpc("/dolan_ai/agentes").then(function (res) {
        var opts = res.agentes || [];
        if (!opts.length) {
          el("dolan-ai-agente-out").textContent = "Sin agentes todavía — recargá (se crea uno de ejemplo).";
          return;
        }
        opts.forEach(function (a) {
          var o = document.createElement("option");
          o.value = a.id; o.textContent = a.name;
          selAg.appendChild(o);
        });
        cargarConversaciones(opts[0].id);
      });
      selAg.addEventListener("change", function () { cargarConversaciones(selAg.value); });
      var selConv = el("dolan-ai-conv");
      if (selConv) selConv.addEventListener("change", function () { cargarMensajes(selConv.value); });
      var bRun = el("dolan-ai-agente-run");
      if (bRun) bRun.addEventListener("click", function () {
        var text = (el("dolan-ai-agente-text").value || "").trim();
        if (!text) return;
        el("dolan-ai-agente-out").innerHTML = "<i>Pensando…</i>";
        rpc("/dolan_ai/agente/run", { agente_id: selAg.value, text: text, conversacion_id: convActual }).then(function (res) {
          if (res.error) {
            el("dolan-ai-agente-out").innerHTML = '<span style="color:#dc2626">Error: ' + res.error + "</span>";
            return;
          }
          if (res.conversacion_id) cargarMensajes(res.conversacion_id);
          if (!res.done) el("dolan-ai-agente-out").innerHTML = "<i>Continuando…</i>";
        });
      });
    }
  });
})();

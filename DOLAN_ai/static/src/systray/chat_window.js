/** @odoo-module **/
// ChatWindow flotante DOLAN AI (vanilla, estética EE refinada).
import { rpc } from "@web/core/network/rpc";

(function initOnce() {
    if (window.__dolanAiChat) return;
    window.__dolanAiChat = true;
    let win = null, open = false, convActual = null, agenteActual = null;
    const CSS = `
    .o_dolan_ai_win{position:fixed;right:16px;bottom:16px;width:400px;max-width:calc(100vw-32px);height:580px;max-height:calc(100vh-80px);background:#fff;border:none;border-radius:16px;box-shadow:0 16px 48px rgba(0,0,0,.18),0 4px 12px rgba(0,0,0,.08);display:flex;flex-direction:column;z-index:1100;overflow:hidden;font-family:Inter,-apple-system,system-ui,sans-serif;animation:dolanIn .2s cubic-bezier(.16,1,.3,1)}
    @keyframes dolanIn{from{transform:translateY(20px) scale(.97);opacity:0}to{transform:translateY(0) scale(1);opacity:1}}
    .o_dolan_ai_win[data-theme="dark"]{background:#1a1a2e;color:#e2e8f0}
    .o_dolan_ai_head{display:flex;align-items:center;gap:10px;padding:14px 16px;background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;flex-shrink:0}
    .o_dolan_ai_logo{width:32px;height:32px;border-radius:10px;background:linear-gradient(135deg,#714b67,#a67d8e);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:13px;color:#fff;flex-shrink:0;letter-spacing:.5px}
    .o_dolan_ai_head .o_dolan_ai_name{font-weight:700;font-size:15px;flex:1;letter-spacing:-.3px}
    .o_dolan_ai_head .o_dolan_ai_status_dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;background:#94a3b8}
    .o_dolan_ai_head .o_dolan_ai_status_dot.ok{background:#34d399;box-shadow:0 0 6px #34d39966}
    .o_dolan_ai_head .o_dolan_ai_status_dot.err{background:#f87171}
    .o_dolan_ai_head button{background:rgba(255,255,255,.12);border:0;color:#fff;cursor:pointer;font-size:15px;padding:4px 8px;border-radius:8px;transition:background .15s}
    .o_dolan_ai_head button:hover{background:rgba(255,255,255,.25)}
    .o_dolan_ai_body{flex:1;overflow-y:auto;padding:16px 14px;display:flex;flex-direction:column;gap:4px;scroll-behavior:smooth}
    .o_dolan_ai_body::-webkit-scrollbar{width:5px}
    .o_dolan_ai_body::-webkit-scrollbar-thumb{background:#d1d5db;border-radius:99px}
    .o_dolan_ai_msg{max-width:85%;padding:10px 14px;font-size:13.5px;line-height:1.5;white-space:pre-wrap;word-break:break-word}
    .o_dolan_ai_msg.user{align-self:flex-end;background:#714b67;color:#fff;border-radius:16px 16px 4px 16px;margin-left:12px}
    .o_dolan_ai_msg.assistant{align-self:flex-start;background:#f4f4f8;color:#1a1a2e;border-radius:16px 16px 16px 4px;margin-right:12px}
    .o_dolan_ai_win[data-theme="dark"] .o_dolan_ai_msg.assistant{background:#2a2a4a;color:#e2e8f0}
    .o_dolan_ai_msg.tool{align-self:center;font-size:11px;color:#94a3b8;padding:4px 8px}
    .o_dolan_ai_typing{align-self:flex-start;display:flex;gap:4px;padding:12px 16px}
    .o_dolan_ai_typing span{width:7px;height:7px;border-radius:50%;background:#b8b8c8;animation:dolanBounce 1.4s infinite}
    .o_dolan_ai_typing span:nth-child(2){animation-delay:.2s}
    .o_dolan_ai_typing span:nth-child(3){animation-delay:.4s}
    @keyframes dolanBounce{0%,60%,100%{transform:translateY(0);opacity:.4}30%{transform:translateY(-6px);opacity:1}}
    .o_dolan_ai_welcome{text-align:center;padding:20px 10px;margin:auto 0}
    .o_dolan_ai_welcome .big{font-size:28px;margin-bottom:8px}
    .o_dolan_ai_welcome .t1{font-weight:700;font-size:15px;color:#1a1a2e}
    .o_dolan_ai_welcome .t2{font-size:12.5px;color:#94a3b8;margin-top:4px}
    .o_dolan_ai_win[data-theme="dark"] .o_dolan_ai_welcome .t1{color:#e2e8f0}
    .o_dolan_ai_chips{display:flex;flex-direction:column;gap:6px;margin-top:16px;padding:0 8px}
    .o_dolan_ai_chip{background:#fff;border:1.5px solid #e5e7eb;border-radius:12px;padding:9px 14px;font-size:12.5px;text-align:left;cursor:pointer;color:#4338ca;font-weight:500;transition:all .15s}
    .o_dolan_ai_chip:hover{border-color:#714b67;background:#faf7f8;transform:translateX(2px)}
    .o_dolan_ai_win[data-theme="dark"] .o_dolan_ai_chip{background:#2a2a4a;border-color:#40406a;color:#c4b5fd}
    .o_dolan_ai_win[data-theme="dark"] .o_dolan_ai_chip:hover{border-color:#714b67}
    .o_dolan_ai_foot{border-top:1px solid #e5e7eb;padding:12px 14px;display:flex;gap:8px;flex-shrink:0}
    .o_dolan_ai_win[data-theme="dark"] .o_dolan_ai_foot{border-color:#40406a}
    .o_dolan_ai_foot input{flex:1;border:1.5px solid #e5e7eb;border-radius:12px;padding:10px 16px;font-size:13.5px;outline:none;transition:border-color .15s;font-family:inherit}
    .o_dolan_ai_foot input:focus{border-color:#714b67;box-shadow:0 0 0 3px #714b6718}
    .o_dolan_ai_foot button{background:#714b67;color:#fff;border:0;border-radius:12px;padding:10px 16px;cursor:pointer;font-weight:600;font-size:13px;transition:background .15s}
    .o_dolan_ai_foot button:hover{background:#5d3d56}
    .o_dolan_ai_min .o_dolan_ai_body,.o_dolan_ai_min .o_dolan_ai_foot,.o_dolan_ai_min .o_dolan_ai_sel_wrap{display:none}
    .o_dolan_ai_min{height:auto !important}
    .o_dolan_ai_sel{background:transparent;border:0;color:#fff;font-weight:600;font-size:13px;max-width:140px;outline:none;cursor:pointer;text-overflow:ellipsis}
    .o_dolan_ai_sel option{color:#1a1a2e}
    .o_dolan_ai_sel_wrap{padding:0 14px 8px;display:flex;align-items:center;gap:8px;flex-shrink:0}
    .o_dolan_ai_sel_wrap label{font-size:11px;color:rgba(255,255,255,.6);text-transform:uppercase;letter-spacing:.5px;font-weight:600}
    .o_dolan_ai_conn_btn{background:rgba(255,255,255,.12);border:0;color:#fff;font-size:11px;padding:3px 8px;border-radius:6px;cursor:pointer;font-weight:600}
    `;
    function injectCSS() {
        if (document.getElementById("o_dolan_ai_css")) return;
        const st = document.createElement("style"); st.id = "o_dolan_ai_css"; st.textContent = CSS;
        document.head.appendChild(st);
    }
    function esc(t) { const d = document.createElement("div"); d.textContent = t || ""; return d.innerHTML; }
    function rpc2(path, params) {
        return fetch(path, { method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: params || {} }),
            credentials: "same-origin" }).then(r => r.json()).then(j => j.result || j.error || { error: "rpc" });
    }
    function addMsg(rol, content) {
        const body = win.querySelector(".o_dolan_ai_body");
        const div = document.createElement("div");
        div.className = "o_dolan_ai_msg " + rol;
        div.innerHTML = rol === "tool" ? "🔧 " + esc(content) : esc(content);
        body.appendChild(div); body.scrollTop = body.scrollHeight;
    }
    function showTyping() {
        const body = win.querySelector(".o_dolan_ai_body");
        const div = document.createElement("div"); div.className = "o_dolan_ai_typing";
        div.innerHTML = "<span></span><span></span><span></span>";
        body.appendChild(div); body.scrollTop = body.scrollHeight;
        return div;
    }
    async function checkStatus() {
        const setDot = (cls, title) => {
            const dot = win && win.querySelector(".o_dolan_ai_status_dot");
            if (dot) { dot.className = "o_dolan_ai_status_dot " + cls; dot.title = title; }
        };
        setDot("pending", "Verificando conexión…");
        let st = null;
        try { st = await rpc2("/dolan_ai/status"); } catch { st = null; }
        if (!st || st.error || typeof st.connected !== "boolean") {
            // sin dato fiable (permisos, red, error): gris, nunca verde ni rojo mentiroso
            setDot("pending", "Estado no disponible");
        } else if (st.connected) {
            setDot("ok", st.expired ? "Conectado — token por renovar" : "Conectado con ChatGPT");
        } else {
            setDot("err", st.device_pending ? "Código de conexión pendiente" : "Sin conexión");
        }
        return st;
    }
    async function loadThread(cid) {
        convActual = cid;
        const body = win.querySelector(".o_dolan_ai_body");
        body.querySelectorAll(".o_dolan_ai_msg,.o_dolan_ai_chips,.o_dolan_ai_welcome,.o_dolan_ai_typing").forEach(e => e.remove());
        const res = await rpc2("/dolan_ai/conv/messages", { conversacion_id: cid });
        (res.mensajes || []).forEach(m => addMsg(m.rol, m.content));
        if (!(res.mensajes || []).length) {
            const w = document.createElement("div"); w.className = "o_dolan_ai_welcome";
            w.innerHTML = '<div class="big">🤖</div><div class="t1">DOLAN AI</div><div class="t2">Tu asistente dentro de Odoo</div>';
            body.appendChild(w);
        }
        await chipsFor(agenteActual);
    }
    async function chipsFor(agenteId) {
        const res = await rpc2("/dolan_ai/prompts", { agente_id: agenteId });
        let pairs = (res.prompts || []).map(p => ({ name: p.name, prompt: p.prompt }));
        if (!pairs.length) {
            const ags = await rpc2("/dolan_ai/agentes");
            const ag = (ags.agentes || []).find(a => String(a.id) === String(agenteId)) || (ags.agentes || [])[0];
            pairs = (ag && ag.sugerencias ? ag.sugerencias.split("\n") : []).filter(x => x.trim()).map(x => ({ name: x.trim(), prompt: x.trim() }));
        }
        if (win && pairs.length) {
            const body = win.querySelector(".o_dolan_ai_body");
            const box = document.createElement("div"); box.className = "o_dolan_ai_chips";
            pairs.slice(0, 3).forEach(p => {
                const c = document.createElement("div"); c.className = "o_dolan_ai_chip";
                c.textContent = p.name; c.title = p.prompt;
                c.addEventListener("click", () => send(p.prompt || p.name));
                box.appendChild(c);
            });
            body.appendChild(box);
        }
    }
    async function loadAgents() {
        const res = await rpc2("/dolan_ai/agentes");
        const sel = win.querySelector(".o_dolan_ai_sel"); sel.innerHTML = "";
        (res.agentes || []).forEach(a => {
            const o = document.createElement("option"); o.value = a.id; o.textContent = a.name; sel.appendChild(o);
        });
        if (sel.options.length) { agenteActual = parseInt(sel.options[0].value); sel.value = String(agenteActual); }
    }
    async function loadConvs() {
        const body = win.querySelector(".o_dolan_ai_body");
        body.querySelectorAll(".o_dolan_ai_msg,.o_dolan_ai_chips,.o_dolan_ai_welcome,.o_dolan_ai_typing").forEach(e => e.remove());
        const w = document.createElement("div"); w.className = "o_dolan_ai_welcome";
        w.innerHTML = '<div class="big">🤖</div><div class="t1">DOLAN AI</div><div class="t2">Tu asistente dentro de Odoo</div>';
        body.appendChild(w);
        await chipsFor(agenteActual);
    }
    let sending = false;
    async function send(text) {
        text = (text || "").trim(); if (!text || sending) return;
        sending = true;
        const body = win.querySelector(".o_dolan_ai_body");
        body.querySelectorAll(".o_dolan_ai_welcome,.o_dolan_ai_chips").forEach(e => e.remove());
        addMsg("user", text);
        const typing = showTyping();
        win.querySelector("input").value = "";
        try {
            const res = await rpc2("/dolan_ai/agente/run", { agente_id: agenteActual, text: text, conversacion_id: convActual });
            typing.remove();
            if (res.error) addMsg("assistant", "⚠ " + (res.detalle || res.error));
            else {
                if (res.conversacion_id) convActual = res.conversacion_id;
                addMsg("assistant", res.reply || "(sin respuesta)");
            }
        } catch (e) { typing.remove(); addMsg("assistant", "⚠ error de conexión"); }
        sending = false; win.querySelector("input").focus();
    }
    function build() {
        injectCSS();
        win = document.createElement("div"); win.className = "o_dolan_ai_win";
        if (document.documentElement.dataset.dolanTheme === "dark") win.dataset.theme = "dark";
        win.innerHTML = `
            <div class="o_dolan_ai_head">
                <div class="o_dolan_ai_logo">IA</div>
                <span class="o_dolan_ai_name">DOLAN AI</span>
                <span class="o_dolan_ai_status_dot pending" title="Verificando conexión…"></span>
                <button data-a="min" title="Minimizar">—</button>
                <button data-a="close" title="Cerrar">✕</button>
            </div>
            <div class="o_dolan_ai_sel_wrap">
                <label>Agente</label>
                <select class="o_dolan_ai_sel"></select>
            </div>
            <div class="o_dolan_ai_body"></div>
            <div class="o_dolan_ai_foot">
                <input placeholder="Escribí tu consulta…" autocomplete="off"/>
                <button data-a="send">➤</button>
            </div>`;
        document.body.appendChild(win);
        win.querySelector('[data-a="close"]').addEventListener("click", () => { win.remove(); win = null; open = false; });
        win.querySelector('[data-a="min"]').addEventListener("click", () => win.classList.toggle("o_dolan_ai_min"));
        win.querySelector('[data-a="send"]').addEventListener("click", () => send(win.querySelector("input").value));
        win.querySelector("input").addEventListener("keydown", (e) => { if (e.key === "Enter") send(e.target.value); });
        win.querySelector(".o_dolan_ai_sel").addEventListener("change", (e) => { agenteActual = parseInt(e.target.value); convActual = null; loadConvs(); });
        loadAgents().then(() => { loadConvs(); checkStatus(); });
    }
    window.addEventListener("dolan-ai-toggle", () => {
        if (open && win) { win.remove(); win = null; open = false; return; }
        if (!win) build();
        open = true;
    });
})();

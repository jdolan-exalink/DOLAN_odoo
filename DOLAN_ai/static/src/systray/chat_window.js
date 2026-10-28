/** @odoo-module **/
// ChatWindow flotante DOLAN AI (vanilla, estilo EE: 380px fixed bottom-right).
import { rpc } from "@web/core/network/rpc";

(function initOnce() {
    if (window.__dolanAiChat) return;
    window.__dolanAiChat = true;
    let win = null, open = false, convActual = null, agenteActual = null;
    const CSS = `
    .o_dolan_ai_win{position:fixed;right:16px;bottom:16px;width:380px;max-width:calc(100vw-32px);height:560px;max-height:calc(100vh-90px);background:#fff;border:1px solid #e5e7eb;border-radius:14px;box-shadow:0 12px 40px rgba(15,23,42,.22);display:flex;flex-direction:column;z-index:1100;overflow:hidden;font-family:system-ui,sans-serif}
    .o_dolan_ai_win[data-theme="dark"]{background:#1e293b;border-color:#334155;color:#e2e8f0}
    .o_dolan_ai_head{display:flex;align-items:center;gap:8px;padding:10px 12px;border-bottom:1px solid #e5e7eb;background:#714b67;color:#fff}
    .o_dolan_ai_head .t{font-weight:800;font-size:14px;flex:1}
    .o_dolan_ai_head button{background:transparent;border:0;color:#fff;cursor:pointer;font-size:14px;padding:2px 6px;border-radius:6px}
    .o_dolan_ai_head button:hover{background:rgba(255,255,255,.15)}
    .o_dolan_ai_body{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px}
    .o_dolan_ai_msg{max-width:88%;padding:8px 12px;border-radius:12px;font-size:13.5px;line-height:1.35;white-space:pre-wrap;word-break:break-word}
    .o_dolan_ai_msg.user{align-self:flex-end;background:#714b67;color:#fff;border-bottom-right-radius:4px}
    .o_dolan_ai_msg.assistant{align-self:flex-start;background:#f1f5f9;color:#1f2937;border-bottom-left-radius:4px}
    .o_dolan_ai_win[data-theme="dark"] .o_dolan_ai_msg.assistant{background:#334155;color:#e2e8f0}
    .o_dolan_ai_msg.tool{align-self:center;font-size:11px;color:#94a3b8;background:transparent}
    .o_dolan_ai_welcome{align-self:center;text-align:center;color:#6b7280;font-size:12.5px;margin:auto 0}
    .o_dolan_ai_chips{display:flex;flex-direction:column;gap:6px;margin-top:10px}
    .o_dolan_ai_chip{background:#fff;border:1px solid #e5e7eb;border-radius:999px;padding:6px 12px;font-size:12.5px;text-align:center;cursor:pointer;color:#4338ca}
    .o_dolan_ai_chip:hover{background:#eef2ff}
    .o_dolan_ai_win[data-theme="dark"] .o_dolan_ai_chip{background:#334155;border-color:#475569;color:#c7d2fe}
    .o_dolan_ai_foot{border-top:1px solid #e5e7eb;padding:10px;display:flex;gap:8px}
    .o_dolan_ai_foot input{flex:1;border:1px solid #d1d5db;border-radius:999px;padding:9px 14px;font-size:13.5px;outline:none}
    .o_dolan_ai_foot input:focus{border-color:#714b67}
    .o_dolan_ai_foot button{background:#714b67;color:#fff;border:0;border-radius:999px;padding:0 16px;cursor:pointer;font-weight:700}
    .o_dolan_ai_min .o_dolan_ai_body,.o_dolan_ai_min .o_dolan_ai_foot{display:none}
    .o_dolan_ai_min{height:auto !important}
    .o_dolan_ai_sel{background:transparent;border:0;color:#fff;font-weight:700;font-size:13px;max-width:150px;outline:none}
    .o_dolan_ai_sel option{color:#1f2937}
    `;
    function rpc2(path, params) {
        return fetch(path, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: params || {} }),
            credentials: "same-origin",
        }).then(r => r.json()).then(j => j.result || j.error || { error: "rpc" });
    }
    function esc(t) { const d = document.createElement("div"); d.textContent = t || ""; return d.innerHTML; }
    function addMsg(rol, content) {
        const body = win.querySelector(".o_dolan_ai_body");
        const div = document.createElement("div");
        div.className = "o_dolan_ai_msg " + rol;
        div.innerHTML = rol === "tool" ? "🔧 " + esc(content) : esc(content);
        body.appendChild(div);
        body.scrollTop = body.scrollHeight;
        return div;
    }
    function chips(agent) {
        const body = win.querySelector(".o_dolan_ai_body");
        if (!body || !agent) return;
        body.querySelectorAll(".o_dolan_ai_chips").forEach(e => e.remove());
        const list = (agent.sugerencias || "").split("\n").map(x => x.trim()).filter(Boolean).slice(0, 3);
        if (!list.length) return;
        const box = document.createElement("div");
        box.className = "o_dolan_ai_chips";
        list.forEach(s => {
            const c = document.createElement("div");
            c.className = "o_dolan_ai_chip"; c.textContent = s.trim();
            c.addEventListener("click", () => { send(s.trim()); });
            box.appendChild(c);
        });
        const welcome = body.querySelector(".o_dolan_ai_welcome");
        if (welcome) body.insertBefore(box, welcome.nextSibling); else body.appendChild(box);
    }
    async function loadThread(cid) {
        const body = win.querySelector(".o_dolan_ai_body");
        body.querySelectorAll(".o_dolan_ai_msg,.o_dolan_ai_chips,.o_dolan_ai_welcome").forEach(e => e.remove());
        const res = await rpc2("/dolan_ai/conv/messages", { conversacion_id: cid });
        (res.mensajes || []).forEach(m => addMsg(m.rol, m.content));
        if (!(res.mensajes || []).length) {
            const w = document.createElement("div");
            w.className = "o_dolan_ai_welcome";
            w.innerHTML = "<b>DOLAN AI</b><br>Tu asistente dentro de Odoo.<br>Probá una sugerencia de abajo 👇";
            body.appendChild(w);
        }
        const ags = await rpc2("/dolan_ai/agentes");
        const ag = (ags.agentes || []).find(a => a.id === agenteActual);
        chips(ag);
    }
    async function loadAgents() {
        const res = await rpc2("/dolan_ai/agentes");
        const sel = win.querySelector(".o_dolan_ai_sel");
        sel.innerHTML = "";
        (res.agentes || []).forEach(a => {
            const o = document.createElement("option");
            o.value = a.id; o.textContent = a.name;
            sel.appendChild(o);
        });
        if (sel.options.length) {
            agenteActual = parseInt(sel.options[0].value);
            sel.value = String(agenteActual);
        }
    }
    async function loadConvs() {
        const res = await rpc2("/dolan_ai/conv/list", { agente_id: agenteActual });
        convActual = null;
        const body = win.querySelector(".o_dolan_ai_body");
        body.querySelectorAll(".o_dolan_ai_msg,.o_dolan_ai_chips,.o_dolan_ai_welcome").forEach(e => e.remove());
        const w = document.createElement("div");
        w.className = "o_dolan_ai_welcome";
        w.innerHTML = "<b>DOLAN AI</b><br>Tu asistente dentro de Odoo.<br>Probá una sugerencia de abajo 👇";
        body.appendChild(w);
        const ags = await rpc2("/dolan_ai/agentes");
        const ag = (ags.agentes || []).find(a => String(a.id) === String(agenteActual)) || (ags.agentes || [])[0];
        chips(ag);
    }
    let sending = false;
    async function send(text) {
        text = (text || "").trim();
        if (!text || sending) return;
        sending = true;
        addMsg("user", text);
        const status = addMsg("tool", "pensando…");
        const input = win.querySelector("input");
        input.value = "";
        try {
            const res = await rpc2("/dolan_ai/agente/run", {
                agente_id: agenteActual, text: text, conversacion_id: convActual,
            });
            status.remove();
            if (res.error) { addMsg("assistant", "⚠ " + (res.detalle || res.error)); }
            else {
                if (res.conversacion_id) convActual = res.conversacion_id;
                addMsg("assistant", res.reply || "(sin respuesta)");
            }
        } catch (e) {
            status.remove();
            addMsg("assistant", "⚠ error de conexión");
        }
        sending = false;
        input.focus();
    }
    function build() {
        if (!document.getElementById("o_dolan_ai_css")) {
            const st = document.createElement("style");
            st.id = "o_dolan_ai_css";
            st.textContent = CSS;
            document.head.appendChild(st);
        }
        win = document.createElement("div");
        win.className = "o_dolan_ai_win";
        if (document.documentElement.dataset.dolanTheme === "dark") win.dataset.theme = "dark";
        win.innerHTML = `
            <div class="o_dolan_ai_head">
              <span class="o_dolan_ai_logo" style="background:#fff;color:#714b67;border-radius:6px;padding:1px 6px;font-weight:800;font-size:11px">IA</span>
              <select class="o_dolan_ai_sel"></select>
              <button data-a="min" title="Minimizar">—</button>
              <button data-a="close" title="Cerrar">✕</button>
            </div>
            <div class="o_dolan_ai_body"></div>
            <div class="o_dolan_ai_foot">
              <input placeholder="Mensaje DOLAN AI…" autocomplete="off"/>
              <button data-a="send">Enviar</button>
            </div>`;
        document.body.appendChild(win);
        win.querySelector('[data-a="close"]').addEventListener("click", () => { win.remove(); win = null; open = false; });
        win.querySelector('[data-a="min"]').addEventListener("click", () => win.classList.toggle("o_dolan_ai_min"));
        win.querySelector('[data-a="send"]').addEventListener("click", () => send(win.querySelector("input").value));
        win.querySelector("input").addEventListener("keydown", (e) => { if (e.key === "Enter") send(e.target.value); });
        win.querySelector(".o_dolan_ai_sel").addEventListener("change", (e) => {
            agenteActual = parseInt(e.target.value); convActual = null; loadConvs();
        });
        loadAgents().then(loadConvs);
    }
    window.addEventListener("dolan-ai-toggle", () => {
        if (open && win) { win.remove(); win = null; open = false; return; }
        if (!win) build();
        open = true;
    });
})();

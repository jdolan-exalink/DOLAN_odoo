/** DOLAN AI — OCR de compras (S2): imagen → borrador. */
(function () {
  "use strict";
  function rpc(path, params) {
    return fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: params }),
      credentials: "same-origin",
    }).then(function (r) { return r.json(); }).then(function (j) { return j.result || j.error || { error: "rpc" }; });
  }
  document.addEventListener("DOMContentLoaded", function () {
    var btn = document.getElementById("dolan-ai-ocr");
    var file = document.getElementById("dolan-ai-file");
    var out = document.getElementById("dolan-ai-ocr-out");
    if (!btn || !file) return;
    btn.addEventListener("click", function () { file.click(); });
    if (location.hash === "#ocr") {
      try { btn.scrollIntoView({ behavior: "smooth", block: "center" }); } catch (e) {}
      setTimeout(function () { try { file.click(); } catch (e) {} }, 600);
    }
    file.addEventListener("change", function () {
      var f = file.files && file.files[0];
      if (!f) return;
      out.innerHTML = "<i>Leyendo comprobante…</i>";
      var reader = new FileReader();
      reader.onload = function () {
        var dataUrl = String(reader.result || "");
        rpc("/dolan_ai/ocr_scan", { image: dataUrl }).then(function (res) {
          if (res.error) { out.innerHTML = '<span style="color:#dc2626">Error: ' + res.error + '</span>'; return; }
          if (res.preview) {
            var d = res.vals || {};
            var lines = (d.lineas || []).map(function (l) { return "<li>" + l.name + " ×" + l.quantity + " — $" + l.price_unit + "</li>"; }).join("");
            out.innerHTML = '<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px">' +
              '<b>' + (d.partner_name_suggest || "—") + '</b> · ' + (d.invoice_date || "sin fecha") +
              ' · ref ' + (d.ref || "—") + '<ul>' + lines + '</ul>' +
              '<button id="dolan-ai-ocr-commit" type="button" style="background:#714b67;color:#fff;border:0;border-radius:8px;padding:8px 14px;cursor:pointer">Crear borrador</button></div>';
            document.getElementById("dolan-ai-ocr-commit").addEventListener("click", function () {
              rpc("/dolan_ai/ocr_scan", { image: dataUrl, commit: true }).then(function (r2) {
                if (r2.ok) {
                  out.innerHTML = '<a href="/odoo/accounting" style="color:#16a34a;font-weight:700">Borrador creado: ' + r2.move_name + " — abrir Facturas de compra</a>";
                } else {
                  out.innerHTML = '<span style="color:#dc2626">Error creando: ' + (r2.detalle || r2.error || "?") + "</span>";
                }
              });
            });
          } else {
            out.innerHTML = '<span style="color:#dc2626">OCR sin datos legibles</span>';
          }
        });
      };
      reader.readAsDataURL(f);
    });
  });
})();

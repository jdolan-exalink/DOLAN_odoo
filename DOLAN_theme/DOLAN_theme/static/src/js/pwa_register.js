/** @odoo-module **/
// F5 — PRD04: register the DOLAN service worker when the stack allows it
// (secure context + SW support). Failures are silent and harmless.
import { registry } from "@web/core/registry";

registry.category("services").add("dolan_pwa", {
    start() {
        if (!("serviceWorker" in navigator) || !window.isSecureContext) {
            return { registered: false, reason: "unsupported" };
        }
        let registered = false;
        navigator.serviceWorker.register("/dolan_theme/dolan-sw.js", { scope: "/" })
            .then(() => { registered = true; })
            .catch(() => { registered = false; });
        return { get: () => registered };
    },
});

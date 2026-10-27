/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

/**
 * App por defecto (DOLAN_theme/dolan_ui): navega con menu.selectMenu —
 * el mismo camino oficial de _loadDefaultApp (contexto de menú, chips de
 * sección y hash quedan consistentes). Fallback: doAction directo.
 */
registry.category("services").add("dolan_default_app", {
    dependencies: ["action", "menu"],
    start(env, { action, menu }) {
        const hash = window.location.hash || "";
        if (hash && /action=|model=|menu_id=/.test(hash)) {
            return;
        }
        rpc("/web/dolan_ui/config").then((cfg) => {
            if (!cfg || !cfg.default_action) {
                return;
            }
            try {
                const root = menu.getMenu("root");
                const target = (root?.children || []).find(
                    (m) => m.xmlid === cfg.default_menu_xmlid);
                if (target) {
                    menu.selectMenu(target);
                    return;
                }
            } catch { /* fallback abajo */ }
            const id = parseInt(cfg.default_action, 10);
            if (!Number.isNaN(id)) {
                action.doAction(id, { clearBreadcrumbs: true });
            }
        }).catch(() => {});
    },
});

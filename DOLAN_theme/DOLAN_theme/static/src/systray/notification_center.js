/** @odoo-module **/
// F6 — PRD04: attention centre in the systray (bell + counts + panel).
// Odoo 20 = Owl 3: state via signal(), dialog props via useProps.
import { registry } from "@web/core/registry";
import { Component, onWillStart, signal, t, useProps } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";

export class DolanNotificationCenter extends Component {
    static template = "DOLAN_theme.NotificationCenter";
    static components = { Dialog };
    props = useProps({ close: t.function() });

    setup() {
        this.action = useService("action");
        this.items = signal([]);
        this.loading = signal(true);
        onWillStart(() => this.reload());
    }

    async reload() {
        this.loading.set(true);
        try {
            const res = await rpc("/dolan/notifications", {});
            this.items.set((res && res.items) || []);
        } catch {
            this.items.set([]);
        } finally {
            this.loading.set(false);
        }
    }

    kindLabel(kind) {
        return {
            info: "Informativo",
            action: "Accion requerida",
            warn: "Advertencia",
            critical: "Critico",
        }[kind] || kind;
    }

    async markRead(item) {
        await rpc("/dolan/notifications/read", { notification_id: item.id });
        await this.reload();
    }

    async snooze(item) {
        await rpc("/dolan/notifications/snooze", { notification_id: item.id, minutes: 60 });
        await this.reload();
    }

    openItem(item) {
        if (item.res_model && item.res_id) {
            this.props.close();
            this.action.doAction({
                type: "ir.actions.act_window",
                res_model: item.res_model,
                res_id: item.res_id,
                views: [[false, "form"]],
                target: "current",
            });
        }
    }
}

export class DolanBell extends Component {
    static template = "DOLAN_theme.NotificationBell";

    setup() {
        this.dialog = useService("dialog");
        this.pending = signal(0);
        this.refresh();
        window.setInterval(() => this.refresh(), 60000);
    }

    async refresh() {
        try {
            const res = await rpc("/dolan/notifications", {});
            this.pending.set((res && res.pending) || 0);
        } catch { /* keep last */ }
    }

    open() {
        this.dialog.add(DolanNotificationCenter, {});
    }
}

registry.category("systray").add("dolan_notification_bell", {
    Component: DolanBell,
    isDisplayed: () => true,
});

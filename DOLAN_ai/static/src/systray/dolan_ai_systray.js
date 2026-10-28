/** @odoo-module **/
// Botón systray DOLAN AI (patrón EE: "Preguntar a la IA") — abre ChatWindow flotante.
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";

export class DolanAiSystray extends Component {
    static template = "DOLAN_ai.SystrayButton";
    toggle() {
        const ev = new CustomEvent("dolan-ai-toggle");
        window.dispatchEvent(ev);
    }
}
registry.category("systray").add("dolan_ai.button", { Component: DolanAiSystray });

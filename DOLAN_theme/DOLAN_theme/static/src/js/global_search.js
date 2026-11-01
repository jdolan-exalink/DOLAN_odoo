/** @odoo-module **/
// F2 — PRD04: global search dialog (g b or the Inicio search button).
// Odoo 20 = Owl 3: state via signal(), dialog props via useProps + t.function().
import { registry } from "@web/core/registry";
import { Component, signal, t, useProps } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";

const LS_RECENT = "dolan_search_recents";
const LS_FAVS = "dolan_search_favs";

function loadList(key) {
    try { return JSON.parse(localStorage.getItem(key) || "[]"); } catch { return []; }
}
function saveList(key, items) {
    try { localStorage.setItem(key, JSON.stringify(items.slice(0, 10))); } catch { /* quota */ }
}

export class DolanGlobalSearch extends Component {
    static template = "DOLAN_theme.GlobalSearch";
    static components = { Dialog };
    props = useProps({ close: t.function() });

    setup() {
        this.action = useService("action");
        this.query = signal("");
        this.results = signal([]);
        this.sel = signal(0);
        this.searching = signal(false);
        this.recents = signal(loadList(LS_RECENT));
        this.favs = signal(loadList(LS_FAVS));
        this._timer = null;
    }

    onInput(ev) {
        this.query.set(ev.target.value);
        this.sel.set(0);
        window.clearTimeout(this._timer);
        this._timer = window.setTimeout(() => this.search(), 220);
    }

    async search() {
        const q = this.query().trim();
        if (q.length < 2) { this.results.set([]); return; }
        this.searching.set(true);
        try {
            const res = await rpc("/dolan/global_search", { query: q });
            this.results.set((res && res.results) || []);
        } catch {
            this.results.set([]);
        } finally {
            this.searching.set(false);
        }
    }

    rows() {
        const q = this.query().trim();
        if (q.length < 2) {
            const fav = this.favs().map((r) => ({ ...r, fav: true }));
            const seen = new Set(fav.map((r) => r.model + r.id));
            const rec = this.recents()
                .filter((r) => !seen.has(r.model + r.id))
                .map((r) => ({ ...r, recent: true }));
            return [...fav, ...rec];
        }
        return this.results();
    }

    onKey(ev) {
        const rows = this.rows();
        if (ev.key === "ArrowDown") {
            ev.preventDefault();
            this.sel.set(Math.min(this.sel() + 1, rows.length - 1));
        } else if (ev.key === "ArrowUp") {
            ev.preventDefault();
            this.sel.set(Math.max(this.sel() - 1, 0));
        } else if (ev.key === "Enter") {
            ev.preventDefault();
            const r = rows[this.sel()];
            if (r) { this.open(r); }
        }
    }

    toggleFav(ev, row) {
        ev.stopPropagation();
        const key = row.model + "|" + row.id;
        const has = this.favs().some((f) => f.model + "|" + f.id === key);
        const next = has
            ? this.favs().filter((f) => f.model + "|" + f.id !== key)
            : [{ model: row.model, id: row.id, label: row.label, title: row.title }, ...this.favs()].slice(0, 10);
        this.favs.set(next);
        saveList(LS_FAVS, next);
    }

    open(row) {
        const next = [
            { model: row.model, id: row.id, label: row.label, title: row.title },
            ...this.recents().filter((r) => !(r.model === row.model && r.id === row.id)),
        ].slice(0, 10);
        this.recents.set(next);
        saveList(LS_RECENT, next);
        this.props.close();
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: row.model,
            res_id: row.id,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

export const globalSearchService = {
    dependencies: ["dialog"],
    start(env, { dialog }) {
        const open = () => dialog.add(DolanGlobalSearch, {});
        // Gmail-style: g then b (same window as the app hotkeys)
        let pending = false;
        document.addEventListener("keydown", (ev) => {
            const el = document.activeElement;
            const editable = el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable);
            if (ev.ctrlKey || ev.metaKey || ev.altKey || editable) return;
            const key = (ev.key || "").toLowerCase();
            if (key === "g") {
                pending = true;
                window.clearTimeout(window.__dolanGsG);
                window.__dolanGsG = window.setTimeout(() => { pending = false; }, 1600);
                return;
            }
            if (pending && key === "b") {
                pending = false;
                window.clearTimeout(window.__dolanGsG);
                ev.preventDefault();
                open();
            }
        }, true);
        return { open };
    },
};

registry.category("services").add("dolan_global_search", globalSearchService);

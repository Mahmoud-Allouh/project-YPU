/** @odoo-module **/

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { renderToFragment } from "@web/core/utils/render";

/**
 * Dynamic "Study Plan" snippet — Interaction API (Odoo 19).
 * Fetches the selected plan via JSON-RPC and renders sections + course tables.
 */
export class StudyPlanSnippet extends Interaction {
    static selector = ".s_study_plan";

    dynamicContent = {
        _root: {
            "t-att-class": () => ({
                o_dynamic_empty: !this.plan,
            }),
        },
    };

    setup() {
        this.plan = null;
    }

    async willStart() {
        await this.fetchPlan();
    }

    start() {
        this.render();
    }

    destroy() {
        const area = this.el.querySelector(".s_study_plan_content");
        if (area) {
            area.replaceChildren();
        }
    }

    async fetchPlan() {
        const ds = this.el.dataset;
        const planId = parseInt(ds.planId || "0", 10) || 0;
        if (!planId) {
            this.plan = null;
            return;
        }
        try {
            const res = await this.waitFor(
                rpc("/ypu_study_plans/snippet/data", { plan_id: planId })
            );
            this.plan = (res && res.plan) || null;
        } catch {
            this.plan = null;
        }
    }

    render() {
        const area = this.el.querySelector(".s_study_plan_content");
        if (!area) return;

        const ds = this.el.dataset;
        const showHeader = (ds.showHeader || "true") !== "false";
        const showDescription = (ds.showDescription || "true") !== "false";

        if (!this.plan) {
            area.innerHTML =
                '<div class="alert alert-info text-center my-3">' +
                "Pick a Study Plan from the right panel to display it here." +
                "</div>";
            return;
        }

        const fragment = renderToFragment("ypu_study_plans.s_study_plan_content", {
            plan: this.plan,
            showHeader,
            showDescription,
        });
        area.replaceChildren(fragment);
    }
}

registry
    .category("public.interactions")
    .add("ypu_study_plans.study_plan", StudyPlanSnippet);

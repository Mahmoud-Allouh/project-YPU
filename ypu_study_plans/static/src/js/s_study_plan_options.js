/** @odoo-module **/

import { BaseOptionComponent, useDomState } from "@html_builder/core/utils";
import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

/**
 * Study Plan — Builder option component (Odoo 19 website builder).
 *
 * Provides a "Plan" select populated from the database, plus a few
 * display toggles.
 */
export class StudyPlanOption extends BaseOptionComponent {
    static template = "ypu_study_plans.StudyPlanOption";
    static selector = ".s_study_plan";

    setup() {
        super.setup();
        this.state = useDomState(async () => {
            try {
                const result = await rpc("/ypu_study_plans/snippet/plans", {});
                return { plans: Array.isArray(result) ? result : [] };
            } catch {
                return { plans: [] };
            }
        });
    }
}

class StudyPlanOptionPlugin extends Plugin {
    static id = "studyPlanOption";

    /** @type {import("plugins").WebsiteResources} */
    resources = {
        builder_options: [StudyPlanOption],
    };
}

registry
    .category("website-plugins")
    .add(StudyPlanOptionPlugin.id, StudyPlanOptionPlugin);

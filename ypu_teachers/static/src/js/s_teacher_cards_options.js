/** @odoo-module **/

import { BaseOptionComponent } from "@html_builder/core/utils";
import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useDomState } from "@html_builder/core/utils";

/**
 * Teacher Cards – Builder option component (Odoo 19 website builder).
 *
 * Provides a "Cards per page" select and a "Category" select.
 * Categories are fetched dynamically from the database via useDomState.
 */
export class TeacherCardsOption extends BaseOptionComponent {
    static template = "ypu_teachers.TeacherCardsOption";
    static selector = ".s_teacher_cards";

    setup() {
        super.setup();
        this.state = useDomState(async () => {
            try {
                const result = await rpc("/ypu_teachers/snippet/categories", {});
                return {
                    categories: Array.isArray(result) ? result : [],
                };
            } catch {
                return {
                    categories: [],
                };
            }
        });
    }
}

class TeacherCardsOptionPlugin extends Plugin {
    static id = "teacherCardsOption";

    /** @type {import("plugins").WebsiteResources} */
    resources = {
        builder_options: [TeacherCardsOption],
    };
}

registry
    .category("website-plugins")
    .add(TeacherCardsOptionPlugin.id, TeacherCardsOptionPlugin);

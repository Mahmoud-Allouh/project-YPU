/** @odoo-module **/

import { BaseOptionComponent } from "@html_builder/core/utils";
import { before, SNIPPET_SPECIFIC_END } from "@html_builder/utils/option_sequence";
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useDomState } from "@html_builder/core/utils";

/**
 * Teacher Cards – Builder option component (Odoo 19 website builder).
 *
 * Uses reactive state with a deferred load to work around builder
 * lifecycle limitations.
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
        builder_options: [
            withSequence(before(SNIPPET_SPECIFIC_END), TeacherCardsOption),
        ],
    };
}

registry
    .category("website-plugins")
    .add(TeacherCardsOptionPlugin.id, TeacherCardsOptionPlugin);

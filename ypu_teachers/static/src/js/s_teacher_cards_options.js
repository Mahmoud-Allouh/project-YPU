/** @odoo-module **/

import { BaseOptionComponent } from "@html_builder/core/utils";
import { before, SNIPPET_SPECIFIC_END } from "@html_builder/utils/option_sequence";
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useState } from "@odoo/owl";

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
        this.categories = useState({ items: [] });
        
        // Start loading immediately after component exists,
        // using a microtask to ensure component structure is ready
        Promise.resolve().then(() => this._loadCategories());
    }

    async _loadCategories() {
        try {
            const result = await rpc("/ypu_teachers/snippet/categories", {});
            this.categories.items = Array.isArray(result) ? result : [];
            console.log("✓ Categories loaded:", this.categories.items.length);
        } catch (e) {
            console.error("✗ Failed to load categories:", e);
            this.categories.items = [];
        }
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

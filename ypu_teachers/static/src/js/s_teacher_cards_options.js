/** @odoo-module **/

import { BaseOptionComponent } from "@html_builder/core/utils";
import { before, SNIPPET_SPECIFIC_END } from "@html_builder/utils/option_sequence";
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useState, onMounted } from "@odoo/owl";

/**
 * Teacher Cards – Builder option component (Odoo 19 website builder).
 *
 * Provides a "Cards per page" select and a "Category" select.
 * Categories are fetched dynamically from the database via onMounted
 * (onWillStart is NOT reliably awaited by the builder framework).
 */
export class TeacherCardsOption extends BaseOptionComponent {
    static template = "ypu_teachers.TeacherCardsOption";
    static selector = ".s_teacher_cards";

    setup() {
        super.setup();
        // Separate reactive object so we don't collide with
        // BaseOptionComponent's own `this.state`.
        this.catState = useState({ categories: [] });
        onMounted(() => {
            this._loadCategories();
        });
    }

    async _loadCategories() {
        try {
            const result = await rpc("/ypu_teachers/snippet/categories", {});
            this.catState.categories = Array.isArray(result) ? result : [];
        } catch (e) {
            console.warn("Failed to load teacher categories:", e);
            this.catState.categories = [];
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

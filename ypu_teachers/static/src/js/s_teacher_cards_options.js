/** @odoo-module **/

import { BaseOptionComponent } from "@html_builder/core/utils";
import { before, SNIPPET_SPECIFIC_END } from "@html_builder/utils/option_sequence";
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useState, onWillStart } from "@odoo/owl";

/**
 * Teacher Cards – Builder option component (Odoo 19 website builder).
 *
 * Provides a "Cards per page" select and a "Category" select.
 * Categories are fetched dynamically from the database.
 */
export class TeacherCardsOption extends BaseOptionComponent {
    static template = "ypu_teachers.TeacherCardsOption";
    static selector = ".s_teacher_cards";

    // Class-level safe default so `this.catState` is never undefined,
    // even if the template renders during component construction.
    catState = { categories: [] };

    setup() {
        super.setup();
        // Replace with reactive version so OWL re-renders when data arrives.
        this.catState = useState({ categories: [] });
        
        // Load categories BEFORE first render by returning a promise
        // that the framework must await.
        onWillStart(async () => {
            await this._loadCategories();
        });
    }

    async _loadCategories() {
        try {
            const result = await rpc("/ypu_teachers/snippet/categories", {});
            this.catState.categories = Array.isArray(result) ? result : [];
            console.log("Teacher categories loaded:", this.catState.categories.length);
        } catch (e) {
            console.error("Failed to load teacher categories:", e);
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

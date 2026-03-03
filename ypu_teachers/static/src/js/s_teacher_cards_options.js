/** @odoo-module **/

console.log("🔵 [LOAD] s_teacher_cards_options.js module is loading...");

import { BaseOptionComponent } from "@html_builder/core/utils";
import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useDomState } from "@html_builder/core/utils";

console.log("🔵 [LOAD] All imports successful");

/**
 * Teacher Cards – Builder option component (Odoo 19 website builder).
 *
 * Uses useDomState async pattern matching Odoo core builder plugins.
 */
export class TeacherCardsOption extends BaseOptionComponent {
    static template = "ypu_teachers.TeacherCardsOption";
    static selector = ".s_teacher_cards";

    setup() {
        console.log("🟢 [SETUP] TeacherCardsOption.setup() called");
        super.setup();
        console.log("🟢 [SETUP] super.setup() completed");
        
        this.state = useDomState(async () => {
            console.log("🟡 [STATE] useDomState callback fired");
            try {
                console.log("🟡 [STATE] Calling RPC to /ypu_teachers/snippet/categories");
                const result = await rpc("/ypu_teachers/snippet/categories", {});
                console.log("🟡 [STATE] RPC returned:", result);
                const cats = Array.isArray(result) ? result : [];
                console.log("✅ [STATE] Returning", cats.length, "categories");
                return {
                    categories: cats,
                };
            } catch (e) {
                console.error("❌ [STATE] RPC failed:", e);
                return {
                    categories: [],
                };
            }
        });
        console.log("🟢 [SETUP] useDomState configured, state object:", this.state);
    }
}

console.log("🔵 [LOAD] TeacherCardsOption class defined");

class TeacherCardsOptionPlugin extends Plugin {
    static id = "teacherCardsOption";

    /** @type {import("plugins").WebsiteResources} */
    resources = {
        builder_options: [
            // Simplified registration without withSequence for compatibility
            TeacherCardsOption,
        ],
    };
}

console.log("🔵 [LOAD] TeacherCardsOptionPlugin defined");

console.log("🔵 [LOAD] Registering plugin in website-plugins...");
registry
    .category("website-plugins")
    .add(TeacherCardsOptionPlugin.id, TeacherCardsOptionPlugin);
console.log("✅ [LOAD] Plugin registered successfully!");

// Global marker so we can verify this file was loaded
window.YPU_TEACHER_OPTIONS_LOADED = true;
console.log("✅ [LOAD] Module fully loaded. window.YPU_TEACHER_OPTIONS_LOADED = true");

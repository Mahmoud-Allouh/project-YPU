/** @odoo-module **/

import { BaseOptionComponent, useDomState } from "@html_builder/core/utils";
import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class HonorStudentsOption extends BaseOptionComponent {
    static template = "ypu_honor_students.HonorStudentsOption";
    static selector = ".s_honor_students";

    setup() {
        super.setup();
        this.state = useDomState(async () => {
            try {
                const result = await rpc("/ypu_honor_students/snippet/faculties", {});
                return {
                    faculties: Array.isArray(result) ? result : [],
                };
            } catch {
                return {
                    faculties: [],
                };
            }
        });
    }
}

class HonorStudentsOptionPlugin extends Plugin {
    static id = "honorStudentsOption";

    resources = {
        builder_options: [HonorStudentsOption],
    };
}

registry
    .category("website-plugins")
    .add(HonorStudentsOptionPlugin.id, HonorStudentsOptionPlugin);

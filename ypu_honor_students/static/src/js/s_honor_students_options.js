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
                const [faculties, years, studyYears] = await Promise.all([
                    rpc("/ypu_honor_students/snippet/faculties", {}),
                    rpc("/ypu_honor_students/snippet/years", {}),
                    rpc("/ypu_honor_students/snippet/study_years", {}),
                ]);
                return {
                    faculties: Array.isArray(faculties) ? faculties : [],
                    years: Array.isArray(years) ? years : [],
                    studyYears: Array.isArray(studyYears) ? studyYears : [],
                };
            } catch {
                return {
                    faculties: [],
                    years: [],
                    studyYears: [],
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

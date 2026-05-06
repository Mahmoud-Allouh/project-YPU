/** @odoo-module **/

import { HonorStudentsSnippet } from "./s_honor_students";
import { registry } from "@web/core/registry";

registry.category("public.interactions.edit").add("ypu_honor_students.honor_students", {
    Interaction: HonorStudentsSnippet,
});

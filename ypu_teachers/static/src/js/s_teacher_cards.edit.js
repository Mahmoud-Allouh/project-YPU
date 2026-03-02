/** @odoo-module **/

import { TeacherCardsSnippet } from "./s_teacher_cards";
import { registry } from "@web/core/registry";

/**
 * Edit-mode registration: re-uses the same Interaction so the
 * editor preview shows real cards with live data.
 */
registry.category("public.interactions.edit").add("ypu_teachers.teacher_cards", {
    Interaction: TeacherCardsSnippet,
});

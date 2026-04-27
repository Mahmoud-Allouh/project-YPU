/** @odoo-module **/

import { StudyPlanSnippet } from "./s_study_plan";
import { registry } from "@web/core/registry";

/**
 * Edit-mode registration: re-uses the same Interaction so the
 * builder iframe shows real plan data while editing.
 */
registry
    .category("public.interactions.edit")
    .add("ypu_study_plans.study_plan", { Interaction: StudyPlanSnippet });

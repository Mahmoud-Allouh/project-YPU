/** @odoo-module **/

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { renderToFragment } from "@web/core/utils/render";
import { uniqueId } from "@web/core/utils/functions";
import { utils as uiUtils } from "@web/core/ui/ui_service";

/**
 * Dynamic "Teacher Cards" snippet – Interaction API (Odoo 19).
 *
 * Uses Bootstrap carousel (o_carousel_multi_items) for reliable
 * navigation in both public and editor modes.
 */
export class TeacherCardsSnippet extends Interaction {
    static selector = ".s_teacher_cards";

    dynamicContent = {
        _root: {
            "t-att-class": () => ({
                o_dynamic_empty: !this.data.length,
            }),
        },
        _window: { "t-on-resize": this.throttled(this.render) },
    };

    setup() {
        this.data = [];
        this.uniqueId = uniqueId("s_teacher_cards_");
    }

    async willStart() {
        await this.fetchTeachers();
    }

    start() {
        this.render();
    }

    destroy() {
        const area = this.el.querySelector(".s_teacher_cards_content");
        if (area) {
            area.replaceChildren();
        }
    }

    // ── Data ─────────────────────────────────────────────────────

    async fetchTeachers() {
        const ds = this.el.dataset;
        const categoryId = parseInt(ds.categoryId || "0", 10) || 0;
        try {
            const res = await this.waitFor(
                rpc("/ypu_teachers/snippet/teachers", {
                    category_id: categoryId || false,
                    limit: 0,
                    page: 1,
                })
            );
            this.data = res.teachers || [];
        } catch {
            this.data = [];
        }
    }

    // ── Render ───────────────────────────────────────────────────

    get chunkSize() {
        const limit = parseInt(this.el.dataset.limit || "4", 10) || 4;
        return uiUtils.isSmall() ? 1 : Math.min(limit, 4);
    }

    render() {
        const area = this.el.querySelector(".s_teacher_cards_content");
        if (!area) return;

        if (!this.data.length) {
            area.innerHTML =
                '<div class="alert alert-info text-center my-3">No teachers found.</div>';
            return;
        }

        const design = this.el.dataset.design || "cards";
        const fragment = renderToFragment(
            "ypu_teachers.s_teacher_cards_content",
            {
                teachers: this.data,
                design: design,
                chunkSize: this.chunkSize,
                unique_id: this.uniqueId,
            }
        );
        area.replaceChildren(fragment);

        // Start Bootstrap carousel if present
        this.waitForTimeout(() => {
            const carouselEl = area.querySelector(".carousel");
            if (carouselEl && window.bootstrap?.Carousel) {
                window.bootstrap.Carousel.getOrCreateInstance(carouselEl, {
                    interval: 0,
                    ride: false,
                    wrap: true,
                });
            }
        }, 0);
    }
}

registry
    .category("public.interactions")
    .add("ypu_teachers.teacher_cards", TeacherCardsSnippet);

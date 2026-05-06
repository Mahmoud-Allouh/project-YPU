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
 * Renders server data into slide groups so Bootstrap carousel behavior
 * stays consistent in both public and builder modes.
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
        this._observer = null;
        this._carousel = null;
        this.syncFromDataset();
    }

    async willStart() {
        await this.fetchTeachers();
    }

    start() {
        this.render();
        this.setupDatasetObserver();
    }

    destroy() {
        if (this._observer) {
            this._observer.disconnect();
            this._observer = null;
        }
        this.disposeCarousel();
        const area = this.el.querySelector(".s_teacher_cards_content");
        if (area) {
            area.replaceChildren();
        }
    }

    disposeCarousel() {
        if (this._carousel) {
            this._carousel.dispose();
            this._carousel = null;
        }
    }

    syncFromDataset() {
        const ds = this.el.dataset;
        this.selectedCategoryId = parseInt(ds.categoryId || "0", 10) || 0;
    }

    setupDatasetObserver() {
        this._observer = new MutationObserver(() => {
            this.syncFromDataset();
            this.fetchTeachers().then(() => this.render());
        });
        this._observer.observe(this.el, {
            attributes: true,
            attributeFilter: ["data-category-id", "data-limit", "data-design"],
        });
    }

    // ── Data ─────────────────────────────────────────────────────

    async fetchTeachers() {
        try {
            const res = await this.waitFor(
                rpc("/ypu_teachers/snippet/teachers", {
                    category_id: this.selectedCategoryId || false,
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
        const rawLimit = parseInt(this.el.dataset.limit || "4", 10) || 4;
        const safeLimit = Math.max(1, Math.min(rawLimit, 6));
        return uiUtils.isSmall() ? 1 : safeLimit;
    }

    get columnClass() {
        const size = this.chunkSize;
        if (size <= 1) {
            return "col-12";
        }
        if (size === 2) {
            return "col-12 col-md-6";
        }
        if (size === 3) {
            return "col-12 col-md-6 col-xl-4";
        }
        if (size === 4) {
            return "col-12 col-md-6 col-xl-3";
        }
        return "col-12 col-sm-6 col-lg-4 col-xxl-2";
    }

    get slides() {
        const size = Math.max(this.chunkSize, 1);
        const slides = [];
        for (let i = 0; i < this.data.length; i += size) {
            slides.push({
                id: i / size,
                teachers: this.data.slice(i, i + size),
            });
        }
        return slides;
    }

    initCarousel(area) {
        const carouselEl = area.querySelector(".ypu-teacher-carousel");
        if (!carouselEl || !window.bootstrap?.Carousel) {
            return;
        }
        this._carousel = window.bootstrap.Carousel.getOrCreateInstance(carouselEl, {
            interval: false,
            ride: false,
            wrap: true,
            touch: true,
        });
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
        const slides = this.slides;
        const fragment = renderToFragment(
            "ypu_teachers.s_teacher_cards_content",
            {
                slides: slides,
                design: design,
                columnClass: this.columnClass,
                unique_id: this.uniqueId,
            }
        );

        this.disposeCarousel();
        area.replaceChildren(fragment);

        // Initialize Bootstrap carousel once the new DOM is in place.
        this.waitForTimeout(() => {
            this.initCarousel(area);
        }, 0);
    }
}

registry
    .category("public.interactions")
    .add("ypu_teachers.teacher_cards", TeacherCardsSnippet);

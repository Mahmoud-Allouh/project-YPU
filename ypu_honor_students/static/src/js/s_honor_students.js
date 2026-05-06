/** @odoo-module **/

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { renderToFragment } from "@web/core/utils/render";

export class HonorStudentsSnippet extends Interaction {
    static selector = ".s_honor_students";

    dynamicContent = {
        _root: {
            "t-att-class": () => ({
                o_dynamic_empty: !this.students.length,
            }),
        },
    };

    setup() {
        this.students = [];
        this.faculties = [];
        this._observer = null;
        this.syncFromDataset();
    }

    async willStart() {
        await Promise.all([this.fetchFaculties(), this.fetchStudents()]);
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
        const area = this.el.querySelector(".s_honor_students_content");
        if (area) {
            area.replaceChildren();
        }
    }

    syncFromDataset() {
        const ds = this.el.dataset;
        this.selectedFacultyId = parseInt(ds.facultyId || "0", 10) || 0;
        this.selectedStudyYear = String(ds.studyYear || "0");
        this.selectedSemester = String(ds.semester || "0");
        this.limit = Math.max(parseInt(ds.limit || "12", 10) || 12, 1);
        this.showFilters = (ds.showFilters || "true") !== "false";
    }

    setupDatasetObserver() {
        this._observer = new MutationObserver(() => {
            this.syncFromDataset();
            this.fetchStudents().then(() => this.render());
        });
        this._observer.observe(this.el, {
            attributes: true,
            attributeFilter: [
                "data-faculty-id",
                "data-study-year",
                "data-semester",
                "data-limit",
                "data-show-filters",
            ],
        });
    }

    async fetchFaculties() {
        try {
            const res = await this.waitFor(rpc("/ypu_honor_students/snippet/faculties", {}));
            this.faculties = Array.isArray(res) ? res : [];
        } catch {
            this.faculties = [];
        }
    }

    async fetchStudents() {
        try {
            const res = await this.waitFor(
                rpc("/ypu_honor_students/snippet/students", {
                    faculty_id: this.selectedFacultyId || false,
                    study_year: this.selectedStudyYear !== "0" ? this.selectedStudyYear : false,
                    semester: this.selectedSemester !== "0" ? this.selectedSemester : false,
                    limit: this.limit,
                    page: 1,
                })
            );
            this.students = (res && res.students) || [];
        } catch {
            this.students = [];
        }
    }

    async onFilterChange(ev) {
        const target = ev.currentTarget;
        const filter = target.dataset.filter;
        const value = target.value || "0";

        if (filter === "faculty") {
            this.selectedFacultyId = parseInt(value, 10) || 0;
            this.el.dataset.facultyId = String(this.selectedFacultyId);
        }
        if (filter === "year") {
            this.selectedStudyYear = value;
            this.el.dataset.studyYear = value;
        }
        if (filter === "semester") {
            this.selectedSemester = value;
            this.el.dataset.semester = value;
        }

        await this.fetchStudents();
        this.render();
    }

    bindFilters(area) {
        const selects = area.querySelectorAll("select[data-filter]");
        for (const selectEl of selects) {
            selectEl.addEventListener("change", (ev) => {
                this.onFilterChange(ev);
            });
        }
    }

    render() {
        const area = this.el.querySelector(".s_honor_students_content");
        if (!area) return;

        const fragment = renderToFragment("ypu_honor_students.s_honor_students_content", {
            students: this.students,
            faculties: this.faculties,
            showFilters: this.showFilters,
            selectedFacultyId: this.selectedFacultyId,
            selectedStudyYear: this.selectedStudyYear,
            selectedSemester: this.selectedSemester,
        });

        area.replaceChildren(fragment);
        this.bindFilters(area);
    }
}

registry
    .category("public.interactions")
    .add("ypu_honor_students.honor_students", HonorStudentsSnippet);

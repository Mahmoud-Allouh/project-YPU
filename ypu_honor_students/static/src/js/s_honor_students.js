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
        this.years = [];
        this.studyYears = [];
        this._observer = null;
        this.syncFromDataset();
    }

    async willStart() {
        await Promise.all([
            this.fetchFaculties(),
            this.fetchYears(),
            this.fetchStudyYears(),
            this.fetchStudents(),
        ]);
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
        this.selectedYearId = parseInt(ds.yearId || "0", 10) || 0;
        this.selectedStudyYearId = parseInt(ds.studyYear || "0", 10) || 0;
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
                "data-year-id",
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

    async fetchYears() {
        try {
            const res = await this.waitFor(rpc("/ypu_honor_students/snippet/years", {}));
            this.years = Array.isArray(res) ? res : [];
        } catch {
            this.years = [];
        }
    }

    async fetchStudyYears() {
        try {
            const res = await this.waitFor(rpc("/ypu_honor_students/snippet/study_years", {}));
            this.studyYears = Array.isArray(res) ? res : [];
        } catch {
            this.studyYears = [];
        }
    }

    async fetchStudents() {
        try {
            const res = await this.waitFor(
                rpc("/ypu_honor_students/snippet/students", {
                    faculty_id: this.selectedFacultyId || false,
                    year_id: this.selectedYearId || false,
                    study_year: this.selectedStudyYearId || false,
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
            this.selectedYearId = parseInt(value, 10) || 0;
            this.el.dataset.yearId = String(this.selectedYearId);
        }
        if (filter === "study-year") {
            this.selectedStudyYearId = parseInt(value, 10) || 0;
            this.el.dataset.studyYear = String(this.selectedStudyYearId);
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
            years: this.years,
            studyYears: this.studyYears,
            showFilters: this.showFilters,
            selectedFacultyId: this.selectedFacultyId,
            selectedYearId: this.selectedYearId,
            selectedStudyYearId: this.selectedStudyYearId,
            selectedSemester: this.selectedSemester,
        });

        area.replaceChildren(fragment);
        this.bindFilters(area);
    }
}

registry
    .category("public.interactions")
    .add("ypu_honor_students.honor_students", HonorStudentsSnippet);

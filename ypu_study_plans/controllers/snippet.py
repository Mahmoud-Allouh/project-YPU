from odoo.http import Controller, request, route


class YpuStudyPlanSnippet(Controller):
    """JSON-RPC controller used by the dynamic Study Plan snippet."""

    @route('/ypu_study_plans/snippet/plans', type='jsonrpc', auth='public', website=True)
    def snippet_plans(self, **kw):
        """List all active plans for the builder option dropdown."""
        Plan = request.env['ypu.study.plan'].sudo()
        plans = Plan.search([('active', '=', True)], order='sequence, name')
        return [{'id': p.id, 'name': p.name, 'code': p.code or ''} for p in plans]

    @route('/ypu_study_plans/snippet/data', type='jsonrpc', auth='public', website=True)
    def snippet_data(self, plan_id=False, plan_code=False, **kw):
        """Return the full plan tree (sections + courses) for rendering."""
        Plan = request.env['ypu.study.plan'].sudo()
        plan = Plan.browse()
        if plan_id:
            try:
                plan = Plan.browse(int(plan_id)).exists()
            except (TypeError, ValueError):
                plan = Plan.browse()
        if not plan and plan_code:
            plan = Plan.search([('code', '=', plan_code)], limit=1)
        if not plan:
            plan = Plan.search([('active', '=', True)], order='sequence, name', limit=1)
        if not plan or not plan.active:
            return {'plan': False}

        sections = []
        for section in plan.section_ids.sorted(lambda s: (s.sequence, s.id)):
            courses = []
            for course in section.course_ids.sorted(lambda c: (c.sequence, c.id)):
                courses.append({
                    'id': course.id,
                    'code': course.code or '',
                    'name_ar': course.name_ar or '',
                    'name_en': course.name_en or '',
                    'theory_hours': course.theory_hours,
                    'practical_hours': course.practical_hours,
                    'credit_hours': course.credit_hours,
                    'prerequisite': course.prerequisite or '',
                    'description': course.description or '',
                })
            sections.append({
                'id': section.id,
                'name': section.name,
                'subtitle': section.subtitle or '',
                'description': section.description or '',
                'section_type': section.section_type,
                'show_total_row': section.show_total_row,
                'show_description_column': section.show_description_column,
                'show_prerequisite_column': section.show_prerequisite_column,
                'total_theory': section.total_theory,
                'total_practical': section.total_practical,
                'total_credit': section.total_credit,
                'courses': courses,
            })

        return {
            'plan': {
                'id': plan.id,
                'name': plan.name,
                'code': plan.code or '',
                'subtitle': plan.subtitle or '',
                'description': plan.description or '',
                'total_credit_hours': plan.total_credit_hours,
                'sections': sections,
            },
        }

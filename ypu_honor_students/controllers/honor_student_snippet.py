from odoo.http import Controller, request, route


class YpuHonorStudentSnippet(Controller):
    """JSON-RPC endpoints used by the Honor Students dynamic snippet."""

    @route('/ypu_honor_students/snippet/faculties', type='jsonrpc', auth='public', website=True)
    def snippet_faculties(self, **kw):
        Faculty = request.env['ypu.honor.faculty'].sudo()
        Student = request.env['ypu.honor.student'].sudo()

        faculties = Faculty.search([('active', '=', True)], order='sequence, name')
        base_domain = [
            ('active', '=', True),
            ('website_published', '=', True),
            ('is_public', '=', True),
        ]

        return [
            {
                'id': fac.id,
                'name': fac.name,
                'student_count': Student.search_count(base_domain + [('faculty_id', '=', fac.id)]),
            }
            for fac in faculties
        ]

    @route('/ypu_honor_students/snippet/years', type='jsonrpc', auth='public', website=True)
    def snippet_years(self, **kw):
        Year = request.env['ypu.honor.year'].sudo()
        Student = request.env['ypu.honor.student'].sudo()

        years = Year.search([('active', '=', True)], order='sequence, code, name')
        base_domain = [
            ('active', '=', True),
            ('website_published', '=', True),
            ('is_public', '=', True),
        ]

        result = []
        for year in years:
            count = Student.search_count(base_domain + [('year_id', '=', year.id)])
            result.append({
                'id': year.id,
                'name': year.name,
                'code': year.code,
                'student_count': count,
            })
        return result

    @route('/ypu_honor_students/snippet/study_years', type='jsonrpc', auth='public', website=True)
    def snippet_study_years(self, **kw):
        StudyYear = request.env['ypu.honor.study.year'].sudo()
        Student = request.env['ypu.honor.student'].sudo()

        years = StudyYear.search([('active', '=', True)], order='sequence, code, name')
        base_domain = [
            ('active', '=', True),
            ('website_published', '=', True),
            ('is_public', '=', True),
        ]

        result = []
        for year in years:
            count = Student.search_count(base_domain + [('study_year_id', '=', year.id)])
            result.append({
                'id': year.id,
                'name': year.name,
                'code': year.code,
                'student_count': count,
            })
        return result

    @route('/ypu_honor_students/snippet/students', type='jsonrpc', auth='public', website=True)
    def snippet_students(
        self,
        faculty_id=False,
        year_id=False,
        study_year=False,
        semester=False,
        search='',
        limit=12,
        page=1,
        **kw,
    ):
        Student = request.env['ypu.honor.student'].sudo()

        domain = Student.website_search_domain(
            search=(search or '').strip(),
            faculty_id=faculty_id,
            year_id=year_id,
            study_year=study_year,
            semester=semester,
        )

        try:
            limit = int(limit or 0)
        except (TypeError, ValueError):
            limit = 12
        try:
            page = max(int(page or 1), 1)
        except (TypeError, ValueError):
            page = 1
        total = Student.search_count(domain)

        if limit <= 0:
            students = Student.search(domain, order='sequence, name')
        else:
            offset = (page - 1) * limit
            students = Student.search(
                domain,
                order='sequence, name',
                limit=limit,
                offset=offset,
            )

        return {
            'total': total,
            'students': [
                {
                    'id': rec.id,
                    'name': rec.name,
                    'student_number': rec.student_number or '',
                    'faculty': rec.faculty_id.name if rec.faculty_id else '',
                    'year_id': rec.year_id.id if rec.year_id else 0,
                    'year': rec.year_id.name if rec.year_id else '',
                    'study_year': rec.study_year_id.code if rec.study_year_id else '',
                    'study_year_id': rec.study_year_id.id if rec.study_year_id else 0,
                    'year_label': rec.year_label or '',
                    'study_year_label': rec.study_year_label or '',
                    'semester': rec.semester or '',
                    'semester_label': rec.semester_label or '',
                    'gpa': rec.gpa or 0,
                    'honor_title': rec.honor_title or '',
                    'achievement': rec.achievement or '',
                    'has_image': bool(rec.image_1920),
                    'image_url': f'/web/image/ypu.honor.student/{rec.id}/image_1920',
                }
                for rec in students
            ],
        }

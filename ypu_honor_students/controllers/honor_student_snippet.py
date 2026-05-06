from odoo.http import Controller, request, route


class YpuHonorStudentSnippet(Controller):
    """JSON-RPC endpoints used by the Honor Students dynamic snippet."""

    @route('/ypu_honor_students/snippet/faculties', type='jsonrpc', auth='public', website=True)
    def snippet_faculties(self, **kw):
        Faculty = request.env['ypu.honor.faculty'].sudo()
        Student = request.env['ypu.honor.student'].sudo()

        faculties = Faculty.search([('active', '=', True)], order='sequence, name')
        grouped = Student.read_group(
            [
                ('faculty_id', 'in', faculties.ids),
                ('active', '=', True),
                ('website_published', '=', True),
                ('is_public', '=', True),
            ],
            ['faculty_id'],
            ['faculty_id'],
        )
        count_map = {g['faculty_id'][0]: g['faculty_id_count'] for g in grouped}

        return [
            {
                'id': fac.id,
                'name': fac.name,
                'student_count': count_map.get(fac.id, 0),
            }
            for fac in faculties
        ]

    @route('/ypu_honor_students/snippet/students', type='jsonrpc', auth='public', website=True)
    def snippet_students(
        self,
        faculty_id=False,
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
                    'study_year': rec.study_year or '',
                    'year_label': rec.year_label or '',
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

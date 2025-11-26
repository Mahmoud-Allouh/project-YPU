# -*- coding: utf-8 -*-
from odoo.http import Controller, route, request


class YpuTeacherPortal(Controller):

    @route(['/teachers'], type='http', auth="public", website=True)
    def list_teachers(self, search=None, category_id=None, available=None, **kwargs):
        Teacher = request.env['ypu.teacher'].sudo()
        Category = request.env['ypu.teacher.category'].sudo()

        category_ids = []
        if category_id:
            try:
                category_ids = [int(category_id)]
            except ValueError:
                category_ids = []

        available_flag = None
        if available is not None:
            if str(available).lower() in ['1', 'true', 'yes']:
                available_flag = True
            elif str(available).lower() in ['0', 'false', 'no']:
                available_flag = False

        domain = Teacher._website_search_domain(
            search=search or '',
            category_ids=category_ids,
            available=available_flag,
        )
        teachers = Teacher.search_read(
            domain=domain,
            fields=[
                'id', 'name', 'subject', 'department', 'email', 'phone', 'category_id',
                'years_of_experience', 'available', 'image_1920',
            ],
            limit=60,
            order='name asc',
        )
        categories = Category.search_read(
            domain=[('active', '=', True)],
            fields=['id', 'name', 'teacher_count'],
            order='sequence, name',
        )

        return request.render('ypu_teachers.website_teachers', {
            'teachers': teachers,
            'categories': categories,
            'search': search or '',
            'selected_category': int(category_id) if category_id and category_id.isdigit() else None,
            'selected_available': available_flag,
        })

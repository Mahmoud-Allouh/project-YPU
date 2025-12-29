# -*- coding: utf-8 -*-
from odoo import api, fields, models


class YpuTeacher(models.Model):
    _name = 'ypu.teacher'
    _description = 'Teacher'
    _order = 'name'

    name = fields.Char(required=True, help="Teacher full name.")
    department = fields.Char(help="Department or faculty.")
    subject = fields.Char(help="Main subject taught.")
    email = fields.Char()
    phone = fields.Char()
    bio = fields.Html(string='Profile')
    category_id = fields.Many2one('ypu.teacher.category', string='Category')
    years_of_experience = fields.Char(string='Social Media', default='')
    is_dean = fields.Boolean(string='Dean Card', default=False)
    research_gate = fields.Char(string='Research Gate')
    available = fields.Boolean(string='Available', default=True)
    image_1920 = fields.Image("Photo", max_width=512, max_height=512)
    website_published = fields.Boolean(string='Publish on Website', default=True)
    is_public = fields.Boolean(
        string='Publicly Visible',
        default=True,
        help="If disabled, the teacher will be hidden from the public listing.",
    )

    def _website_search_domain(self, search='', category_ids=None, available=None):
        domain = [('website_published', '=', True), ('is_public', '=', True)]
        if search:
            domain += ['|', ('name', 'ilike', search), ('subject', 'ilike', search)]
        if category_ids:
            domain.append(('category_id', 'in', category_ids))
        if available is not None:
            domain.append(('available', '=', available))
        return domain

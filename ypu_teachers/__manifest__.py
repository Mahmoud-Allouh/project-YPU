# -*- coding: utf-8 -*-
{
    'name': "YP University - Teachers",
    'summary': "Teacher profiles with public website listing",
    'description': """
        Standalone teacher directory with backend forms and a public website page to browse teachers.
    """,
    'author': "Kaizen",
    'website': "https://www.kaizenae.com",
    'category': 'Website',
    'version': '19.0.1.0.0',
    'depends': ['base', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/teacher_category_views.xml',
        'views/teacher_views.xml',
        'data/website_menu.xml',
        'views/website_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ypu_teachers/static/src/css/teachers.css',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}

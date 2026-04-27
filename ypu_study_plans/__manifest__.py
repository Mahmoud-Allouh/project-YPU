{
    'name': "YPU Study Plans",
    'summary': "Manage faculty study plans and embed them on website pages as a dynamic snippet",
    'description': """
Build curricula in the backend (plan -> sections -> courses) and drop a
configurable Study Plan table onto any website page. Designed for non-technical
content editors: drag-and-drop ordering, inline editable course tables, and a
simple snippet picker on the page.
    """,
    'author': "Komorebi Technologies",
    'website': "https://www.komorebitechnologies.com",
    'category': 'Website',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['base', 'website', 'ypu_teachers'],
    'data': [
        'security/ir.model.access.csv',
        'views/study_plan_views.xml',
        'views/menu.xml',
        'views/website_templates.xml',
        'views/snippets.xml',
        'data/website_menu.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ypu_study_plans/static/src/scss/s_study_plan.scss',
            'ypu_study_plans/static/src/xml/s_study_plan.xml',
            'ypu_study_plans/static/src/js/s_study_plan.js',
        ],
        'website.assets_inside_builder_iframe': [
            'ypu_study_plans/static/src/js/s_study_plan.edit.js',
        ],
        'website.website_builder_assets': [
            'ypu_study_plans/static/src/js/s_study_plan_options.js',
            'ypu_study_plans/static/src/xml/s_study_plan_options.xml',
        ],
    },
    'installable': True,
    'application': True,
}

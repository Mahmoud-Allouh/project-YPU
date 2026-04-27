{
    'name': "YPU Teachers",
    'summary': "Teacher profiles with a public website directory",
    'description': """
Manage university teacher profiles from the backend and display
a searchable, filterable directory on the public website.

Key Features
============
* Teacher records with photo, contact info, and bio
* Categorise teachers and assign academic positions
* Control card ordering via drag-and-drop sequence in the backend
* Public /teachers page with search, category filter, and pagination
* Featured "dean" card displayed at the top of the listing
* Optional external-link / CV button per teacher card
    """,
    'author': "Komorebi Technologies",
    'website': "https://www.komorebitechnologies.com",
    'category': 'Website',
    'version': '19.0.4.0.0',
    'license': 'LGPL-3',
    'depends': ['base', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/teacher_category_views.xml',
        'views/teacher_position_views.xml',
        'views/teacher_views.xml',
        'views/teacher_import_views.xml',
        'data/website_menu.xml',
        'views/website_templates.xml',
        'views/snippets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ypu_teachers/static/src/css/teachers.css',
            'ypu_teachers/static/src/scss/s_teacher_cards.scss',
            'ypu_teachers/static/src/xml/s_teacher_cards.xml',
            'ypu_teachers/static/src/js/s_teacher_cards.js',
        ],
        'website.assets_inside_builder_iframe': [
            'ypu_teachers/static/src/js/s_teacher_cards.edit.js',
        ],
        'website.website_builder_assets': [
            'ypu_teachers/static/src/js/s_teacher_cards_options.js',
            'ypu_teachers/static/src/xml/s_teacher_cards_options.xml',
        ],
    },
    'installable': True,
    'application': True,
}

{
    'name': "YPU Honor Students",
    'summary': "Manage honor students by faculty, year, and semester",
    'description': """
Manage honor students from the backend and display them dynamically
on website pages with frontend filtering.

Key Features
============
* Faculty management
* Honor student records with year and semester assignment
* Website publication controls
* Dynamic website snippet with Faculty / Year / Semester filters
    """,
    'author': "Komorebi Technologies",
    'website': "https://www.komorebitechnologies.com",
    'category': 'Website',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['base', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/honor_faculty_views.xml',
        'views/honor_student_views.xml',
        'views/snippets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ypu_honor_students/static/src/scss/s_honor_students.scss',
            'ypu_honor_students/static/src/xml/s_honor_students.xml',
            'ypu_honor_students/static/src/js/s_honor_students.js',
        ],
        'website.assets_inside_builder_iframe': [
            'ypu_honor_students/static/src/js/s_honor_students.edit.js',
        ],
        'website.website_builder_assets': [
            'ypu_honor_students/static/src/js/s_honor_students_options.js',
            'ypu_honor_students/static/src/xml/s_honor_students_options.xml',
        ],
    },
    'installable': True,
    'application': True,
}

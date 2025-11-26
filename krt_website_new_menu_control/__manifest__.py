{
    "name": "KRT Website New Menu Control",
    "version": "19.0.1.0.0",
    "summary": "Show/Hide entries in the Website “+ New” menu",
    "author": "Komorebi Technologies",
    "license": "LGPL-3",
    "depends": ["website"],
    "assets": {
        "website.assets_frontend": [
            "krt_website_new_menu_control/static/src/js/new_menu_filter.js",
        ],
        "website.assets_wysiwyg": [
            "krt_website_new_menu_control/static/src/js/new_menu_filter.js",
        ],
        "web.assets_backend": [
            "krt_website_new_menu_control/static/src/js/new_menu_filter.js",
        ],
    },
    "data": [
        "views/res_config_settings.xml",
        "views/website_hide_styles.xml",
    ],
    "installable": True,
    "application": False,
}

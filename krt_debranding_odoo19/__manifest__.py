{
    "name": "KRT Debranding Odoo19",
    "version": "19.0",
    "summary": "Remove Odoo branding (login & website) for Odoo 19",
    "author": "Komorebi Technologies",
    "depends": ["web", "website"],
    "data": [
        "views/login_debrand.xml",
        "views/website_debrand.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
}

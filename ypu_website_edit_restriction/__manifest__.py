{
    "name": "YPU Website Edit Restriction",
    "summary": "Restrict website page and blog editing per user",
    "description": """
Limit what each user can modify on the website.

Administrators can enable website edit restrictions per user and choose:
- Which website pages the user can edit
- Which blogs the user can manage
    """,
    "author": "Komorebi Technologies",
    "website": "https://www.komorebitechnologies.com",
    "category": "Website",
    "version": "19.0.1.0.0",
    "license": "LGPL-3",
    "depends": ["base", "website", "website_blog"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/cleanup_legacy_views.xml",
        "views/website_edit_restriction_views.xml",
        "views/website_edit_restriction_menus.xml",
    ],
    "installable": True,
    "application": True,
}

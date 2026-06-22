# -*- coding: utf-8 -*-
{
    "name": "Backup Manager",
    "version": "19.0.1.0.0",
    "category": "Extra Tools",
    "summary": "Automated database backup with support for Nextcloud, Amazon S3, FTP, and SFTP.",
    "description": (
        "Automate backups of your Odoo databases using a modern, easy-to-use interface. "
        "Backups can be stored securely on Nextcloud, Amazon S3, a local server, or a remote server via FTP or SFTP."
    ),
    "author": "komorebi",
    "depends": ["base", "mail"],
    "sequence": "-300",
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/mail_template_data.xml",
        "data/ir_cron_data.xml",
        "wizard/restore_wizard.xml",
        "wizard/backup_delete_wizard.xml",
        "views/backup.xml",
        "views/manager.xml",
        "views/base.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "krt_backup_manager/static/src/scss/dashboard.scss",
            "krt_backup_manager/static/src/xml/dashboard.xml",
            "krt_backup_manager/static/src/js/chart.js",
            "krt_backup_manager/static/src/js/dashboard.js",
        ],
    },
    "external_dependencies": {
        "python": [
            "nextcloud_client",
            "boto3",
            "paramiko",
            "humanize",
        ]
    },
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": True,
}

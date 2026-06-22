from odoo import _

DESTINATION = [
    ("local", "Local"),
    ("ftp", "FTP"),
    ("sftp", "SFTP"),
    ("next_cloud", "NextCloud"),
    ("amazon_s3", "AWS S3"),
]

BACKUP_FORMAT = [("zip", "Zip"), ("dump", "Dump")]

BACKUP_STATUS = [
    ("fail", _("Failed")),
    ("success", _("Done")),
]

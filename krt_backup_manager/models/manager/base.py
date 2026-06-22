import boto3
import ftplib
import paramiko
import random
import nextcloud_client
from odoo import _, api, fields, models, exceptions, service, SUPERUSER_ID

from odoo.addons.krt_backup_manager.models.const import DESTINATION, BACKUP_FORMAT
from odoo.addons.krt_backup_manager.models.utils import get_selection_display_name


class DatabaseBackupConfiguration(models.Model):
    """
    [DataBase Backup Configure] class provides an interface to manage database backups of:
        - Local Server
        - Remote Server
        - Nextcloud
        - Amazon S3
    """

    _name = "db.backup.configure"
    _description = _("Automated Database Backup")
    _inherits = {"ir.cron": "ir_cron_id"}

    ir_cron_id = fields.Many2one(
        "ir.cron", "Ir Cron", delegate=True, ondelete="cascade", required=True
    )

    def _default_db_backup_color(self):
        return random.randint(0, 11)

    color = fields.Integer(string=_("Color"), default=_default_db_backup_color)
    db_name = fields.Char(
        string=_("Database Name"),
        default=lambda self: self.env.cr.dbname,
        required=True,
    )
    master_pwd = fields.Char(
        string=_("Master Password"), required=True, help=_("Master password")
    )
    backup_format = fields.Selection(
        BACKUP_FORMAT, string=_("Backup Format"), default="zip", required=True
    )
    backup_destination = fields.Selection(
        DESTINATION, required=True, string=_("Backup Destination")
    )
    hide_active = fields.Boolean(
        string=_("Hide Active"), help=_("Make active field readonly")
    )
    backup_path = fields.Char(
        string=_("Backup Path"), help=_("Path to store backups on local server")
    )

    sftp_host = fields.Char(string=_("SFTP Host"))
    sftp_port = fields.Char(string=_("SFTP Port"), default=22)
    sftp_user = fields.Char(string=_("SFTP User"), copy=False)
    sftp_password = fields.Char(string=_("SFTP Password"), copy=False)
    sftp_path = fields.Char(
        string=_("SFTP Path"),
        help=_("Path to store backups on SFTP server"),
    )

    ftp_host = fields.Char(string=_("FTP Host"))
    ftp_port = fields.Char(string=_("FTP Port"), default=21)
    ftp_user = fields.Char(string=_("FTP User"), copy=False)
    ftp_password = fields.Char(string=_("FTP Password"), copy=False)
    ftp_path = fields.Char(
        string=_("FTP Path"),
        help=_("Path to store backups on FTP server"),
    )

    domain = fields.Char(
        string=_("Domain"),
        help=_("Used to store the domain name"),
    )
    next_cloud_username = fields.Char(
        string=_("Nextcloud Username"), help=_("Nextcloud username")
    )
    next_cloud_password = fields.Char(
        string=_("Nextcloud Password"), help=_("Nextcloud password")
    )
    nextcloud_folder_key = fields.Char(
        string=_("Next Cloud Folder Identifier"),
        help=_("Unique identifier of the Nextcloud folder"),
    )

    aws_access_key = fields.Char(string=_("AWS Access Key"))
    aws_secret_access_key = fields.Char(string=_("AWS Secret Access Key"))
    bucket_file_name = fields.Char(
        string=_("Bucket Name"), help=_("Name of the S3 bucket")
    )
    aws_folder_name = fields.Char(
        string=_("AWS Folder Name"), help=_("Name of the S3 folder")
    )
    historiques_ids = fields.One2many(
        "db.backup.instance", "manager_id", string=_("Backup History")
    )
    historiques_count = fields.Integer(
        _("Number of Backups"), compute="_compute_historiques_count"
    )
    enable_user_notify = fields.Boolean(
        string=_("Notify User"),
        help=_(
            "Send an email notification to the user when a backup is successful or fails"
        ),
    )
    notify_user_id = fields.Many2one(
        "res.users", string=_("User"), help=_("User to notify")
    )
    auto_remove = fields.Boolean(
        string=_("Remove Old Backups"), help=_("Remove old backups")
    )
    auto_remove_mode = fields.Selection(
        [
            ("days_number", _("Number of Days")),
            ("database_number", _("Number of Databases")),
        ],
        string=_("Auto Remove Mode"),
        help=_(
            "Number of Days: Remove backups older than X days\nNumber of Databases: Keep only the X most recent backups"
        ),
    )
    auto_remove_number = fields.Integer(
        string=_("Remove After"),
        help=_("Remove backups after the number of [days | databases] specified."),
    )
    backup_filename = fields.Char(
        string=_("Backup Filename"),
        help=_("To store the filename of the generated backup"),
    )  # Used in the email template
    generated_exception = fields.Char(
        string=_("Exception"),
        help=_("Exception encountered during backup creation"),
    )  # Used in the email template

    def _compute_historiques_count(self):
        for rec in self:
            rec.historiques_count = len(rec.historiques_ids)

    @api.model
    def _using_both_ref_and_model_id(self):
        ir_model = (
            self.env["ir.model"]
            .sudo()
            .search([("model", "=", "db.backup.configure")], limit=1)
        )
        return {
            "search_default_all": 1,
            "default_interval_type": "days",
            "default_state": "code",
            "default_code": "model._schedule_auto_backup(record)",
            "default_user_id": self.env["res.users"].browse(SUPERUSER_ID).id,
            "default_model_id": ir_model.id if ir_model else False,
        }

    @api.constrains("db_name")
    def _check_db_credentials(self):
        """Validate entered database name and master password"""
        database_list = service.db.list_dbs(force=True)
        if self.db_name not in database_list:
            raise exceptions.ValidationError(_("Invalid Database Name!"))
        try:
            service.db.check_super(self.master_pwd)
        except Exception:
            raise exceptions.ValidationError(_("Invalid Master Password!"))

    def view_backup_history(self):
        action = (
            self.env.ref("krt_backup_manager.db_backup_instance_action").sudo().read()[0]
        )
        action["domain"] = [("manager_id", "=", self.id)]
        action["context"] = {"default_manager_id": self.id}
        return action

    def run_s3cloud_connection(self):
        """
        If it has aws_secret_access_key, which will perform s3 cloud operations for connection test
        """

        if self.aws_access_key and self.aws_secret_access_key:
            try:
                s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_access_key,
                )
                response = s3_client.head_bucket(Bucket=self.bucket_file_name)
                if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                    self.active = True
                    self.hide_active = True
                    return {
                        "type": "ir.actions.client",
                        "tag": "display_notification",
                        "params": {
                            "type": "success",
                            "title": _("Connection Test Successful!"),
                            "message": _(
                                "Everything seems to be correctly configured!"
                            ),
                            "sticky": False,
                        },
                    }
                raise exceptions.UserError(
                    _(
                        "Bucket not found. Please verify the name of the bucket and retry."
                    )
                )
            except Exception:
                self.active = False
                self.hide_active = False
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "type": "danger",
                        "title": _("Connection Test Failed!"),
                        "message": _("An error occurred during the connection test."),
                        "sticky": False,
                    },
                }

    def run_nextcloud_connection(self):
        """If it has next_cloud_password, domain, and next_cloud_username
        which will perform an action for nextcloud connection test
        """
        if self.domain and self.next_cloud_password and self.next_cloud_username:
            try:
                nc = nextcloud_client.Client(self.domain)
                nc.login(self.next_cloud_username, self.next_cloud_password)
                nc.list("/")
                self.active = True
                self.hide_active = True
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "type": "success",
                        "title": _("Connection Test Successful!"),
                        "message": _(
                            "Everything seems to be correctly configured!"
                        ),
                        "sticky": False,
                    },
                }
            except Exception:
                self.active = False
                self.hide_active = False
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "type": "danger",
                        "title": _("Connection Test Failed!"),
                        "message": _("An error occurred during the connection test."),
                        "sticky": False,
                    },
                }

    def run_sftp_connection(self):
        """Test the sftp and ftp connection using entered credentials"""
        if self.backup_destination == "sftp":
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(
                    hostname=self.sftp_host,
                    username=self.sftp_user,
                    password=self.sftp_password,
                    port=self.sftp_port,
                )
                sftp = client.open_sftp()
                sftp.close()
            except Exception as e:
                raise exceptions.UserError(_("SFTP Exception: %s", e))
            finally:
                client.close()
        elif self.backup_destination == "ftp":
            try:
                ftp_server = ftplib.FTP()
                ftp_server.connect(self.ftp_host, int(self.ftp_port))
                ftp_server.login(self.ftp_user, self.ftp_password)
                ftp_server.quit()
            except Exception as e:
                raise exceptions.UserError(_("Exception FTP : %s", e))
        self.hide_active = True
        self.active = True
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Test de connexion réussi !"),
                "message": _("Tout semble correctement configuré !"),
                "sticky": False,
            },
        }

    @api.onchange("backup_destination")
    def _onchange_back_up_local(self):
        """
        On change handler for the 'backup_destination' field. This method is
        triggered when the value of 'backup_destination' is changed. If the
        chosen backup destination is 'local', it sets the 'hide_active' field
        to True which make active field to readonly to False.
        """
        if self.backup_destination == "local":
            self.hide_active = True

    def to_json(self):
        return [
            {
                "id": rec.id,
                "name": rec.name,
                "db_name": rec.db_name,
                "active": rec.active,
                "backup_format": get_selection_display_name(
                    rec.backup_format, BACKUP_FORMAT
                ),
                "backup_destination": get_selection_display_name(
                    rec.backup_destination, DESTINATION
                ),
                "historiques_count": f"{rec.historiques_count:0>2,}",
            }
            for rec in self
        ]

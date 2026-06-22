import time
import boto3
import ftplib
import logging
import requests
import paramiko
import tempfile
import humanize
import nextcloud_client
from pathlib import Path
from odoo.service import db
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import str2bool
from datetime import datetime, timedelta
from .const import BACKUP_STATUS, DESTINATION
from .utils import get_selection_display_name

_logger = logging.getLogger(__name__)


class DataBaseBackupInstance(models.Model):
    """
    [DataBase Backup Instance] class provides an interface to manage database backups of:
        - Local Server
        - Remote Server
        - Nextcloud
        - Amazon S3
    """

    _name = "db.backup.instance"
    _order = "create_date desc"
    _description = _("Backup Instance")

    name = fields.Char(string=_("File Name"), required=True)
    active = fields.Boolean(default=True, string=_("Active"))
    status = fields.Selection(
        BACKUP_STATUS,
        string=_("Backup Status"),
        default="success",
        required=True,
    )
    error_message = fields.Text(_("Error message"))
    file_size = fields.Integer(_("File Size (Bytes)"), group_operator="sum")
    file_size_human = fields.Char(_("File Size"), compute="_compute_file_size_human")
    manager_id = fields.Many2one(
        "db.backup.configure", string=_("Backup Manager"), required=True
    )
    manager_status = fields.Boolean(
        string=_("Active Manager"), related="manager_id.active"
    )
    file_is_present = fields.Boolean(default=True, string=_("File is present"))
    download_path = fields.Text(_("File download location"))

    deletion_error_message = fields.Text(_("File deletion error"))
    download_error_message = fields.Text(_("File download error"))
    check_exist_error_message = fields.Text(_("File verification error"))
    restore_error_message = fields.Text(_("Database restoration error"))

    def _compute_file_size_human(self):
        for rec in self:
            rec.file_size_human = humanize.naturalsize(rec.file_size)

    def to_json(self):
        return [
            {
                "id": rec.id,
                "name": rec.name,
                "active": rec.active,
                "status": rec.status,
                "status_display": get_selection_display_name(rec.status, BACKUP_STATUS),
                "file_size": humanize.naturalsize(rec.file_size),
                "manager_id": {
                    "id": rec.manager_id.id,
                    "name": rec.manager_id.name,
                },
                "manager_status": rec.manager_status,
                "file_is_present": rec.file_is_present,
                "error_message": rec.error_message,
                "destination": get_selection_display_name(
                    rec.manager_id.backup_destination, DESTINATION
                ),
                "create_datetime": rec.create_date.strftime("%d/%m/%Y %H:%M"),
            }
            for rec in self.sorted("create_date", reverse=True)
        ]

    def write_db_to_tmp_file(self, temp_file):
        #   For Local Storage
        if self.manager_id.backup_destination == "local":
            try:
                file_path = (Path(self.manager_id.backup_path) / self.name).resolve()
                temp_file.name = file_path.as_posix()
            except Exception as e:
                return str(e)

        #   For FTP
        if self.manager_id.backup_destination == "ftp":
            try:
                ftp_server = ftplib.FTP()
                ftp_server.connect(
                    self.manager_id.ftp_host, int(self.manager_id.ftp_port)
                )
                ftp_server.login(self.manager_id.ftp_user, self.manager_id.ftp_password)
                ftp_server.cwd(self.manager_id.ftp_path)
                ftp_server.retrbinary(f"RETR {self.name}", temp_file.write)
                temp_file.seek(0)
                ftp_server.quit()
            except Exception as e:
                return str(e)

        #   For SFTP
        if self.manager_id.backup_destination == "sftp":
            sftp_client = paramiko.SSHClient()
            sftp_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                sftp_client.connect(
                    hostname=self.manager_id.sftp_host,
                    username=self.manager_id.sftp_user,
                    password=self.manager_id.sftp_password,
                    port=self.manager_id.sftp_port,
                )
                sftp_server = sftp_client.open_sftp()
                sftp_server.chdir(self.manager_id.sftp_path)
                sftp_server.getfo(self.name, temp_file)
                temp_file.seek(0)
                sftp_server.close()
            except Exception as e:
                return str(e)
            finally:
                sftp_client.close()

        #   For Next Cloud
        if self.manager_id.backup_destination == "next_cloud":
            try:
                nc_access = nextcloud_client.Client(self.manager_id.domain)
                nc_access.login(
                    self.manager_id.next_cloud_username,
                    self.manager_id.next_cloud_password,
                )
                link_info = nc_access.share_file_with_link(
                    f"/{self.manager_id.nextcloud_folder_key}/{self.name}",
                    publicUpload=False,
                )
                file_url = f"{link_info.get_link()}/download"
                response = requests.get(file_url, stream=True)
                temp_file.write(response.content)
                temp_file.seek(0)
            except Exception as e:
                return str(e)

        #   For Amazon S3
        if self.manager_id.backup_destination == "amazon_s3":
            try:
                client = boto3.client(
                    "s3",
                    aws_access_key_id=self.manager_id.aws_access_key,
                    aws_secret_access_key=self.manager_id.aws_secret_access_key,
                )
                region = client.get_bucket_location(
                    Bucket=self.manager_id.bucket_file_name
                )
                client = boto3.client(
                    "s3",
                    region_name=region["LocationConstraint"],
                    aws_access_key_id=self.manager_id.aws_access_key,
                    aws_secret_access_key=self.manager_id.aws_secret_access_key,
                )
                Key = f"{self.manager_id.aws_folder_name}/{self.backup_filename}"
                file_url = client.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={
                        "Bucket": self.manager_id.bucket_file_name,
                        "Key": Key,
                    },
                    ExpiresIn=3600,
                )
                response = requests.get(file_url, stream=True)
                temp_file.write(response.content)
                temp_file.seek(0)
            except Exception as e:
                return str(e)
        self.download_path = temp_file.name

    def restore_backup(self, db_name, copy=False, neutralize_database=False):
        for rec in self:
            temp_file = None
            try:
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                rec.write_db_to_tmp_file(temp_file)
                db.restore_db(
                    db_name, temp_file.name, str2bool(copy), neutralize_database
                )
                temp_file.close()
            except Exception as e:
                rec.restore_error_message = f"{rec.restore_error_message} \n {time.strftime('%d/%m/%Y %H:%M:%S').center(30, '=')} \n {e}"
                raise UserError(_(f"Backup restoration error: {(str(e) or repr(e))}"))
            finally:
                if (
                    temp_file
                ):  # Ensure temp_file is not None before attempting to unlink
                    file_ = Path(temp_file.name).resolve()
                    file_.unlink(missing_ok=True)
        return {
            "type": "ir.actions.act_url",
            "url": "/web/database/manager",
            "target": "current",
        }

    def download_backup(self):
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            self.write_db_to_tmp_file(temp_file)
        except Exception as e:
            self.download_error_message = (
                f"{self.download_error_message} \n {'-' * 15} \n {e}"
            )
            raise UserError(  # Raise an error if download fails
                _(f"Backup download error: {(str(e) or repr(e))}")
            )
        temp_file.seek(0)
        try:
            temp_file.close()
        except:
            pass
        action = {
            "type": "ir.actions.act_url",
            "name": self.name,
            "url": (
                "/web/binary/download-backup?model=db.backup.instance"
                + "&id="
                + str(self.id)
                + "&file_name_field=name&file_path_field=download_path&file_format="
                + self.manager_id.backup_format
            ),
            "target": "new",
        }
        return action

    def _auto_check_if_file_exist(self):
        for rec in self.search([]):
            try:
                if rec.manager_id.backup_destination == "local":
                    file_path = (Path(rec.manager_id.backup_path) / rec.name).resolve()
                    rec.file_is_present = file_path.exists()

                elif rec.manager_id.backup_destination == "ftp":
                    ftp_server = ftplib.FTP(rec.manager_id.ftp_host)
                    ftp_server.login(
                        rec.manager_id.ftp_user, rec.manager_id.ftp_password
                    )
                    ftp_server.cwd(rec.manager_id.ftp_path)
                    rec.file_is_present = rec.name in ftp_server.nlst()
                    ftp_server.quit()

                elif rec.manager_id.backup_destination == "sftp":
                    sftp_client = paramiko.SSHClient()
                    sftp_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    sftp_client.connect(
                        hostname=rec.manager_id.sftp_host,
                        username=rec.manager_id.sftp_user,
                        password=rec.manager_id.sftp_password,
                        port=rec.manager_id.sftp_port,
                    )
                    sftp_server = sftp_client.open_sftp()
                    sftp_server.chdir(rec.manager_id.sftp_path)
                    rec.file_is_present = rec.name in sftp_server.listdir()
                    sftp_server.close()
                    sftp_client.close()

                elif rec.manager_id.backup_destination == "next_cloud":
                    nc_access = nextcloud_client.Client(rec.manager_id.domain)
                    nc_access.login(
                        rec.manager_id.next_cloud_username,
                        rec.manager_id.next_cloud_password,
                    )
                    files = nc_access.list_folders(rec.manager_id.nextcloud_folder_key)
                    rec.file_is_present = any(f["fileid"] == rec.name for f in files)

                elif rec.manager_id.backup_destination == "amazon_s3":
                    client = boto3.client(
                        "s3",
                        aws_access_key_id=rec.manager_id.aws_access_key,
                        aws_secret_access_key=rec.manager_id.aws_secret_access_key,
                    )
                    try:
                        client.head_object(
                            Bucket=rec.manager_id.bucket_file_name,
                            Key=f"{rec.manager_id.aws_folder_name}/{rec.name}",
                        )
                        rec.file_is_present = True
                    except client.exceptions.ClientError:
                        rec.file_is_present = False

            except Exception as e:
                rec.check_exist_error_message = str(e)
                rec.file_is_present = False

    def delete_db_backup_file(self):
        for rec in self:
            record_instance = rec.manager_id
            if record_instance.auto_remove_mode == "days_number":
                to_delete_list = (
                    self.env["db.backup.instance"]
                    .sudo()
                    .search(
                        [
                            ("file_is_present", "=", True),
                            ("active", "=", True),
                            ("manager_id", "=", record_instance.id),
                            (
                                "create_date",
                                "<",
                                datetime.now()
                                - timedelta(days=record_instance.auto_remove_number),
                            ),
                        ]
                    )
                )
            elif record_instance.auto_remove_mode == "database_number":
                to_delete_list = self.env["db.backup.instance"].search(
                    [
                        ("file_is_present", "=", True),
                        ("active", "=", True),
                        ("manager_id", "=", record_instance.id),
                    ],
                    order="create_date desc",
                )
                to_delete_list = to_delete_list[record_instance.auto_remove_number :]

            if record_instance.backup_destination == "local":
                for rec in to_delete_list:
                    try:
                        backup_file = (
                            Path(record_instance.backup_path) / rec.name
                        ).resolve()  # Resolve the absolute path
                        backup_file.unlink(missing_ok=True)
                    except Exception as e:
                        _logger.error(_("Local exception: {e}"))
                        rec.deletion_error_message = str(e)
                    finally:
                        rec.file_is_present = False

            elif record_instance.backup_destination == "ftp":
                ftp_server = ftplib.FTP()
                ftp_server.connect(
                    record_instance.ftp_host, int(record_instance.ftp_port)
                )
                ftp_server.login(record_instance.ftp_user, record_instance.ftp_password)
                ftp_server.cwd(record_instance.ftp_path)
                for rec in to_delete_list:
                    try:
                        ftp_server.delete(rec.name)
                    except Exception as e:
                        _logger.error(_("FTP exception: {e}"))
                        rec.deletion_error_message = str(e)
                    finally:
                        rec.file_is_present = False
                ftp_server.quit()

            elif record_instance.backup_destination == "sftp":
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=record_instance.sftp_host,
                    username=record_instance.sftp_user,
                    password=record_instance.sftp_password,
                    port=record_instance.sftp_port,
                )
                sftp = client.open_sftp()
                sftp.chdir(record_instance.sftp_path)
                for rec in to_delete_list:
                    try:
                        sftp.unlink(rec.name)
                    except Exception as e:
                        _logger.error(_("SFTP exception: {e}"))
                        rec.deletion_error_message = str(e)
                    finally:
                        rec.file_is_present = False
                sftp.close()
                client.close()

            elif record_instance.backup_destination == "next_cloud":
                nc = nextcloud_client.Client(record_instance.domain)
                nc.login(
                    record_instance.next_cloud_username,
                    record_instance.next_cloud_password,
                )
                for rec in to_delete_list:
                    try:
                        nc.delete(record_instance.nextcloud_folder_key + "/" + rec.name)
                    except Exception as e:
                        _logger.error(_("NextCloud exception: {e}"))
                        rec.deletion_error_message = str(e)
                    finally:
                        rec.file_is_present = False

            elif record_instance.backup_destination == "amazon_s3":
                bo3 = boto3.client(
                    "s3",
                    aws_access_key_id=record_instance.aws_access_key,
                    aws_secret_access_key=record_instance.aws_secret_access_key,
                )
                for rec in to_delete_list:
                    try:
                        bo3.delete_objects(
                            Bucket=record_instance.bucket_file_name,
                            Delete={
                                "Objects": [
                                    {
                                        "Key": f"{record_instance.aws_folder_name}/{rec.name}"
                                    }
                                    # for rec in to_delete_list
                                ]
                            },
                        )
                    except Exception as e:  # Catch any exceptions during S3 deletion
                        _logger.error(_("Amazon S3 exception: {e}"))
                        rec.deletion_error_message = str(e)
                    finally:
                        rec.file_is_present = False
                        # for rec in to_delete_list:
                        #     rec.file_is_present = False

    def retore_db_view(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "krt_backup_manager.db_restore_instance_wizard_wizard_action"
        )
        action.update(
            {
                "views": [[False, "form"]],
                "context": "{'default_backup_id': " + str(self.id) + "}",
            }
        )
        return action

import json
import errno
import boto3
import shutil
import ftplib
import logging
import paramiko
import tempfile
import subprocess
import humanize
import nextcloud_client
from pathlib import Path
from datetime import datetime, timedelta, UTC
from odoo import _, api, fields, models, exceptions, release, sql_db, tools
from odoo.tools.misc import exec_pg_environ, find_pg_tool
_logger = logging.getLogger(__name__)


class DatabaseBackupConfigurationExtras(models.Model):
    _inherit = "db.backup.configure"

    def _schedule_auto_delete(self):
        """
        Function for deleting the backup.
        Database backup for all the active records in backup configuration model will be deleted.
        """

        record_instances = self.search([("auto_remove", "=", True)])

        for record_instance in record_instances:
            to_delete_list = []

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
                        ).resolve()
                        backup_file.unlink(missing_ok=True)
                    except Exception as e:
                        _logger.error(_(f"Exception locale: {e}"))
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
                        _logger.error(_(f"Exception FTP: {e}"))
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
                        _logger.error(_(f"SFTP Exception: {e}"))
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
                        _logger.error(_(f"NextCloud Exception: {e}"))
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
                    except Exception as e:
                        _logger.error(_(f"Exception Amazon S3: {e}"))
                        rec.deletion_error_message = str(e)
                    finally:
                        rec.file_is_present = False
                        # for rec in to_delete_list:
                        #     rec.file_is_present = False

    def send_user_notify_mail(self, record, success=True):
        mail_template_success = self.env.ref(
            "krt_backup_manager.mail_template_data_db_backup_successful"
        )
        mail_template_failed = self.env.ref(
            "krt_backup_manager.mail_template_data_db_backup_failed"
        )
        try:
            if record.enable_user_notify:
                if success:
                    mail_template_success.send_mail(record.id, force_send=True)
                else:
                    mail_template_failed.send_mail(record.id, force_send=True)
        except Exception:
            pass

    @api.model
    def _schedule_auto_backup(self, *_):
        """Function for generating and storing backup.
        Database backup for all the active records in backup configuration
        model will be created."""

        cron_instance = None
        cron_id = self.env.context.get("cron_id", False)

        if cron_id:
            cron_instance = self.env["ir.cron"].browse(cron_id)

        if not cron_instance:
            return

        records = self.search([("ir_cron_id", "=", cron_instance.id)])

        success = True
        generated_exception = ""

        for rec in records:
            backup_time = datetime.now(UTC).strftime("%d-%m-%Y_%H-%M-%S")
            backup_filename = f"{rec.db_name}_{backup_time}.{rec.backup_format}"
            rec.backup_filename = backup_filename
            file_size = 0

            # Local backup
            if rec.backup_destination == "local":
                try:
                    bfile = Path(rec.backup_path).resolve()
                    if not bfile.exists() or not bfile.is_dir():
                        bfile.mkdir(parents=True)
                    backup_file = bfile / backup_filename
                    f = open(backup_file, "wb")
                    self.dump_data(rec.db_name, f, rec.backup_format)
                    f.close()
                    file_size = backup_file.stat().st_size
                    self.send_user_notify_mail(rec, True)
                except Exception as e:
                    generated_exception = e
                    success = False
                    self.send_user_notify_mail(rec, False)

            # FTP backup
            elif rec.backup_destination == "ftp":
                try:
                    ftp_server = ftplib.FTP()
                    ftp_server.connect(rec.ftp_host, int(rec.ftp_port))
                    ftp_server.login(rec.ftp_user, rec.ftp_password)
                    ftp_server.encoding = "utf-8"
                    temp = tempfile.NamedTemporaryFile(suffix=".%s" % rec.backup_format)
                    try:
                        ftp_server.cwd(rec.ftp_path)
                    except ftplib.error_perm:
                        ftp_server.mkd(rec.ftp_path)
                        ftp_server.cwd(rec.ftp_path)
                    with open(temp.name, "wb+") as tmp:
                        self.dump_data(rec.db_name, tmp, rec.backup_format)
                    ftp_server.storbinary(
                        "STOR %s" % backup_filename, open(temp.name, "rb")
                    )
                    file_size = ftp_server.size(backup_filename)
                    ftp_server.quit()
                    self.send_user_notify_mail(rec, True)
                except Exception as e:
                    generated_exception = e
                    success = False
                    self.send_user_notify_mail(rec, False)

            # SFTP backup
            elif rec.backup_destination == "sftp":
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                try:
                    client.connect(
                        hostname=rec.sftp_host,
                        username=rec.sftp_user,
                        password=rec.sftp_password,
                        port=rec.sftp_port,
                    )
                    sftp = client.open_sftp()
                    temp = tempfile.NamedTemporaryFile(suffix=".%s" % rec.backup_format)
                    with open(temp.name, "wb+") as tmp:
                        self.dump_data(rec.db_name, tmp, rec.backup_format)
                    try:
                        sftp.chdir(rec.sftp_path)
                    except IOError as e:
                        if e.errno == errno.ENOENT:
                            sftp.mkdir(rec.sftp_path)
                            sftp.chdir(rec.sftp_path)
                    sftp.put(temp.name, backup_filename)
                    file_info = sftp.stat(backup_filename)
                    file_size = file_info.st_size
                    sftp.close()
                    self.send_user_notify_mail(rec, True)
                except Exception as e:
                    generated_exception = e
                    success = False
                    self.send_user_notify_mail(rec, False)
                finally:
                    client.close()

            # NextCloud Backup
            elif rec.backup_destination == "next_cloud":
                # Get the folder name from the NextCloud folder ID
                folder_name = rec.nextcloud_folder_key
                try:
                    if (
                        rec.domain
                        and rec.next_cloud_password
                        and rec.next_cloud_username
                    ):
                        try:
                            nc = nextcloud_client.Client(rec.domain)
                            nc.login(rec.next_cloud_username, rec.next_cloud_password)
                            self.send_user_notify_mail(rec, True)
                        except Exception as error:
                            generated_exception = error
                            success = False
                            self.send_user_notify_mail(rec, False)
                        # Ensure folder exists (ignore errors if it already exists)
                        if folder_name:
                            try:
                                nc.mkdir(folder_name)
                            except Exception:
                                pass

                        if not folder_name:
                            raise exceptions.ValidationError("Please set Nextcloud folder")

                        # Dump the database to a temporary file then upload
                        temp = tempfile.NamedTemporaryFile(
                            suffix=".%s" % rec.backup_format
                        )
                        with open(temp.name, "wb+") as tmp:
                            self.dump_data(rec.db_name, tmp, rec.backup_format)
                        remote_file_path = (
                            f"/{folder_name}/{rec.db_name}_"
                            f"{backup_time}.{rec.backup_format}"
                        )
                        nc.put_file(remote_file_path, temp.name)
                        file_info = nc.file_info(remote_file_path)
                        file_size = file_info["size"]
                except Exception:
                    raise exceptions.ValidationError("Please check connection")

            # Amazon S3 Backup
            elif rec.backup_destination == "amazon_s3":
                if rec.aws_access_key and rec.aws_secret_access_key:
                    try:
                        # Create a boto3 resource for Amazon S3 with provided
                        # access key id and secret access key
                        s3 = boto3.resource(
                            "s3",
                            aws_access_key_id=rec.aws_access_key,
                            aws_secret_access_key=rec.aws_secret_access_key,
                        )
                        # Create a folder in the specified bucket, if it
                        # doesn't already exist
                        s3.Object(rec.bucket_file_name, rec.aws_folder_name + "/").put()
                        bucket = s3.Bucket(rec.bucket_file_name)
                        # Get all the prefixes in the bucket
                        prefixes = set()
                        for obj in bucket.objects.all():
                            key = obj.key
                            if key.endswith("/"):
                                prefix = key[:-1]  # Remove the trailing slash
                                prefixes.add(prefix)
                        # If the specified folder is present in the bucket,
                        # take a backup of the database and upload it to the
                        #   S3 bucket
                        assert (
                            rec.aws_folder_name in prefixes
                        ), "The specified folder is not present in the bucket"
                        temp = tempfile.NamedTemporaryFile(
                            suffix=".%s" % rec.backup_format
                        )
                        with open(temp.name, "wb+") as tmp:
                            self.dump_data(rec.db_name, tmp, rec.backup_format)
                        remote_file_path = (
                            f"{rec.aws_folder_name}/{rec.db_name}_"
                            f"{backup_time}.{rec.backup_format}"
                        )
                        s3.Object(rec.bucket_file_name, remote_file_path).upload_file(
                            temp.name
                        )
                        response = s3.head_object(
                            Bucket=rec.bucket_file_name, Key=remote_file_path
                        )
                        file_size = response["ContentLength"]
                        self.send_user_notify_mail(rec, True)
                    except Exception as e:
                        # If any error occurs, set the 'generated_exception'
                        # field to the error message and log the error
                        generated_exception = e
                        success = False
                        self.send_user_notify_mail(rec, False)

            # Creation of history
            self.env["db.backup.instance"].sudo().create(
                {
                    "name": backup_filename,
                    "manager_id": rec.id,
                    "status": "success" if success else "fail",
                    "error_message": generated_exception,
                    "file_size": int(file_size),
                }
            )

    def dump_data(self, db_name, stream, backup_format):
        """
        Dump database "db" into file-like object "stream" if stream is None
        return a file object with the dump.
        """

        _logger.info("DUMP DB: %s format %s", db_name, backup_format)

        cmd = [find_pg_tool("pg_dump"), "--no-owner", db_name]
        env = exec_pg_environ()
        if backup_format == "zip":
            with tempfile.TemporaryDirectory() as dump_dir:
                filestore = tools.config.filestore(db_name)
                file_path = Path(dump_dir) / "dump.sql"
                cmd.insert(-1, "--file=" + file_path.as_posix())
                subprocess.run(
                    cmd,
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                    check=True,
                )
                if Path(filestore).exists():
                    shutil.copytree(
                        filestore, (Path(dump_dir) / "filestore").as_posix()
                    )
                with open((Path(dump_dir) / "manifest.json").as_posix(), "w") as fh:
                    db = sql_db.db_connect(db_name)
                    with db.cursor() as cr:
                        json.dump(self._dump_db_manifest(cr), fh, indent=4)
                if stream:
                    tools.osutil.zip_dir(
                        dump_dir,
                        stream,
                        include_dir=False,
                        fnct_sort=lambda file_name: file_name != "dump.sql",
                    )
                else:
                    t = tempfile.TemporaryFile()
                    tools.osutil.zip_dir(
                        dump_dir,
                        t,
                        include_dir=False,
                        fnct_sort=lambda file_name: file_name != "dump.sql",
                    )
                    t.seek(0)
                    return t
        else:
            cmd.insert(-1, "--format=c")
            process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
            stdout, _ = process.communicate()
            if stream:
                stream.write(stdout)
            else:
                return stdout

    def _dump_db_manifest(self, cr):
        """This function generates a manifest dictionary for database dump."""
        pg_version = "%d.%d" % divmod(cr._obj.connection.server_version / 100, 100)
        cr.execute(
            "SELECT name, latest_version FROM ir_module_module WHERE state = 'installed'"
        )
        modules = dict(cr.fetchall())
        manifest = {
            "odoo_dump": "1",
            "db_name": cr.dbname,
            "version": release.version,
            "version_info": release.version_info,
            "major_version": release.major_version,
            "pg_version": pg_version,
            "modules": modules,
        }
        return manifest

    @api.model
    def dashboard_global_backup_instance_datas(self, limit=50, offset=0):
        instance_all = (
            self.env["db.backup.instance"]
            .sudo()
            .search([("active", "in", [False, True])], limit=limit, offset=offset)
        )

        return {
            "instances": instance_all.to_json(),
            "limit": limit,
            "offset": offset,
        }

    @api.model
    def dashboard_global_datas(self):
        instance_all = (
            self.env["db.backup.instance"]
            .sudo()
            .search([("active", "in", [False, True])])
        )
        instance_total = len(instance_all)
        instance_present = (
            self.env["db.backup.instance"]
            .sudo()
            .search_count(
                [("file_is_present", "=", True), ("active", "in", [False, True])]
            )
        )
        pourcentage_presence = (
            (instance_present * 100 / instance_total) if instance_total else 0
        )
        configs_all = (
            self.env["db.backup.configure"]
            .sudo()
            .search([("active", "in", [False, True])])
        )
        configs_total = len(configs_all)
        configs_active = (
            self.env["db.backup.configure"].sudo().search([("active", "in", [True])])
        )
        configs_active_count = len(configs_active)
        instance_success = (
            self.env["db.backup.instance"]
            .sudo()
            .search_count([("status", "=", "success"), ("active", "in", [False, True])])
        )
        instance_fail = (
            self.env["db.backup.instance"]
            .sudo()
            .search_count([("status", "=", "fail"), ("active", "in", [False, True])])
        )
        pourcentage_instance_success = (
            (instance_success * 100 / instance_total) if instance_total else 0
        )
        pourcentage_instance_fail = (
            (instance_fail * 100 / instance_total) if instance_total else 0
        )
        fichier_present_file_size = humanize.naturalsize(
            sum(
                self.env["db.backup.instance"]
                .sudo()
                .search(
                    [("active", "in", [False, True]), ("file_is_present", "=", True)]
                )
                .mapped("file_size")
            )
        )
        fichier_absent_file_size = humanize.naturalsize(
            sum(
                self.env["db.backup.instance"]
                .sudo()
                .search(
                    [("active", "in", [False, True]), ("file_is_present", "=", False)]
                )
                .mapped("file_size")
            )
        )
        instance_list = instance_all[:5].to_json()
        configs_list = configs_all.to_json()

        aujourd_hui = datetime.now()
        aujourd_hui = aujourd_hui.replace(hour=23, minute=59, second=59)
        il_y_a_7_jours = aujourd_hui - timedelta(days=6)
        il_y_a_7_jours = il_y_a_7_jours.replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        all_grouped = (
            self.env["db.backup.instance"]
            .sudo()
            ._read_group(
                domain=[
                    ("active", "in", [False, True]),
                    ("create_date", ">=", il_y_a_7_jours),
                    ("create_date", "<=", aujourd_hui),
                ],
                groupby=["create_date:day", "status"],
                aggregates=["id:count", "status:count_distinct"],
            )
        )

        days_items = {}

        for line in all_grouped:
            jour = line[0].strftime("%d/%m/%Y")
            if not jour in days_items:
                days_items[jour] = {"success": 0, "fail": 0}
            for row in all_grouped:
                jour_sub = row[0].strftime("%d/%m/%Y")
                if jour_sub == jour:
                    if row[1] == "success":
                        days_items[jour]["success"] = row[2]
                    elif row[1] == "fail":
                        days_items[jour]["fail"] = row[2]

        return {
            "instance_total": instance_total,
            "instance_pourcentage_presence": int(pourcentage_presence),
            "configs_total": f"{configs_total:0>2,}",
            "configs_active": f"{configs_active_count:0>2,}",
            "pourcentage_instance_success": round(pourcentage_instance_success, 2),
            "pourcentage_instance_fail": round(pourcentage_instance_fail, 2),
            "fichier_present_file_size": fichier_present_file_size,
            "fichier_absent_file_size": fichier_absent_file_size,
            # List of backup instances
            "last_dashboard_instance_list": instance_list,
            "all_instance_list": instance_list,
            # List of configuration instances
            "configs_active_list": configs_active.to_json(),
            "all_configs_list": configs_list,
            "backupHistory": list(days_items.items()),
        }

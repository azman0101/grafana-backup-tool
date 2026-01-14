from grafana_backup.create_org import main as create_org
from grafana_backup.api_checks import main as api_checks
from grafana_backup.create_folder import main as create_folder
from grafana_backup.update_folder_permissions import main as update_folder_permissions
from grafana_backup.create_datasource import main as create_datasource
from grafana_backup.create_dashboard import main as create_dashboard
from grafana_backup.create_alert_channel import main as create_alert_channel
from grafana_backup.create_alert_rule import main as create_alert_rule
from grafana_backup.create_user import main as create_user
from grafana_backup.create_snapshot import main as create_snapshot
from grafana_backup.create_annotation import main as create_annotation
from grafana_backup.create_team import main as create_team
from grafana_backup.create_team_member import main as create_team_member
from grafana_backup.create_library_element import main as create_library_element
from grafana_backup.create_contact_point import main as create_contact_point
from grafana_backup.update_notification_policy import main as update_notification_policy
from grafana_backup.s3_download import main as s3_download
from grafana_backup.azure_storage_download import main as azure_storage_download
from grafana_backup.gcs_download import main as gcs_download
from glob import glob
import sys
import tarfile
import tempfile
import os
import shutil
import fnmatch
import collections


def main(args, settings):
    def open_compressed_backup(compressed_backup):
        try:
            tar = tarfile.open(fileobj=compressed_backup, mode='r:gz')
            return tar
        except Exception as e:
            print(str(e))
            sys.exit(1)

    arg_archive_file = args.get('<archive_file>', None)
    aws_s3_bucket_name = settings.get('AWS_S3_BUCKET_NAME')
    azure_storage_container_name = settings.get('AZURE_STORAGE_CONTAINER_NAME')
    gcs_bucket_name = settings.get('GCS_BUCKET_NAME')

    (status, json_resp, dashboard_uid_support, datasource_uid_support,
     paging_support, contact_point_support) = api_checks(settings)
    settings.update({'CONTACT_POINT_SUPPORT': contact_point_support})

    # Do not continue if API is unavailable or token is not valid
    if not status == 200:
        sys.exit(1)

    # Use tar data stream if S3 bucket name is specified
    if aws_s3_bucket_name:
        print('Download archives from S3:')
        s3_data = s3_download(args, settings)
        tar = open_compressed_backup(s3_data)

    elif azure_storage_container_name:
        print('Download archives from Azure:')
        azure_storage_data = azure_storage_download(args, settings)
        tar = open_compressed_backup(azure_storage_data)

    elif gcs_bucket_name:
        print('Download archives from GCS:')
        gcs_storage_data = gcs_download(args, settings)
        tar = open_compressed_backup(gcs_storage_data)

    else:
        try:
            tarfile.is_tarfile(name=arg_archive_file)
        except IOError as e:
            print(str(e))
            sys.exit(1)
        try:
            tar = tarfile.open(name=arg_archive_file, mode='r:gz')
        except Exception as e:
            print(str(e))
            sys.exit(1)

    # TODO:
    # Shell game magic warning: restore_function keys require the 's'
    # to be removed in order to match file extension names...
    restore_functions = collections.OrderedDict()
    # Folders must be restored before Library-Elements
    restore_functions['folder'] = create_folder
    restore_functions['datasource'] = create_datasource
    # Library-Elements must be restored before dashboards
    restore_functions['library_element'] = create_library_element
    restore_functions['dashboard'] = create_dashboard
    restore_functions['alert_channel'] = create_alert_channel
    restore_functions['organization'] = create_org
    restore_functions['user'] = create_user
    restore_functions['snapshot'] = create_snapshot
    restore_functions['annotation'] = create_annotation
    restore_functions['team'] = create_team
    restore_functions['team_member'] = create_team_member
    restore_functions['folder_permission'] = update_folder_permissions
    restore_functions['alert_rule'] = create_alert_rule
    restore_functions['contact_point'] = create_contact_point
    # There are some issues of notification policy restore api, it will lock the notification policy page and cannot be edited.
    # restore_functions['notification_policys'] = update_notification_policy

    restore_components(args, settings, restore_functions, tar)


def restore_components(args, settings, restore_functions, tar):
    arg_components = args.get('--components', [])
    if arg_components:
        arg_components_list = arg_components.replace("-", "_").split(',')
    else:
        arg_components_list = restore_functions.keys()

    for member in tar.getmembers():
        if member.isfile():
            # TODO: add some sort of --no-ssl-check, ideally this would be better
            os.environ['PYTHONHTTPSVERIFY'] = "0"

            file_path = member.name
            fname, fext = file_path.split(os.extsep, 1)

            if fext in arg_components_list:
                print("restoring {0}: {1}".format(fext, file_path))
                # create a temporary file to read the extracted member
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
                    # extract member to temporary file
                    shutil.copyfileobj(tar.extractfile(member), tmp)
                    # restore single file
                    restore_functions[fext](args, settings, tmp.name)

    tar.close()

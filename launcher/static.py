import getpass
import os
import sys
from datetime import timedelta, datetime

import pandas as pd
from requests_ntlm import HttpNtlmAuth
from sharepoint import Site

user_main = getpass.getuser()


class UserFriendlyError(Exception):
    """Custom exception for user-friendly error messages"""
    pass


def pslv_action_entry(dictionary_as_list):
    """Enhanced SharePoint action entry with better error handling"""
    try:
        cred = HttpNtlmAuth(SID, "")
        site = Site(SITE_URL, auth=cred, verify_ssl=False)
        sp_list = site.List(ACTION_HISTORY)
        sp_list.UpdateListItems(data=dictionary_as_list, kind='New')
    except ConnectionError:
        raise UserFriendlyError("Unable to connect to SharePoint. Please check your network connection.")
    except Exception as e:
        if "authentication" in str(e).lower() or "auth" in str(e).lower():
            raise UserFriendlyError("SharePoint authentication failed. Please contact IT support.")
        else:
            raise UserFriendlyError(f"Failed to save action history: {str(e)}")


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def expire_sort(row):
    """Check if application has expired"""
    try:
        release_date = pd.Timestamp(row['Release_Date'])
        expiry_date = release_date + timedelta(days=row['Validity_Period'])
        return datetime.now() > expiry_date
    except (ValueError, TypeError, KeyError) as e:
        print(f"Error checking expiry for row: {e}")
        return False


def split_user(users):
    """Split user string into list"""
    if isinstance(users, str):
        return users.split(';')
    else:
        return []


def add_new_user_to_userbase(data):
    """Enhanced user addition with better error handling"""
    try:
        cred = HttpNtlmAuth(SID, password="")
        site = Site(SITE_URL, auth=cred, verify_ssl=False)
        sp_list = site.List(USERBASE)
        dictionary_as_list = [{
            'id': data[0],
            'display_name': data[1],
            'email': data[2],
            'job_title': data[3],
            'building_name': data[4],
            'cost_center_id': data[5]
        }]
        sp_list.UpdateListItems(data=dictionary_as_list, kind='New')
        print(f'User {data[0]} added to userbase.')
    except ConnectionError:
        raise UserFriendlyError("Unable to connect to SharePoint. Please check your network connection.")
    except Exception as e:
        if "authentication" in str(e).lower():
            raise UserFriendlyError("SharePoint authentication failed. Please contact IT support.")
        else:
            raise UserFriendlyError(f"Failed to add user to database: {str(e)}")


def validate_configuration():
    """Validate configuration constants"""
    required_configs = {
        'SITE_URL': SITE_URL,
        'SHAREPOINT_LIST': SHAREPOINT_LIST,
        'USERBASE': USERBASE,
        'COST_CENTER': COST_CENTER,
        'ACTION_HISTORY': ACTION_HISTORY
    }

    missing_configs = []
    for config_name, config_value in required_configs.items():
        if not config_value or config_value.strip() == "":
            missing_configs.append(config_name)

    if missing_configs:
        raise UserFriendlyError(
            f"Missing configuration values: {', '.join(missing_configs)}. Please contact IT support.")

    return True


# Configuration constants
STO_CONFIG = r''
SITE_URL = ""
SID = ""
BACKUP_PATH = 'scratch/pslv_cache/access'
SHAREPOINT_LIST = 'STO_Inventory'
USERBASE = 'pslv_users'
COST_CENTER = 'cost_center'
ACTION_HISTORY = 'action_history'
ADMIN = 'pslv_sto_partner_admins'
BACKUP_FILE_NAME = 'launcher.xlsx'
APP_DIR = 'scratch/PSLV_Apps'
LABEL_TEXT = 'Developed and Maintained by <strong>To, GrSEM India</strong>'
DETAILS = [
    (getpass.getuser(), 'license-id-50.png'),
    ('john Doe', 'license-user-64.png'),
    ('john.doe@jpmorgan.com', 'license-email-50.png'),
    ('Associate', 'license-job-50.png'),
    ('GFGEM, India', 'license-location-50.png')
]

LOB = ['AAMI', 'CIB-GEFT', 'CIB-MS&OPS', 'CORP', 'FFCGEFSA', 'GFSM CPN', 'GFSM STO']
STATUS = ['UAT', 'BETA', 'PROD']

# Form fields with corrected validation
FIELDS = [
    ('Solution_Item_Epic_ID', 'JIRA ID', 'Enter the JIRA ID', None, 'text', 'text', True),
    ('Solution_Name', 'Application Name', 'Enter the name of the application', None, 'text', 'text', True),
    ('Description', 'Application Description', 'Enter a brief description', None, 'text', 'text', True),
    ('Line_of_Business', 'Line of Business', 'Select line or department', LOB, 'dropdown', 'dropdown', False),
    ('AAMI_Lead_ID', 'IAMID ID', 'Enter the IAMID registration id', None, 'text', 'text', False),
    ('Version_Number', 'Version', 'Enter application version', None, 'text', 'version', True),
    ('Release_Date', 'Release Date', 'Enter last update date (YYYY-MM-DD)', None, 'text', 'date', True),
    ('Status', 'Release Environment', 'Enter application release status', STATUS, 'dropdown', 'dropdown', False),
    ('ApplicationExePath', 'Executable Path', 'Enter the full path to the executable', None, 'text', 'app', True),
    ('Developer_By', 'Developer', 'Enter Developer\'s SID', None, 'text', 'text', True),
    ('TechnologyUsed', 'Technology Stack', 'Enter technology stack details', None, 'text', 'text', True)
]

# Styling constants
UAT = '#ea7317'
PROD = '#006770'
BETA = '#2a8265'
# ============================================================================
# METHOD 1: Using Office365-REST-Python-Client Library (Popular Choice)
# ============================================================================

"""
Install: pip install Office365-REST-Python-Client
This is a popular third-party library specifically for SharePoint/Office 365
"""

from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential
import json

class SharePointClientLibrary:
    def __init__(self, site_url, username, password):
        self.site_url = site_url
        self.username = username
        self.password = password
        self.ctx = None
        
    def authenticate(self):
        """Authenticate using username/password"""
        try:
            # Method 1: Username/Password authentication
            credentials = UserCredential(self.username, self.password)
            self.ctx = ClientContext(self.site_url).with_credentials(credentials)
            
            # Test authentication
            web = self.ctx.web
            self.ctx.load(web)
            self.ctx.execute_query()
            
            print(f"✅ Connected to: {web.properties['Title']}")
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {str(e)}")
            return False
    
    def authenticate_with_app(self, client_id, client_secret):
        """Authenticate using app credentials"""
        try:
            from office365.runtime.auth.client_credential import ClientCredential
            credentials = ClientCredential(client_id, client_secret)
            self.ctx = ClientContext(self.site_url).with_credentials(credentials)
            
            # Test authentication
            web = self.ctx.web
            self.ctx.load(web)
            self.ctx.execute_query()
            
            print(f"✅ Connected to: {web.properties['Title']}")
            return True
            
        except Exception as e:
            print(f"❌ App authentication failed: {str(e)}")
            return False
    
    def get_lists(self):
        """Get all lists"""
        try:
            lists = self.ctx.web.lists
            self.ctx.load(lists)
            self.ctx.execute_query()
            
            print(f"✅ Found {len(lists)} lists:")
            for lst in lists:
                print(f"  - {lst.properties['Title']} (Items: {lst.properties['ItemCount']})")
            
            return lists
        except Exception as e:
            print(f"❌ Error getting lists: {str(e)}")
            return []
    
    def read_list_items(self, list_name):
        """Read items from a list"""
        try:
            target_list = self.ctx.web.lists.get_by_title(list_name)
            items = target_list.items
            self.ctx.load(items)
            self.ctx.execute_query()
            
            print(f"✅ Retrieved {len(items)} items from '{list_name}':")
            for item in items:
                print(f"  ID: {item.properties['Id']}, Title: {item.properties.get('Title', 'N/A')}")
            
            return items
        except Exception as e:
            print(f"❌ Error reading list items: {str(e)}")
            return []
    
    def create_list_item(self, list_name, item_data):
        """Create a new list item"""
        try:
            target_list = self.ctx.web.lists.get_by_title(list_name)
            new_item = target_list.add_item(item_data)
            self.ctx.execute_query()
            
            print(f"✅ Item created with ID: {new_item.properties['Id']}")
            return new_item
        except Exception as e:
            print(f"❌ Error creating item: {str(e)}")
            return None

# ============================================================================
# METHOD 2: Direct SharePoint REST API with Requests
# ============================================================================

import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET

class SharePointRESTAPI:
    def __init__(self, site_url, username, password):
        self.site_url = site_url.rstrip('/')
        self.username = username
        self.password = password
        self.auth_cookies = None
        self.form_digest = None
    
    def authenticate(self):
        """Authenticate and get required tokens"""
        try:
            # Get authentication cookies
            auth_url = f"{self.site_url}/_api/contextinfo"
            
            response = requests.post(
                auth_url,
                auth=HTTPBasicAuth(self.username, self.password),
                headers={'Accept': 'application/json;odata=verbose'}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.form_digest = data['d']['GetContextWebInformation']['FormDigestValue']
                self.auth_cookies = response.cookies
                print("✅ REST API authentication successful")
                return True
            else:
                print(f"❌ REST API authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ REST API authentication error: {str(e)}")
            return False
    
    def get_lists(self):
        """Get all lists using REST API"""
        try:
            url = f"{self.site_url}/_api/web/lists"
            headers = {
                'Accept': 'application/json;odata=verbose',
                'X-RequestDigest': self.form_digest
            }
            
            response = requests.get(url, headers=headers, cookies=self.auth_cookies)
            
            if response.status_code == 200:
                data = response.json()
                lists = data['d']['results']
                print(f"✅ Found {len(lists)} lists via REST API")
                for lst in lists:
                    print(f"  - {lst['Title']} (Items: {lst['ItemCount']})")
                return lists
            else:
                print(f"❌ Failed to get lists: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting lists: {str(e)}")
            return []
    
    def read_list_items(self, list_name):
        """Read items using REST API"""
        try:
            url = f"{self.site_url}/_api/web/lists/getbytitle('{list_name}')/items"
            headers = {
                'Accept': 'application/json;odata=verbose'
            }
            
            response = requests.get(url, headers=headers, cookies=self.auth_cookies)
            
            if response.status_code == 200:
                data = response.json()
                items = data['d']['results']
                print(f"✅ Retrieved {len(items)} items from '{list_name}' via REST API")
                return items
            else:
                print(f"❌ Failed to get items: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error reading items: {str(e)}")
            return []

# ============================================================================
# METHOD 3: Using SharePlum Library (Legacy SharePoint Support)
# ============================================================================

"""
Install: pip install shareplum
Good for both SharePoint Online and On-Premises
"""

from shareplum import Site, Office365
from shareplum.site import Version

class SharePointSharePlum:
    def __init__(self, site_url, username, password):
        self.site_url = site_url
        self.username = username
        self.password = password
        self.site = None
    
    def authenticate(self):
        """Authenticate using SharePlum"""
        try:
            # For SharePoint Online
            authcookie = Office365(self.site_url, username=self.username, password=self.password).GetCookies()
            self.site = Site(self.site_url, version=Version.v365, authcookie=authcookie)
            
            print("✅ SharePlum authentication successful")
            return True
            
        except Exception as e:
            print(f"❌ SharePlum authentication failed: {str(e)}")
            return False
    
    def get_lists(self):
        """Get all lists using SharePlum"""
        try:
            lists = self.site.GetListCollection()
            print(f"✅ Found {len(lists)} lists via SharePlum:")
            for lst in lists:
                print(f"  - {lst['Title']}")
            return lists
            
        except Exception as e:
            print(f"❌ Error getting lists: {str(e)}")
            return []
    
    def read_list_items(self, list_name):
        """Read items using SharePlum"""
        try:
            sp_list = self.site.List(list_name)
            items = sp_list.GetListItems()
            
            print(f"✅ Retrieved {len(items)} items from '{list_name}' via SharePlum")
            return items
            
        except Exception as e:
            print(f"❌ Error reading items: {str(e)}")
            return []

# ============================================================================
# METHOD 4: PowerShell Script (Alternative for Windows environments)
# ============================================================================

powershell_script = '''
# PowerShell approach using PnP PowerShell module
# Install: Install-Module -Name PnP.PowerShell

# Connect to SharePoint
Connect-PnPOnline -Url "https://site.company.com" -Interactive

# Get all lists
$lists = Get-PnPList
Write-Host "Found $($lists.Count) lists:"
foreach($list in $lists) {
    Write-Host "- $($list.Title) (Items: $($list.ItemCount))"
}

# Read items from a specific list
$listItems = Get-PnPListItem -List "Tasks"
Write-Host "Retrieved $($listItems.Count) items from Tasks list"
foreach($item in $listItems) {
    Write-Host "ID: $($item.Id), Title: $($item['Title'])"
}

# Create a new item
$newItem = @{
    'Title' = 'New Task from PowerShell'
    'Description' = 'Created via PnP PowerShell'
}
Add-PnPListItem -List "Tasks" -Values $newItem
Write-Host "✅ New item created successfully"

# Update an existing item
Set-PnPListItem -List "Tasks" -Identity 1 -Values @{'Title'='Updated Title'}
Write-Host "✅ Item updated successfully"
'''

# ============================================================================
# METHOD 5: Using Microsoft Graph SDK
# ============================================================================

"""
Install: pip install msgraph-core msgraph-sdk
More modern approach using Microsoft Graph
"""

from msgraph.graph_service_client import GraphServiceClient
from azure.identity import ClientSecretCredential

class SharePointGraphSDK:
    def __init__(self, tenant_id, client_id, client_secret):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.client = None
    
    def authenticate(self):
        """Authenticate using Graph SDK"""
        try:
            credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            scopes = ['https://graph.microsoft.com/.default']
            self.client = GraphServiceClient(credentials=credential, scopes=scopes)
            
            print("✅ Graph SDK authentication successful")
            return True
            
        except Exception as e:
            print(f"❌ Graph SDK authentication failed: {str(e)}")
            return False
    
    async def get_site_lists(self, hostname, site_path=""):
        """Get lists using Graph SDK"""
        try:
            site_id = f"{hostname}:/{site_path}" if site_path else hostname
            lists = await self.client.sites.by_site_id(site_id).lists.get()
            
            print(f"✅ Retrieved {len(lists.value)} lists via Graph SDK")
            for lst in lists.value:
                print(f"  - {lst.display_name}")
            
            return lists.value
            
        except Exception as e:
            print(f"❌ Error getting lists: {str(e)}")
            return []

# ============================================================================
# EXAMPLE USAGE FUNCTIONS
# ============================================================================

def example_office365_client():
    """Example using Office365-REST-Python-Client"""
    print("\n" + "="*60)
    print("METHOD 1: Office365-REST-Python-Client")
    print("="*60)
    
    sp = SharePointClientLibrary(
        "https://site.company.com",
        "username@company.com",
        "password"
    )
    
    if sp.authenticate():
        sp.get_lists()
        sp.read_list_items("Tasks")
        sp.create_list_item("Tasks", {"Title": "New Task from Python Client"})

def example_rest_api():
    """Example using direct REST API"""
    print("\n" + "="*60)
    print("METHOD 2: Direct SharePoint REST API")
    print("="*60)
    
    sp = SharePointRESTAPI(
        "https://site.company.com",
        "username@company.com",
        "password"
    )
    
    if sp.authenticate():
        sp.get_lists()
        sp.read_list_items("Tasks")

def example_shareplum():
    """Example using SharePlum"""
    print("\n" + "="*60)
    print("METHOD 3: SharePlum Library")
    print("="*60)
    
    sp = SharePointSharePlum(
        "https://site.company.com",
        "username@company.com",
        "password"
    )
    
    if sp.authenticate():
        sp.get_lists()
        sp.read_list_items("Tasks")

if __name__ == "__main__":
    print("SharePoint Online - Multiple Connection Methods")
    print("=" * 60)
    print("Choose your preferred method based on your requirements:")
    print("1. Office365-REST-Python-Client - Most popular, feature-rich")
    print("2. Direct REST API - Full control, custom implementation")
    print("3. SharePlum - Good for legacy SharePoint support")
    print("4. PowerShell PnP - For Windows environments")
    print("5. Microsoft Graph SDK - Modern, recommended for new projects")
    
    # Uncomment the method you want to test
    # example_office365_client()
    # example_rest_api()
    # example_shareplum()

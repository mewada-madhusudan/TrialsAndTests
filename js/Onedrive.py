"""
OneDrive for Business Access Test Script
Specifically designed for personal OneDrive sites and MSIS7068 troubleshooting
"""

import requests
import json
from msal import ConfidentialClientApplication, PublicClientApplication
import urllib.parse
from datetime import datetime
import re

class OneDriveAccessTester:
    def __init__(self):
        self.session = requests.Session()
        
    def extract_site_info(self, onedrive_url):
        """
        Extract tenant and user info from OneDrive URL
        """
        # Pattern: https://drive.companyname.com/personal/user_domain_com
        pattern = r'https://([^.]+)\.([^/]+)/personal/([^/]+)'
        match = re.search(pattern, onedrive_url)
        
        if match:
            subdomain = match.group(1)  # e.g., 'drive'
            domain = match.group(2)     # e.g., 'companyname.com'
            user_part = match.group(3)  # e.g., 'user_domain_com'
            
            # Convert user part back to email format
            user_email = user_part.replace('_', '.').replace('.', '@', 1)
            
            # Construct proper SharePoint URLs
            sharepoint_root = f"https://{subdomain.replace('drive', 'companyname')}.sharepoint.com"
            personal_site = f"{sharepoint_root}/personal/{user_part}"
            
            return {
                'tenant_domain': domain,
                'user_email': user_email,
                'sharepoint_root': sharepoint_root,
                'personal_site': personal_site,
                'user_part': user_part
            }
        return None
    
    def test_onedrive_permissions(self, access_token, site_info):
        """
        Test various OneDrive API endpoints to identify permission issues
        """
        print(f"\n📋 Testing OneDrive permissions for: {site_info['user_email']}")
        print("-" * 50)
        
        tests = [
            {
                'name': 'Site Access',
                'url': f"{site_info['personal_site']}/_api/web",
                'description': 'Basic site access'
            },
            {
                'name': 'Document Library',
                'url': f"{site_info['personal_site']}/_api/web/lists/getbytitle('Documents')",
                'description': 'Default Documents library'
            },
            {
                'name': 'List All Lists',
                'url': f"{site_info['personal_site']}/_api/web/lists",
                'description': 'All lists and libraries'
            },
            {
                'name': 'User Profile',
                'url': f"{site_info['sharepoint_root']}/_api/SP.UserProfiles.PeopleManager/GetMyProperties",
                'description': 'User profile information'
            },
            {
                'name': 'Site Users',
                'url': f"{site_info['personal_site']}/_api/web/siteusers",
                'description': 'Site user permissions'
            }
        ]
        
        results = {}
        
        for test in tests:
            print(f"\n🔍 Testing: {test['name']} ({test['description']})")
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json;odata=verbose',
                'Content-Type': 'application/json'
            }
            
            try:
                response = requests.get(test['url'], headers=headers)
                
                if response.status_code == 200:
                    print(f"✅ SUCCESS: {test['name']}")
                    results[test['name']] = 'SUCCESS'
                elif response.status_code == 403:
                    print(f"❌ FORBIDDEN (403): {test['name']}")
                    print(f"   This indicates insufficient permissions")
                    results[test['name']] = 'FORBIDDEN'
                elif response.status_code == 404:
                    print(f"⚠️  NOT FOUND (404): {test['name']}")
                    print(f"   Resource doesn't exist or URL is incorrect")
                    results[test['name']] = 'NOT_FOUND'
                else:
                    print(f"❌ ERROR ({response.status_code}): {test['name']}")
                    print(f"   Response: {response.text[:200]}...")
                    results[test['name']] = f'ERROR_{response.status_code}'
                    
            except Exception as e:
                print(f"❌ EXCEPTION: {test['name']} - {str(e)}")
                results[test['name']] = 'EXCEPTION'
        
        return results
    
    def test_graph_api_access(self, access_token, site_info):
        """
        Test Microsoft Graph API access (alternative to SharePoint REST API)
        """
        print(f"\n🌐 Testing Microsoft Graph API access")
        print("-" * 50)
        
        # Extract user principal name
        user_email = site_info['user_email']
        
        tests = [
            {
                'name': 'User Drive',
                'url': f"https://graph.microsoft.com/v1.0/users/{user_email}/drive",
                'description': 'User OneDrive access via Graph'
            },
            {
                'name': 'Drive Items',
                'url': f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/root/children",
                'description': 'Files in root folder'
            },
            {
                'name': 'My Drive',
                'url': "https://graph.microsoft.com/v1.0/me/drive",
                'description': 'Current user drive (if accessing own drive)'
            }
        ]
        
        results = {}
        
        for test in tests:
            print(f"\n🔍 Testing Graph: {test['name']}")
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
            
            try:
                response = requests.get(test['url'], headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ SUCCESS: {test['name']}")
                    if 'name' in data:
                        print(f"   Drive Name: {data['name']}")
                    results[test['name']] = 'SUCCESS'
                elif response.status_code == 403:
                    print(f"❌ FORBIDDEN (403): {test['name']}")
                    results[test['name']] = 'FORBIDDEN'
                elif response.status_code == 404:
                    print(f"⚠️  NOT FOUND (404): {test['name']}")
                    results[test['name']] = 'NOT_FOUND'
                else:
                    print(f"❌ ERROR ({response.status_code}): {test['name']}")
                    print(f"   Response: {response.text[:200]}...")
                    results[test['name']] = f'ERROR_{response.status_code}'
                    
            except Exception as e:
                print(f"❌ EXCEPTION: {test['name']} - {str(e)}")
                results[test['name']] = 'EXCEPTION'
        
        return results
    
    def get_token_with_onedrive_scopes(self, tenant_id, client_id, client_secret=None, username=None, password=None):
        """
        Get access token with proper OneDrive/SharePoint scopes
        """
        print(f"\n🔐 Acquiring token with OneDrive scopes...")
        
        # Define comprehensive scopes
        scopes = [
            "https://graph.microsoft.com/Files.ReadWrite.All",
            "https://graph.microsoft.com/Sites.ReadWrite.All", 
            "https://graph.microsoft.com/User.Read"
        ]
        
        sharepoint_scopes = [
            "https://companyname.sharepoint.com/.default"  # Replace with your tenant
        ]
        
        if client_secret:
            # App-only flow
            print("Using app-only authentication...")
            app = ConfidentialClientApplication(
                client_id=client_id,
                client_credential=client_secret,
                authority=f"https://login.microsoftonline.com/{tenant_id}"
            )
            
            result = app.acquire_token_for_client(scopes=scopes)
            
        elif username and password:
            # Username/password flow
            print("Using username/password authentication...")
            app = PublicClientApplication(
                client_id=client_id,
                authority=f"https://login.microsoftonline.com/{tenant_id}"
            )
            
            result = app.acquire_token_by_username_password(
                username=username,
                password=password,
                scopes=scopes
            )
        else:
            # Interactive flow
            print("Using interactive authentication...")
            app = PublicClientApplication(
                client_id=client_id,
                authority=f"https://login.microsoftonline.com/{tenant_id}"
            )
            
            result = app.acquire_token_interactive(scopes=scopes)
        
        if "access_token" in result:
            print("✅ Token acquired successfully!")
            return result['access_token']
        else:
            print("❌ Failed to acquire token!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"Description: {result.get('error_description', 'No description')}")
            return None
    
    def diagnose_msis7068_error(self, onedrive_url, access_token):
        """
        Specific diagnosis for MSIS7068 errors
        """
        print(f"\n🔍 MSIS7068 Error Diagnosis")
        print("=" * 60)
        
        site_info = self.extract_site_info(onedrive_url)
        if not site_info:
            print("❌ Could not parse OneDrive URL format")
            return
        
        print(f"Parsed URL Information:")
        print(f"  Tenant Domain: {site_info['tenant_domain']}")
        print(f"  User Email: {site_info['user_email']}")
        print(f"  Personal Site: {site_info['personal_site']}")
        
        # Common MSIS7068 causes and checks
        print(f"\n📋 MSIS7068 Common Causes Checklist:")
        print("1. ❓ Insufficient permissions (most common)")
        print("2. ❓ Accessing another user's OneDrive without proper permissions")
        print("3. ❓ App registration lacks required API permissions")
        print("4. ❓ Conditional Access policies blocking access")
        print("5. ❓ User's OneDrive not provisioned or disabled")
        print("6. ❓ Incorrect tenant or URL format")
        
        # Test different approaches
        sharepoint_results = self.test_onedrive_permissions(access_token, site_info)
        graph_results = self.test_graph_api_access(access_token, site_info)
        
        # Provide recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if any('SUCCESS' in result for result in sharepoint_results.values()):
            print("✅ SharePoint REST API is working - permission issue is specific to certain resources")
        elif any('SUCCESS' in result for result in graph_results.values()):
            print("✅ Microsoft Graph API is working - consider using Graph instead of SharePoint REST")
            print("   Graph API often has better permission handling for OneDrive access")
        else:
            print("❌ Both APIs failing - likely authentication or permission configuration issue")
            
        print(f"\n🔧 TROUBLESHOOTING STEPS:")
        print("1. Verify app permissions include:")
        print("   - Files.ReadWrite.All (for Graph API)")
        print("   - Sites.FullControl.All (for SharePoint API)")
        print("   - User.Read (for user context)")
        
        print("2. Check if accessing your own OneDrive vs someone else's:")
        print("   - Own OneDrive: Use /me/drive endpoints")
        print("   - Other user's: Requires admin permissions or sharing")
        
        print("3. Verify OneDrive provisioning:")
        print("   - User must have accessed OneDrive at least once")
        print("   - Check OneDrive license assignment")
        
        print("4. Test with Graph API instead of SharePoint REST:")
        print("   - Graph API: https://graph.microsoft.com/v1.0/me/drive")
        print("   - Often more reliable for OneDrive access")
    
    def run_comprehensive_test(self, config):
        """
        Run comprehensive OneDrive access test
        """
        print("🚀 Starting OneDrive for Business Access Test")
        print("=" * 60)
        
        # Extract site information
        site_info = self.extract_site_info(config['onedrive_url'])
        if not site_info:
            print("❌ Invalid OneDrive URL format")
            return
        
        print(f"Target OneDrive: {config['onedrive_url']}")
        print(f"Extracted User: {site_info['user_email']}")
        
        # Get access token
        access_token = self.get_token_with_onedrive_scopes(
            config['tenant_id'],
            config['client_id'],
            config.get('client_secret'),
            config.get('username'),
            config.get('password')
        )
        
        if not access_token:
            print("❌ Could not acquire access token. Cannot proceed with tests.")
            return
        
        # Run diagnosis
        self.diagnose_msis7068_error(config['onedrive_url'], access_token)


def main():
    """
    Main function - configure your OneDrive access test
    """
    
    # ⚠️  CONFIGURE THESE SETTINGS
    config = {
        # Required
        'tenant_id': 'your-tenant-id',  # or tenant.onmicrosoft.com
        'client_id': 'your-client-id',
        'onedrive_url': 'https://drive.companyname.com/personal/mail-id',  # Your actual OneDrive URL
        
        # Choose ONE authentication method:
        
        # Option 1: App-only (recommended for service accounts)
        'client_secret': 'your-client-secret',
        
        # Option 2: User credentials (for testing)
        # 'username': 'user@tenant.onmicrosoft.com',
        # 'password': 'password',
        
        # Option 3: Interactive (uncomment to use)
        # Leave both username/password and client_secret empty for interactive
    }
    
    # Validate configuration
    if not config.get('tenant_id') or config['tenant_id'].startswith('your-'):
        print("❌ Please configure your tenant_id in the config")
        return
    
    if not config.get('client_id') or config['client_id'].startswith('your-'):
        print("❌ Please configure your client_id in the config")
        return
    
    if not config.get('onedrive_url') or 'mail-id' in config['onedrive_url']:
        print("❌ Please configure your actual OneDrive URL")
        print("Example: https://drive.companyname.com/personal/john_doe_company_com")
        return
    
    # Run the test
    tester = OneDriveAccessTester()
    tester.run_comprehensive_test(config)


if __name__ == "__main__":
    main()


# ADDITIONAL SETUP FOR ONEDRIVE ACCESS:
"""
Azure AD App Registration Permissions for OneDrive:

Microsoft Graph (Recommended):
- Files.ReadWrite.All (Application/Delegated)
- Sites.ReadWrite.All (Application/Delegated) 
- User.Read (Delegated)

SharePoint (Alternative):
- Sites.FullControl.All (Application)
- AllSites.FullControl (Delegated)

IMPORTANT NOTES:
1. OneDrive URLs use format: https://tenant.sharepoint.com/personal/user_domain_com
2. MSIS7068 often indicates permission issues or unprovisioned OneDrive
3. Graph API generally has better OneDrive support than SharePoint REST API
4. Accessing another user's OneDrive requires admin-level permissions
5. User must have accessed their OneDrive at least once for it to be provisioned
"""

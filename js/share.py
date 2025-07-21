import requests

# Replace with your values
tenant_id = "your-tenant-id"
client_id = "your-client-id"
username = "your-username@company.com"
password = "your-password"

# Resource you want access to (e.g., Microsoft Graph, SharePoint)
scope = "https://graph.microsoft.com/.default"
# or for SharePoint Online:
# scope = "https://yourtenant.sharepoint.com/.default"

# Token endpoint
url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

# ROPC grant type
data = {
    'client_id': client_id,
    'username': username,
    'password': password,
    'grant_type': 'password',
    'scope': scope
}

headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}

response = requests.post(url, data=data, headers=headers)

if response.status_code == 200:
    token = response.json()
    print("Access Token:\n", token['access_token'])
else:
    print("Failed to obtain token:")
    print(response.status_code, response.text)

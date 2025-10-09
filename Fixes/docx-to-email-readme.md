# DOCX to Outlook Email with Inline Images

Complete guide for converting DOCX files to HTML and sending them via Outlook Graph API with properly embedded inline images.

## Table of Contents
- [Prerequisites](#prerequisites)
- [The Problem](#the-problem)
- [Solution Overview](#solution-overview)
- [Option 1: pypandoc (Recommended)](#option-1-pypandoc-recommended)
- [Option 2: docx2html](#option-2-docx2html)
- [Option 3: mammoth (Images Only)](#option-3-mammoth-images-only)
- [Option 4: aspose-words (Commercial)](#option-4-aspose-words-commercial)
- [Basic Email Sending (No DOCX)](#basic-email-sending-no-docx)
- [Comparison Table](#comparison-table)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

```bash
# Install required packages
pip install requests beautifulsoup4

# For specific options, install:
pip install pypandoc        # Option 1
pip install docx2html       # Option 2
pip install mammoth         # Option 3
pip install aspose-words    # Option 4 (Commercial)
```

**Additional Requirements:**
- Microsoft Graph API access token
- Outlook/Microsoft 365 account
- For pypandoc: Install pandoc system binary ([Download here](https://pandoc.org/installing.html))

---

## The Problem

When converting DOCX to HTML and sending via Outlook Graph API:
1. **mammoth**: Images work but loses formatting (tables, borders, colors)
2. **Direct attachment**: Images show as attachments, not inline
3. **Outlook Desktop**: Blocks images even when web/mobile works

---

## Solution Overview

All solutions follow this pattern:
1. Convert DOCX to HTML
2. Extract images from DOCX
3. Encode images as base64
4. Replace image `src` with `cid:` references
5. Send via Graph API with inline attachments

---

## Option 1: pypandoc (Recommended)

**Pros:** Free, excellent formatting preservation, handles tables/borders/colors well

**Cons:** Requires pandoc system installation

```python
import pypandoc
import os
import base64
from bs4 import BeautifulSoup
import shutil
import requests
import json

def send_docx_email_pypandoc(docx_path, recipient_email, subject, access_token):
    """
    Convert DOCX to HTML using pypandoc and send via Outlook Graph API
    """
    # Create temp directory for extracted media
    media_dir = "temp_media"
    os.makedirs(media_dir, exist_ok=True)
    
    try:
        # Convert DOCX to HTML
        html_content = pypandoc.convert_file(
            docx_path,
            'html',
            extra_args=[f'--extract-media={media_dir}']
        )
        
        # Process images from media directory
        attachments = []
        soup = BeautifulSoup(html_content, 'html.parser')
        image_counter = 1
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            
            if src:
                # Build full path
                image_path = os.path.join(os.getcwd(), src)
                
                if os.path.exists(image_path):
                    with open(image_path, 'rb') as img_file:
                        image_data = base64.b64encode(img_file.read()).decode('utf-8')
                    
                    content_id = f"image{image_counter}@contoso.com"
                    
                    # Determine content type
                    ext = src.lower().split('.')[-1]
                    content_type_map = {
                        'png': 'image/png',
                        'jpg': 'image/jpeg',
                        'jpeg': 'image/jpeg',
                        'gif': 'image/gif',
                        'bmp': 'image/bmp'
                    }
                    content_type = content_type_map.get(ext, 'image/png')
                    
                    attachments.append({
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": os.path.basename(src),
                        "contentType": content_type,
                        "contentId": content_id,
                        "isInline": True,
                        "contentBytes": image_data
                    })
                    
                    img['src'] = f"cid:{content_id}"
                    image_counter += 1
        
        updated_html = str(soup)
        
        # Send email
        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": updated_html
                },
                "toRecipients": [{
                    "emailAddress": {"address": recipient_email}
                }],
                "attachments": attachments
            }
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = 'https://graph.microsoft.com/v1.0/me/sendMail'
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        return response.status_code, response.text
        
    finally:
        # Cleanup
        if os.path.exists(media_dir):
            shutil.rmtree(media_dir)

# Usage
access_token = "your_access_token_here"
status, response = send_docx_email_pypandoc(
    "document.docx",
    "recipient@company.com",
    "Document with Formatting",
    access_token
)
print(f"Status: {status}")
print(f"Response: {response}")
```

---

## Option 2: docx2html

**Pros:** Pure Python, no external dependencies, decent formatting

**Cons:** Less accurate than pypandoc for complex documents

```python
from docx2html import convert
import base64
from bs4 import BeautifulSoup
import os
import zipfile
import tempfile
import shutil
import requests
import json

def extract_images_from_docx(docx_path):
    """Extract images from DOCX file"""
    images = {}
    temp_dir = tempfile.mkdtemp()
    
    # DOCX is a ZIP file, extract it
    with zipfile.ZipFile(docx_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # Find all images in word/media/
    media_path = os.path.join(temp_dir, 'word', 'media')
    if os.path.exists(media_path):
        for filename in os.listdir(media_path):
            filepath = os.path.join(media_path, filename)
            with open(filepath, 'rb') as img_file:
                images[filename] = base64.b64encode(img_file.read()).decode('utf-8')
    
    return images, temp_dir

def send_docx_email_docx2html(docx_path, recipient_email, subject, access_token):
    """
    Convert DOCX to HTML using docx2html and send via Outlook Graph API
    """
    # Convert DOCX to HTML
    html_content = convert(docx_path)
    
    # Extract images
    images_data, temp_dir = extract_images_from_docx(docx_path)
    
    try:
        # Parse and replace image sources
        soup = BeautifulSoup(html_content, 'html.parser')
        attachments = []
        image_counter = 1
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            
            # Extract filename from src (e.g., "word/media/image1.png" -> "image1.png")
            if 'media/' in src:
                filename = src.split('media/')[-1]
            else:
                filename = os.path.basename(src)
            
            if filename in images_data:
                content_id = f"image{image_counter}@contoso.com"
                
                # Determine content type
                ext = filename.lower().split('.')[-1]
                content_type_map = {
                    'png': 'image/png',
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'gif': 'image/gif',
                    'bmp': 'image/bmp'
                }
                content_type = content_type_map.get(ext, 'image/png')
                
                attachments.append({
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": filename,
                    "contentType": content_type,
                    "contentId": content_id,
                    "isInline": True,
                    "contentBytes": images_data[filename]
                })
                
                img['src'] = f"cid:{content_id}"
                image_counter += 1
        
        updated_html = str(soup)
        
        # Send email
        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": updated_html
                },
                "toRecipients": [{
                    "emailAddress": {"address": recipient_email}
                }],
                "attachments": attachments
            }
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = 'https://graph.microsoft.com/v1.0/me/sendMail'
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        return response.status_code, response.text
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

# Usage
access_token = "your_access_token_here"
status, response = send_docx_email_docx2html(
    "document.docx",
    "recipient@company.com",
    "Document with Formatting",
    access_token
)
print(f"Status: {status}")
print(f"Response: {response}")
```

---

## Option 3: mammoth (Images Only)

**Pros:** Clean HTML output, good for simple documents

**Cons:** Loses formatting (tables, borders, colors)

```python
import mammoth
import base64
import requests
import json

def send_docx_email_mammoth(docx_path, recipient_email, subject, access_token):
    """
    Convert DOCX to HTML using mammoth and send via Outlook Graph API
    Note: This loses table formatting but preserves images
    """
    images_dict = {}
    
    def image_handler(image):
        """Custom image handler for mammoth"""
        with image.open() as image_bytes:
            encoded = base64.b64encode(image_bytes.read()).decode('utf-8')
            content_id = f"image_{id(image)}@contoso.com"
            
            images_dict[content_id] = {
                "contentBytes": encoded,
                "contentType": image.content_type,
                "name": f"image_{len(images_dict)}.{image.content_type.split('/')[-1]}"
            }
            
            return {"src": f"cid:{content_id}"}
    
    # Convert DOCX to HTML with custom image handler
    with open(docx_path, "rb") as docx_file:
        result = mammoth.convert_to_html(
            docx_file,
            convert_image=mammoth.images.img_element(image_handler)
        )
        html_content = result.value
    
    # Build attachments from images_dict
    attachments = [
        {
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": data["name"],
            "contentType": data["contentType"],
            "contentId": cid,
            "isInline": True,
            "contentBytes": data["contentBytes"]
        }
        for cid, data in images_dict.items()
    ]
    
    # Send email
    payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": html_content
            },
            "toRecipients": [{
                "emailAddress": {"address": recipient_email}
            }],
            "attachments": attachments
        }
    }
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    url = 'https://graph.microsoft.com/v1.0/me/sendMail'
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    return response.status_code, response.text

# Usage
access_token = "your_access_token_here"
status, response = send_docx_email_mammoth(
    "document.docx",
    "recipient@company.com",
    "Simple Document",
    access_token
)
print(f"Status: {status}")
print(f"Response: {response}")
```

---

## Option 4: aspose-words (Commercial)

**Pros:** Best formatting preservation, handles complex layouts perfectly

**Cons:** Requires paid license

```python
import aspose.words as aw
import base64
import os
from bs4 import BeautifulSoup
import requests
import json

def send_docx_email_aspose(docx_path, recipient_email, subject, access_token):
    """
    Convert DOCX to HTML using Aspose.Words and send via Outlook Graph API
    Note: Requires Aspose.Words license
    """
    # Convert DOCX to HTML
    doc = aw.Document(docx_path)
    
    # Save with options to keep formatting
    save_options = aw.saving.HtmlSaveOptions()
    save_options.export_images_as_base64 = False
    save_options.export_fonts_as_base64 = True
    save_options.css_style_sheet_type = aw.saving.CssStyleSheetType.INLINE
    
    # Save to HTML
    output_path = "temp_output.html"
    images_folder = "temp_images"
    save_options.images_folder = images_folder
    
    doc.save(output_path, save_options)
    
    try:
        # Read generated HTML
        with open(output_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Process images
        soup = BeautifulSoup(html_content, 'html.parser')
        attachments = []
        image_counter = 1
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            
            if src and os.path.exists(src):
                with open(src, 'rb') as img_file:
                    image_data = base64.b64encode(img_file.read()).decode('utf-8')
                
                content_id = f"image{image_counter}@contoso.com"
                
                ext = src.lower().split('.')[-1]
                content_type_map = {
                    'png': 'image/png',
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'gif': 'image/gif'
                }
                content_type = content_type_map.get(ext, 'image/png')
                
                attachments.append({
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": os.path.basename(src),
                    "contentType": content_type,
                    "contentId": content_id,
                    "isInline": True,
                    "contentBytes": image_data
                })
                
                img['src'] = f"cid:{content_id}"
                image_counter += 1
        
        updated_html = str(soup)
        
        # Send email
        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": updated_html
                },
                "toRecipients": [{
                    "emailAddress": {"address": recipient_email}
                }],
                "attachments": attachments
            }
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = 'https://graph.microsoft.com/v1.0/me/sendMail'
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        return response.status_code, response.text
        
    finally:
        # Cleanup
        if os.path.exists(output_path):
            os.remove(output_path)
        if os.path.exists(images_folder):
            import shutil
            shutil.rmtree(images_folder)

# Usage
access_token = "your_access_token_here"
status, response = send_docx_email_aspose(
    "document.docx",
    "recipient@company.com",
    "Professional Document",
    access_token
)
print(f"Status: {status}")
print(f"Response: {response}")
```

---

## Basic Email Sending (No DOCX)

If you just want to send HTML emails with inline images (no DOCX conversion):

```python
import requests
import json
import base64

def send_html_email_with_images(html_content, image_paths, recipient_email, subject, access_token):
    """
    Send HTML email with inline images using Outlook Graph API
    
    Args:
        html_content: HTML string with <img src="cid:imageX@domain.com"> references
        image_paths: Dict mapping content_ids to file paths {"image1@domain.com": "path/to/image.png"}
        recipient_email: Recipient's email address
        subject: Email subject
        access_token: Microsoft Graph API access token
    """
    attachments = []
    
    for content_id, image_path in image_paths.items():
        with open(image_path, 'rb') as img_file:
            image_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        # Determine content type from extension
        ext = image_path.lower().split('.')[-1]
        content_type_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'bmp': 'image/bmp'
        }
        content_type = content_type_map.get(ext, 'image/png')
        
        attachments.append({
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": os.path.basename(image_path),
            "contentType": content_type,
            "contentId": content_id,
            "isInline": True,
            "contentBytes": image_data
        })
    
    payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": html_content
            },
            "toRecipients": [{
                "emailAddress": {"address": recipient_email}
            }],
            "attachments": attachments
        }
    }
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    url = 'https://graph.microsoft.com/v1.0/me/sendMail'
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    return response.status_code, response.text

# Usage Example
html = """
<html>
    <body>
        <h1>Hello!</h1>
        <p>Here's an image:</p>
        <img src="cid:logo@company.com" alt="Logo">
        <p>And another:</p>
        <img src="cid:banner@company.com" alt="Banner">
    </body>
</html>
"""

images = {
    "logo@company.com": "images/logo.png",
    "banner@company.com": "images/banner.jpg"
}

access_token = "your_access_token_here"
status, response = send_html_email_with_images(
    html,
    images,
    "recipient@company.com",
    "Test Email with Images",
    access_token
)
print(f"Status: {status}")
```

---

## Comparison Table

| Library | Tables | Borders | Colors | Images | Complex Layouts | Cost | External Dependencies |
|---------|--------|---------|--------|--------|-----------------|------|----------------------|
| **pypandoc** | ✅ | ✅ | ✅ | ✅ | ⚠️ | Free | Pandoc binary |
| **docx2html** | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | Free | None |
| **mammoth** | ❌ | ❌ | ⚠️ | ✅ | ❌ | Free | None |
| **aspose-words** | ✅ | ✅ | ✅ | ✅ | ✅ | Paid | License |

**Legend:**
- ✅ Full support
- ⚠️ Partial support
- ❌ Not supported

---

## Troubleshooting

### Images not showing in Outlook Desktop

**Check Trust Center Settings:**
1. Open Outlook Desktop
2. File → Options → Trust Center → Trust Center Settings
3. Automatic Download → Uncheck "Don't download pictures automatically"

### Images showing as attachments

**Problem:** `isInline` not set to `True`

```python
# Wrong
"isInline": "true"  # String

# Correct
"isInline": True     # Python boolean
```

### CID mismatch error

**Problem:** Content-ID in HTML doesn't match attachment contentId

```python
# HTML must match exactly:
html: '<img src="cid:image1@company.com">'
attachment: "contentId": "image1@company.com"

# Common mistakes:
html: '<img src="cid:image1">'           # Missing @domain
attachment: "contentId": "image1@company.com"  # Mismatch!
```

### Base64 encoding error

```python
# Wrong - bytes object
image_data = base64.b64encode(img_file.read())

# Correct - string
image_data = base64.b64encode(img_file.read()).decode('utf-8')
```

### Import error with pypandoc

```bash
# Install pandoc system-wide first:
# Ubuntu/Debian
sudo apt-get install pandoc

# macOS
brew install pandoc

# Windows
# Download from https://pandoc.org/installing.html

# Then install Python package
pip install pypandoc
```

### Graph API authentication

```python
# Get access token using MSAL
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(
    client_id="your_client_id",
    client_credential="your_client_secret",
    authority="https://login.microsoftonline.com/your_tenant_id"
)

result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
access_token = result['access_token']
```

---

## Best Practices

1. **Always use unique Content-IDs** with domain suffix (e.g., `image1@company.com`)
2. **Set `isInline: True`** for all inline attachments
3. **Match CID references exactly** between HTML and attachments
4. **Clean up temporary files** after sending
5. **Handle errors gracefully** with try-except blocks
6. **Test with small documents first** before processing large files
7. **Validate HTML output** before sending

---

## License

This code is provided as-is for educational purposes. Modify as needed for your use case.

## Contributing

Feel free to submit issues or pull requests for improvements!
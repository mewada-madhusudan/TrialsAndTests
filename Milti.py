import re
import base64
from bs4 import BeautifulSoup
import mammoth  # or your conversion library

# Step 1: Convert DOCX to HTML
with open("document.docx", "rb") as docx_file:
    result = mammoth.convert_to_html(docx_file)
    html_content = result.value

# Step 2: Parse HTML and extract images
soup = BeautifulSoup(html_content, 'html.parser')
images = soup.find_all('img')

attachments = []
image_counter = 1

# Step 3: Process each image
for img in images:
    src = img.get('src', '')
    
    # Handle different src formats
    if src:
        # Generate unique content ID
        content_id = f"image{image_counter}@contoso.com"
        
        # Read the actual image file
        # Adjust this based on where your images are stored
        try:
            # If src is a file path
            if src.startswith('file:///'):
                image_path = src.replace('file:///', '')
            elif src.startswith('word/media/'):
                # Extract from DOCX structure
                image_path = src
            else:
                image_path = src
            
            # Read and encode image
            with open(image_path, 'rb') as img_file:
                image_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Determine content type
            if image_path.lower().endswith('.png'):
                content_type = 'image/png'
            elif image_path.lower().endswith(('.jpg', '.jpeg')):
                content_type = 'image/jpeg'
            elif image_path.lower().endswith('.gif'):
                content_type = 'image/gif'
            else:
                content_type = 'image/png'
            
            # Create attachment
            attachments.append({
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": f"image{image_counter}.png",
                "contentType": content_type,
                "contentId": content_id,
                "isInline": True,
                "contentBytes": image_data
            })
            
            # Replace src with CID
            img['src'] = f"cid:{content_id}"
            
            image_counter += 1
            
        except Exception as e:
            print(f"Error processing image {src}: {e}")

# Step 4: Get updated HTML
updated_html = str(soup)

# Step 5: Send email
payload = {
    "message": {
        "subject": "Document with images",
        "body": {
            "contentType": "HTML",
            "content": updated_html
        },
        "toRecipients": [{
            "emailAddress": {"address": "your-email@company.com"}
        }],
        "attachments": attachments
    }
}

response = requests.post(url, headers=headers, data=json.dumps(payload))

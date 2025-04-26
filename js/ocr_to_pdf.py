from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json

def create_pdf_from_ocr(ocr_results, output_path, image_height=None, page_size=letter):
    """
    Create a PDF from OCR results with improved positioning.
    
    Args:
        ocr_results: List of dictionaries with 'text', 'confidence', and 'bounding_box'
        output_path: Path to save the PDF
        image_height: Height of the original image (needed for y-coordinate conversion)
        page_size: Size of the PDF page (default is letter)
    """
    page_width, page_height = page_size
    
    # If image_height is not provided, estimate it from bounding boxes
    if image_height is None:
        max_y = 0
        for item in ocr_results:
            for point in item['bounding_box']:
                max_y = max(max_y, point[1])
        image_height = max_y + 50  # Add some margin
    
    # Create PDF canvas
    c = canvas.Canvas(output_path, pagesize=page_size)
    
    # Optional: Register a font that supports a wide range of characters
    # pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
    
    # Sort text blocks by y-coordinate (top to bottom)
    sorted_results = sorted(ocr_results, key=lambda x: x['bounding_box'][0][1])
    
    for item in sorted_results:
        text = item['text']
        bbox = item['bounding_box']
        
        # Calculate text position
        # Use top-left corner as reference point
        x = bbox[0][0]
        
        # Convert y-coordinate from image space to PDF space
        # In image, y=0 is at top; in PDF, y=0 is at bottom
        y = page_height - (bbox[0][1] * page_height / image_height)
        
        # Calculate width and height of the text box
        width = max(bbox[1][0] - bbox[0][0], bbox[2][0] - bbox[3][0])
        height = max(bbox[3][1] - bbox[0][1], bbox[2][1] - bbox[1][1])
        
        # Calculate font size based on height
        font_size = height * 0.75  # Adjust this factor as needed
        font_size = max(6, min(font_size, 72))  # Limit font size to reasonable range
        
        # Set font
        c.setFont("Helvetica", font_size)
        
        # Draw text
        c.drawString(x, y, text)
        
        # Optional: Draw bounding box for debugging
        # c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Light gray
        # c.rect(x, y - height, width, height, stroke=1, fill=0)
    
    c.save()

# Example usage
ocr_results = [
    {
        "text": "Hello World",
        "confidence": 0.95,
        "bounding_box": [[100, 100], [200, 100], [200, 120], [100, 120]]
    },
    {
        "text": "OCR Example",
        "confidence": 0.92,
        "bounding_box": [[150, 150], [250, 150], [250, 170], [150, 170]]
    }
]

# Use this if you know the image height
create_pdf_from_ocr(ocr_results, "ocr_output.pdf", image_height=1000)

# Or let the function estimate the image height
# create_pdf_from_ocr(ocr_results, "ocr_output.pdf")

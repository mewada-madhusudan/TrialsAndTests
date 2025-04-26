from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import json

def create_pdf_from_ocr(ocr_results, output_path, page_width=612, page_height=792):
    """
    Create a PDF from OCR results.
    
    Args:
        ocr_results: List of dictionaries with 'text', 'confidence', and 'bounding_box'
        output_path: Path to save the PDF
        page_width: Width of the PDF page (default is letter width in points)
        page_height: Height of the PDF page (default is letter height in points)
    """
    c = canvas.Canvas(output_path, pagesize=(page_width, page_height))
    
    for item in ocr_results:
        text = item['text']
        # confidence = item['confidence']  # Uncomment if you want to use confidence
        bbox = item['bounding_box']
        
        # Calculate text position
        # OCR usually gives coordinates in [x0, y0, x1, y1, x2, y2, x3, y3] format
        # where points are clockwise from top-left
        # For simplicity, we'll use the top-left point (x0, y0) as reference
        x = bbox[0][0]
        
        # PDF coordinates start from bottom, but image coordinates usually start from top
        # So we need to flip the y-coordinate
        y = page_height - bbox[0][1]
        
        # Set font size based on bounding box height
        # This is an approximation
        height = abs(bbox[0][1] - bbox[2][1])
        font_size = height * 0.8  # Adjust this factor as needed
        
        c.setFont("Helvetica", font_size)
        c.drawString(x, y, text)
    
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

create_pdf_from_ocr(ocr_results, "ocr_output.pdf")

import os
import json
import requests
import fitz  # PyMuPDF
import io
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class PDFProcessor:
    def __init__(self, llm_api_url=None, output_dir="editable_pdfs"):
        """
        Initialize the PDF processor.
        
        Args:
            llm_api_url (str, optional): URL for the LLM API service for text extraction.
            output_dir (str, optional): Directory to save output files.
        """
        self.llm_api_url = llm_api_url
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def extract_images_from_pdf(self, pdf_path):
        """
        Extract images from a PDF file.
        
        Args:
            pdf_path (str): Path to the PDF file.
            
        Returns:
            list: List of extracted images as PIL Image objects.
        """
        # Open the PDF file
        pdf_document = fitz.open(pdf_path)
        images = []
        
        # Iterate through each page
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            
            # Get page as an image
            pix = page.get_pixmap(alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
            
            print(f"Processed page {page_num + 1}/{len(pdf_document)}")
        
        pdf_document.close()
        return images
    
    def convert_pdf_to_images(self, pdf_path, dpi=300):
        """
        Convert PDF to images using pdf2image for better quality.
        
        Args:
            pdf_path (str): Path to the PDF file.
            dpi (int): DPI for image conversion quality.
            
        Returns:
            list: List of PIL Image objects.
        """
        try:
            print(f"Converting PDF to images: {pdf_path}")
            images = convert_from_path(pdf_path, dpi=dpi)
            print(f"Converted {len(images)} pages to images")
            return images
        except Exception as e:
            print(f"Error converting PDF to images: {e}")
            # Fallback to PyMuPDF method
            return self.extract_images_from_pdf(pdf_path)
    
    def extract_text_with_ocr(self, image):
        """
        Extract text from an image using Tesseract OCR.
        
        Args:
            image (PIL.Image): Input image.
            
        Returns:
            str: Extracted text.
        """
        try:
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""
    
    def extract_text_with_llm(self, image):
        """
        Extract text from an image using the LLM API.
        
        Args:
            image (PIL.Image): Input image.
            
        Returns:
            str: Extracted text.
        """
        if not self.llm_api_url:
            return self.extract_text_with_ocr(image)
        
        try:
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Send image to LLM API
            files = {'image': ('image.png', img_byte_arr, 'image/png')}
            response = requests.post(self.llm_api_url, files=files)
            
            if response.status_code == 200:
                data = response.json()
                # Extract text based on the format you provided
                if "message" in data:
                    message = data["message"]
                    if "```" in message:
                        # Extract text between triple backticks
                        start = message.find("```") + 3
                        end = message.rfind("```")
                        if start < end:
                            extracted_text = message[start:end].strip()
                            return extracted_text
                return data.get("message", "")
            else:
                print(f"LLM API Error: {response.status_code}")
                return self.extract_text_with_ocr(image)
        except Exception as e:
            print(f"LLM API Error: {e}")
            return self.extract_text_with_ocr(image)
    
    def create_editable_pdf(self, texts, output_path):
        """
        Create an editable PDF from extracted texts with page numbers.
        
        Args:
            texts (list): List of extracted text strings, one per page.
            output_path (str): Path to save the output PDF.
        """
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter
        
        # Register a default font that supports a wide range of characters
        try:
            pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
            font_name = 'Arial'
        except:
            font_name = 'Helvetica'  # Fallback to built-in font
        
        c.setFont(font_name, 10)
        
        for page_num, text in enumerate(texts, 1):
            # Add text to the PDF
            y_position = height - 40  # Start from top with margin
            x_position = 40  # Left margin
            
            # Split text into lines and add to PDF
            for line in text.split('\n'):
                if y_position < 50:  # Bottom margin with space for page number
                    c.showPage()
                    page_num += 1
                    y_position = height - 40
                
                # Add line to PDF
                c.drawString(x_position, y_position, line)
                y_position -= 12  # Line spacing
            
            # Add page number at the bottom center
            c.saveState()
            c.setFont(font_name, 10)
            page_text = f"Page {page_num}"
            page_width = c.stringWidth(page_text, font_name, 10)
            c.drawString((width - page_width) / 2, 30, page_text)
            c.restoreState()
            
            c.showPage()  # Move to next page
        
        c.save()
        print(f"Created editable PDF: {output_path}")
    
    def process_pdf(self, pdf_path, use_llm=True):
        """
        Process a PDF file: extract images, extract text, create editable PDF.
        
        Args:
            pdf_path (str): Path to the PDF file.
            use_llm (bool): Whether to use LLM for text extraction.
            
        Returns:
            str: Path to the created editable PDF.
        """
        # Get base filename without extension
        base_name = os.path.basename(pdf_path)
        file_name = os.path.splitext(base_name)[0]
        output_path = os.path.join(self.output_dir, f"{file_name}_editable.pdf")
        
        # Convert PDF to images
        images = self.convert_pdf_to_images(pdf_path)
        
        # Extract text from images
        texts = []
        for i, image in enumerate(images):
            print(f"Processing page {i+1}/{len(images)}")
            if use_llm and self.llm_api_url:
                text = self.extract_text_with_llm(image)
            else:
                text = self.extract_text_with_ocr(image)
            texts.append(text)
        
        # Create editable PDF
        self.create_editable_pdf(texts, output_path)
        
        return output_path
    
    def process_directory(self, directory_path, use_llm=True):
        """
        Process all PDF files in a directory.
        
        Args:
            directory_path (str): Path to directory containing PDF files.
            use_llm (bool): Whether to use LLM for text extraction.
            
        Returns:
            list: Paths to all created editable PDFs.
        """
        output_paths = []
        
        for filename in os.listdir(directory_path):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(directory_path, filename)
                output_path = self.process_pdf(pdf_path, use_llm)
                output_paths.append(output_path)
        
        return output_paths


# Example usage
if __name__ == "__main__":
    # Configure the processor
    llm_api_url = "http://your-llm-api-endpoint/extract-text"  # Replace with your actual API endpoint
    processor = PDFProcessor(llm_api_url=llm_api_url)
    
    # Example 1: Process a single PDF file
    pdf_path = "path/to/your/scanned_document.pdf"
    editable_pdf = processor.process_pdf(pdf_path)
    print(f"Editable PDF created: {editable_pdf}")
    
    # Example 2: Process all PDFs in a directory
    # directory_path = "path/to/pdf/directory"
    # editable_pdfs = processor.process_directory(directory_path)
    # print(f"Created {len(editable_pdfs)} editable PDFs")

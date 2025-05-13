def create_editable_pdf(self, texts, output_path, font_size=12):
    """
    Create an editable PDF from extracted texts with page numbers.
    
    Args:
        texts (list): List of extracted text strings, one per page.
        output_path (str): Path to save the output PDF.
        font_size (int): Font size to use for the text. Default is 12.
    """
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Register a default font that supports a wide range of characters
    try:
        pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
        font_name = 'Arial'
    except:
        font_name = 'Helvetica'  # Fallback to built-in font
    
    for page_num, text in enumerate(texts, 1):
        # Set the font and size for each page
        c.setFont(font_name, font_size)
        
        # Add text to the PDF
        y_position = height - 40  # Start from top with margin
        x_position = 40  # Left margin
        line_spacing = font_size * 1.2  # Adjust line spacing based on font size
        
        # Split text into lines and add to PDF
        for line in text.split('\n'):
            if y_position < 50:  # Bottom margin with space for page number
                c.showPage()
                # Reset font settings for the new page
                c.setFont(font_name, font_size)
                y_position = height - 40
            
            # Add line to PDF
            c.drawString(x_position, y_position, line)
            y_position -= line_spacing  # Adjusted line spacing
        
        # Add page number at the bottom center
        c.saveState()
        c.setFont(font_name, 10)  # Consistent font size for page numbers
        page_text = f"Page {page_num}"
        page_width = c.stringWidth(page_text, font_name, 10)
        c.drawString((width - page_width) / 2, 30, page_text)
        c.restoreState()
        
        c.showPage()  # Move to next page
    
    c.save()
    print(f"Created editable PDF: {output_path}")

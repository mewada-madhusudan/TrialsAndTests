def create_editable_pdf(self, texts, output_path):
    """
    Create an editable PDF from extracted texts with page numbers.
    Ensures text stays within visible margins and handles proper word wrapping.
    
    Args:
        texts (list): List of extracted text strings, one per page.
        output_path (str): Path to save the output PDF.
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Define margins
    left_margin = 40
    right_margin = 40
    top_margin = 40
    bottom_margin = 50  # Increased bottom margin for page number
    
    # Calculate text width
    text_width = width - left_margin - right_margin
    
    # Register a default font that supports a wide range of characters
    try:
        pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
        font_name = 'Arial'
    except:
        font_name = 'Helvetica'  # Fallback to built-in font
    
    font_size = 10
    line_height = font_size * 1.2  # 120% of font size for readable line spacing
    
    # Useful constants
    text_area_height = height - top_margin - bottom_margin
    max_lines_per_page = int(text_area_height / line_height)
    
    page_num = 1
    
    for input_page_text in texts:
        # Reset Y position for new content
        y_position = height - top_margin
        
        if not input_page_text or input_page_text.strip() == "":
            # Add empty page with just a page number if text is empty
            self._add_page_number(c, page_num, width, font_name, font_size)
            c.showPage()
            page_num += 1
            continue
            
        # Split text into paragraphs
        paragraphs = input_page_text.split('\n')
        
        # Process all paragraphs
        i = 0
        while i < len(paragraphs):
            paragraph = paragraphs[i]
            
            # Skip empty paragraphs but add space
            if not paragraph.strip():
                y_position -= line_height / 2
                if y_position < bottom_margin + line_height:
                    # Not enough space, move to next page
                    self._add_page_number(c, page_num, width, font_name, font_size)
                    c.showPage()
                    page_num += 1
                    c.setFont(font_name, font_size)
                    y_position = height - top_margin
                i += 1
                continue
            
            # Process paragraph for word wrapping
            words = paragraph.split()
            if not words:
                i += 1
                continue
                
            current_line = words[0]
            word_index = 1
            
            # Process all words in the paragraph
            while word_index < len(words):
                word = words[word_index]
                
                # Check if adding this word exceeds the line width
                test_line = current_line + " " + word
                line_width = c.stringWidth(test_line, font_name, font_size)
                
                if line_width <= text_width:
                    # Word fits, add it to the current line
                    current_line = test_line
                    word_index += 1
                else:
                    # Word doesn't fit, print current line and start a new one
                    # Check if we need a new page
                    if y_position < bottom_margin + line_height:
                        # Add page number and start a new page
                        self._add_page_number(c, page_num, width, font_name, font_size)
                        c.showPage()
                        page_num += 1
                        c.setFont(font_name, font_size)
                        y_position = height - top_margin
                    
                    # Draw the line
                    c.drawString(left_margin, y_position, current_line)
                    y_position -= line_height
                    current_line = word
                    word_index += 1
            
            # Don't forget to process the last line of the paragraph
            if current_line:
                # Check if we need a new page
                if y_position < bottom_margin + line_height:
                    # Add page number and start a new page
                    self._add_page_number(c, page_num, width, font_name, font_size)
                    c.showPage()
                    page_num += 1
                    c.setFont(font_name, font_size)
                    y_position = height - top_margin
                
                # Draw the line
                c.drawString(left_margin, y_position, current_line)
                y_position -= line_height
            
            # Add extra space after paragraph
            y_position -= line_height / 2
            
            # If we've processed this paragraph, move to the next
            i += 1
            
            # Check if we need a new page before starting the next paragraph
            if i < len(paragraphs) and y_position < bottom_margin + 2 * line_height:
                self._add_page_number(c, page_num, width, font_name, font_size)
                c.showPage()
                page_num += 1
                c.setFont(font_name, font_size)
                y_position = height - top_margin
        
        # Add page number at the bottom center of the last page for this input text
        self._add_page_number(c, page_num, width, font_name, font_size)
        c.showPage()
        page_num += 1
    
    c.save()
    print(f"Created editable PDF: {output_path}")

def _add_page_number(self, canvas_obj, page_num, width, font_name, font_size):
    """Helper method to add page number at the bottom of the page"""
    canvas_obj.saveState()
    canvas_obj.setFont(font_name, font_size)
    page_text = f"Page {page_num}"
    page_width = canvas_obj.stringWidth(page_text, font_name, font_size)
    canvas_obj.drawString((width - page_width) / 2, 30, page_text)
    canvas_obj.restoreState()
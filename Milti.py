def create_editable_pdf(self, texts, output_path):
        """
        Create an editable PDF from extracted texts with page numbers.
        Ensures text stays within visible margins and handles proper word wrapping.
        
        Args:
            texts (list): List of extracted text strings, one per page.
            output_path (str): Path to save the output PDF.
        """
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
        
        c.setFont(font_name, font_size)
        
        for page_num, text in enumerate(texts, 1):
            if not text:
                # Add empty page with just a page number if text is empty
                c.saveState()
                c.setFont(font_name, font_size)
                page_text = f"Page {page_num}"
                page_width = c.stringWidth(page_text, font_name, font_size)
                c.drawString((width - page_width) / 2, 30, page_text)
                c.restoreState()
                c.showPage()
                continue
                
            # Current Y position (start from top)
            y_position = height - top_margin
            
            # Split text into paragraphs
            paragraphs = text.split('\n')
            
            for paragraph in paragraphs:
                # Skip empty paragraphs
                if not paragraph.strip():
                    y_position -= line_height / 2  # Add a smaller space for empty lines
                    continue
                
                # Process the paragraph for word wrapping
                words = paragraph.split()
                if not words:
                    continue
                    
                current_line = words[0]
                
                for word in words[1:]:
                    # Check if adding this word exceeds the line width
                    test_line = current_line + " " + word
                    line_width = c.stringWidth(test_line, font_name, font_size)
                    
                    if line_width <= text_width:
                        # Word fits, add it to the current line
                        current_line = test_line
                    else:
                        # Word doesn't fit, print current line and start a new one
                        # Check if we need a new page
                        if y_position < bottom_margin + line_height:
                            # Add page number
                            c.saveState()
                            c.setFont(font_name, font_size)
                            page_text = f"Page {page_num}"
                            page_width = c.stringWidth(page_text, font_name, font_size)
                            c.drawString((width - page_width) / 2, 30, page_text)
                            c.restoreState()
                            
                            # Move to next page
                            c.showPage()
                            c.setFont(font_name, font_size)
                            page_num += 1
                            y_position = height - top_margin
                        
                        # Draw the line
                        c.drawString(left_margin, y_position, current_line)
                        y_position -= line_height
                        current_line = word
                
                # Don't forget to print the last line of the paragraph
                if current_line:
                    # Check if we need a new page
                    if y_position < bottom_margin + line_height:
                        # Add page number
                        c.saveState()
                        c.setFont(font_name, font_size)
                        page_text = f"Page {page_num}"
                        page_width = c.stringWidth(page_text, font_name, font_size)
                        c.drawString((width - page_width) / 2, 30, page_text)
                        c.restoreState()
                        
                        # Move to next page
                        c.showPage()
                        c.setFont(font_name, font_size)
                        page_num += 1
                        y_position = height - top_margin
                    
                    # Draw the line
                    c.drawString(left_margin, y_position, current_line)
                    y_position -= line_height
                
                # Add extra space after paragraph
                y_position -= line_height / 2
            
            # Add page number at the bottom center
            c.saveState()
            c.setFont(font_name, font_size)
            page_text = f"Page {page_num}"
            page_width = c.stringWidth(page_text, font_name, font_size)
            c.drawString((width - page_width) / 2, 30, page_text)
            c.restoreState()
            
            c.showPage()  # Move to next page
        
        c.save()
        print(f"Created editable PDF: {output_path}")

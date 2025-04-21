        from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
        from sqlalchemy.orm import Session
        import os
        import tempfile
        import requests
        from typing import List
        import PyPDF2
        from io import BytesIO
        from PIL import Image
        import fitz  # PyMuPDF
        
        @app.post("/api/documents", response_model=schemas.Document)
        async def upload_document(
            background_tasks: BackgroundTasks,
            file: UploadFile = File(...),
            knowledge_base_name: str = Form(...),
            db: Session = Depends(get_db)
        ):
            """Upload a document to the LLM server and create a record in the database"""
            try:
                # Read the uploaded file into memory
                file_contents = await file.read()
                
                # Check if the file is a PDF
                if file.filename.lower().endswith('.pdf'):
                    # Get the base filename without extension
                    base_filename = os.path.splitext(file.filename)[0]
                    
                    # Create a parent document record
                    parent_document = models.Document(
                        filename=file.filename,
                        knowledge_base_name=knowledge_base_name,
                        file_id="parent_" + file.filename,  # This is just a placeholder
                        is_parent=True
                    )
                    db.add(parent_document)
                    db.commit()
                    db.refresh(parent_document)
                    
                    # Use PyMuPDF (fitz) to extract pages as images
                    pdf_document = fitz.open(stream=file_contents, filetype="pdf")
                    
                    # Process each page
                    for page_number in range(len(pdf_document)):
                        # Get the page
                        page = pdf_document.load_page(page_number)
                        
                        # Render page to an image (PNG)
                        pix = page.get_pixmap()
                        
                        # Create a filename for this page's image
                        page_filename = f"{base_filename}_page{page_number + 1}.png"
                        
                        # Save the image to a temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                            pix.save(temp_file.name)
                            temp_file_path = temp_file.name
                        
                        # Upload the image to the LLM server
                        with open(temp_file_path, 'rb') as page_file:
                            response = requests.post(
                                f"{LLM_API_URL}/upload",
                                files={"file": (page_filename, page_file)},
                                headers={"Authorization": f"Bearer {LLM_API_KEY}"}
                            )
                            
                            if response.status_code != 200:
                                raise HTTPException(status_code=400, detail=f"Failed to upload page {page_number + 1} to LLM server")
                            
                            file_id = response.json().get("file_id")
                        
                        # Clean up the temporary file
                        os.unlink(temp_file_path)
                        
                        # Create document record in database for this page
                        db_document = models.Document(
                            filename=page_filename,
                            knowledge_base_name=knowledge_base_name,
                            file_id=file_id,
                            page_number=page_number + 1,
                            parent_id=parent_document.id
                        )
                        db.add(db_document)
                        db.commit()
                        db.refresh(db_document)
                        
                        # Process the document with OCR in the background
                        background_tasks.add_task(process_document, db_document.id)
                    
                    return parent_document
                    
                else:
                    # Handle non-PDF files (original behavior)
                    # Reset file position after reading
                    await file.seek(0)
                    
                    # Call your LLM API to upload file
                    response = requests.post(
                        f"{LLM_API_URL}/upload",
                        files={"file": (file.filename, file_contents)},
                        headers={"Authorization": f"Bearer {LLM_API_KEY}"}
                    )
                    
                    if response.status_code != 200:
                        raise HTTPException(status_code=400, detail="Failed to upload file to LLM server")
                    
                    file_id = response.json().get("file_id")
                    
                    # Create document record in database
                    db_document = models.Document(
                        filename=file.filename,
                        knowledge_base_name=knowledge_base_name,
                        file_id=file_id
                    )
                    db.add(db_document)
                    db.commit()
                    db.refresh(db_document)
                    
                    # Process the document with OCR in the background
                    background_tasks.add_task(process_document, db_document.id)
                    
                    return db_document
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

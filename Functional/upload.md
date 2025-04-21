
mewada-madhusudan/TrialsAndTests
main

GITHUB

In the upload_dpcument code in python before calling api to upload file to llm, I want to divide the pdf page wise, as on every page there is one scanned image of documents. Hence all pages should upload separately while maintaining the filename and page number for document.

Edit
I'll help you modify the upload_document function to divide a PDF document page by page and upload each page as a separate file to the LLM server. This approach will maintain the original filename and include page numbers for better organization.

Here's how you can modify your upload_document function in the FastAPI backend:

python
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import os
import tempfile
import requests
from typing import List
import PyPDF2
from io import BytesIO

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
            # Process PDF file page by page
            pdf_file = BytesIO(file_contents)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
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
            
            # Process each page
            for i, _ in enumerate(pdf_reader.pages):
                # Create a single-page PDF for this page
                page_number = i + 1
                page_filename = f"{base_filename}_page{page_number}.pdf"
                
                # Extract the page
                output = PyPDF2.PdfWriter()
                output.add_page(pdf_reader.pages[i])
                
                # Save the page to a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    output.write(temp_file)
                    temp_file_path = temp_file.name
                
                # Upload the page to the LLM server
                with open(temp_file_path, 'rb') as page_file:
                    response = requests.post(
                        f"{LLM_API_URL}/upload",
                        files={"file": (page_filename, page_file)},
                        headers={"Authorization": f"Bearer {LLM_API_KEY}"}
                    )
                    
                    if response.status_code != 200:
                        raise HTTPException(status_code=400, detail=f"Failed to upload page {page_number} to LLM server")
                    
                    file_id = response.json().get("file_id")
                
                # Clean up the temporary file
                os.unlink(temp_file_path)
                
                # Create document record in database for this page
                db_document = models.Document(
                    filename=page_filename,
                    knowledge_base_name=knowledge_base_name,
                    file_id=file_id,
                    page_number=page_number,
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
You'll also need to update your database model to support the new structure:

python
# In app/models.py, update the Document model:

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    knowledge_base_name = Column(String, nullable=False, index=True)
    file_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # New fields for page handling
    is_parent = Column(Boolean, default=False)
    parent_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    page_number = Column(Integer, nullable=True)
    
    # Relationships
    text_chunks = relationship("TextChunk", back_populates="document")
    child_documents = relationship("Document", backref=backref("parent", remote_side=[id]))
Don't forget to install the PyPDF2 library:

bash
pip install PyPDF2
This implementation does the following:

Checks if the uploaded file is a PDF
If it's a PDF, creates a parent document record
Splits the PDF page by page
For each page:
Creates a single-page PDF file
Uploads it to the LLM server with a filename that includes the page number
Creates a document record in the database linked to the parent document
Triggers the OCR processing for each page
If it's not a PDF, handles it with the original logic
You'll also need to update your Pydantic schema to include the new fields:

python
# In app/schemas.py, update the Document schema:

class Document(DocumentBase):
    id: int
    created_at: datetime
    is_parent: Optional[bool] = False
    parent_id: Optional[int] = None
    page_number: Optional[int] = None
    
    class Config:
        orm_mode = True
With these changes, your system will now handle PDF documents page by page, uploading each page as a separate document while maintaining the relationship between pages and their parent documen

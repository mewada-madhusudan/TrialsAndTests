# AI Document Question-Answering System

Based on your requirements, I'll help you build a Python-based application that leverages your LLM server to extract text from images (OCR), save the information to a knowledge base, and enable users to ask questions about the uploaded documents.

Let's break this down into components:

## System Architecture

1. **Backend (Python)**
   - FastAPI for the API server
   - Database (SQLite for development, PostgreSQL for production)
   - Integration with your LLM API
   - Document processing pipeline

2. **Frontend**
   - React with a modern UI library (Chakra UI)
   - Clean, intuitive interface for document upload and Q&A

## Implementation Plan

### 1. Backend Setup

First, let's create the basic project structure:

```python:app/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import requests
import json

from .database import engine, SessionLocal
from . import models, schemas

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Document QA System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# LLM API configuration
LLM_API_URL = os.getenv("LLM_API_URL", "http://your-llm-server.com/api")
LLM_API_KEY = os.getenv("LLM_API_KEY", "your-api-key")

@app.post("/api/documents", response_model=schemas.Document)
async def upload_document(
    file: UploadFile = File(...),
    knowledge_base_name: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upload a document to the LLM server and create a record in the database"""
    try:
        # Upload file to LLM server
        file_contents = await file.read()
        
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
        
        # Process the document with OCR
        process_document.delay(db_document.id)
        
        return db_document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@app.get("/api/documents", response_model=List[schemas.Document])
def get_documents(db: Session = Depends(get_db)):
    """Get all documents"""
    return db.query(models.Document).all()

@app.post("/api/ask", response_model=schemas.Answer)
async def ask_question(
    question: schemas.QuestionCreate,
    db: Session = Depends(get_db)
):
    """Ask a question based on the knowledge base"""
    try:
        # Get knowledge base contents related to the question
        knowledge_base = None
        if question.knowledge_base_name:
            # Get text chunks from specific knowledge base
            text_chunks = db.query(models.TextChunk).join(
                models.Document, 
                models.TextChunk.document_id == models.Document.id
            ).filter(
                models.Document.knowledge_base_name == question.knowledge_base_name
            ).all()
            
            knowledge_base = [chunk.text for chunk in text_chunks]
        
        # Call LLM API to answer the question
        response = requests.post(
            f"{LLM_API_URL}/ask",
            json={
                "question": question.question,
                "knowledge_base": knowledge_base
            },
            headers={"Authorization": f"Bearer {LLM_API_KEY}"}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get answer from LLM")
        
        answer_text = response.json().get("answer")
        
        # Save the Q&A to database
        db_qa = models.QA(
            question=question.question,
            answer=answer_text,
            knowledge_base_name=question.knowledge_base_name
        )
        db.add(db_qa)
        db.commit()
        db.refresh(db_qa)
        
        return {"question": question.question, "answer": answer_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")
```

Now, let's set up the database models:

```python:app/models.py
from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    knowledge_base_name = Column(String, nullable=False, index=True)
    file_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    text_chunks = relationship("TextChunk", back_populates="document")

class TextChunk(Base):
    __tablename__ = "text_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    page_number = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    document = relationship("Document", back_populates="text_chunks")

class QA(Base):
    __tablename__ = "qa"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    knowledge_base_name = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

Let's create the database connection setup:

```python:app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

And the schema models for validation:

```python:app/schemas.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TextChunkBase(BaseModel):
    page_number: int
    text: str

class TextChunkCreate(TextChunkBase):
    pass

class TextChunk(TextChunkBase):
    id: int
    document_id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class DocumentBase(BaseModel):
    filename: str
    knowledge_base_name: str
    file_id: str

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class QuestionCreate(BaseModel):
    question: str
    knowledge_base_name: Optional[str] = None

class Answer(BaseModel):
    question: str
    answer: str

class QABase(BaseModel):
    question: str
    answer: str
    knowledge_base_name: Optional[str] = None

class QA(QABase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True
```

Now, let's implement the background task to process the documents with OCR:

```python:app/tasks.py
import requests
import os
from sqlalchemy.orm import Session

from .database import SessionLocal
from . import models

# LLM API configuration
LLM_API_URL = os.getenv("LLM_API_URL", "http://your-llm-server.com/api")
LLM_API_KEY = os.getenv("LLM_API_KEY", "your-api-key")

def process_document(document_id: int):
    """
    Process a document by sending it to the LLM API for OCR,
    and save the extracted text to the database.
    """
    db = SessionLocal()
    try:
        # Get document from database
        document = db.query(models.Document).filter(models.Document.id == document_id).first()
        if not document:
            print(f"Document with ID {document_id} not found")
            return
        
        # Call LLM API to perform OCR
        response = requests.post(
            f"{LLM_API_URL}/ocr",
            json={"file_id": document.file_id},
            headers={"Authorization": f"Bearer {LLM_API_KEY}"}
        )
        
        if response.status_code != 200:
            print(f"Failed to process document with OCR: {response.text}")
            return
        
        # Extract OCR results
        ocr_results = response.json().get("results", [])
        
        # Save each page's text to the database
        for result in ocr_results:
            page_number = result.get("page_number", 0)
            text = result.get("text", "")
            
            # Create text chunk
            text_chunk = models.TextChunk(
                document_id=document.id,
                page_number=page_number,
                text=text
            )
            db.add(text_chunk)
        
        db.commit()
        print(f"Successfully processed document {document.filename}")
    except Exception as e:
        print(f"Error processing document: {str(e)}")
    finally:
        db.close()
```

### 2. Frontend Setup

Let's create a React frontend with Chakra UI for a clean user interface:

```jsx:frontend/src/App.js
import React, { useState, useEffect } from 'react';
import {
  ChakraProvider,
  Box,
  VStack,
  Grid,
  theme,
  Container,
  Heading,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel
} from '@chakra-ui/react';
import { ColorModeSwitcher } from './ColorModeSwitcher';
import UploadDocument from './components/UploadDocument';
import DocumentList from './components/DocumentList';
import QuestionAnswering from './components/QuestionAnswering';

function App() {
  return (
    <ChakraProvider theme={theme}>
      <Box textAlign="center" fontSize="xl">
        <Grid minH="100vh" p={3}>
          <ColorModeSwitcher justifySelf="flex-end" />
          <VStack spacing={8}>
            <Container maxW="container.xl" centerContent>
              <Heading as="h1" size="xl" mb={8}>
                Document Q&A System
              </Heading>
              
              <Tabs variant="enclosed" width="100%">
                <TabList>
                  <Tab>Upload Document</Tab>
                  <Tab>Ask Questions</Tab>
                  <Tab>Document Library</Tab>
                </TabList>
                <TabPanels>
                  <TabPanel>
                    <UploadDocument />
                  </TabPanel>
                  <TabPanel>
                    <QuestionAnswering />
                  </TabPanel>
                  <TabPanel>
                    <DocumentList />
                  </TabPanel>
                </TabPanels>
              </Tabs>
            </Container>
          </VStack>
        </Grid>
      </Box>
    </ChakraProvider>
  );
}

export default App;
```

Now, let's create the components:

```jsx:frontend/src/components/UploadDocument.js
import React, { useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  useToast,
  Progress,
  Text,
  Heading,
} from '@chakra-ui/react';
import api from '../api';

const UploadDocument = () => {
  const [file, setFile] = useState(null);
  const [knowledgeBaseName, setKnowledgeBaseName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const toast = useToast();

  const handleFileChange = (e) => {
    if (e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      toast({
        title: 'No file selected',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    if (!knowledgeBaseName) {
      toast({
        title: 'Knowledge base name is required',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    setIsUploading(true);
    setUploadProgress(0);
    
    // Create a simulated upload progress
    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => {
        const newValue = prev + 5;
        return newValue >= 90 ? 90 : newValue;
      });
    }, 300);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('knowledge_base_name', knowledgeBaseName);
      
      const response = await api.uploadDocument(formData);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      toast({
        title: 'Document uploaded!',
        description: `${file.name} was successfully uploaded. It's now being processed for OCR.`,
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      
      // Reset form
      setFile(null);
      setKnowledgeBaseName('');
      
      // Reset file input
      const fileInput = document.getElementById('file-upload');
      if (fileInput) fileInput.value = '';
      
    } catch (error) {
      clearInterval(progressInterval);
      
      toast({
        title: 'Upload failed',
        description: error.message || 'There was an error uploading your document.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress(0);
      }, 1000);
    }
  };

  return (
    <Box p={5} shadow="md" borderWidth="1px" borderRadius="md" bg="white">
      <Heading size="md" mb={4}>Upload a New Document</Heading>
      <form onSubmit={handleSubmit}>
        <VStack spacing={4} align="flex-start">
          <FormControl isRequired>
            <FormLabel>Knowledge Base Name</FormLabel>
            <Input
              type="text"
              value={knowledgeBaseName}
              onChange={(e) => setKnowledgeBaseName(e.target.value)}
              placeholder="E.g., Company Policies, Product Manual"
            />
          </FormControl>
          
          <FormControl isRequired>
            <FormLabel>Document</FormLabel>
            <Input
              id="file-upload"
              type="file"
              onChange={handleFileChange}
              accept="image/*,.pdf"
              padding={1}
            />
          </FormControl>
          
          {file && (
            <Text>Selected file: {file.name}</Text>
          )}
          
          {isUploading && (
            <Box width="100%">
              <Text mb={2}>Uploading... {uploadProgress}%</Text>
              <Progress value={uploadProgress} size="xs" colorScheme="blue" />
            </Box>
          )}
          
          <Button
            mt={4}
            colorScheme="blue"
            isLoading={isUploading}
            type="submit"
            width="full"
          >
            Upload Document
          </Button>
        </VStack>
      </form>
    </Box>
  );
};

export default UploadDocument;
```

```jsx:frontend/src/components/DocumentList.js
import React, { useState, useEffect } from 'react';
import {
  Box,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Text,
  Badge,
  Spinner,
  Alert,
  AlertIcon,
  HStack,
  Select,
  Button,
} from '@chakra-ui/react';
import api from '../api';

const DocumentList = () => {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('');
  const [knowledgeBases, setKnowledgeBases] = useState([]);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const data = await api.getDocuments();
      setDocuments(data);
      
      // Extract unique knowledge base names
      const uniqueKbs = [...new Set(data.map(doc => doc.knowledge_base_name))];
      setKnowledgeBases(uniqueKbs);
      
    } catch (err) {
      setError('Failed to fetch documents. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Filter documents based on selected knowledge base
  const filteredDocuments = filter
    ? documents.filter(doc => doc.knowledge_base_name === filter)
    : documents;

  return (
    <Box p={5} shadow="md" borderWidth="1px" borderRadius="md" bg="white">
      <HStack justify="space-between" mb={4}>
        <Heading size="md">Document Library</Heading>
        
        <HStack>
          <Select 
            placeholder="Filter by Knowledge Base" 
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            size="sm"
            maxW="250px"
          >
            {knowledgeBases.map(kb => (
              <option key={kb} value={kb}>{kb}</option>
            ))}
          </Select>
          
          {filter && (
            <Button size="sm" onClick={() => setFilter('')}>
              Clear
            </Button>
          )}
          
          <Button 
            size="sm" 
            colorScheme="blue"
            onClick={fetchDocuments}
          >
            Refresh
          </Button>
        </HStack>
      </HStack>
      
      {isLoading ? (
        <Box textAlign="center" py={10}>
          <Spinner size="xl" />
          <Text mt={4}>Loading documents...</Text>
        </Box>
      ) : error ? (
        <Alert status="error" mb={4}>
          <AlertIcon />
          {error}
        </Alert>
      ) : filteredDocuments.length === 0 ? (
        <Box textAlign="center" py={10}>
          <Text>No documents found{filter ? ` in "${filter}" knowledge base` : ''}.</Text>
        </Box>
      ) : (
        <Table variant="simple">
          <Thead>
            <Tr>
              <Th>File Name</Th>
              <Th>Knowledge Base</Th>
              <Th>Uploaded</Th>
            </Tr>
          </Thead>
          <Tbody>
            {filteredDocuments.map((doc) => (
              <Tr key={doc.id}>
                <Td>{doc.filename}</Td>
                <Td>
                  <Badge colorScheme="blue">{doc.knowledge_base_name}</Badge>
                </Td>
                <Td>{new Date(doc.created_at).toLocaleString()}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      )}
    </Box>
  );
};

export default DocumentList;
```

```jsx:frontend/src/components/QuestionAnswering.js
import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Textarea,
  useToast,
  Text,
  Heading,
  Select,
  Spinner,
  Flex,
  Card,
  CardHeader,
  CardBody,
  Divider
} from '@chakra-ui/react';
import api from '../api';

const QuestionAnswering = () => {
  const [question, setQuestion] = useState('');
  const [knowledgeBaseName, setKnowledgeBaseName] = useState('');
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isKbLoading, setIsKbLoading] = useState(true);
  const [answer, setAnswer] = useState('');
  const [history, setHistory] = useState([]);
  const toast = useToast();

  useEffect(() => {
    fetchKnowledgeBases();
  }, []);

  const fetchKnowledgeBases = async () => {
    setIsKbLoading(true);
    try {
      const docs = await api.getDocuments();
      const uniqueKbs = [...new Set(docs.map(doc => doc.knowledge_base_name))];
      setKnowledgeBases(uniqueKbs);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch knowledge bases.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsKbLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!question.trim()) {
      toast({
        title: 'Question is required',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    setIsLoading(true);
    setAnswer('');
    
    try {
      const data = await api.askQuestion({
        question,
        knowledge_base_name: knowledgeBaseName || null
      });
      
      setAnswer(data.answer);
      
      // Add to history
      setHistory(prev => [
        { question, answer: data.answer, kb: knowledgeBaseName || 'All' },
        ...prev
      ]);
      
    } catch (error) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to get answer.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box>
      <Box p={5} shadow="md" borderWidth="1px" borderRadius="md" bg="white" mb={6}>
        <Heading size="md" mb={4}>Ask a Question</Heading>
        <form onSubmit={handleSubmit}>
          <VStack spacing={4} align="flex-start">
            <FormControl>
              <FormLabel>Knowledge Base (Optional)</FormLabel>
              {isKbLoading ? (
                <Flex align="center">
                  <Spinner size="sm" mr={2} />
                  <Text>Loading knowledge bases...</Text>
                </Flex>
              ) : (
                <Select
                  value={knowledgeBaseName}
                  onChange={(e) => setKnowledgeBaseName(e.target.value)}
                  placeholder="All knowledge bases"
                >
                  {knowledgeBases.map(kb => (
                    <option key={kb} value={kb}>{kb}</option>
                  ))}
                </Select>
              )}
            </FormControl>
            
            <FormControl isRequired>
              <FormLabel>Your Question</FormLabel>
              <Textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask something about the uploaded documents..."
                size="lg"
                rows={3}
              />
            </FormControl>
            
            <Button
              mt={4}
              colorScheme="blue"
              isLoading={isLoading}
              type="submit"
              width="full"
            >
              Ask Question
            </Button>
          </VStack>
        </form>
      </Box>
      
      {isLoading && (
        <Box textAlign="center" my={8}>
          <Spinner size="xl" />
          <Text mt={2}>Thinking...</Text>
        </Box>
      )}
      
      {answer && (
        <Box p={5} shadow="md" borderWidth="1px" borderRadius="md" bg="white" mb={6}>
          <Heading size="md" mb={2}>Answer</Heading>
          <Text whiteSpace="pre-wrap">{answer}</Text>
        </Box>
      )}
      
      {history.length > 0 && (
        <Box>
          <Heading size="md" mb={4}>Recent Questions</Heading>
          <VStack spacing={4} align="stretch">
            {history.map((item, index) => (
              <Card key={index} variant="outline">
                <CardHeader pb={2}>
                  <Heading size="sm">Q: {item.question}</Heading>
                  <Text fontSize="xs" color="gray.500">Knowledge Base: {item.kb}</Text>
                </CardHeader>
                <Divider />
                <CardBody pt={3}>
                  <Text fontSize="sm">{item.answer}</Text>
                </CardBody>
              </Card>
            ))}
          </VStack>
        </Box>
      )}
    </Box>
  );
};

export default QuestionAnswering;
```

Let's create the API service to communicate with our backend:

```javascript:frontend/src/api.js
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API methods
export default {
  // Upload a document
  uploadDocument: async (formData) => {
    try {
      const response = await api.post('/documents', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Error uploading document');
    }
  },
  
  // Get all documents
  getDocuments: async () => {
    try {
      const response = await api.get('/documents');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Error fetching documents');
    }
  },
  
  // Ask a question
  askQuestion: async (data) => {
    try {
      const response = await api.post('/ask', data);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Error processing question');
    }
  },
};
```

### 3. Deployment Configuration

First, let's create a Docker configuration for easy deployment:

```dockerfile:Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

And a Docker Compose file for local development:

```yaml:docker-compose.yml
version: '3'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/docqa
      - LLM_API_URL=http://your-llm-server.com/api
      - LLM_API_KEY=your-api-key
    volumes:
      - ./app:/app/app
    depends_on:
      - db
  
  db:
    image: postgres:13
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=docqa
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000/api
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  postgres_data:
```

### 4. Requirements.txt

```text:requirements.txt
fastapi==0.95.1
uvicorn==0.22.0
sqlalchemy==2.0.12
python-multipart==0.0.6
requests==2.28.2
psycopg2-binary==2.9.6
python-dotenv==1.0.0
celery==5.2.7
redis==4.5.5
```

## System Features

1. **Document Management**
   - Upload documents to the LLM server
   - Document OCR processing
   - Storage of extracted text in a structured database

2. **Knowledge Base Organization**
   - Group documents by knowledge base
   - Maintain


# Running the AI Document QA System Without Docker (Using SQLite)

Absolutely! Let's modify the setup to run without Docker and use SQLite as the database. This will make the application much easier to set up and run on a local machine.

## Backend Setup (Using SQLite)

First, let's make sure our database configuration uses SQLite by default:

```python:app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Set SQLite as the default database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

Now let's create a simplified setup script to initialize the application:

```python:setup.py
from setuptools import setup, find_packages

setup(
    name="doc-qa-system",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.95.1",
        "uvicorn==0.22.0",
        "sqlalchemy==2.0.12",
        "python-multipart==0.0.6",
        "requests==2.28.2",
        "python-dotenv==1.0.0",
    ],
)
```

Let's also create a simplified version of our `tasks.py` that doesn't rely on Celery:

```python:app/tasks.py
import requests
import os
from sqlalchemy.orm import Session

from .database import SessionLocal
from . import models

# LLM API configuration
LLM_API_URL = os.getenv("LLM_API_URL", "http://your-llm-server.com/api")
LLM_API_KEY = os.getenv("LLM_API_KEY", "your-api-key")

def process_document(document_id: int):
    """
    Process a document by sending it to the LLM API for OCR,
    and save the extracted text to the database.
    """
    db = SessionLocal()
    try:
        # Get document from database
        document = db.query(models.Document).filter(models.Document.id == document_id).first()
        if not document:
            print(f"Document with ID {document_id} not found")
            return
        
        # Call LLM API to perform OCR
        response = requests.post(
            f"{LLM_API_URL}/ocr",
            json={"file_id": document.file_id},
            headers={"Authorization": f"Bearer {LLM_API_KEY}"}
        )
        
        if response.status_code != 200:
            print(f"Failed to process document with OCR: {response.text}")
            return
        
        # Extract OCR results
        ocr_results = response.json().get("results", [])
        
        # Save each page's text to the database
        for result in ocr_results:
            page_number = result.get("page_number", 0)
            text = result.get("text", "")
            
            # Create text chunk
            text_chunk = models.TextChunk(
                document_id=document.id,
                page_number=page_number,
                text=text
            )
            db.add(text_chunk)
        
        db.commit()
        print(f"Successfully processed document {document.filename}")
    except Exception as e:
        print(f"Error processing document: {str(e)}")
    finally:
        db.close()
```

Now let's modify our `main.py` to run the document processing task directly instead of using a background task:

```python:app/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import requests
import json

from .database import engine, SessionLocal
from . import models, schemas
from .tasks import process_document

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Document QA System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# LLM API configuration
LLM_API_URL = os.getenv("LLM_API_URL", "http://your-llm-server.com/api")
LLM_API_KEY = os.getenv("LLM_API_KEY", "your-api-key")

@app.post("/api/documents", response_model=schemas.Document)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    knowledge_base_name: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upload a document to the LLM server and create a record in the database"""
    try:
        # Upload file to LLM server
        file_contents = await file.read()
        
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

@app.get("/api/documents", response_model=List[schemas.Document])
def get_documents(db: Session = Depends(get_db)):
    """Get all documents"""
    return db.query(models.Document).all()

@app.post("/api/ask", response_model=schemas.Answer)
async def ask_question(
    question: schemas.QuestionCreate,
    db: Session = Depends(get_db)
):
    """Ask a question based on the knowledge base"""
    try:
        # Get knowledge base contents related to the question
        knowledge_base = None
        if question.knowledge_base_name:
            # Get text chunks from specific knowledge base
            text_chunks = db.query(models.TextChunk).join(
                models.Document, 
                models.TextChunk.document_id == models.Document.id
            ).filter(
                models.Document.knowledge_base_name == question.knowledge_base_name
            ).all()
            
            knowledge_base = [chunk.text for chunk in text_chunks]
        
        # Call LLM API to answer the question
        response = requests.post(
            f"{LLM_API_URL}/ask",
            json={
                "question": question.question,
                "knowledge_base": knowledge_base
            },
            headers={"Authorization": f"Bearer {LLM_API_KEY}"}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get answer from LLM")
        
        answer_text = response.json().get("answer")
        
        # Save the Q&A to database
        db_qa = models.QA(
            question=question.question,
            answer=answer_text,
            knowledge_base_name=question.knowledge_base_name
        )
        db.add(db_qa)
        db.commit()
        db.refresh(db_qa)
        
        return {"question": question.question, "answer": answer_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")
```

Let's create a simple script to run the application:

```python:run.py
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

Create a `.env` file for your API configuration:

```text:.env
LLM_API_URL=http://your-llm-server.com/api
LLM_API_KEY=your-api-key
```

## Frontend (React) Setup

The frontend code remains the same as in the previous answer. You'll just need to install the dependencies and run it locally:

1. Create a `.env` file in the frontend directory:

```text:frontend/.env
REACT_APP_API_URL=http://localhost:8000/api
```

## Running the Application (No Docker)

### Step 1: Set up and run the backend

```bash
# Clone your repository or create a new directory
mkdir doc-qa-system && cd doc-qa-system

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy python-multipart requests python-dotenv

# Create the app directory structure and copy the files
mkdir -p app

# Now create all the Python files mentioned above in the appropriate directories

# Start the backend server
python run.py
```

### Step 2: Set up and run the frontend

```bash
# In a new terminal, navigate to your project directory
cd doc-qa-system

# Create a React app
npx create-react-app frontend

# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install axios @chakra-ui/react @emotion/react @emotion/styled framer-motion

# Copy the React components and code to the appropriate locations

# Start the frontend development server
npm start
```

## Project Structure

Here's the simplified project structure for reference:

```
doc-qa-system/
├── .env                     # Environment variables for the backend
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application 
│   ├── database.py          # Database configuration (SQLite)
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   └── tasks.py             # Document processing tasks
├── run.py                   # Script to run the application
└── frontend/                # React frontend
    ├── public/
    ├── src/
    │   ├── App.js
    │   ├── index.js
    │   ├── api.js           # API service
    │   └── components/
    │       ├── UploadDocument.js
    │       ├── DocumentList.js
    │       └── QuestionAnswering.js
    ├── package.json
    └── .env                 # Environment variables for the frontend
```

## Using SQLite Benefits

Using SQLite provides several advantages for this setup:

1. No need to install or configure a separate database server
2. Data is stored in a single file that's easy to backup
3. Zero configuration required
4. Works well for development and small to medium applications
5. Portable across operating systems

This simplified setup makes it much easier to get started with the application without Docker or complex database configurations, while still maintaining all the functionality of the original system.
# Serving the Frontend from the Python Backend

You can serve your React frontend directly from your FastAPI backend, eliminating the need to run `npm start` separately. Here's how to do it:

## Step 1: Build the React Frontend

First, you need to build your React application to generate static files:

```bash
# In the frontend directory
cd frontend
npm run build
```

This creates a `build` directory with optimized production files.

## Step 2: Configure FastAPI to Serve Static Files

Modify your FastAPI application to serve these static files:

```python:app/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import requests
import json

from .database import engine, SessionLocal
from . import models, schemas
from .tasks import process_document

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Document QA System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# LLM API configuration
LLM_API_URL = os.getenv("LLM_API_URL", "http://your-llm-server.com/api")
LLM_API_KEY = os.getenv("LLM_API_KEY", "your-api-key")

# API endpoints (Keep all your existing endpoints)
@app.post("/api/documents", response_model=schemas.Document)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    knowledge_base_name: str = Form(...),
    db: Session = Depends(get_db)
):
    # ... existing code ...

@app.get("/api/documents", response_model=List[schemas.Document])
def get_documents(db: Session = Depends(get_db)):
    # ... existing code ...

@app.post("/api/ask", response_model=schemas.Answer)
async def ask_question(
    question: schemas.QuestionCreate,
    db: Session = Depends(get_db)
):
    # ... existing code ...

# Mount the React build folder as a static directory
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

# Serve the React index.html at the root
@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    # If the path doesn't point to an API endpoint, serve the React app
    if not full_path.startswith("api"):
        return FileResponse("frontend/build/index.html")
```

## Step 3: Update the Frontend API Configuration

Since your frontend will be served from the same server, you should update the API URL in the frontend:

```javascript:frontend/src/api.js
import axios from 'axios';

// Since the frontend is served from the same server as the backend,
// we can use a relative URL
const API_URL = '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Rest of your API code...
export default {
  // Upload a document
  uploadDocument: async (formData) => {
    // ... existing code ...
  },
  
  // Get all documents
  getDocuments: async () => {
    // ... existing code ...
  },
  
  // Ask a question
  askQuestion: async (data) => {
    // ... existing code ...
  },
};
```

## Step 4: Update Frontend Build Configuration

Create (or modify) a `.env.production` file in your frontend directory:

```text:frontend/.env.production
# Use relative path for API URL in production build
REACT_APP_API_URL=/api
# Disable source maps in production build for smaller files
GENERATE_SOURCEMAP=false
```

## Step 5: Create a Setup Script

Let's create a script that builds the frontend and sets up everything:

```python:setup_app.py
import os
import subprocess
import sys

def setup_application():
    print("Setting up Document QA System...")
    
    # Ensure we have a frontend/build directory
    if not os.path.exists("frontend/build"):
        print("Building frontend application...")
        
        # Navigate to frontend directory
        os.chdir("frontend")
        
        # Install npm dependencies
        print("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], check=True)
        
        # Build the frontend
        print("Building frontend...")
        subprocess.run(["npm", "run", "build"], check=True)
        
        # Navigate back to root
        os.chdir("..")
    else:
        print("Frontend build already exists. Skipping build step.")
    
    print("Setup complete! Run 'python run.py' to start the application.")

if __name__ == "__main__":
    setup_application()
```

## Step 6: Create a Combined Project Structure

Here's the updated project structure:

```
doc-qa-system/
├── .env                     # Environment variables for the backend
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application (updated to serve frontend)
│   ├── database.py          # Database configuration (SQLite)
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   └── tasks.py             # Document processing tasks
├── frontend/                # React frontend
│   ├── public/
│   ├── src/
│   │   ├── App.js
│   │   ├── index.js
│   │   ├── api.js           # API service (updated to use relative path)
│   │   └── components/
│   │       ├── UploadDocument.js
│   │       ├── DocumentList.js
│   │       └── QuestionAnswering.js
│   ├── package.json
│   ├── .env.development     # Development environment variables
│   └── .env.production      # Production environment variables
├── run.py                   # Script to run the application
└── setup_app.py             # Script to set up the application
```

## Step 7: Running the Application

Now you can run the application with just two commands:

```bash
# First time only: Set up the application
python setup_app.py

# Start the application
python run.py
```

The application will be available at http://localhost:8000, with both the frontend and backend served from the same server.

## Additional Improvements

### 1. Automatic Frontend Rebuilding

You can add a flag to rebuild the frontend when needed:

```python:setup_app.py
import os
import subprocess
import argparse

def setup_application(force_rebuild=False):
    print("Setting up Document QA System...")
    
    # Ensure we have a frontend/build directory or rebuild if forced
    if not os.path.exists("frontend/build") or force_rebuild:
        print("Building frontend application...")
        
        # Navigate to frontend directory
        os.chdir("frontend")
        
        # Install npm dependencies
        print("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], check=True)
        
        # Build the frontend
        print("Building frontend...")
        subprocess.run(["npm", "run", "build"], check=True)
        
        # Navigate back to root
        os.chdir("..")
    else:
        print("Frontend build already exists. Skipping build step.")
    
    print("Setup complete! Run 'python run.py' to start the application.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up Document QA System")
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild of the frontend")
    args = parser.parse_args()
    
    setup_application(force_rebuild=args.rebuild)
```

### 2. Installation Requirements

Create a requirements.txt file to make dependency installation easier:

```text:requirements.txt
fastapi==0.95.1
uvicorn==0.22.0
sqlalchemy==2.0.12
python-multipart==0.0.6
requests==2.28.2
python-dotenv==1.0.0
aiofiles==23.1.0  # Required for serving static files
```

### 3. Development

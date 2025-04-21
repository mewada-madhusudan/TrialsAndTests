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

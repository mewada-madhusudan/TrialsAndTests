import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  LinearProgress,
  Alert,
  Stack
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import api from '../api';

const UploadDocument = () => {
  const [file, setFile] = useState(null);
  const [knowledgeBaseName, setKnowledgeBaseName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [alert, setAlert] = useState({ show: false, severity: 'info', message: '' });

  const handleFileChange = (e) => {
    if (e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const showAlert = (severity, message) => {
    setAlert({
      show: true,
      severity,
      message
    });

    // Auto-hide the alert after 5 seconds
    setTimeout(() => {
      setAlert({ show: false, severity: 'info', message: '' });
    }, 5000);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      showAlert('error', 'No file selected');
      return;
    }
    
    if (!knowledgeBaseName) {
      showAlert('error', 'Knowledge base name is required');
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
      
      showAlert('success', `${file.name} was successfully uploaded. It's now being processed for OCR.`);
      
      // Reset form
      setFile(null);
      setKnowledgeBaseName('');
      
      // Reset file input
      const fileInput = document.getElementById('file-upload');
      if (fileInput) fileInput.value = '';
      
    } catch (error) {
      clearInterval(progressInterval);
      showAlert('error', error.message || 'There was an error uploading your document.');
    } finally {
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress(0);
      }, 1000);
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" component="h2" gutterBottom>
        Upload a New Document
      </Typography>
      
      {alert.show && (
        <Alert severity={alert.severity} sx={{ mb: 2 }}>
          {alert.message}
        </Alert>
      )}
      
      <form onSubmit={handleSubmit}>
        <Stack spacing={3}>
          <TextField
            fullWidth
            required
            label="Knowledge Base Name"
            value={knowledgeBaseName}
            onChange={(e) => setKnowledgeBaseName(e.target.value)}
            placeholder="E.g., Company Policies, Product Manual"
            variant="outlined"
          />
          
          <Box>
            <Button
              variant="contained"
              component="label"
              startIcon={<CloudUploadIcon />}
            >
              Select File
              <input
                id="file-upload"
                type="file"
                hidden
                onChange={handleFileChange}
                accept="image/*,.pdf"
              />
            </Button>
            {file && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                Selected file: {file.name}
              </Typography>
            )}
          </Box>
          
          {isUploading && (
            <Box sx={{ width: '100%' }}>
              <Typography variant="body2" gutterBottom>
                Uploading... {uploadProgress}%
              </Typography>
              <LinearProgress variant="determinate" value={uploadProgress} />
            </Box>
          )}
          
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={isUploading}
            fullWidth
          >
            Upload Document
          </Button>
        </Stack>
      </form>
    </Paper>
  );
};

export default UploadDocument;

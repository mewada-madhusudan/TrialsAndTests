// src/api/reportApi.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

// Create an axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

// API functions
export const uploadReportFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await api.post('/upload-report-file', formData);
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error uploading file');
  }
};

export const getConfigurations = async () => {
  try {
    const response = await api.get('/configurations');
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error fetching configurations');
  }
};

export const getConfiguration = async (configId) => {
  try {
    const response = await api.get(`/configurations/${configId}`);
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error fetching configuration');
  }
};

export const generateReport = async (file, configId) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('configId', configId);
  
  try {
    const response = await api.post('/generate-report', formData);
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error generating report');
  }
};

export const getReports = async () => {
  try {
    const response = await api.get('/reports');
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error fetching reports');
  }
};

export const getReport = async (reportId) => {
  try {
    const response = await api.get(`/reports/${reportId}`);
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error fetching report');
  }
};

export default {
  uploadReportFile,
  getConfigurations,
  getConfiguration,
  generateReport,
  getReports,
  getReport
};

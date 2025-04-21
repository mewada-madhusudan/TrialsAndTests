import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Stack
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
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
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" component="h2">Document Library</Typography>
        
        <Stack direction="row" spacing={2} alignItems="center">
          <FormControl sx={{ minWidth: 200 }} size="small">
            <InputLabel id="kb-filter-label">Filter by Knowledge Base</InputLabel>
            <Select
              labelId="kb-filter-label"
              value={filter}
              label="Filter by Knowledge Base"
              onChange={(e) => setFilter(e.target.value)}
              displayEmpty
            >
              <MenuItem value="">All Knowledge Bases</MenuItem>
              {knowledgeBases.map(kb => (
                <MenuItem key={kb} value={kb}>{kb}</MenuItem>
              ))}
            </Select>
          </FormControl>
          
          {filter && (
            <Button 
              variant="outlined" 
              size="small"
              onClick={() => setFilter('')}
            >
              Clear
            </Button>
          )}
          
          <Button 
            variant="contained"
            size="small"
            startIcon={<RefreshIcon />}
            onClick={fetchDocuments}
          >
            Refresh
          </Button>
        </Stack>
      </Box>
      
      {isLoading ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 5 }}>
          <CircularProgress />
          <Typography sx={{ mt: 2 }}>Loading documents...</Typography>
        </Box>
      ) : error ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      ) : filteredDocuments.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 5 }}>
          <Typography>No documents found{filter ? ` in "${filter}" knowledge base` : ''}.</Typography>
        </Box>
      ) : (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>File Name</TableCell>
                <TableCell>Knowledge Base</TableCell>
                <TableCell>Uploaded</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredDocuments.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell>{doc.filename}</TableCell>
                  <TableCell>
                    <Chip label={doc.knowledge_base_name} color="primary" variant="outlined" />
                  </TableCell>
                  <TableCell>{new Date(doc.created_at).toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Paper>
  );
};

export default DocumentList;

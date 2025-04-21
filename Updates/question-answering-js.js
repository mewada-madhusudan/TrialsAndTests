import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Divider,
  Stack,
  Card,
  CardContent,
  CardHeader
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import api from '../api';

const QuestionAnswering = () => {
  const [question, setQuestion] = useState('');
  const [knowledgeBaseName, setKnowledgeBaseName] = useState('');
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isKbLoading, setIsKbLoading] = useState(true);
  const [answer, setAnswer] = useState('');
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);

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
      setError('Failed to fetch knowledge bases.');
      console.error(error);
    } finally {
      setIsKbLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!question.trim()) {
      setError('Question is required');
      return;
    }
    
    setIsLoading(true);
    setAnswer('');
    setError(null);
    
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
      setError(error.message || 'Failed to get answer.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" component="h2" gutterBottom>
          Ask a Question
        </Typography>
        
        {error && (
          <Box sx={{ mb: 2 }}>
            <Typography color="error">{error}</Typography>
          </Box>
        )}
        
        <form onSubmit={handleSubmit}>
          <Stack spacing={3}>
            <FormControl fullWidth>
              <InputLabel id="kb-select-label">Knowledge Base (Optional)</InputLabel>
              <Select
                labelId="kb-select-label"
                value={knowledgeBaseName}
                label="Knowledge Base (Optional)"
                onChange={(e) => setKnowledgeBaseName(e.target.value)}
                disabled={isKbLoading}
              >
                <MenuItem value="">All knowledge bases</MenuItem>
                {knowledgeBases.map(kb => (
                  <MenuItem key={kb} value={kb}>{kb}</MenuItem>
                ))}
              </Select>
              {isKbLoading && (
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                  <CircularProgress size={16} sx={{ mr: 1 }} />
                  <Typography variant="caption">Loading knowledge bases...</Typography>
                </Box>
              )}
            </FormControl>
            
            <TextField
              label="Your Question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask something about the uploaded documents..."
              required
              multiline
              rows={3}
              fullWidth
            />
            
            <Button
              type="submit"
              variant="contained"
              endIcon={<SendIcon />}
              disabled={isLoading}
              fullWidth
            >
              Ask Question
            </Button>
          </Stack>
        </form>
      </Paper>
      
      {isLoading && (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', my: 4 }}>
          <CircularProgress />
          <Typography sx={{ mt: 2 }}>Thinking...</Typography>
        </Box>
      )}
      
      {answer && (
        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="h6" gutterBottom>Answer</Typography>
          <Typography sx={{ whiteSpace: 'pre-wrap' }}>{answer}</Typography>
        </Paper>
      )}
      
      {history.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" gutterBottom>Recent Questions</Typography>
          <Stack spacing={2}>
            {history.map((item, index) => (
              <Card key={index} variant="outlined">
                <CardHeader 
                  title={`Q: ${item.question}`}
                  subheader={`Knowledge Base: ${item.kb}`}
                  titleTypographyProps={{ variant: 'subtitle1' }}
                  subheaderTypographyProps={{ variant: 'caption' }}
                  sx={{ pb: 1 }}
                />
                <Divider />
                <CardContent sx={{ pt: 2 }}>
                  <Typography variant="body2">{item.answer}</Typography>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </Box>
      )}
    </Box>
  );
};

export default QuestionAnswering;

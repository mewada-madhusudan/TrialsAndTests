import React from 'react';
import { 
  ThemeProvider, 
  createTheme,
  CssBaseline,
  Container,
  Box,
  Typography,
  Tabs,
  Tab,
  Paper
} from '@mui/material';
import UploadDocument from './components/UploadDocument';
import DocumentList from './components/DocumentList';
import QuestionAnswering from './components/QuestionAnswering';

// Create a theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function App() {
  const [value, setValue] = React.useState(0);

  const handleChange = (event, newValue) => {
    setValue(newValue);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Typography variant="h3" component="h1" align="center" gutterBottom>
            Document Q&A System
          </Typography>
          
          <Paper sx={{ width: '100%', mb: 2 }}>
            <Tabs
              value={value}
              onChange={handleChange}
              indicatorColor="primary"
              textColor="primary"
              centered
            >
              <Tab label="Upload Document" />
              <Tab label="Ask Questions" />
              <Tab label="Document Library" />
            </Tabs>
            
            <TabPanel value={value} index={0}>
              <UploadDocument />
            </TabPanel>
            <TabPanel value={value} index={1}>
              <QuestionAnswering />
            </TabPanel>
            <TabPanel value={value} index={2}>
              <DocumentList />
            </TabPanel>
          </Paper>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;

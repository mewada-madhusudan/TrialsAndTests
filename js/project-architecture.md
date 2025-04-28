# Report Learning App - System Architecture

This document outlines the architecture of the Report Configuration Learning Application with machine learning capabilities using a Python Flask backend and React frontend.

## Architecture Overview

![Architecture Diagram](https://i.imgur.com/6jRzOy4.png)

### Components

1. **Frontend (React)**
   - User interface for uploading reports
   - Configuration selection and management
   - Report generation and viewing

2. **Backend (Python Flask)**
   - File processing and analysis
   - Machine learning model training and application
   - Report generation
   - REST API endpoints

3. **Database (SQLite)**
   - Store configurations
   - Store generated reports
   - Track ML models

4. **ML Components**
   - Field type classification
   - Pattern recognition
   - Report structure learning

## Machine Learning Implementation

The application uses several machine learning approaches:

### 1. Field Type Classification

**Model**: Random Forest Classifier
- Predicts field types (numeric, date, text) based on column name and sample data
- Features: Character n-grams from field names, basic statistics from data samples
- Improves as more report templates are processed

### 2. Pattern Recognition

**Techniques**: 
- Clustering to identify related fields
- Time series detection for temporal data
- Text analysis for categorical fields

### 3. Incremental Learning

The system gets smarter over time by:
- Training on each new report configuration
- Building a knowledge base of common report structures
- Learning how to map similar fields across different reports

## Project Setup Guide

### Prerequisites

- Python 3.8+ with pip
- Node.js and npm
- Git (optional)

### Backend Setup

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install flask flask-cors pandas numpy scikit-learn joblib werkzeug sqlite3
   ```

3. **Create project structure**:
   ```
   report-learning-app/
   ├── backend/
   │   ├── app.py
   │   ├── uploads/
   │   └── ml_models/
   ├── frontend/
   ```

4. **Copy the Flask app code** to `app.py`

5. **Initialize the database**:
   ```bash
   python app.py
   ```

### Frontend Setup

1. **Create React app**:
   ```bash
   npx create-react-app frontend
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install axios tailwindcss postcss autoprefixer lucide-react
   ```

3. **Configure Tailwind CSS**:
   ```bash
   npx tailwindcss init -p
   ```

4. **Update the React code** with our component

5. **Start development server**:
   ```bash
   npm start
   ```

### Running the Full Stack

1. **Start the backend** (in one terminal):
   ```bash
   cd backend
   python app.py
   ```

2. **Start the frontend** (in another terminal):
   ```bash
   cd frontend
   npm start
   ```

3. **Access the application** at http://localhost:3000

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload-report-file` | POST | Upload file for learning |
| `/api/configurations` | GET | Get all configurations |
| `/api/configurations/<id>` | GET | Get specific configuration |
| `/api/generate-report` | POST | Generate report from config and new data |
| `/api/reports` | GET | Get all generated reports |
| `/api/reports/<id>` | GET | Get specific report |

## Machine Learning Model Training Process

1. **Data Collection**:
   - Extract field names, types, and sample data from uploaded reports

2. **Feature Engineering**:
   - For field names: Character n-grams (2-5)
   - For data: Statistical features (variance, distribution, unique count)

3. **Model Training**:
   - Train Random Forest classifier when sufficient data is available (3+ configurations)
   - Label encoding for field types

4. **Model Application**:
   - Enhance rule-based configuration with ML predictions
   - Override uncertain classifications

## Example ML Feature Generation

For field name "monthly_revenue":
1. Character n-grams: "mo", "on", "nt", "th", "hl", "ly", "y_", "_r", "re", "ev", etc.
2. Statistical features: range, variance, correlation with date fields

## Next Steps & Future Enhancements

1. **Advanced ML Models**:
   - Deep learning for complex pattern recognition
   - NLP for semantic understanding of field names and values

2. **Report Template Generation**:
   - Automatically create visualization templates
   - Smart data aggregation suggestions

3. **Database Migration**:
   - Move from SQLite to PostgreSQL for production use
   - Implement proper migrations and schemas

4. **User Authentication**:
   - Add multi-user support
   - Role-based access control

5. **Report Scheduling**:
   - Automated report generation on schedule
   - Email or notification system

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import pandas as pd
import numpy as np
import sqlite3
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import LabelEncoder
import re

app = Flask(__name__, static_folder='../frontend/build')
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
DB_PATH = 'report_configs.db'
ML_MODELS_FOLDER = 'ml_models'

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ML_MODELS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create configurations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS configurations (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        source_file_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        config_data TEXT NOT NULL
    )
    ''')
    
    # Create reports table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        config_id TEXT NOT NULL,
        name TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        report_data TEXT NOT NULL,
        FOREIGN KEY (config_id) REFERENCES configurations (id)
    )
    ''')
    
    # Create ML models table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ml_models (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        model_type TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        accuracy REAL,
        model_path TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_file(file_path):
    """Parse CSV or Excel file into pandas DataFrame"""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.csv':
        return pd.read_csv(file_path)
    elif file_ext in ['.xlsx', '.xls']:
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")

def detect_field_types(df):
    """Detect data types for each column in the DataFrame"""
    field_types = {}
    
    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            field_types[column] = 'numeric'
        elif pd.api.types.is_datetime64_any_dtype(df[column]):
            field_types[column] = 'date'
        elif is_potential_date(df[column]):
            field_types[column] = 'date'
        else:
            field_types[column] = 'text'
    
    return field_types

def is_potential_date(series):
    """Check if a column might contain dates"""
    # Check a sample of the data
    sample = series.dropna().head(10).astype(str)
    
    # Date patterns
    date_patterns = [
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # 01/23/2020, 1-23-20
        r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',    # 2020/01/23, 2020-1-23
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # January 23, 2020
        r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',    # 23 January 2020
    ]
    
    # Check if any of the patterns match the samples
    for pattern in date_patterns:
        if any(series.dropna().astype(str).str.match(pattern)):
            return True
    
    # Check for month names
    month_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b'
    if any(series.dropna().astype(str).str.contains(month_pattern, case=False)):
        return True
    
    return False

def detect_time_fields(df, field_types):
    """Detect columns that might represent time periods"""
    time_fields = []
    
    # Months, quarters, years patterns
    month_names = ['january', 'february', 'march', 'april', 'may', 'june', 
                  'july', 'august', 'september', 'october', 'november', 'december',
                  'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    quarter_pattern = r'\bq[1-4]\b|\bquarter [1-4]\b'
    year_pattern = r'\b20\d{2}\b|\b19\d{2}\b'  # Years like 2020, 1999 etc.
    
    for column in df.columns:
        # Skip if already identified as date
        if field_types.get(column) == 'date':
            time_fields.append(column)
            continue
            
        sample_values = df[column].dropna().astype(str).str.lower().tolist()
        sample_values = sample_values[:100] if len(sample_values) > 100 else sample_values
        
        # Check for month names
        if any(month in ' '.join(sample_values) for month in month_names):
            time_fields.append(column)
            continue
            
        # Check for quarters
        if any(re.search(quarter_pattern, value) for value in sample_values):
            time_fields.append(column)
            continue
            
        # Check for years
        if any(re.search(year_pattern, value) for value in sample_values):
            time_fields.append(column)
            continue
    
    return time_fields

def analyze_report_structure(df, filename):
    """Analyze the structure of the report and create a configuration"""
    # Detect data types
    field_types = detect_field_types(df)
    
    # Identify metrics (numeric fields) and dimensions (categorical fields)
    numeric_fields = [col for col, type_info in field_types.items() if type_info == 'numeric']
    categorical_fields = [col for col, type_info in field_types.items() if type_info == 'text']
    date_fields = [col for col, type_info in field_types.items() if type_info == 'date']
    
    # Detect time-related fields
    time_fields = detect_time_fields(df, field_types)
    
    # Identify potential aggregations
    potential_aggregations = {}
    for field in numeric_fields:
        potential_aggregations[field] = ['sum', 'avg', 'min', 'max']
    
    # Generate ID and name
    config_id = str(uuid.uuid4())
    config_name = re.sub(r'[^a-zA-Z0-9]', '_', os.path.splitext(filename)[0])
    
    # Create configuration object
    file_ext = os.path.splitext(filename)[1].lower()
    file_type = 'csv' if file_ext == '.csv' else 'excel'
    
    configuration = {
        'id': config_id,
        'name': config_name,
        'sourceFileName': filename,
        'fileType': file_type,
        'fields': list(df.columns),
        'fieldTypes': field_types,
        'numericFields': numeric_fields,
        'categoricalFields': categorical_fields,
        'dateFields': date_fields,
        'timeFields': time_fields,
        'potentialAggregations': potential_aggregations,
        'createdAt': datetime.now().isoformat()
    }
    
    return configuration

def train_field_type_model(config_data_list):
    """Train a machine learning model to predict field types based on features"""
    if len(config_data_list) < 3:
        return None  # Not enough data to train a meaningful model
    
    # Extract features and labels
    field_names = []
    field_types = []
    
    for config in config_data_list:
        config_dict = json.loads(config) if isinstance(config, str) else config
        for field, field_type in config_dict.get('fieldTypes', {}).items():
            field_names.append(field)
            field_types.append(field_type)
    
    # Vectorize field names
    vectorizer = CountVectorizer(analyzer='char', ngram_range=(2, 5))
    X = vectorizer.fit_transform(field_names)
    
    # Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(field_types)
    
    # Train a random forest classifier
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # Save model and encoders
    model_id = str(uuid.uuid4())
    model_path = os.path.join(ML_MODELS_FOLDER, f"field_type_model_{model_id}.joblib")
    
    joblib.dump({
        'model': model,
        'vectorizer': vectorizer,
        'label_encoder': label_encoder
    }, model_path)
    
    # Save model metadata to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ml_models (id, name, model_type, created_at, model_path) VALUES (?, ?, ?, ?, ?)",
        (model_id, "Field Type Classifier", "RandomForest", datetime.now().isoformat(), model_path)
    )
    conn.commit()
    conn.close()
    
    return model_id

def apply_ml_to_config(df, file_name):
    """Apply ML model to enhance configuration if available"""
    # Get the latest field type model
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT model_path FROM ml_models WHERE model_type = 'RandomForest' ORDER BY created_at DESC LIMIT 1"
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        # No model available, use rule-based approach only
        return analyze_report_structure(df, file_name)
    
    # Load the model
    model_data = joblib.load(result[0])
    model = model_data['model']
    vectorizer = model_data['vectorizer']
    label_encoder = model_data['label_encoder']
    
    # Create basic configuration
    config = analyze_report_structure(df, file_name)
    
    # Enhance with ML predictions for ambiguous fields
    ambiguous_fields = [col for col in df.columns if config['fieldTypes'][col] == 'text']
    
    if ambiguous_fields:
        # Vectorize field names
        X = vectorizer.transform(ambiguous_fields)
        
        # Predict field types
        predictions = model.predict(X)
        predicted_types = label_encoder.inverse_transform(predictions)
        
        # Update configuration with ML predictions
        for field, predicted_type in zip(ambiguous_fields, predicted_types):
            # Only override if ML is confident (can add confidence check here)
            config['fieldTypes'][field] = predicted_type
            
            # Update related field lists
            if predicted_type == 'numeric' and field not in config['numericFields']:
                config['numericFields'].append(field)
                config['categoricalFields'].remove(field)
            elif predicted_type == 'date' and field not in config['dateFields']:
                config['dateFields'].append(field)
                config['categoricalFields'].remove(field)
    
    return config

def generate_report(df, config):
    """Generate a report based on the configuration and new data"""
    config_dict = json.loads(config) if isinstance(config, str) else config
    
    # Extract required fields
    field_types = config_dict.get('fieldTypes', {})
    numeric_fields = config_dict.get('numericFields', [])
    
    # Basic validation - check if required fields exist
    missing_fields = [field for field in config_dict.get('fields', []) if field not in df.columns]
    if missing_fields:
        return {"error": f"Missing fields in new data: {', '.join(missing_fields)}"}
    
    # Convert data types based on configuration
    for field, field_type in field_types.items():
        if field not in df.columns:
            continue
            
        if field_type == 'numeric':
            df[field] = pd.to_numeric(df[field], errors='coerce')
        elif field_type == 'date':
            try:
                df[field] = pd.to_datetime(df[field], errors='coerce')
            except:
                pass  # Keep as is if conversion fails
    
    # Calculate aggregations for numeric fields
    aggregations = {}
    for field in numeric_fields:
        if field in df.columns:
            values = df[field].dropna()
            if not values.empty:
                aggregations[field] = {
                    'sum': float(values.sum()),
                    'avg': float(values.mean()),
                    'min': float(values.min()),
                    'max': float(values.max()),
                    'count': int(values.count())
                }
    
    # Create report
    report_id = str(uuid.uuid4())
    report = {
        'id': report_id,
        'configId': config_dict.get('id'),
        'configName': config_dict.get('name'),
        'generatedAt': datetime.now().isoformat(),
        'recordCount': len(df),
        'aggregations': aggregations,
        'data': df.to_dict(orient='records'),
        'summary': f"Report generated using configuration '{config_dict.get('name')}' with {len(df)} records."
    }
    
    return report

# API Routes
@app.route('/api/upload-report-file', methods=['POST'])
def upload_report_file():
    """Upload report files for learning"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Parse file and analyze structure
            df = parse_file(file_path)
            config = apply_ml_to_config(df, filename)
            
            # Save configuration to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO configurations (id, name, source_file_name, file_type, created_at, config_data) VALUES (?, ?, ?, ?, ?, ?)",
                (config['id'], config['name'], filename, config['fileType'], config['createdAt'], json.dumps(config))
            )
            conn.commit()
            conn.close()
            
            # Retrain ML model with new configuration data
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT config_data FROM configurations")
            all_configs = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if len(all_configs) >= 3:
                train_field_type_model(all_configs)
            
            return jsonify(config), 201
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/configurations', methods=['GET'])
def get_configurations():
    """Get all available configurations"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, source_file_name, file_type, created_at, config_data FROM configurations")
    rows = cursor.fetchall()
    conn.close()
    
    configurations = []
    for row in rows:
        config_data = json.loads(row['config_data'])
        configurations.append({
            'id': row['id'],
            'name': row['name'],
            'sourceFileName': row['source_file_name'],
            'fileType': row['file_type'],
            'createdAt': row['created_at'],
            'fields': config_data.get('fields', []),
            'numericFields': config_data.get('numericFields', []),
            'categoricalFields': config_data.get('categoricalFields', []),
        })
    
    return jsonify(configurations)

@app.route('/api/configurations/<config_id>', methods=['GET'])
def get_configuration(config_id):
    """Get a specific configuration"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT config_data FROM configurations WHERE id = ?", (config_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'error': 'Configuration not found'}), 404
    
    return jsonify(json.loads(row['config_data']))

@app.route('/api/generate-report', methods=['POST'])
def create_report():
    """Generate a report based on configuration and new data"""
    if 'file' not in request.files or 'configId' not in request.form:
        return jsonify({'error': 'Missing file or configuration ID'}), 400
    
    file = request.files['file']
    config_id = request.form['configId']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Get configuration
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT config_data FROM configurations WHERE id = ?", (config_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return jsonify({'error': 'Configuration not found'}), 404
            
            config = json.loads(row['config_data'])
            
            # Parse file
            df = parse_file(file_path)
            
            # Generate report
            report = generate_report(df, config)
            
            # Save report to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reports (id, config_id, name, created_at, report_data) VALUES (?, ?, ?, ?, ?)",
                (report['id'], config_id, f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}", 
                 report['generatedAt'], json.dumps(report))
            )
            conn.commit()
            conn.close()
            
            return jsonify(report), 201
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/reports', methods=['GET'])
def get_reports():
    """Get all generated reports"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, r.name, r.created_at, r.config_id, c.name as config_name 
        FROM reports r JOIN configurations c ON r.config_id = c.id
    """)
    rows = cursor.fetchall()
    conn.close()
    
    reports = []
    for row in rows:
        reports.append({
            'id': row['id'],
            'name': row['name'],
            'configId': row['config_id'],
            'configName': row['config_name'],
            'createdAt': row['created_at']
        })
    
    return jsonify(reports)

@app.route('/api/reports/<report_id>', methods=['GET'])
def get_report(report_id):
    """Get a specific report"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT report_data FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'error': 'Report not found'}), 404
    
    return jsonify(json.loads(row['report_data']))

# Serve React frontend in production
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# Initialize database and start server
if __name__ == '__main__':
    init_db()
    app.run(debug=True)

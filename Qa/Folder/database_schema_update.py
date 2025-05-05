# Add this to your database initialization script

def initialize_database_with_folders(self):
    """Initialize database with tables for documents, knowledge bases, and folders"""
    # Create knowledge_bases table
    self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_bases (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE,
            directory TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    
    # Create folders table
    self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS folders (
            id TEXT PRIMARY KEY,
            kb_id TEXT,
            folder_path TEXT,
            folder_name TEXT,
            file_count INTEGER,
            processed_files INTEGER DEFAULT 0,
            conversion_status TEXT,
            conversion_progress INTEGER DEFAULT 0,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (kb_id) REFERENCES knowledge_bases (id)
        )
    ''')
    
    # Create documents table with folder_id reference
    self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            kb_id TEXT,
            folder_id TEXT NULL,
            original_filename TEXT,
            original_path TEXT,
            relative_path TEXT NULL,
            is_scanned BOOLEAN,
            conversion_status TEXT,
            conversion_progress INTEGER DEFAULT 0,
            converted_path TEXT NULL,
            page_count INTEGER NULL,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (kb_id) REFERENCES knowledge_bases (id),
            FOREIGN KEY (folder_id) REFERENCES folders (id)
        )
    ''')
    
    # Create indices
    self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_kb_id ON documents (kb_id)")
    self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_folder_id ON documents (folder_id)")
    self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_folders_kb_id ON folders (kb_id)")
    
    self.conn.commit()

# Function to update existing database to add folders support
def update_database_schema_for_folders(self):
    """Update existing database to add folders support"""
    # Check if folders table exists
    self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='folders'")
    if self.cursor.fetchone() is None:
        # Create folders table
        self.cursor.execute('''
            CREATE TABLE folders (
                id TEXT PRIMARY KEY,
                kb_id TEXT,
                folder_path TEXT,
                folder_name TEXT,
                file_count INTEGER,
                processed_files INTEGER DEFAULT 0,
                conversion_status TEXT,
                conversion_progress INTEGER DEFAULT 0,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (kb_id) REFERENCES knowledge_bases (id)
            )
        ''')
        
        # Create index
        self.cursor.execute("CREATE INDEX idx_folders_kb_id ON folders (kb_id)")
    
    # Check if documents table has folder_id and relative_path columns
    self.cursor.execute("PRAGMA table_info(documents)")
    columns = {info[1] for info in self.cursor.fetchall()}
    
    # Add folder_id column if it doesn't exist
    if 'folder_id' not in columns:
        self.cursor.execute("ALTER TABLE documents ADD COLUMN folder_id TEXT NULL REFERENCES folders(id)")
        self.cursor.execute("CREATE INDEX idx_documents_folder_id ON documents (folder_id)")
    
    # Add relative_path column if it doesn't exist
    if 'relative_path' not in columns:
        self.cursor.execute("ALTER TABLE documents ADD COLUMN relative_path TEXT NULL")
    
    self.conn.commit()

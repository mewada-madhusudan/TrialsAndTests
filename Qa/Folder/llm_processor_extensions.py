# Extend the LLMProcessor class with these methods

def add_folder_to_kb(self, kb_name, folder_path, folder_name, file_count):
    """
    Add a folder to a knowledge base for OCR processing
    
    Args:
        kb_name (str): Knowledge base name
        folder_path (str): Full path to the folder
        folder_name (str): Name of the folder
        file_count (int): Number of PDF files in the folder
        
    Returns:
        str: Folder ID if successful, None otherwise
    """
    # Get knowledge base ID
    kb = self.db_manager.get_knowledge_base_by_name(kb_name)
    if not kb:
        return None
    
    # Add folder to database
    folder_id = self.db_manager.add_folder(
        kb_id=kb["id"],
        folder_path=folder_path,
        folder_name=folder_name,
        file_count=file_count,
        conversion_status="pending"
    )
    
    return folder_id

def get_kb_folders(self, kb_name):
    """
    Get all folders for a knowledge base
    
    Args:
        kb_name (str): Knowledge base name
        
    Returns:
        list: List of folder dictionaries
    """
    # Get knowledge base ID
    kb = self.db_manager.get_knowledge_base_by_name(kb_name)
    if not kb:
        return []
    
    # Get folders from database
    return self.db_manager.get_folders_by_kb_id(kb["id"])

def get_pending_folders(self, kb_name):
    """
    Get all pending folders for a knowledge base
    
    Args:
        kb_name (str): Knowledge base name
        
    Returns:
        list: List of pending folder dictionaries
    """
    # Get knowledge base ID
    kb = self.db_manager.get_knowledge_base_by_name(kb_name)
    if not kb:
        return []
    
    # Get pending folders from database
    return self.db_manager.get_folders_by_status(kb["id"], ["pending", "failed"])

def update_folder_conversion(self, folder_id, status, progress=None, processed_files=None):
    """
    Update folder conversion status
    
    Args:
        folder_id (str): Folder ID
        status (str): New status (pending, in_progress, completed, failed)
        progress (int, optional): Conversion progress percentage
        processed_files (int, optional): Number of processed files
    
    Returns:
        bool: True if successful, False otherwise
    """
    return self.db_manager.update_folder(
        folder_id=folder_id,
        conversion_status=status,
        conversion_progress=progress,
        processed_files=processed_files
    )


# Extend the DatabaseManager class with these methods

def add_folder(self, kb_id, folder_path, folder_name, file_count, conversion_status="pending"):
    """
    Add a folder to the database
    
    Args:
        kb_id (str): Knowledge base ID
        folder_path (str): Full path to the folder
        folder_name (str): Name of the folder
        file_count (int): Number of PDF files in the folder
        conversion_status (str): Initial conversion status
        
    Returns:
        str: Folder ID if successful, None otherwise
    """
    import uuid
    
    folder_id = str(uuid.uuid4())
    
    # Create folder entry
    self.cursor.execute('''
        INSERT INTO folders (
            id, kb_id, folder_path, folder_name, file_count, 
            conversion_status, conversion_progress, processed_files,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    ''', (
        folder_id, kb_id, folder_path, folder_name, file_count,
        conversion_status, 0, 0
    ))
    
    self.conn.commit()
    return folder_id

def get_folder_by_id(self, folder_id):
    """
    Get folder by ID
    
    Args:
        folder_id (str): Folder ID
        
    Returns:
        dict: Folder data or None if not found
    """
    self.cursor.execute('''
        SELECT * FROM folders WHERE id = ?
    ''', (folder_id,))
    
    folder = self.cursor.fetchone()
    if folder:
        return dict(folder)
    return None

def get_folders_by_kb_id(self, kb_id):
    """
    Get all folders for a knowledge base
    
    Args:
        kb_id (str): Knowledge base ID
        
    Returns:
        list: List of folder dictionaries
    """
    self.cursor.execute('''
        SELECT * FROM folders 
        WHERE kb_id = ?
        ORDER BY created_at DESC
    ''', (kb_id,))
    
    folders = self.cursor.fetchall()
    return [dict(folder) for folder in folders]

def get_folders_by_status(self, kb_id, statuses):
    """
    Get folders by status
    
    Args:
        kb_id (str): Knowledge base ID
        statuses (list): List of statuses to filter by
        
    Returns:
        list: List of folder dictionaries
    """
    placeholders = ', '.join(['?'] * len(statuses))
    query = f'''
        SELECT * FROM folders 
        WHERE kb_id = ? AND conversion_status IN ({placeholders})
        ORDER BY created_at DESC
    '''
    
    self.cursor.execute(query, [kb_id] + list(statuses))
    
    folders = self.cursor.fetchall()
    return [dict(folder) for folder in folders]

def update_folder(self, folder_id, conversion_status=None, conversion_progress=None, processed_files=None):
    """
    Update folder status
    
    Args:
        folder_id (str): Folder ID
        conversion_status (str, optional): New status
        conversion_progress (int, optional): Conversion progress percentage
        processed_files (int, optional): Number of processed files
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Build update query dynamically
    update_fields = []
    params = []
    
    if conversion_status is not None:
        update_fields.append("conversion_status = ?")
        params.append(conversion_status)
    
    if conversion_progress is not None:
        update_fields.append("conversion_progress = ?")
        params.append(conversion_progress)
    
    if processed_files is not None:
        update_fields.append("processed_files = ?")
        params.append(processed_files)
    
    if not update_fields:
        return False
    
    # Add updated_at timestamp
    update_fields.append("updated_at = datetime('now')")
    
    # Build and execute query
    query = f'''
        UPDATE folders
        SET {', '.join(update_fields)}
        WHERE id = ?
    '''
    params.append(folder_id)
    
    self.cursor.execute(query, params)
    self.conn.commit()
    
    return self.cursor.rowcount > 0

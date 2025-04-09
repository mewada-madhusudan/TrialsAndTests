def import_from_excel(self, table_name, file_path):
    table_config = self.table_configs.get(table_name)
    if not table_config or not table_config.excel_support:
        return False, "Excel import not supported for this table"
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Map display names to DB column names
        display_to_db = {col[1]: col[0] for col in table_config.columns}
        db_to_type = {col[0]: col[2] for col in table_config.columns}
        
        # Get primary key info
        primary_key = table_config.primary_key
        primary_key_display = None
        for col in table_config.columns:
            if col[0] == primary_key:
                primary_key_display = col[1]
                break
        
        cursor = self.conn.cursor()
        
        # Get existing records data for matching
        existing_records = {}
        
        # Get all existing records with their attributes
        columns_str = ", ".join([col[0] for col in table_config.columns])
        cursor.execute(f"SELECT id, {columns_str} FROM {table_name} WHERE is_active = 1")
        columns = [desc[0] for desc in cursor.description]
        
        for row in cursor.fetchall():
            record_data = dict(zip(columns, row))
            # Store by database ID and keep full record data
            existing_records[record_data['id']] = record_data
        
        # Process each row
        new_count = 0
        update_count = 0
        
        for _, row in df.iterrows():
            # Convert Excel row to database format
            db_values = {}
            for display_name, db_name in display_to_db.items():
                if display_name in df.columns and not pd.isna(row.get(display_name)):
                    value = row.get(display_name)
                    data_type = db_to_type.get(db_name)
                    
                    # Handle data type conversion
                    if data_type == "REAL":
                        try:
                            db_values[db_name] = float(value)
                        except (ValueError, TypeError):
                            db_values[db_name] = 0.0
                    elif data_type == "INTEGER":
                        try:
                            db_values[db_name] = int(value)
                        except (ValueError, TypeError):
                            db_values[db_name] = 0
                    else:
                        db_values[db_name] = str(value)
            
            # Try to find a matching record
            matching_id = None
            
            # Use primary key for matching if it exists in the Excel data
            if primary_key_display in df.columns and primary_key in db_values:
                pk_value = db_values[primary_key]
                # Look for a record with matching primary key
                for record_id, record_data in existing_records.items():
                    if str(record_data[primary_key]) == str(pk_value):
                        matching_id = record_id
                        break
            
            # If no match by primary key, try to match by other "unique" columns
            # This is a simplified approach - you might need to define which columns 
            # should be used for matching in your system
            if matching_id is None and db_values:
                potential_matches = []
                for record_id, record_data in existing_records.items():
                    match_score = 0
                    for db_col, value in db_values.items():
                        if db_col in record_data and str(record_data[db_col]) == str(value):
                            match_score += 1
                    
                    # If multiple columns match, consider it a potential match
                    if match_score >= min(2, len(db_values)):
                        potential_matches.append((record_id, match_score))
                
                # Get the best match if any
                if potential_matches:
                    potential_matches.sort(key=lambda x: x[1], reverse=True)
                    matching_id = potential_matches[0][0]
            
            if matching_id is not None:
                # Update existing record
                set_clauses = []
                update_values = []
                
                for db_name, value in db_values.items():
                    set_clauses.append(f"{db_name} = ?")
                    update_values.append(value)
                
                # Always update modified date
                set_clauses.append("modified_date = CURRENT_TIMESTAMP")
                
                # Execute UPDATE
                if set_clauses:
                    sql = f"""
                        UPDATE {table_name} 
                        SET {', '.join(set_clauses)}
                        WHERE id = ?
                    """
                    update_values.append(matching_id)
                    cursor.execute(sql, update_values)
                    update_count += 1
            else:
                # Insert new record
                if db_values:
                    # Insert into database
                    columns_str = ", ".join(db_values.keys())
                    placeholders = ", ".join(["?" for _ in db_values])
                    values = list(db_values.values())
                    
                    sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    cursor.execute(sql, values)
                    new_count += 1
        
        self.conn.commit()
        return True, f"Import completed: {new_count} new records added, {update_count} records updated"
    except Exception as e:
        return False, f"Error importing from Excel: {e}"

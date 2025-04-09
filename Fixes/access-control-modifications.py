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
        
        if not primary_key_display or primary_key_display not in df.columns:
            return False, f"Primary key column '{primary_key_display}' not found in Excel file"
        
        cursor = self.conn.cursor()
        
        # Get existing records for checking duplicates
        existing_records = {}
        cursor.execute(f"SELECT {primary_key} FROM {table_name} WHERE is_active = 1")
        for row in cursor.fetchall():
            existing_records[row[0]] = True
        
        # Process each row
        new_count = 0
        update_count = 0
        
        for _, row in df.iterrows():
            # Get primary key value for this row
            pk_value = row.get(primary_key_display)
            if pd.isna(pk_value):
                continue  # Skip rows without primary key
            
            pk_value = str(pk_value) if pk_value is not None else ""
            
            # Check if record exists
            record_exists = pk_value in existing_records
            
            # Prepare column names and values
            db_columns = []
            values = []
            
            # First, get all available columns from Excel
            excel_values = {}
            for display_name, db_name in display_to_db.items():
                if display_name in df.columns:
                    value = row.get(display_name)
                    data_type = db_to_type.get(db_name)
                    
                    # Handle data type conversion
                    if data_type == "REAL" and pd.notna(value):
                        try:
                            excel_values[db_name] = float(value)
                        except (ValueError, TypeError):
                            excel_values[db_name] = 0.0
                    elif data_type == "INTEGER" and pd.notna(value):
                        try:
                            excel_values[db_name] = int(value)
                        except (ValueError, TypeError):
                            excel_values[db_name] = 0
                    else:
                        excel_values[db_name] = str(value) if pd.notna(value) else ""
            
            if record_exists:
                # Update existing record
                set_clauses = []
                update_values = []
                
                for db_name, value in excel_values.items():
                    if db_name != primary_key:  # Don't update primary key
                        set_clauses.append(f"{db_name} = ?")
                        update_values.append(value)
                
                # Always update modified date
                set_clauses.append("modified_date = CURRENT_TIMESTAMP")
                
                # Add primary key value for WHERE clause
                update_values.append(pk_value)
                
                # Execute UPDATE
                if set_clauses:
                    sql = f"""
                        UPDATE {table_name} 
                        SET {', '.join(set_clauses)}
                        WHERE {primary_key} = ? AND is_active = 1
                    """
                    cursor.execute(sql, update_values)
                    update_count += 1
            else:
                # Insert new record
                db_columns = list(excel_values.keys())
                values = [excel_values[col] for col in db_columns]
                
                if db_columns:
                    # Insert into database
                    columns_str = ", ".join(db_columns)
                    placeholders = ", ".join(["?" for _ in db_columns])
                    
                    sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    cursor.execute(sql, values)
                    new_count += 1
                    existing_records[pk_value] = True  # Add to existing records
        
        self.conn.commit()
        return True, f"Import completed: {new_count} new records added, {update_count} records updated"
    except Exception as e:
        return False, f"Error importing from Excel: {e}"

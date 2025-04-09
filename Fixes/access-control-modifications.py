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
        
        # Get existing primary keys
        existing_records = set()
        cursor.execute(f"SELECT {primary_key} FROM {table_name} WHERE is_active = 1")
        for row in cursor.fetchall():
            if row[0]:  # Only add non-empty values
                existing_records.add(str(row[0]))
        
        # Process each row
        new_count = 0
        update_count = 0
        
        for _, row in df.iterrows():
            # Convert Excel row to database column format
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
            
            # Check if primary key exists and is in Excel
            pk_value = None
            if primary_key in db_values:
                pk_value = str(db_values[primary_key])
                
            # Decide whether to update or insert
            if pk_value and pk_value in existing_records:
                # UPDATE: Record with this primary key exists
                set_clauses = []
                update_values = []
                
                for db_name, value in db_values.items():
                    if db_name != primary_key:  # Don't update primary key
                        set_clauses.append(f"{db_name} = ?")
                        update_values.append(value)
                
                # Always update modified date
                set_clauses.append("modified_date = CURRENT_TIMESTAMP")
                
                # Add primary key for WHERE clause
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
                # INSERT: No matching record found, or primary key not in Excel
                if db_values:
                    # Remove primary key if it's empty or null
                    if primary_key in db_values and not db_values[primary_key]:
                        del db_values[primary_key]
                    
                    # Insert into database
                    columns = list(db_values.keys())
                    placeholders = ", ".join(["?" for _ in columns])
                    values = [db_values[col] for col in columns]
                    
                    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                    cursor.execute(sql, values)
                    new_count += 1
        
        self.conn.commit()
        return True, f"Import completed: {new_count} new records added, {update_count} records updated"
    except Exception as e:
        return False, f"Error importing from Excel: {e}"

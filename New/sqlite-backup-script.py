import os
import shutil
import sqlite3
from datetime import datetime
import glob

def backup_sqlite_db(source_path, backup_dir, keep_count=5):
    """
    Backup a SQLite database to another location and keep only the most recent backups.
    
    Args:
        source_path (str): Full path to the source SQLite database
        backup_dir (str): Directory where backups will be stored
        keep_count (int): Number of recent backups to keep
    """
    # Ensure the backup directory exists
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Create a timestamped filename for the backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_filename = os.path.basename(source_path)
    backup_filename = f"{os.path.splitext(db_filename)[0]}_{timestamp}{os.path.splitext(db_filename)[1]}"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    # Check if the source database is accessible
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source database not found: {source_path}")
    
    # Connect to the database to ensure it's not corrupted
    try:
        conn = sqlite3.connect(source_path)
        conn.close()
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Error connecting to source database: {e}")
    
    # Perform the backup
    try:
        # Method 1: Simple file copy (works when the database is not in use)
        shutil.copy2(source_path, backup_path)
        print(f"Backup created: {backup_path}")
    except shutil.Error as e:
        # Method 2: Use SQLite's backup API (works even if the database is in use)
        try:
            source_conn = sqlite3.connect(source_path)
            backup_conn = sqlite3.connect(backup_path)
            source_conn.backup(backup_conn)
            source_conn.close()
            backup_conn.close()
            print(f"Backup created using SQLite backup API: {backup_path}")
        except sqlite3.Error as e2:
            raise Exception(f"Failed to backup database: {e} then {e2}")
    
    # Keep only the most recent backups
    all_backups = glob.glob(os.path.join(backup_dir, f"{os.path.splitext(db_filename)[0]}_*{os.path.splitext(db_filename)[1]}"))
    all_backups.sort(key=os.path.getmtime, reverse=True)  # Sort by modification time, newest first
    
    # Remove older backups beyond the keep_count
    if len(all_backups) > keep_count:
        for old_backup in all_backups[keep_count:]:
            try:
                os.remove(old_backup)
                print(f"Removed old backup: {old_backup}")
            except OSError as e:
                print(f"Error removing old backup {old_backup}: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Backup SQLite database and keep N most recent copies')
    parser.add_argument('source', help='Path to the source SQLite database')
    parser.add_argument('backup_dir', help='Directory to store backups')
    parser.add_argument('--keep', type=int, default=5, help='Number of recent backups to keep (default: 5)')
    
    args = parser.parse_args()
    
    try:
        backup_sqlite_db(args.source, args.backup_dir, args.keep)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

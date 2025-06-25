import sqlite3
import pyodbc

def get_sqlite_schema_and_data(sqlite_db_path):
    conn = sqlite3.connect(sqlite_db_path)
    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    schema = {}
    data = {}

    for table in tables:
        # Get create statement
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
        create_stmt = cursor.fetchone()[0]

        # Get data
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        col_names = [description[0] for description in cursor.description]

        schema[table] = create_stmt
        data[table] = {"columns": col_names, "rows": rows}

    conn.close()
    return schema, data

def convert_sqlite_to_access(sqlite_db_path, access_db_path):
    # Step 1: Extract schema and data from SQLite
    schema, data = get_sqlite_schema_and_data(sqlite_db_path)

    # Step 2: Connect to Access DB
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={access_db_path};"
    )
    access_conn = pyodbc.connect(conn_str)
    access_cursor = access_conn.cursor()

    for table, create_stmt in schema.items():
        # Replace SQLite types with Access types (basic mapping)
        create_stmt = create_stmt.replace("AUTOINCREMENT", "AUTOINCREMENT")
        create_stmt = create_stmt.replace("INTEGER", "INT")
        create_stmt = create_stmt.replace("TEXT", "TEXT")
        create_stmt = create_stmt.replace("REAL", "DOUBLE")

        try:
            print(f"Creating table {table}...")
            access_cursor.execute(f"DROP TABLE {table}")  # Just in case
        except:
            pass

        access_cursor.execute(create_stmt)

        # Insert data
        rows = data[table]["rows"]
        cols = data[table]["columns"]
        placeholders = ','.join(['?'] * len(cols))
        col_names = ','.join(cols)

        print(f"Inserting {len(rows)} rows into {table}...")
        for row in rows:
            access_cursor.execute(
                f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})", row
            )

    access_conn.commit()
    access_cursor.close()
    access_conn.close()
    print("Migration complete!")

# ==== Example Usage ====
sqlite_file = r"C:\path\to\your\source.sqlite"
access_file = r"C:\path\to\your\target.accdb"

convert_sqlite_to_access(sqlite_file, access_file)

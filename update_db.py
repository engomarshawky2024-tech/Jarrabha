import sqlite3
import os

db_path = 'instance/jarrabha.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE course ADD COLUMN thumbnail_url VARCHAR(500);")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()

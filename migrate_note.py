import sqlite3
import os

DB_PATH = "data/database.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Skipping migration (it will be created with new schema on start).")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(mini_programs)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "note" not in columns:
            print("Adding 'note' column to mini_programs table...")
            cursor.execute("ALTER TABLE mini_programs ADD COLUMN note TEXT")
            conn.commit()
            print("Migration successful.")
        else:
            print("'note' column already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

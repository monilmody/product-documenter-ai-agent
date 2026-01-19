# migrate_database.py
import sqlite3
from activity_tracker import ActivityTracker

def migrate_existing_database():
    tracker = ActivityTracker("documenter.db")
    tracker.add_file_path_column_if_missing()
    
    # Also check for other missing columns
    conn = sqlite3.connect("documenter.db")
    cursor = conn.cursor()
    
    # Check activities table
    cursor.execute("PRAGMA table_info(activities)")
    activity_columns = [col[1] for col in cursor.fetchall()]
    
    if 'human_time_seconds' not in activity_columns:
        cursor.execute("ALTER TABLE activities ADD COLUMN human_time_seconds INTEGER DEFAULT 0")
        print("✅ Added 'human_time_seconds' column to activities table")
    
    conn.commit()
    conn.close()
    
    print("✅ Database migration completed!")

if __name__ == "__main__":
    migrate_existing_database()
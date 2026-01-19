import sqlite3
import json
from datetime import datetime
import os
from pathlib import Path
import traceback

class ActivityTracker:
    def __init__(self, db_path="documenter.db"):
        """Initialize activity tracker with SQLite database"""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Activities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                activity_type TEXT,
                source TEXT,
                details TEXT,
                ai_tokens_used INTEGER DEFAULT 0,
                ai_cost REAL DEFAULT 0,
                human_time_seconds INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER REFERENCES activities(id),
                doc_type TEXT,
                draft_content TEXT,
                final_content TEXT,
                filename TEXT,
                review_filepath TEXT,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                reviewed_at DATETIME,
                review_time_seconds INTEGER,
                quality_score REAL
            )
        ''')
        
        # AI costs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                provider TEXT,
                model TEXT,
                tokens_used INTEGER,
                cost REAL,
                prompt_hash TEXT,
                activity_id INTEGER REFERENCES activities(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized at {self.db_path}")
    
    def log_activity(self, activity_type, source, details):
        """Log a new activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO activities (activity_type, source, details)
            VALUES (?, ?, ?)
        ''', (activity_type, source, json.dumps(details)))
        
        activity_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return activity_id
    
    def update_activity_cost(self, activity_id, ai_tokens=0, ai_cost=0.0, provider="openai"):
        """Update activity with AI cost information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE activities 
            SET ai_tokens_used = ?, ai_cost = ?, status = 'generated'
            WHERE id = ?
        ''', (ai_tokens, ai_cost, activity_id))
        
        conn.commit()
        conn.close()
    
    def complete_activity(self, activity_id, human_time_seconds):
        """Mark activity as completed with human review time"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE activities 
            SET human_time_seconds = ?, status = 'completed'
            WHERE id = ?
        ''', (human_time_seconds, activity_id))
        
        conn.commit()
        conn.close()
    
    def save_document(self, activity_id, doc_type, draft_content, filename=None):
        """Save document to database"""
        try:
            conn = sqlite3.connect(self.db_path)  # FIX: Use sqlite3.connect directly
            cursor = conn.cursor()
            
            # Generate a filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{doc_type}_{activity_id}_{timestamp}.md"
            
            # Check if filename column exists
            cursor.execute("PRAGMA table_info(documents)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'filename' not in columns:
                print("⚠️ Adding filename column to documents table...")
                cursor.execute("ALTER TABLE documents ADD COLUMN filename TEXT")
                conn.commit()
            
            cursor.execute('''
                INSERT INTO documents (activity_id, doc_type, draft_content, filename, generated_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            ''', (activity_id, doc_type, draft_content, filename))
            
            doc_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"📄 Document saved: ID={doc_id}, filename={filename}")
            return doc_id
            
        except Exception as e:
            print(f"❌ Error saving document: {e}")
            traceback.print_exc()
            return None

    def update_document_review_path(self, doc_id, review_filepath):
        """Update document with review filepath"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if review_filepath column exists
            cursor.execute("PRAGMA table_info(documents)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'review_filepath' not in columns:
                print("⚠️ Adding review_filepath column to documents table...")
                cursor.execute("ALTER TABLE documents ADD COLUMN review_filepath TEXT")
                conn.commit()
            
            cursor.execute('''
                UPDATE documents 
                SET review_filepath = ?
                WHERE id = ?
            ''', (review_filepath, doc_id))
            
            conn.commit()
            conn.close()
            print(f"✅ Updated document {doc_id} with review path: {review_filepath}")
            return True
        except Exception as e:
            print(f"❌ Error updating document review path: {e}")
            return False
        
    def update_document(self, doc_id, final_content, review_time_seconds, quality_score=0.8):
        """Update document with reviewed version"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE documents 
            SET final_content = ?, reviewed_at = CURRENT_TIMESTAMP,
                review_time_seconds = ?, quality_score = ?
            WHERE id = ?
        ''', (final_content, review_time_seconds, quality_score, doc_id))
        
        conn.commit()
        conn.close()
    
    def get_recent_activities(self, days=7):
        """Get recent activities for analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                id,
                timestamp,
                activity_type,
                source,
                ai_tokens_used,
                ai_cost,
                human_time_seconds,
                status
            FROM activities
            WHERE timestamp >= datetime('now', ?)
            ORDER BY timestamp DESC
        ''', (f'-{days} days',))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        conn.close()
        return results
    
    def get_stats(self):
        """Get basic statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_activities,
                SUM(ai_cost) as total_ai_cost,
                SUM(human_time_seconds) as total_human_time,
                AVG(human_time_seconds) as avg_review_time
            FROM activities
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "total_activities": result[0] or 0,
                "total_ai_cost": result[1] or 0.0,
                "total_human_time": result[2] or 0,
                "avg_review_time": result[3] or 0
            }
        return {
            "total_activities": 0,
            "total_ai_cost": 0.0,
            "total_human_time": 0,
            "avg_review_time": 0
        }

# Test the tracker
if __name__ == "__main__":
    tracker = ActivityTracker("test.db")
    print("✅ Activity tracker created successfully")
    
    # Test logging
    test_id = tracker.log_activity(
        activity_type="test",
        source="test_script",
        details={"message": "Testing activity tracker"}
    )
    print(f"✅ Logged activity ID: {test_id}")
    
    stats = tracker.get_stats()
    print(f"✅ Stats: {stats}")
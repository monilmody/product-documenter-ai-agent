import sqlite3
import json
from datetime import datetime

def setup_database():
    """Create the database with all required tables"""
    
    print("🔧 Setting up Product Documenter Database...")
    
    conn = sqlite3.connect('documenter.db')
    cursor = conn.cursor()
    
    # 1. Activities Table
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
    
    # 2. Documents Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER,
            doc_type TEXT,
            draft_content TEXT,
            final_content TEXT,
            generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            reviewed_at DATETIME,
            review_time_seconds INTEGER,
            quality_score REAL
        )
    ''')
    
    # 3. AI Costs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            provider TEXT,
            model TEXT,
            tokens_used INTEGER,
            cost REAL,
            activity_id INTEGER
        )
    ''')
    
    # 4. Monthly Budget Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_budget (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month_year TEXT,
            budget REAL,
            spent REAL DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Database setup complete!")
    print("📊 Tables created: activities, documents, ai_costs, monthly_budget")
    
    return True

if __name__ == "__main__":
    setup_database()
    
    print("\n" + "="*60)
    print("🎉 DATABASE READY!")
    print("="*60)
    print("\nNow run:")
    print("1. python api_server.py")
    print("2. In another terminal: streamlit run monitor_dashboard.py")
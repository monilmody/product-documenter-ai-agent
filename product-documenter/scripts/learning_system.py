import sqlite3
import difflib
import json
from datetime import datetime, timedelta
import hashlib

class LearningSystem:
    def __init__(self, db_path="documenter.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize learning database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,
                context TEXT,
                correction TEXT,
                learned_from_doc_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                applied_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_name TEXT,
                metric_value REAL,
                recommendation TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _calculate_hash(self, text):
        """Calculate hash for text to identify patterns"""
        return hashlib.md5(text.encode()).hexdigest()[:10]
    
    def extract_patterns(self, original, revised):
        """Extract patterns from human edits"""
        patterns = []
        
        # Simple diff analysis
        original_lines = original.split('\n')
        revised_lines = revised.split('\n')
        
        diff = list(difflib.unified_diff(
            original_lines,
            revised_lines,
            lineterm='',
            n=3
        ))
        
        # Analyze diff for patterns
        changes = []
        for line in diff:
            if line.startswith('- ') and not line.startswith('---'):
                changes.append(('remove', line[2:]))
            elif line.startswith('+ ') and not line.startswith('+++'):
                changes.append(('add', line[2:]))
        
        if changes:
            # Group by change type
            removals = [c[1] for c in changes if c[0] == 'remove']
            additions = [c[1] for c in changes if c[0] == 'add']
            
            if removals:
                patterns.append({
                    "type": "content_removed",
                    "examples": removals[:3],
                    "count": len(removals),
                    "hash": self._calculate_hash('\n'.join(removals[:2]))
                })
            
            if additions:
                patterns.append({
                    "type": "content_added",
                    "examples": additions[:3],
                    "count": len(additions),
                    "hash": self._calculate_hash('\n'.join(additions[:2]))
                })
        
        return patterns
    
    def save_feedback(self, doc_id, original, revised, review_time, doc_type="unknown"):
        """Save learning from human feedback"""
        patterns = self.extract_patterns(original, revised)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for pattern in patterns:
            cursor.execute('''
                INSERT INTO learning_patterns 
                (pattern_type, context, correction, learned_from_doc_id)
                VALUES (?, ?, ?, ?)
            ''', (
                pattern['type'],
                f"Doc type: {doc_type}",
                json.dumps(pattern),
                doc_id
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Saved {len(patterns)} learning patterns from document {doc_id}")
        return len(patterns)
    
    def apply_learnings(self, new_content, content_type="technical"):
        """Apply learned patterns to improve new content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pattern_type, correction, applied_count
            FROM learning_patterns 
            WHERE context LIKE ?
            ORDER BY applied_count DESC
            LIMIT 10
        ''', (f'%{content_type}%',))
        
        patterns = cursor.fetchall()
        improved_content = new_content
        
        for pattern_type, correction_json, applied_count in patterns:
            pattern = json.loads(correction_json)
            
            # Simple pattern application examples
            if pattern_type == "content_removed":
                # If certain phrases were commonly removed, avoid them
                for example in pattern.get('examples', []):
                    if example in improved_content:
                        print(f"⚠️  Removing pattern: {example[:50]}...")
                        # Mark as applied
                        cursor.execute('''
                            UPDATE learning_patterns 
                            SET applied_count = applied_count + 1
                            WHERE correction = ?
                        ''', (correction_json,))
            
            elif pattern_type == "content_added":
                # If certain phrases were commonly added, consider including them
                example = pattern.get('examples', [''])[0]
                if example and example not in improved_content:
                    print(f"➕ Adding learned pattern: {example[:50]}...")
                    # Mark as applied
                    cursor.execute('''
                        UPDATE learning_patterns 
                        SET applied_count = applied_count + 1
                        WHERE correction = ?
                    ''', (correction_json,))
        
        conn.commit()
        conn.close()
        return improved_content
    
    def generate_insights(self, days=7):
        """Generate improvement insights"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        insights = []
        
        # Insight 1: Review time trends
        cursor.execute('''
            SELECT 
                AVG(review_time_seconds)/60 as avg_review_minutes,
                COUNT(*) as docs_reviewed
            FROM documents
            WHERE reviewed_at >= datetime('now', ?)
        ''', (f'-{days} days',))
        
        review_data = cursor.fetchone()
        if review_data and review_data[1] > 0:
            avg_minutes = review_data[0] or 0
            insights.append({
                "metric_name": "avg_review_time_minutes",
                "metric_value": avg_minutes,
                "recommendation": f"Average review time: {avg_minutes:.1f} minutes. Target: under 5 minutes."
            })
        
        # Insight 2: Pattern frequency
        cursor.execute('''
            SELECT pattern_type, COUNT(*) as frequency
            FROM learning_patterns
            WHERE created_at >= datetime('now', ?)
            GROUP BY pattern_type
            ORDER BY frequency DESC
        ''', (f'-{days} days',))
        
        patterns = cursor.fetchall()
        for pattern_type, frequency in patterns:
            if frequency > 2:  # Only significant patterns
                action = "Reduce" if "removed" in pattern_type else "Include"
                insights.append({
                    "metric_name": f"pattern_{pattern_type}",
                    "metric_value": frequency,
                    "recommendation": f"{action} content matching pattern: {pattern_type} (occurred {frequency} times)"
                })
        
        # Save insights
        for insight in insights:
            cursor.execute('''
                INSERT INTO insights (metric_name, metric_value, recommendation)
                VALUES (?, ?, ?)
            ''', (insight['metric_name'], insight['metric_value'], insight['recommendation']))
        
        conn.commit()
        conn.close()
        
        return insights

# Test
if __name__ == "__main__":
    learner = LearningSystem("test.db")
    
    # Test pattern extraction
    original = "The API endpoint returns data in JSON format."
    revised = "The API endpoint returns data in JSON format with error handling."
    
    patterns = learner.extract_patterns(original, revised)
    print(f"✅ Extracted {len(patterns)} patterns")
    
    insights = learner.generate_insights(1)
    print(f"✅ Generated {len(insights)} insights")
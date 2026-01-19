"""
Complete API Server for Product Documenter AI
"""

import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import traceback
import signal

load_dotenv(override=True)

# Initialize Flask
app = Flask(__name__)

# Import local modules
try:
    from document_generator import EnhancedDocumentGenerator
    from activity_tracker import ActivityTracker
    from learning_system import LearningSystem
    from review_workflow import ReviewWorkflow
    
    MODULES_AVAILABLE = True
    print("✅ All modules loaded successfully")
    
except ImportError as e:
    print(f"⚠️  Missing module: {e}")
    print("   Creating simplified versions...")
    MODULES_AVAILABLE = False
    
    # Create simplified versions if modules missing
    class ActivityTracker:
        def __init__(self, db_path="documenter.db"):
            self.db_path = db_path
        
        def log_activity(self, activity_type, source, details):
            return 1
        
        def update_activity_cost(self, activity_id, ai_tokens, ai_cost, provider):
            pass
        
        def save_document(self, activity_id, doc_type, draft_content):
            return 1

# Initialize components
if MODULES_AVAILABLE:
    tracker = ActivityTracker("documenter.db")
    learner = LearningSystem("documenter.db")
    generator = EnhancedDocumentGenerator()
    
    # Create docs folder if it doesn't exist
    os.makedirs("docs/review", exist_ok=True)
    os.makedirs("docs/approved", exist_ok=True)
    os.makedirs("docs/licensing_ready", exist_ok=True)
    
    workflow = ReviewWorkflow("docs")
else:
    tracker = None
    learner = None
    generator = None
    workflow = None

# Routes
@app.route('/')
def home():
    return jsonify({
        "service": "Product Documenter AI",
        "version": "1.0",
        "status": "running",
        "openai_available": generator.client is not None if generator else False,
        "modules_available": MODULES_AVAILABLE,
        "endpoints": {
            "GET /health": "Check system health",
            "POST /generate": "Generate documentation",
            "GET /costs": "Get cost analysis",
            "GET /insights": "Get improvement insights",
            "POST /submit-review": "Submit reviewed document",
            "POST /create-licensing-package": "Create licensing package"
        }
    })
    
@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Shutdown the API server gracefully"""
    print("🔴 Shutdown signal received")
    os.kill(os.getpid(), signal.SIGINT)
    return 'Server shutting down...', 200

@app.route('/health', methods=['GET'])
def health():
    """Check system health"""
    try:
        # Check database
        conn = sqlite3.connect('documenter.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
        table_count = cursor.fetchone()[0]
        conn.close()
        
        # Check OpenAI
        openai_configured = generator and generator.client is not None
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database_tables": table_count,
            "openai_configured": openai_configured,
            "modules_loaded": MODULES_AVAILABLE,
            "docs_folder_exists": os.path.exists("docs")
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/generate', methods=['POST'])
def generate_docs():
    """Generate documentation with cost tracking"""
    try:
        data = request.get_json()
        
        if not data or 'context' not in data:
            return jsonify({"error": "Missing 'context' in request"}), 400
        
        if not generator:
            return jsonify({"error": "Document generator not available"}), 500
        
        # Log activity
        activity_id = tracker.log_activity(
            activity_type="documentation_generation",
            source=data.get('source', 'api'),
            details={
                "doc_type": data.get('doc_type', 'technical_spec'),
                "context_length": len(data['context']),
                "licensing_focus": data.get('licensing_focus', False)
            }
        ) if tracker else 1
        
        # Generate documentation
        result = generator.generate_document(
            doc_type=data.get('doc_type', 'technical_spec'),
            context=data['context'],
            features=data.get('features')
        )
        
        # Log cost to database
        if tracker:
            generator.log_cost_to_db(activity_id, result)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{data.get('doc_type', 'technical_spec')}_{activity_id}_{timestamp}.md"
        
        # Save document to database WITH filename
        doc_id = tracker.save_document(
            activity_id=activity_id,
            doc_type=data.get('doc_type', 'technical_spec'),
            draft_content=result['content'],
            filename=filename  # <-- Pass filename here
        ) if tracker else 1
        
        # Add to review workflow if licensing focused
        review_path = None
        if data.get('licensing_focus', False) and workflow:
            metadata = {
                "doc_id": doc_id,
                "doc_type": data.get('doc_type', 'technical_spec'),
                "filename": filename,
                "cost": result['cost'],
                "tokens": result['tokens'],
                "model": result['model'],
                "generated_at": result['generated_at'],
                "activity_id": activity_id
            }
            
            review_path = workflow.save_for_review(
                doc_id=doc_id,
                content=result['content'],
                doc_type=data.get('doc_type', 'technical_spec'),
                metadata=metadata,
            )
        
        # Update database with review filepath
        if tracker and review_path:
            tracker.update_document_review_path(doc_id, review_path)
                
        response_data = {
            "status": "success",
            "activity_id": activity_id,
            "document_id": doc_id,
            "filename": filename,
            "content": result['content'],
            "tokens": result['tokens'],
            "cost": result['cost'],
            "model": result['model'],
            "provider": result['provider'],
            "openai_used": result['provider'] == 'openai',
            "needs_review": data.get('licensing_focus', False),
            "message": "Document generated successfully"
        }
        
        if review_path:
            response_data["review_path"] = review_path
            response_data["message"] += ". Document saved for review."
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/costs', methods=['GET'])
def get_costs():
    """Get cost analysis"""
    try:
        days = request.args.get('days', 30, type=int)
        
        conn = sqlite3.connect('documenter.db', check_same_thread=False)
        
        # Get cost data
        cost_df = pd.read_sql_query(f"""
            SELECT 
                DATE(timestamp) as date,
                SUM(ai_cost) as daily_cost,
                SUM(ai_tokens_used) as daily_tokens,
                COUNT(*) as requests
            FROM activities
            WHERE DATE(timestamp) >= DATE('now', '-{days} days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """, conn)
        
        # Get total stats
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_activities,
                SUM(ai_cost) as total_cost,
                SUM(ai_tokens_used) as total_tokens
            FROM activities
        """)
        
        total_stats = cursor.fetchone()
        conn.close()
        
        if total_stats and total_stats[0]:
            total_activities, total_cost, total_tokens = total_stats
        else:
            total_activities, total_cost, total_tokens = 0, 0, 0
        
        # Calculate averages
        avg_cost_per_doc = total_cost / total_activities if total_activities > 0 else 0
        
        return jsonify({
            "period_days": days,
            "total_activities": int(total_activities),
            "total_cost": float(total_cost or 0),
            "total_tokens": int(total_tokens or 0),
            "avg_cost_per_document": float(avg_cost_per_doc),
            "daily_breakdown": cost_df.to_dict('records') if not cost_df.empty else []
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/submit-review', methods=['POST'])
def submit_review():
    """Submit reviewed document"""
    try:
        if not workflow:
            return jsonify({"error": "Review workflow not available"}), 500
        
        data = request.get_json()
        
        required = ['filepath', 'changes_summary', 'reviewer_name']
        for field in required:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        filepath = data['filepath']
        
        # Verify file exists
        if not os.path.exists(filepath):
            return jsonify({"error": f"File not found: {filepath}"}), 404
        
        # Read the ENTIRE file content directly
        with open(filepath, 'r', encoding='utf-8') as f:
            full_content = f.read()
        
        print(f"📄 Read file: {len(full_content)} characters")
        print(f"📄 First 200 chars: {full_content[:200]}...")
        
 # Don't rely on workflow.submit_review for content - use what we read
        reviewed_path = None
        try:
            # Try to submit to workflow (for metadata/tracking)
            reviewed_path, metadata = workflow.submit_review(
                filepath=filepath,
                reviewed_content=full_content,
                changes_summary=data['changes_summary'],
                reviewer_name=data['reviewer_name']
            )
        except Exception as e:
            print(f"⚠️ Workflow error (will continue anyway): {e}")
            # Create reviewed path manually
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            reviewed_filename = f"reviewed_{os.path.basename(filepath)}"
            reviewed_path = os.path.join("docs/review", reviewed_filename)
        
        database_updated = False
        doc_id = None
        activity_id = None
        
        try:
            # Simple approach: Update the MOST RECENT document
            conn = sqlite3.connect('documenter.db')
            cursor = conn.cursor()
            
            # Extract filename from the filepath
            submitted_filename = os.path.basename(filepath)
            
            # Look for document by filename (remove "review_" prefix if present)
            # Look for document by filename (remove "reviewed_" prefix if present)
            search_filename = submitted_filename
            if search_filename.startswith("review_"):
                search_filename = search_filename[7:]
            if search_filename.startswith("reviewed_"):
                search_filename = search_filename[9:]
                            
            print(f"🔍 Searching for filename containing: {search_filename}")
            
            # Try multiple search strategies
            search_patterns = [
                f"%{search_filename}%",
                f"%{submitted_filename}%",
                f"%{search_filename.replace('reviewed_', '')}%",
                f"%{search_filename.replace('review_', '')}%"
            ]
            
            result = None
            for pattern in search_patterns:
                cursor.execute('''
                    SELECT id, activity_id, filename FROM documents 
                    WHERE filename LIKE ? OR review_filepath LIKE ?
                    ORDER BY id DESC LIMIT 1
                ''', (pattern, pattern))
                
                result = cursor.fetchone()
                if result:
                    print(f"✅ Found with pattern: {pattern}")
                    break
            
            if result:
                doc_id, activity_id, found_filename = result
                print(f"✅ Found document: ID={doc_id}, filename={found_filename}")

                # Update document with reviewed content
                cursor.execute('''
                    UPDATE documents 
                    SET final_content = ?, reviewed_at = datetime('now'),
                        review_time_seconds = 300, quality_score = 0.8
                    WHERE id = ?
                ''', (full_content, doc_id))
                
               # Update activity status
                if activity_id:
                    cursor.execute('''
                        UPDATE activities 
                        SET human_time_seconds = 300, status = 'completed'
                        WHERE id = ?
                    ''', (activity_id,))
                
                # Update review filepath if we have it
                if reviewed_path:
                    cursor.execute("SELECT * FROM pragma_table_info('documents') WHERE name='review_filepath';")
                    if cursor.fetchone():
                        cursor.execute('''
                            UPDATE documents 
                            SET review_filepath = ?
                            WHERE id = ?
                        ''', (reviewed_path, doc_id))
                        print(f"✅ Updated review_filepath: {reviewed_path}")
                
                conn.commit()
                
                # Verify the update
                cursor.execute('SELECT LENGTH(final_content) FROM documents WHERE id = ?', (doc_id,))
                content_length = cursor.fetchone()[0]
                print(f"✅ Database updated! Content length: {content_length} characters")
                database_updated = True
                
            else:
                print("⚠️ No matching document found in database")
                print("   Available documents:")
                cursor.execute("SELECT id, filename, review_filepath FROM documents ORDER BY id DESC LIMIT 10;")
                for row in cursor.fetchall():
                    print(f"   - ID {row[0]}: filename='{row[1]}', review_path='{row[2]}'")
                    
        except Exception as db_error:
            print(f"❌ Database update error: {db_error}")
            traceback.print_exc()
            database_updated = False
        finally:
            try:
                conn.close()
            except:
                pass
        
        # Prepare for licensing if requested
        licensing_path = None
        if data.get('prepare_for_licensing', False):
            licensing_path = workflow.prepare_for_licensing(
                reviewed_filepath=reviewed_path,
                additional_metadata=data.get('additional_metadata')
            )
        
        return jsonify({
            "status": "success",
            "reviewed_path": reviewed_path,
            "licensing_path": licensing_path,
            "message": "Review submitted successfully"
        })
        
    except Exception as e:
        print(f"❌ Error in submit-review: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/create-licensing-package', methods=['POST'])
def create_licensing_package():
    """Create complete licensing package"""
    try:
        if not workflow:
            return jsonify({"error": "Review workflow not available"}), 500
        
        data = request.get_json()
        
        product_name = data.get('product_name', 'Unnamed_Product')
        version = data.get('version', '1.0')
        
        package_path = workflow.generate_licensing_package(
            product_name=product_name,
            version=version
        )
        
        return jsonify({
            "status": "success",
            "package_path": package_path,
            "product_name": product_name,
            "version": version,
            "message": f"Licensing package created for {product_name} v{version}"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/test-openai', methods=['GET'])
def test_openai():
    """Test OpenAI connection"""
    if not generator:
        return jsonify({"error": "Generator not available"}), 500
    
    result = generator.generate_document(
        doc_type="technical_spec",
        context="Test connection to OpenAI API"
    )
    
    return jsonify({
        "openai_available": result['provider'] == 'openai',
        "model": result['model'],
        "tokens": result['tokens'],
        "cost": result['cost'],
        "success": result['success'],
        "message": "OpenAI is working!" if result['provider'] == 'openai' else "OpenAI not configured"
    })

def main():
    """Start the API server"""
    print("=" * 60)
    print("🚀 PRODUCT DOCUMENTER AI - API SERVER")
    print("=" * 60)
    print()
    
    # Check OpenAI
    if generator and generator.client:
        print("✅ OpenAI: Configured")
        print(f"   Model: {generator.model}")
    else:
        print("⚠️  OpenAI: Not configured (simulated mode)")
        print("   Add OPENAI_API_KEY to .env file for real AI generation")
        print("   Get key from: https://platform.openai.com/api-keys")
    
    # Check database
    try:
        conn = sqlite3.connect('documenter.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        conn.close()
        
        print(f"✅ Database: Connected ({len(tables)} tables)")
    except:
        print("❌ Database: Not connected")
        print("   Run: python setup_database.py")
    
    print()
    print("📡 API Server running on: http://localhost:8000")
    print("📊 Dashboard: http://localhost:8501 (run separately)")
    print()
    print("🛑 Press Ctrl+C to stop")
    print("=" * 60)
    
    # Start Flask
    app.run(host='0.0.0.0', port=8000, debug=True)

if __name__ == '__main__':
    # Import pandas for costs endpoint
    import pandas as pd
    main()
"""
Monitors the parent project for file changes and auto-documents
"""

import os
import time
import json
import hashlib
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests

class ParentProjectMonitor(FileSystemEventHandler):
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.project_root = "../../"  # Go up from product-documenter/scripts/
        self.last_documented = {}
        self.change_buffer = []
        self.buffer_time = 30  # Seconds to buffer changes before documenting
        
        # Load previous state
        self.state_file = "parent_project_state.json"
        self.load_state()
    
    def load_state(self):
        """Load previous file states for comparison"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                self.last_documented = json.load(f)
    
    def save_state(self):
        """Save current file states"""
        with open(self.state_file, 'w') as f:
            json.dump(self.last_documented, f, indent=2)
    
    def on_modified(self, event):
        if not event.is_directory:
            self._handle_change(event.src_path, "modified")
    
    def on_created(self, event):
        if not event.is_directory:
            self._handle_change(event.src_path, "created")
    
    def on_deleted(self, event):
        if not event.is_directory:
            self._handle_change(event.src_path, "deleted")
    
    def _handle_change(self, filepath, change_type):
        # Skip product_documenter's own files
        if 'product-documenter' in filepath and not 'product-documenter/docs/' in filepath:
            return
        
        # Get relative path from project root
        rel_path = os.path.relpath(filepath, self.project_root)
        
        # Buffer changes to avoid too many API calls
        self.change_buffer.append({
            'time': datetime.now().isoformat(),
            'path': rel_path,
            'type': change_type
        })
        
        # If buffer has enough changes or time has passed, document them
        if len(self.change_buffer) >= 5:
            self._document_changes()
    
    def _document_changes(self):
        if not self.change_buffer:
            return
        
        # Group by change type
        changes_by_type = {}
        for change in self.change_buffer:
            changes_by_type.setdefault(change['type'], []).append(change['path'])
        
        # Create context
        context_lines = ["📊 Parent Project Activity Detected"]
        context_lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        context_lines.append("")
        
        for change_type, files in changes_by_type.items():
            context_lines.append(f"{change_type.upper()} ({len(files)}):")
            for file in files[:5]:  # Show first 5 of each type
                context_lines.append(f"  • {file}")
            if len(files) > 5:
                context_lines.append(f"  ... and {len(files)-5} more")
            context_lines.append("")
        
        context = "\n".join(context_lines)
        
        # Send to documenter
        try:
            payload = {
                'context': context,
                'doc_type': 'project_activity',
                'source': 'file_monitor',
                'metadata': {
                    'total_changes': len(self.change_buffer),
                    'change_types': changes_by_type,
                    'monitor_time': datetime.now().isoformat()
                }
            }
            
            response = requests.post(f"{self.api_url}/generate", 
                                   json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Documented {len(self.change_buffer)} changes")
                # Save state
                for change in self.change_buffer:
                    self.last_documented[change['path']] = {
                        'last_modified': change['time'],
                        'change_type': change['type']
                    }
                self.save_state()
            else:
                print(f"⚠️  Failed to document changes: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error documenting changes: {e}")
        
        # Clear buffer
        self.change_buffer.clear()
    
    def start(self):
        """Start monitoring the parent project"""
        observer = Observer()
        observer.schedule(self, self.project_root, recursive=True)
        observer.start()
        
        print(f"👁️  Monitoring parent project: {os.path.abspath(self.project_root)}")
        print("   Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(10)
                # Auto-document buffered changes every 10 seconds
                if self.change_buffer:
                    self._document_changes()
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

if __name__ == "__main__":
    monitor = ParentProjectMonitor()
    monitor.start()
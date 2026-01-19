"""
Scans Git history periodically for missed commits
"""

import subprocess
import requests
import json
import os
import time
from datetime import datetime, timedelta

class GitHistoryMonitor:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.state_file = "git_monitor_state.json"
        self.total_documented = 0
        self.last_checked = self.load_state()
    
    def load_state(self):
        """Load last check time"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    content = f.read().strip()
                    if content:  # Check if file is not empty
                        state = json.loads(content)
                        self.total_documented = state.get('total_commits_documented', 0)
                        return datetime.fromisoformat(state.get('last_checked', '2025-01-01'))
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"⚠️  Corrupted state file, resetting: {e}")
            # Create a backup of corrupted file
            if os.path.exists(self.state_file):
                backup_name = f"{self.state_file}.corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(self.state_file, backup_name)
                print(f"   Backup saved as: {backup_name}")
        
        # Default fallback
        self.total_documented = 0
        return datetime.now() - timedelta(days=1)
    
    def save_state(self):
        """Save check time"""
        with open(self.state_file, 'w') as f:
            json.dump({
                'last_checked': datetime.now().isoformat(),
                'total_commits_documented': self.total_documented
            }, f, indent=2)
    
    def get_new_commits(self):
        """Get commits since last check"""
        # Go to main project
        original_dir = os.getcwd()
        os.chdir("../../")
        
        # Get commits in JSON format
        cmd = [
            'git', 'log',
            f'--since="{self.last_checked}"',
            '--pretty=format:{"hash":"%H","author":"%an","date":"%ad","message":"%s"}',
            '--name-only',
            '--date=iso'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            os.chdir(original_dir)
            
            if result.returncode != 0:
                return []
            
            # Parse the complex git log output
            lines = result.stdout.strip().split('\n')
            commits = []
            current_commit = None
            
            for line in lines:
                if line.startswith('{'):
                    if current_commit:
                        commits.append(current_commit)
                    current_commit = json.loads(line)
                    current_commit['files'] = []
                elif line.strip() and current_commit:
                    current_commit['files'].append(line.strip())
            
            if current_commit:
                commits.append(current_commit)
            
            return commits
            
        except Exception as e:
            print(f"❌ Git scan error: {e}")
            os.chdir(original_dir)
            return []
    
    def document_commit(self, commit):
        """Document a single commit"""
        short_hash = commit['hash'][:8]
        
        context = f"""
Git History Scan - Missed Commit

Commit: {short_hash}
Date: {commit['date']}
Author: {commit['author']}
Message: {commit['message']}

Changed Files ({len(commit['files'])}):
{chr(10).join(['• ' + f for f in commit['files'][:15]])}
{f"... and {len(commit['files'])-15} more" if len(commit['files']) > 15 else ""}
"""
        
        payload = {
            'context': context,
            'doc_type': 'git_history',
            'source': 'git_history_scan',
            'licensing_focus': False,
            'metadata': {
                'commit_hash': short_hash,
                'commit_date': commit['date'],
                'files_changed': len(commit['files']),
                'scan_type': 'periodic'
            }
        }
        
        try:
            response = requests.post(self.api_url + "/generate", json=payload, timeout=10)
            if response.status_code == 200:
                print(f"✅ Documented missed commit: {short_hash}")
                return True
        except Exception as e:
            print(f"⚠️  Failed to document commit {short_hash}: {e}")
        
        return False
    
    def run(self):
        """Run the monitor once"""
        print(f"🔍 Scanning Git history since {self.last_checked}")
        commits = self.get_new_commits()
        
        if commits:
            print(f"📝 Found {len(commits)} new commits to document")
            documented = 0
            
            for commit in commits[:10]:  # Limit to 10 per run
                if self.document_commit(commit):
                    documented += 1
            
            print(f"✅ Documented {documented}/{len(commits)} commits")
        else:
            print("📭 No new commits found")
        
        # Save state
        self.last_checked = datetime.now()
        self.save_state()
        
        return len(commits)
    
    def start_monitoring(self, interval_minutes=60):
        """Start periodic monitoring"""
        print(f"🔄 Starting Git history monitor (every {interval_minutes} minutes)")
        print(f"   First scan since: {self.last_checked}")
        
        try:
            while True:
                self.run()
                print(f"⏰ Next scan in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("👋 Stopping Git monitor")

if __name__ == "__main__":
    monitor = GitHistoryMonitor()
    monitor.start_monitoring(interval_minutes=60)  # Check every hour
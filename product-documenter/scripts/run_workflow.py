"""
Complete workflow for generating licensing-ready documentation
"""

import requests
import json
from datetime import datetime
import time

class CompleteDocumentationWorkflow:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
    
    def generate_product_docs(self, product_details):
        """Generate complete documentation for a product"""
        print(f"🚀 Generating documentation for: {product_details['name']}")
        print("=" * 60)
        
        docs = {}
        
        # Generate each document type
        doc_types = [
            ("technical_spec", "Technical Specification"),
            ("api_documentation", "API Documentation"),
            ("user_manual", "User Manual"),
            ("license_readiness", "License Readiness")
        ]
        
        for doc_type, doc_name in doc_types:
            print(f"\n📄 Generating {doc_name}...")
            
            payload = {
                "context": product_details['description'],
                "doc_type": doc_type,
                "features": product_details.get('features', ''),
                "requirements": product_details.get('requirements', ''),
                "licensing_focus": True,
                "source": "workflow_automation"
            }
            
            try:
                response = requests.post(
                    f"{self.api_url}/generate",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    docs[doc_type] = {
                        "content": data['content'][:500] + "..." if len(data['content']) > 500 else data['content'],
                        "cost": data['cost'],
                        "tokens": data['tokens'],
                        "review_path": data.get('review_path'),
                        "needs_review": data.get('needs_review', False)
                    }
                    print(f"   ✅ Generated ({data['tokens']} tokens, ${data['cost']:.6f})")
                    print(f"   📁 Review file: {data.get('review_path', 'Not saved for review')}")
                else:
                    print(f"   ❌ Failed: {response.status_code}")
                    print(f"   Error: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
        
        print("\n" + "=" * 60)
        print(f"✅ Documentation generation complete!")
        
        # Calculate totals
        total_cost = sum(doc['cost'] for doc in docs.values())
        total_tokens = sum(doc['tokens'] for doc in docs.values())
        
        print(f"   Total documents: {len(docs)}")
        print(f"   Total tokens: {total_tokens}")
        print(f"   Total cost: ${total_cost:.6f}")
        
        return docs
    
    def check_review_status(self):
        """Check documents pending review"""
        print("\n🔍 Checking review status...")
        
        # List files in review folder (simplified check)
        import os
        review_folder = "docs/review"
        if os.path.exists(review_folder):
            review_files = [f for f in os.listdir(review_folder) if f.endswith('.md')]
            print(f"   Documents pending review: {len(review_files)}")
            for file in review_files[:5]:  # Show first 5
                print(f"   • {file}")
            if len(review_files) > 5:
                print(f"   ... and {len(review_files) - 5} more")
        else:
            print("   No review folder found")
    
    def simulate_review_process(self, product_name):
        """Simulate a review process (for testing)"""
        print(f"\n👨‍💼 Simulating review for {product_name}...")
        
        # This would normally be done by a human
        # For demo, we'll create a simple reviewed version
        import os
        review_folder = "docs/review"
        
        if os.path.exists(review_folder):
            review_files = [f for f in os.listdir(review_folder) if f.endswith('.md')]
            
            for review_file in review_files[:2]:  # Simulate reviewing first 2
                filepath = os.path.join(review_folder, review_file)
                
                # Read the file
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simulate some edits
                reviewed_content = content.replace(
                    "To be specified",
                    "As documented in the configuration guide"
                ).replace(
                    "Component A",
                    "Homogenization Control Module"
                )
                
                # Submit review via API
                payload = {
                    "filepath": filepath,
                    "reviewed_content": reviewed_content,
                    "changes_summary": "Updated technical terms and clarified specifications",
                    "reviewer_name": "AI_Documenter_Test",
                    "prepare_for_licensing": True
                }
                
                try:
                    response = requests.post(
                        f"{self.api_url}/submit-review",
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        print(f"   ✅ Reviewed: {review_file}")
                    else:
                        print(f"   ❌ Failed to submit review: {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Error submitting review: {str(e)}")
    
    def create_final_package(self, product_name, version="1.0"):
        """Create final licensing package"""
        print(f"\n📦 Creating licensing package for {product_name} v{version}...")
        
        payload = {
            "product_name": product_name,
            "version": version
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/create-licensing-package",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Package created: {data['package_path']}")
                print(f"   📋 {data['message']}")
                return data['package_path']
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    def run_complete_workflow(self):
        """Run complete workflow from generation to packaging"""
        print("🎯 PRODUCT DOCUMENTATION LICENSING WORKFLOW")
        print("=" * 60)
        
        # Define your product
        product_details = {
            "name": "Almond Milk Homogenization System",
            "description": """A sophisticated control system for almond milk homogenization processes.
            Features real-time monitoring, pressure control, quality assurance, and IoT integration.
            Designed for food production facilities requiring precise homogenization control.""",
            "features": """- Real-time temperature and pressure monitoring
- Automated pressure adjustment during homogenization
- Batch tracking with full traceability
- Quality metrics and analytics dashboard
- IoT sensor integration
- Cloud-based data synchronization
- Predictive maintenance alerts
- Compliance reporting (FDA, HACCP)""",
            "requirements": """- Operating System: Windows 10/11 or Linux Ubuntu 20.04+
- CPU: Quad-core 2.5GHz or higher
- RAM: 8GB minimum, 16GB recommended
- Storage: 50GB available space
- Network: Stable internet connection for cloud features
- Browser: Chrome 90+ or Firefox 88+ for web interface"""
        }
        
        # Step 1: Generate all documentation
        docs = self.generate_product_docs(product_details)
        
        # Step 2: Check review status
        self.check_review_status()
        
        # Step 3: Simulate review process (in real use, you would do this manually)
        self.simulate_review_process(product_details['name'])
        
        # Step 4: Create final licensing package
        package_path = self.create_final_package(
            product_name=product_details['name'],
            version="1.0"
        )
        
        print("\n" + "=" * 60)
        print("✅ WORKFLOW COMPLETE!")
        print(f"\n📊 Summary:")
        print(f"   • Product: {product_details['name']}")
        print(f"   • Documents generated: {len(docs)}")
        print(f"   • Licensing package: {package_path}")
        print(f"\n📍 Next steps:")
        print(f"   1. Review documents in 'docs/review/' folder")
        print(f"   2. Edit as needed for accuracy")
        print(f"   3. Use the API to submit your reviews")
        print(f"   4. Final package will be in 'docs/licensing_ready/'")

if __name__ == "__main__":
    # Start the API server first if not running
    import subprocess
    import sys
    
    print("🔧 Starting Product Documenter AI Workflow")
    print("Make sure the API server is running on http://localhost:8000")
    print()
    
    workflow = CompleteDocumentationWorkflow()
    
    # Test connection
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
            workflow.run_complete_workflow()
        else:
            print("❌ API server not responding properly")
    except requests.exceptions.ConnectionError:
        print("❌ API server not running")
        print("\nStart it with: python api_server.py")
        print("Then run this script again.")
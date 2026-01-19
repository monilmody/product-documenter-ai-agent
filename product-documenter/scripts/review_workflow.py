import os
import json
from datetime import datetime
from pathlib import Path

class ReviewWorkflow:
    def __init__(self, docs_folder="docs"):
        self.docs_folder = Path(docs_folder)
        self.review_folder = self.docs_folder / "review"
        self.approved_folder = self.docs_folder / "approved"
        self.licensing_folder = self.docs_folder / "licensing_ready"
        
        # Create folders
        for folder in [self.docs_folder, self.review_folder, self.approved_folder, self.licensing_folder]:
            folder.mkdir(exist_ok=True)
    
    def save_for_review(self, doc_id, content, doc_type, metadata):
        """Save document for human review"""
        filename = f"{doc_type}_{doc_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = self.review_folder / filename
        
        # Add review header
        review_content = f"""---
# DOCUMENT FOR REVIEW
# ID: {doc_id}
# Type: {doc_type}
# Generated: {metadata.get('generated_at', datetime.now().isoformat())}
# Cost: ${metadata.get('cost', 0):.6f}
# Tokens: {metadata.get('tokens', 0)}
# Model: {metadata.get('model', 'unknown')}
---
# REVIEW INSTRUCTIONS
1. Check technical accuracy
2. Verify completeness for licensing
3. Mark sections needing clarification with [REVIEW]
4. Add licensing-specific details
5. Update any placeholder content
---

{content}
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(review_content)
        
        # Save metadata
        metadata['filepath'] = str(filepath)
        metadata['status'] = 'pending_review'
        metadata['saved_at'] = datetime.now().isoformat()
        
        metadata_file = filepath.with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Document saved for review: {filename}")
        return str(filepath)
    
    def submit_review(self, filepath, reviewed_content, changes_summary, reviewer_name):
        """Submit reviewed document"""
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Document not found: {filepath}")
        
        # Load metadata
        metadata_file = filepath.with_suffix('.json')
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Update metadata
        metadata['reviewed_at'] = datetime.now().isoformat()
        metadata['reviewer'] = reviewer_name
        metadata['changes_summary'] = changes_summary
        metadata['status'] = 'reviewed'
        
        # Save reviewed version
        reviewed_filename = f"reviewed_{filepath.name}"
        reviewed_path = self.approved_folder / reviewed_filename
        
        reviewed_with_metadata = f"""---
# REVIEWED DOCUMENT
# Original ID: {metadata.get('doc_id', 'unknown')}
# Type: {metadata.get('doc_type', 'unknown')}
# Generated: {metadata.get('generated_at')}
# Reviewed: {metadata['reviewed_at']}
# Reviewer: {reviewer_name}
# Changes: {changes_summary}
---
{reviewed_content}
"""
        
        with open(reviewed_path, 'w', encoding='utf-8') as f:
            f.write(reviewed_with_metadata)
        
        # Update metadata
        metadata['reviewed_filepath'] = str(reviewed_path)
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Extract learning
        self._extract_learning(filepath, reviewed_path, metadata)
        
        print(f"✅ Review submitted: {reviewed_filename}")
        return str(reviewed_path), metadata
    
    def prepare_for_licensing(self, reviewed_filepath, additional_metadata=None):
        """Format document for final licensing package"""
        filepath = Path(reviewed_filepath)
        
        # Read reviewed content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove metadata headers if present
        if content.startswith('---'):
            lines = content.split('\n')
            in_header = True
            clean_lines = []
            for line in lines:
                if line == '---' and in_header:
                    in_header = False
                    continue
                if in_header:
                    continue
                clean_lines.append(line)
            content = '\n'.join(clean_lines).strip()
        
        # Add licensing header
        today = datetime.now().strftime('%Y-%m-%d')
        licensing_content = f"""# SOFTWARE DOCUMENTATION FOR LICENSING
# Document Version: 1.0
# Preparation Date: {today}
# Confidential - For Licensee Review Only

{content}

---
## LICENSING ACKNOWLEDGMENT

This document is part of the software licensing package. 
All technical specifications are accurate as of the preparation date.

**Contact:** Licensing Department
**Email:** licensing@yourcompany.com
**Effective Date:** {today}
"""
        
        # Save to licensing folder
        licensing_filename = f"licensing_{filepath.name}"
        licensing_path = self.licensing_folder / licensing_filename
        
        with open(licensing_path, 'w', encoding='utf-8') as f:
            f.write(licensing_content)
        
        print(f"✅ Document prepared for licensing: {licensing_filename}")
        return str(licensing_path)
    
    def _extract_learning(self, original_path, reviewed_path, metadata):
        """Extract learning from review changes"""
        from learning_system import LearningSystem
        
        # Read both versions
        with open(original_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        with open(reviewed_path, 'r', encoding='utf-8') as f:
            reviewed_content = f.read()
        
        # Extract actual content (remove headers)
        def extract_body(content):
            if '---' in content:
                parts = content.split('---')
                return parts[-1].strip() if len(parts) > 2 else content
            return content
        
        original_body = extract_body(original_content)
        reviewed_body = extract_body(reviewed_content)
        
        # Save to learning system
        learner = LearningSystem()
        learner.save_feedback(
            doc_id=metadata.get('doc_id', 0),
            original=original_body,
            revised=reviewed_body,
            review_time=0,  # Would need actual timing
            doc_type=metadata.get('doc_type', 'unknown')
        )
        
        print(f"✅ Learning extracted from review")
    
    def generate_licensing_package(self, product_name, version="1.0"):
        """Generate complete licensing package"""
        package_folder = self.licensing_folder / f"{product_name}_v{version}"
        package_folder.mkdir(exist_ok=True)
        
        # Copy all licensing-ready documents
        licensing_files = list(self.licensing_folder.glob("licensing_*.md"))
        
        package_contents = []
        for file in licensing_files:
            if file.parent != package_folder:  # Don't copy from package folder itself
                dest = package_folder / file.name
                with open(file, 'r', encoding='utf-8') as src:
                    content = src.read()
                with open(dest, 'w', encoding='utf-8') as dst:
                    dst.write(content)
                package_contents.append(file.name)
        
        # Create package manifest
        manifest = {
            "product_name": product_name,
            "version": version,
            "generated_date": datetime.now().isoformat(),
            "documents": package_contents,
            "total_documents": len(package_contents)
        }
        
        manifest_path = package_folder / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Create README
        readme_content = f"""# SOFTWARE LICENSING DOCUMENTATION PACKAGE

## Product: {product_name}
## Version: {version}
## Package Date: {datetime.now().strftime('%Y-%m-%d')}

### INCLUDED DOCUMENTS:
{chr(10).join([f'- {doc}' for doc in package_contents])}

### PURPOSE:
This package contains all technical documentation required for software licensing, 
including technical specifications, API documentation, user manuals, and licensing 
readiness documents.

### CONFIDENTIALITY:
These documents contain proprietary information and are provided under 
confidentiality agreement for the purpose of software licensing evaluation.

### CONTACT:
For questions or additional information, contact the licensing department.
"""
        
        readme_path = package_folder / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✅ Licensing package created: {package_folder}")
        print(f"   Contains {len(package_contents)} documents")
        return str(package_folder)

# Test the workflow
if __name__ == "__main__":
    workflow = ReviewWorkflow()
    
    # Test saving for review
    test_content = "# Test Document\n\nThis is a test document for review."
    metadata = {
        "doc_id": 1,
        "doc_type": "technical_spec",
        "cost": 0.000134,
        "tokens": 67,
        "model": "gpt-3.5-turbo",
        "generated_at": datetime.now().isoformat()
    }
    
    saved_path = workflow.save_for_review(
        doc_id=1,
        content=test_content,
        doc_type="technical_spec",
        metadata=metadata
    )
    
    print(f"Document saved at: {saved_path}")
Product Documenter AI Agent 📝

An intelligent documentation system that automatically tracks code changes, generates documents for review, and prepares licensing-ready technical packages with human oversight.

🚀 What It Does
Automated Documentation Workflow:
[You Work on Code] → [Trigger Document Update] → [Review & Approve] → [System Learns]

This agent monitors your development activity, creates structured documentation from your commits and file changes, lets you manually review and approve content, then organizes approved documents into professional licensing packages.

✨ Key Features
🤖 AI-Powered Document Generation: Automatically creates technical specs, changelogs, and API documentation from your code changes

👩‍💻 Human-in-the-Loop Review: Every document requires manual approval before finalization

💰 Cost Tracking: Real-time monitoring of AI generation expenses with detailed logging

📦 Licensing Package Assembly: Bundle multiple approved documents into complete product documentation sets

📊 Live Dashboard: Monitor costs, review status, and document pipeline in real-time

🛠️ Quick Start

Prerequisites:
# Clone the repository
git clone https://github.com/monilmody/product-documenter-ai-agent.git

cd product-documenter-ai-agent

# Install dependencies
pip install -r requirements.txt

Start the System
# Navigate to scripts folder
cd scripts

# Start everything with one command
.\start_project.ps1
This launches:

API Server (Port 8000) - Core document generation engine

Monitoring Dashboard (Streamlit) - Real-time visualization

📖 How It Works: The Review & Approval Process
Step 1: Generate a Document
powershell
# Trigger document creation based on your recent work
$body = @{
    context = "Implemented user authentication with JWT tokens"
    doc_type = "technical_spec"
    licensing_focus = $true
} | ConvertTo-Json

$response = irm http://localhost:8000/generate -Method Post -ContentType "application/json" -Body $body
✅ Result: Document saved to docs/review/technical_spec_2_20251216_112746.md
✅ Cost Tracked: $0.0015 logged to database
✅ Status: Awaiting review in the dashboard

Step 2: Review & Edit (Human Approval)
Open the generated file and make your improvements:

markdown
# BEFORE (AI-generated content):
## Authentication System
- **JWT Implementation**: User tokens expire after 24 hours
- **Password Security**: Passwords hashed using bcrypt

# AFTER (Your human review and edits):
## Authentication System - v1.2
- **JWT Implementation**: User tokens expire after 24 hours with refresh token capability
- **Password Security**: Passwords hashed using bcrypt with 12 rounds (security audit passed)
- **Rate Limiting**: Added 5 requests/minute limit on login endpoint
- [REVIEW NOTE] Need to document token blacklist cleanup schedule
Key Principle: You edit the document directly as a human reviewer. The system doesn't send it back to AI for revision.

Step 3: Submit Your Approved Version
powershell
$body = @{
    filepath = "docs/review/technical_spec_2_20251216_112746.md"
    reviewed_content = "# Authentication System - v1.2`n`n## Implementation Details:`n✅ JWT tokens with 24-hour expiration + refresh tokens`n✅ Password hashing: bcrypt (12 rounds) - security audit passed`n✅ Rate limiting: 5 requests/minute on /login endpoint`n`n## Review Notes:`n- Token blacklist cleanup scheduled for nightly maintenance"
    changes_summary = "Added refresh token capability, confirmed security audit, documented rate limiting"
    reviewer_name = "DevTeam Lead"
    prepare_for_licensing = $true
} | ConvertTo-Json

$result = irm http://localhost:8000/submit-review -Method Post -ContentType "application/json" -Body $body
✅ Result:

Database updated with your final content

Document status changed to "completed"

Quality score recorded (optional)

Document queued for licensing package

Step 4: Create Licensing Packages
When you have multiple approved documents:

powershell
$body = @{
    product_name = "SecureAuth API"
    version = "2.1.0"
} | ConvertTo-Json

irm http://localhost:8000/create-licensing-package -Method Post -ContentType "application/json" -Body $body
✅ Result: Professional PDF/HTML bundle in docs/licensing/ containing all approved technical documentation.

🎯 Daily Workflow
powershell
# Morning routine
.\start_project.ps1

# During work - generate documents for significant changes
irm http://localhost:8000/generate -Method Post -Body (@{
    context="Added rate limiting middleware to authentication endpoints"
    doc_type="api_spec"
} | ConvertTo-Json)

# Monitor costs and status in dashboard (auto-opens in browser)
# Review documents when ready (usually end of day or milestone)

# End of day check
.\check_status.ps1
📊 Real-Time Monitoring
The dashboard shows:

💰 Current Session Costs: Live updating of AI generation expenses

📄 Document Pipeline: Generated → Under Review → Approved → Licensed

⏱️ Response Times: API performance metrics

📈 Activity Timeline: Visual history of all documentation events

🔧 Advanced Usage
Document Types Available
powershell
# Technical Specification
@{context="Database schema migration"; doc_type="technical_spec"}

# API Documentation  
@{context="New REST endpoints"; doc_type="api_doc"}

# Change Log
@{context="Version 2.0 release notes"; doc_type="changelog"}

# Installation Guide
@{context="Docker deployment setup"; doc_type="installation"}
Quality Scoring (Optional)
python
# When submitting review, include a quality score
tracker.approve_document(
    doc_id=document_id,
    final_content=edited_content,
    quality_score=0.92  # 0.0-1.0 scale
)
Batch Processing
powershell
# Document an entire project at once
.\document_main_project.ps1

# Submit multiple reviews
.\submit_review.ps1 -FilePath "docs\review\spec_*.md"
📁 Project Structure
text
product-documenter-ai-agent/
├── api_server.py           # Flask API server
├── monitor_dashboard.py    # Streamlit monitoring UI
├── docs/
│   ├── review/            # Documents awaiting approval
│   ├── licensed/          # Final licensing packages
│   └── archive/           # Historical versions
├── scripts/
│   ├── start_project.ps1  # One-click launcher
│   ├── check_status.ps1   # Quick system check
│   └── submit_review.ps1  # Review automation
└── database/
    └── activities.db      # SQLite tracking database

🚨 Troubleshooting
Issue	Solution
API not responding	--> Check python api_server.py is running in Terminal 1
Dashboard not loading --> Verify streamlit run monitor_dashboard.py in Terminal 2
Documents not saving --> Ensure docs/review/ folder exists with write permissions
Database errors	Delete --> database/activities.db to reset (loses history)
📈 Example: Full Feature Documentation Cycle
Scenario: You just added a new caching layer to your API.

Generate initial doc:

powershell
irm http://localhost:8000/generate -Method Post -Body (@{
    context="Implemented Redis caching for user profile endpoints"
    doc_type="technical_spec"
    licensing_focus=$true
} | ConvertTo-Json)
Review & enhance (edit docs/review/technical_spec_*.md):

Add cache invalidation strategy

Document performance benchmarks

Note memory usage considerations

Submit approved version:

powershell
# Use the submit-review API with your enhanced content
Next day: Document another feature, repeat process

Release time: Create complete licensing package with all approved docs

🤝 Contributing
This system learns from your review patterns! The more you use it:

Better context understanding for future document generation

More accurate cost predictions

Improved template suggestions based on your edits

💡 Pro Tip: Use consistent review comments like [REVIEW], [TODO], or [VERIFIED] to help the system learn your quality standards.

Last Updated: January 2026 | Version: 1.0

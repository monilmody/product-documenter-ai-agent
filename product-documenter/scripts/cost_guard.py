#!/usr/bin/env python3
"""
Automated cost control for OpenAI API
Runs as a cron job or GitHub Action
"""

import os
import sys
from document_generator import SmartDocumentGenerator
import smtplib
from email.mime.text import MIMEText
import json

def check_budget():
    """Check budget and send alerts"""
    generator = SmartDocumentGenerator()
    cost_tracker = generator.cost_tracker
    
    monthly_spent = cost_tracker.get_monthly_spent()
    remaining = cost_tracker.get_remaining_budget()
    budget = float(os.getenv('MONTHLY_BUDGET', 50))
    
    utilization = (monthly_spent / budget) * 100
    
    alerts = []
    
    if utilization >= 90:
        alerts.append({
            "level": "CRITICAL",
            "message": f"Budget exceeded: {utilization:.1f}% used",
            "action": "All new requests will use local models"
        })
        # Update configuration to force local
        update_config(force_local=True)
        
    elif utilization >= 80:
        alerts.append({
            "level": "WARNING",
            "message": f"Budget warning: {utilization:.1f}% used",
            "action": "Consider reviewing cost optimization recommendations"
        })
    
    elif utilization >= 50:
        alerts.append({
            "level": "INFO",
            "message": f"Budget tracking: {utilization:.1f}% used",
            "action": "Continue monitoring"
        })
    
    # Send alerts
    if alerts:
        send_alerts(alerts, monthly_spent, remaining)
    
    return {
        "monthly_spent": monthly_spent,
        "remaining": remaining,
        "utilization": utilization,
        "alerts": alerts
    }

def update_config(force_local=False):
    """Update configuration based on budget"""
    config = {
        "force_local": force_local,
        "updated": datetime.now().isoformat()
    }
    
    with open('scripts/config.json', 'w') as f:
        json.dump(config, f)
    
    print(f"Config updated: force_local={force_local}")

def send_alerts(alerts, spent, remaining):
    """Send email/Slack alerts"""
    # Email configuration (optional)
    email_enabled = os.getenv('ALERT_EMAIL', '')
    
    if email_enabled:
        msg = MIMEText(f"""
        OpenAI Cost Alert
        
        Monthly Spent: ${spent:.2f}
        Remaining: ${remaining:.2f}
        
        Alerts:
        {chr(10).join([f'{a["level"]}: {a["message"]}' for a in alerts])}
        
        Dashboard: http://localhost:3000
        """)
        
        msg['Subject'] = 'Documenter AI Cost Alert'
        msg['From'] = 'documenter@yourcompany.com'
        msg['To'] = email_enabled
        
        # Send email
        # server = smtplib.SMTP('smtp.gmail.com', 587)
        # server.starttls()
        # server.login(user, password)
        # server.send_message(msg)
        # server.quit()
    
    # Simple print for now
    print("📢 Cost Alerts:")
    for alert in alerts:
        print(f"  {alert['level']}: {alert['message']}")
        print(f"  Action: {alert['action']}")

if __name__ == "__main__":
    result = check_budget()
    print(json.dumps(result, indent=2))
    
    # Exit code for automation
    if any(a['level'] == 'CRITICAL' for a in result['alerts']):
        sys.exit(1)  # Critical - trigger action
    elif any(a['level'] == 'WARNING' for a in result['alerts']):
        sys.exit(2)  # Warning - log only
    else:
        sys.exit(0)  # OK
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import threading

st.set_page_config(page_title="Documentation Dashboard", layout="wide")

st.title("📊 Product Documentation Dashboard")
st.markdown("Monitor costs, review progress, and licensing readiness")

# Thread-local storage for SQLite connections
thread_local = threading.local()

def get_thread_connection():
    """Get a thread-local SQLite connection"""
    if not hasattr(thread_local, "connection"):
        thread_local.connection = sqlite3.connect('documenter.db', check_same_thread=False)
    return thread_local.connection

def close_thread_connection():
    """Close thread-local SQLite connection"""
    if hasattr(thread_local, "connection"):
        thread_local.connection.close()
        del thread_local.connection

# Use a single connection with check_same_thread=False
@st.cache_resource
def get_connection():
    """Create a single connection for Streamlit"""
    return sqlite3.connect('documenter.db', check_same_thread=False)

# Main app
conn = get_connection()

# Helper function for safe queries
def safe_query(query, params=None):
    """Execute SQL query safely in Streamlit"""
    try:
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Costs", "📋 Review Queue", "📦 Licensing", "💡 Insights"])

with tab1:
    st.subheader("Cost Analysis")
    
    # Load cost data
    cost_df = safe_query("""
        SELECT 
            DATE(timestamp) as date,
            SUM(ai_cost) as daily_cost,
            SUM(ai_tokens_used) as daily_tokens,
            COUNT(*) as requests
        FROM activities
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        LIMIT 30
    """)
    
    if not cost_df.empty and len(cost_df) > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            total_cost = cost_df['daily_cost'].sum()
            st.metric("Total Cost", f"${total_cost:.4f}")
        with col2:
            total_tokens = cost_df['daily_tokens'].sum()
            st.metric("Total Tokens", f"{total_tokens:,}")
        with col3:
            total_requests = cost_df['requests'].sum()
            avg_cost = total_cost / total_requests if total_requests > 0 else 0
            st.metric("Avg Cost/Doc", f"${avg_cost:.6f}")
        
        # Display data table
        st.dataframe(cost_df.style.format({
            'daily_cost': '${:.4f}',
            'daily_tokens': '{:,}'
        }), use_container_width=True)
        
        # Simple bar chart using Streamlit's native chart
        st.subheader("Cost Trend")
        if len(cost_df) > 1:
            st.bar_chart(cost_df.set_index('date')['daily_cost'])
        else:
            st.info("Need more data points for chart")
        
    else:
        st.info("No cost data yet. Generate some documentation!")

with tab2:
    st.subheader("Documents Pending Review")
    
    # Check review folder
    review_folder = "docs/review"
    
    if os.path.exists(review_folder):
        review_files = []
        for file in os.listdir(review_folder):
            if file.endswith('.md'):
                filepath = os.path.join(review_folder, file)
                try:
                    size_kb = os.path.getsize(filepath) / 1024
                    modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                    age_days = (datetime.now() - modified).days
                    
                    review_files.append({
                        'Document': file,
                        'Size': f"{size_kb:.1f} KB",
                        'Modified': modified.strftime('%Y-%m-%d %H:%M'),
                        'Age (days)': age_days,
                        'Status': '⚠️ Overdue' if age_days > 3 else '📝 Ready'
                    })
                except Exception as e:
                    st.warning(f"Could not read {file}: {e}")
        
        if review_files:
            df = pd.DataFrame(review_files)
            st.dataframe(df, use_container_width=True)
            
            # Summary stats
            col1, col2 = st.columns(2)
            with col1:
                overdue = len([f for f in review_files if f['Age (days)'] > 3])
                st.metric("Documents Overdue", overdue, delta=None)
            with col2:
                st.metric("Total Pending", len(review_files), delta=None)
            
            # Age distribution
            if len(review_files) > 1:
                st.subheader("Review Aging")
                age_data = pd.DataFrame([f['Age (days)'] for f in review_files], columns=['days'])
                st.bar_chart(age_data['days'].value_counts().sort_index())
        else:
            st.success("✅ No documents pending review!")
    else:
        st.warning("Review folder not found. Generate some documents first.")

with tab3:
    st.subheader("Licensing Package Status")
    
    licensing_folder = "docs/licensing_ready"
    
    if os.path.exists(licensing_folder):
        packages = []
        for item in os.listdir(licensing_folder):
            item_path = os.path.join(licensing_folder, item)
            if os.path.isdir(item_path):
                try:
                    # Count files
                    md_files = [f for f in os.listdir(item_path) if f.endswith('.md')]
                    json_files = [f for f in os.listdir(item_path) if f.endswith('.json')]
                    total_files = len(md_files) + len(json_files)
                    
                    # Get creation time
                    created = datetime.fromtimestamp(os.path.getctime(item_path))
                    
                    packages.append({
                        'Package': item,
                        'Documents': len(md_files),
                        'Total Files': total_files,
                        'Created': created.strftime('%Y-%m-%d'),
                        'Path': item_path
                    })
                except Exception as e:
                    st.warning(f"Could not read package {item}: {e}")
        
        if packages:
            for package in packages:
                with st.expander(f"📦 {package['Package']} ({package['Documents']} docs)"):
                    st.write(f"**Created:** {package['Created']}")
                    st.write(f"**Path:** `{package['Path']}`")
                    
                    # List documents in the package
                    try:
                        docs = [f for f in os.listdir(package['Path']) if f.endswith('.md')]
                        st.write("**Documents included:**")
                        for doc in docs[:5]:  # Show first 5
                            st.write(f"• {doc}")
                        if len(docs) > 5:
                            st.write(f"• ... and {len(docs) - 5} more")
                    except Exception as e:
                        st.write(f"Could not list documents: {e}")
            st.metric("Total Packages", len(packages))
        else:
            st.info("No licensing packages created yet")
    else:
        st.info("Licensing folder not created yet. Submit reviewed documents to create packages.")

with tab4:
    st.subheader("Improvement Insights")
    
    # Load insights from learning system
    insights_df = safe_query("""
        SELECT 
            metric_name,
            metric_value,
            recommendation,
            generated_at
        FROM insights
        ORDER BY generated_at DESC
        LIMIT 10
    """)
    
    if not insights_df.empty and len(insights_df) > 0:
        for _, row in insights_df.iterrows():
            with st.expander(f"{row['metric_name']} - {row['generated_at'][:10]}"):
                st.write(f"**Value:** {row['metric_value']}")
                st.write(f"**Recommendation:** {row['recommendation']}")
    else:
        st.info("No insights generated yet. Review some documents to generate insights!")

# Sidebar
st.sidebar.header("Quick Actions")
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

st.sidebar.header("Database Status")
# Check database connectivity
try:
    status_df = safe_query("SELECT COUNT(*) as activities FROM activities")
    if not status_df.empty:
        activity_count = status_df['activities'].iloc[0]
        st.sidebar.metric("Total Activities", activity_count)
    else:
        st.sidebar.info("No activities yet")
except Exception as e:
    st.sidebar.error(f"DB Error: {e}")

st.sidebar.header("Cost Control")
monthly_budget = st.sidebar.number_input("Monthly Budget ($)", 10, 500, 50, key="monthly_budget")
current_month = datetime.now().strftime("%Y-%m")

# Calculate current month spending
month_cost_df = safe_query(f"""
    SELECT SUM(ai_cost) as month_cost
    FROM activities
    WHERE strftime('%Y-%m', timestamp) = ?
""", (current_month,))

if not month_cost_df.empty:
    month_cost = month_cost_df['month_cost'].iloc[0] or 0
else:
    month_cost = 0

budget_used = (month_cost / monthly_budget) * 100 if monthly_budget > 0 else 0

st.sidebar.progress(min(budget_used/100, 1))
st.sidebar.write(f"${month_cost:.2f} / ${monthly_budget} ({budget_used:.1f}%)")

if budget_used > 80:
    st.sidebar.warning("⚠️ Budget nearly exhausted")
elif budget_used > 50:
    st.sidebar.info("Budget tracking")

# Add a section to generate test data
st.sidebar.header("Development Tools")
if st.sidebar.button("Generate Test Data"):
    try:
        # Create test activities
        test_data = [
            ("documentation_generation", "test", '{"test": true}', 100, 0.002),
            ("code_review", "github", '{"files": 3}', 50, 0.001),
            ("api_documentation", "api", '{"endpoints": 5}', 200, 0.004),
        ]
        
        cursor = conn.cursor()
        for activity_type, source, details, tokens, cost in test_data:
            cursor.execute("""
                INSERT INTO activities (activity_type, source, details, ai_tokens_used, ai_cost)
                VALUES (?, ?, ?, ?, ?)
            """, (activity_type, source, details, tokens, cost))
        
        conn.commit()
        st.sidebar.success("Test data generated!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

# Footer
st.sidebar.markdown("---")
st.sidebar.write(f"Dashboard updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# Close connection on app close
import atexit
@atexit.register
def cleanup():
    if hasattr(thread_local, "connection"):
        thread_local.connection.close()
    if 'conn' in locals():
        conn.close()
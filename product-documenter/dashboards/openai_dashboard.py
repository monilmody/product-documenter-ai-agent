import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="OpenAI Cost Dashboard", layout="wide")

# Initialize database
@st.cache_resource
def init_db():
    conn = sqlite3.connect('scripts/documenter.db')
    return conn

conn = init_db()

st.title("🤖 OpenAI Cost & Performance Dashboard")

# Sidebar filters
st.sidebar.header("Filters")
days = st.sidebar.slider("Time period (days)", 1, 90, 30)
budget = st.sidebar.number_input("Monthly Budget ($)", 10, 500, 50)

# Load data
@st.cache_data(ttl=300)
def load_cost_data(days):
    query = f"""
    SELECT 
        date(timestamp) as date,
        provider,
        model,
        SUM(tokens_used) as tokens,
        SUM(cost) as cost,
        COUNT(*) as requests
    FROM ai_costs
    WHERE date(timestamp) >= date('now', '-{days} days')
    GROUP BY date(timestamp), provider, model
    """
    return pd.read_sql_query(query, conn)

@st.cache_data(ttl=300)
def load_activity_data(days):
    query = f"""
    SELECT 
        date(timestamp) as date,
        activity_type,
        SUM(ai_cost) as ai_cost,
        SUM(human_time_seconds)/3600 as human_hours,
        COUNT(*) as activities
    FROM activities
    WHERE date(timestamp) >= date('now', '-{days} days')
    GROUP BY date(timestamp), activity_type
    """
    return pd.read_sql_query(query, conn)

# Main dashboard
tab1, tab2, tab3, tab4 = st.tabs(["Cost Overview", "Efficiency", "Usage Patterns", "Recommendations"])

with tab1:
    col1, col2, col3 = st.columns(3)
    
    # Summary metrics
    total_cost = load_cost_data(days)['cost'].sum()
    total_activities = load_activity_data(days)['activities'].sum()
    avg_cost_per_doc = total_cost / total_activities if total_activities > 0 else 0
    
    with col1:
        st.metric("Total Cost", f"${total_cost:.2f}", 
                 f"${total_cost/days:.2f}/day")
    with col2:
        st.metric("Documents Generated", total_activities,
                 f"${avg_cost_per_doc:.3f}/doc")
    with col3:
        # Monthly projection
        monthly_projection = (total_cost / days) * 30
        budget_usage = (monthly_projection / budget) * 100
        st.metric("Monthly Projection", f"${monthly_projection:.2f}",
                 f"{budget_usage:.1f}% of budget")
    
    # Cost over time
    cost_data = load_cost_data(days)
    if not cost_data.empty:
        fig = px.area(cost_data, x='date', y='cost', color='provider',
                     title="Cost Over Time by Provider")
        st.plotly_chart(fig, use_container_width=True)
    
    # Provider breakdown
    provider_summary = cost_data.groupby('provider').agg({
        'cost': 'sum',
        'requests': 'sum',
        'tokens': 'sum'
    }).reset_index()
    
    if not provider_summary.empty:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(provider_summary, values='cost', names='provider',
                        title="Cost Distribution by Provider")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(provider_summary, x='provider', y='requests',
                        title="Number of Requests by Provider")
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    # ROI calculation
    activity_data = load_activity_data(days)
    
    if not activity_data.empty:
        # Calculate efficiency metrics
        total_human_hours = activity_data['human_hours'].sum()
        total_ai_cost = activity_data['ai_cost'].sum()
        
        # Assuming $50/hour human cost
        human_cost_saved = total_human_hours * 50
        roi = ((human_cost_saved - total_ai_cost) / total_ai_cost) * 100 if total_ai_cost > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Human Hours Saved", f"{total_human_hours:.1f}h",
                     f"${human_cost_saved:.0f} value")
        with col2:
            st.metric("AI Investment", f"${total_ai_cost:.2f}")
        with col3:
            st.metric("ROI", f"{roi:.0f}%",
                     "Savings vs manual" if roi > 0 else "Review needed")
        
        # Time vs cost analysis
        fig = px.scatter(activity_data, x='ai_cost', y='human_hours',
                        size='activities', color='activity_type',
                        title="AI Cost vs Human Review Time",
                        labels={'ai_cost': 'AI Cost ($)', 'human_hours': 'Human Hours'})
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    # Usage patterns
    st.subheader("Token Usage Analysis")
    
    token_data = load_cost_data(days)
    if not token_data.empty:
        fig = px.scatter(token_data, x='tokens', y='cost',
                        color='model', size='requests',
                        title="Tokens vs Cost by Model",
                        trendline="ols")
        st.plotly_chart(fig, use_container_width=True)
        
        # Cost per token by model
        token_data['cost_per_token'] = token_data['cost'] / token_data['tokens']
        fig = px.box(token_data, x='model', y='cost_per_token',
                    title="Cost per Token Distribution by Model")
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Cost Optimization Recommendations")
    
    # Analyze for recommendations
    cost_data = load_cost_data(30)
    activity_data = load_activity_data(30)
    
    recommendations = []
    
    if not cost_data.empty:
        # Check OpenAI vs local usage
        openai_share = cost_data[cost_data['provider'] == 'openai']['cost'].sum() / cost_data['cost'].sum() * 100
        
        if openai_share > 80:
            recommendations.append({
                "priority": "High",
                "recommendation": "Consider using local models for draft documentation to reduce OpenAI costs",
                "savings": "~70% cost reduction"
            })
        
        # Check token efficiency
        avg_tokens_per_request = cost_data['tokens'].sum() / cost_data['requests'].sum()
        if avg_tokens_per_request > 1000:
            recommendations.append({
                "priority": "Medium",
                "recommendation": "Optimize prompts to use fewer tokens (shorter, more focused)",
                "savings": "~20-30% token reduction"
            })
        
        # Check model selection
        if 'gpt-4' in cost_data['model'].values:
            gpt4_cost = cost_data[cost_data['model'] == 'gpt-4']['cost'].sum()
            if gpt4_cost > 10:  # More than $10 spent on GPT-4
                recommendations.append({
                    "priority": "High",
                    "recommendation": "Switch from GPT-4 to GPT-3.5 for routine documentation",
                    "savings": "~90% cost reduction for similar quality"
                })
    
    if recommendations:
        for rec in recommendations:
            with st.expander(f"{rec['priority']} Priority: {rec['recommendation']}"):
                st.write(f"**Potential Savings:** {rec['savings']}")
                st.write("**Action:** Add 'force_local: true' to API calls for draft documents")
    else:
        st.success("✅ Your current configuration is cost-optimal!")
    
    # Budget planning
    st.subheader("Budget Planning")
    projected_monthly = (cost_data['cost'].sum() / 30) * 30 if not cost_data.empty else 0
    
    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode = "gauge+number+delta",
        value = projected_monthly,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Monthly Cost Projection"},
        delta = {'reference': budget, 'increasing': {'color': "red"}},
        gauge = {
            'axis': {'range': [0, budget*1.5]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, budget*0.7], 'color': "green"},
                {'range': [budget*0.7, budget], 'color': "yellow"},
                {'range': [budget, budget*1.5], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': budget
            }
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

# Real-time alert
if total_cost > budget * 0.8:
    st.sidebar.warning(f"⚠️ Budget alert: {budget_usage:.1f}% of monthly budget used")
    st.sidebar.info("Consider enabling 'force_local' mode for non-critical docs")

st.sidebar.info(f"Dashboard updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
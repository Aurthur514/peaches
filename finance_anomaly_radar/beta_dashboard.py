import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# FAR Beta Testing Dashboard
st.set_page_config(
    page_title="FAR Beta Testing Dashboard", 
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #e6e6e6;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .success-metric {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
    }
    .warning-metric {
        background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
    }
    .danger-metric {
        background: linear-gradient(135deg, #F44336 0%, #D32F2F 100%);
    }
    .user-feedback {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🛡️ Finance Anomaly Radar - Beta Testing Dashboard</h1>', unsafe_allow_html=True)

# Beta Program Overview
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-card success-metric">
        <h3>87</h3>
        <p>Total Beta Users</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <h3>62</h3>
        <p>Daily Active Users</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card warning-metric">
        <h3>91.3%</h3>
        <p>Detection Accuracy</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-card success-metric">
        <h3>8.7</h3>
        <p>Average NPS Score</p>
    </div>
    """, unsafe_allow_html=True)

# Real-time Testing Interface
st.header("🔍 Live Fraud Detection Testing")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Test Message Analysis")
    test_message = st.text_area(
        "Enter a message to analyze for fraud:",
        placeholder="Paste a suspicious message here...",
        height=100
    )
    
    if st.button("🚀 Analyze Message", type="primary"):
        if test_message:
            with st.spinner("Analyzing message..."):
                # Simulate API call to FAR detection system
                import time
                time.sleep(1.5)  # Simulate processing time
                
                # Mock analysis result
                risk_score = 0.78 if "investment" in test_message.lower() or "urgent" in test_message.lower() else 0.23
                risk_level = "HIGH" if risk_score > 0.7 else "MEDIUM" if risk_score > 0.4 else "LOW"
                
                # Display results
                if risk_level == "HIGH":
                    st.error(f"🚨 **HIGH RISK DETECTED** - Score: {risk_score:.2f}")
                elif risk_level == "MEDIUM":
                    st.warning(f"⚠️ **MEDIUM RISK** - Score: {risk_score:.2f}")
                else:
                    st.success(f"✅ **LOW RISK** - Score: {risk_score:.2f}")
                
                # Analysis details
                st.subheader("Analysis Details")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Risk Score", f"{risk_score:.2f}", f"+{risk_score*100:.1f}%")
                    st.metric("Confidence", "94%", "+5%")
                    st.metric("Processing Time", "847ms", "-23ms")
                
                with col2:
                    indicators = [
                        "Urgency language detected",
                        "Financial amounts mentioned", 
                        "External links present",
                        "Suspicious contact methods"
                    ]
                    st.write("**Risk Indicators:**")
                    for indicator in indicators:
                        if risk_score > 0.5:
                            st.write(f"🔴 {indicator}")
                        else:
                            st.write(f"🟢 {indicator}")

with col2:
    st.subheader("Quick Actions")
    
    if st.button("📊 View Detection Stats"):
        st.info("Loading detection statistics...")
    
    if st.button("👥 Check User Feedback"):
        st.info("Displaying latest user feedback...")
    
    if st.button("🔄 Refresh Dashboard"):
        st.rerun()
    
    st.subheader("Beta User Distribution")
    user_segments = {
        "First-time Investors": 28,
        "Senior Citizens": 23, 
        "Small Business": 21,
        "International Workers": 9,
        "Tech Early Adopters": 6
    }
    
    fig = px.pie(
        values=list(user_segments.values()),
        names=list(user_segments.keys()),
        title="Beta Users by Segment"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

# Performance Analytics
st.header("📈 Performance Analytics")

# Create tabs for different analytics views
tab1, tab2, tab3, tab4 = st.tabs(["Detection Accuracy", "User Engagement", "System Performance", "Feedback Analysis"])

with tab1:
    st.subheader("Fraud Detection Performance")
    
    # Mock performance data
    dates = pd.date_range(start="2024-11-15", end="2024-11-28", freq="D")
    accuracy_data = {
        "Date": dates,
        "Overall Accuracy": [0.87, 0.89, 0.91, 0.88, 0.92, 0.90, 0.93, 0.91, 0.89, 0.94, 0.92, 0.91, 0.93, 0.90],
        "Scam Detection": [0.85, 0.88, 0.90, 0.86, 0.91, 0.89, 0.92, 0.90, 0.87, 0.93, 0.91, 0.89, 0.92, 0.88],
        "False Positive Rate": [0.12, 0.10, 0.08, 0.11, 0.07, 0.09, 0.06, 0.08, 0.10, 0.05, 0.07, 0.08, 0.06, 0.09]
    }
    
    df = pd.DataFrame(accuracy_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df["Overall Accuracy"],
            mode='lines+markers', name="Overall Accuracy",
            line=dict(color='#1f77b4', width=3)
        ))
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df["Scam Detection"],
            mode='lines+markers', name="Scam Detection",
            line=dict(color='#ff7f0e', width=3)
        ))
        fig.update_layout(
            title="Detection Accuracy Trends",
            xaxis_title="Date",
            yaxis_title="Accuracy Rate",
            yaxis=dict(range=[0.8, 1.0])
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(df, x="Date", y="False Positive Rate", 
                     title="False Positive Rate", 
                     color_discrete_sequence=['#d62728'])
        fig.update_layout(yaxis=dict(range=[0, 0.15]))
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("User Engagement Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Daily active users
        engagement_data = {
            "Date": dates,
            "Daily Active Users": [45, 48, 52, 49, 56, 54, 58, 61, 59, 65, 62, 64, 67, 63],
            "Messages Scanned": [234, 267, 298, 276, 321, 312, 345, 387, 356, 412, 389, 398, 423, 401]
        }
        
        eng_df = pd.DataFrame(engagement_data)
        
        fig = px.bar(eng_df, x="Date", y="Daily Active Users", 
                    title="Daily Active Users",
                    color_discrete_sequence=['#2ca02c'])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(eng_df, x="Date", y="Messages Scanned",
                     title="Daily Messages Scanned",
                     color_discrete_sequence=['#9467bd'])
        st.plotly_chart(fig, use_container_width=True)
    
    # User retention analysis
    st.subheader("User Retention Analysis")
    retention_data = {
        "Week": ["Week 1", "Week 2", "Week 3", "Week 4"],
        "Active Users": [87, 76, 68, 62],
        "Retention Rate": [100, 87, 78, 71]
    }
    
    ret_df = pd.DataFrame(retention_data)
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(ret_df, x="Week", y="Active Users",
                    title="Weekly Active Users",
                    color_discrete_sequence=['#ff7f0e'])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(ret_df, x="Week", y="Retention Rate",
                     title="User Retention Rate (%)",
                     color_discrete_sequence=['#d62728'])
        fig.update_layout(yaxis=dict(range=[60, 105]))
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("System Performance Monitoring")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Average Response Time",
            value="847ms",
            delta="-23ms",
            delta_color="inverse"
        )
        
        st.metric(
            label="API Uptime",
            value="99.7%",
            delta="+0.2%"
        )
    
    with col2:
        st.metric(
            label="Requests/Second",
            value="156",
            delta="+12"
        )
        
        st.metric(
            label="Error Rate",
            value="0.3%",
            delta="-0.1%",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="Data Processed",
            value="2.3TB",
            delta="+0.4TB"
        )
        
        st.metric(
            label="Models Deployed",
            value="5",
            delta="0"
        )
    
    # Performance trends
    perf_data = {
        "Time": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
        "Response Time (ms)": [823, 798, 967, 1203, 891, 745],
        "Throughput (req/s)": [134, 98, 187, 245, 189, 156]
    }
    
    perf_df = pd.DataFrame(perf_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.line(perf_df, x="Time", y="Response Time (ms)",
                     title="Response Time Throughout Day",
                     color_discrete_sequence=['#1f77b4'])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(perf_df, x="Time", y="Throughput (req/s)",
                    title="Request Throughput",
                    color_discrete_sequence=['#ff7f0e'])
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("User Feedback Analysis")
    
    # NPS Score tracking
    nps_data = {
        "Week": ["Week 1", "Week 2", "Week 3", "Week 4"],
        "NPS Score": [7.2, 8.1, 8.7, 8.9],
        "Response Rate": [78, 82, 79, 85]
    }
    
    nps_df = pd.DataFrame(nps_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.line(nps_df, x="Week", y="NPS Score",
                     title="Net Promoter Score Trend",
                     color_discrete_sequence=['#2ca02c'])
        fig.update_layout(yaxis=dict(range=[6, 10]))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        feedback_categories = {
            "Very Positive": 45,
            "Positive": 28,
            "Neutral": 12,
            "Negative": 8,
            "Very Negative": 3
        }
        
        fig = px.pie(
            values=list(feedback_categories.values()),
            names=list(feedback_categories.keys()),
            title="Feedback Sentiment Distribution",
            color_discrete_sequence=px.colors.sequential.RdYlGn_r
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent user feedback
    st.subheader("Latest User Feedback")
    
    sample_feedback = [
        {
            "user": "FirstTimeInvestor_23",
            "rating": "⭐⭐⭐⭐⭐",
            "comment": "Caught a crypto scam before I lost $500! The alerts are super clear and easy to understand.",
            "date": "2024-11-28"
        },
        {
            "user": "SeniorUser_67",
            "rating": "⭐⭐⭐⭐",
            "comment": "Love the audio alerts - I can hear warnings even when I can't read the screen clearly.",
            "date": "2024-11-27"
        },
        {
            "user": "BusinessOwner_41",
            "rating": "⭐⭐⭐⭐⭐", 
            "comment": "Saved our company from a payment fraud attempt. The API integration was smooth.",
            "date": "2024-11-26"
        },
        {
            "user": "TechUser_29",
            "rating": "⭐⭐⭐",
            "comment": "Good detection but some false positives on legitimate investment emails. Needs tuning.",
            "date": "2024-11-25"
        }
    ]
    
    for feedback in sample_feedback:
        st.markdown(f"""
        <div class="user-feedback">
            <strong>{feedback['user']}</strong> {feedback['rating']} <span style="float: right; color: #666;">{feedback['date']}</span>
            <br><br>
            "{feedback['comment']}"
        </div>
        """, unsafe_allow_html=True)

# Beta Program Status
st.header("🎯 Beta Program Status")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Recruitment Progress")
    progress_data = {
        "Target": [30, 25, 25, 10, 10],
        "Recruited": [28, 23, 21, 9, 6],
        "Segment": ["First-time Investors", "Senior Citizens", "Small Business", "International", "Tech Early Adopters"]
    }
    
    prog_df = pd.DataFrame(progress_data)
    fig = px.bar(prog_df, x="Segment", y=["Target", "Recruited"],
                title="Recruitment vs Target",
                barmode='group')
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Testing Milestones")
    milestones = [
        {"task": "✅ Beta app deployed", "status": "Complete"},
        {"task": "✅ User onboarding flow", "status": "Complete"},
        {"task": "🔄 Active testing phase", "status": "In Progress"},
        {"task": "📋 User interviews", "status": "Scheduled"},
        {"task": "📊 Final analysis", "status": "Pending"}
    ]
    
    for milestone in milestones:
        if milestone["status"] == "Complete":
            st.success(milestone["task"])
        elif milestone["status"] == "In Progress":
            st.warning(milestone["task"])
        else:
            st.info(milestone["task"])

with col3:
    st.subheader("Key Insights")
    insights = [
        "🎯 91.3% accuracy exceeds 85% target",
        "📱 71% retention rate above industry average", 
        "💡 Multi-modal alerts most appreciated feature",
        "⚠️ Need to reduce false positives for investment emails",
        "👥 Senior users prefer audio alerts",
        "🚀 Ready for public beta based on current metrics"
    ]
    
    for insight in insights:
        st.write(insight)

# Action Items
st.header("📋 Next Steps")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Immediate Actions")
    actions = [
        "🔧 Tune detection algorithm to reduce false positives",
        "📞 Complete remaining user interviews (15/20 done)",
        "📊 Prepare final beta report for investors",
        "🚀 Plan public beta launch for December 20"
    ]
    
    for action in actions:
        st.checkbox(action, value=False)

with col2:
    st.subheader("Upcoming Milestones")
    upcoming = [
        {"date": "Dec 1", "task": "Complete beta testing phase"},
        {"date": "Dec 5", "task": "Analysis and insights report"},
        {"date": "Dec 10", "task": "Investor presentation prep"},
        {"date": "Dec 15", "task": "Public beta launch decision"},
        {"date": "Dec 20", "task": "Public beta launch"}
    ]
    
    for item in upcoming:
        st.write(f"**{item['date']}**: {item['task']}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    🛡️ Finance Anomaly Radar Beta Testing Dashboard - Last updated: November 28, 2024
    <br>
    📧 Contact: beta-support@far-ai.com | 📞 Support: 1-800-FAR-HELP
</div>
""", unsafe_allow_html=True)
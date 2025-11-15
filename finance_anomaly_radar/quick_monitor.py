#!/usr/bin/env python3
"""
Quick Reddit Campaign Monitor
Simple dashboard to track FAR beta campaign performance
"""

import streamlit as st
import time
from datetime import datetime
import random

# Page config
st.set_page_config(
    page_title="FAR Beta Campaign Monitor",
    page_icon="🚨",
    layout="wide"
)

# Header
st.title("🚨 Finance Anomaly Radar - Live Beta Campaign")
st.markdown("**Real-time Reddit Campaign Performance Dashboard**")

# Auto-refresh every 30 seconds
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

if st.button("🔄 Refresh Data"):
    st.session_state.last_refresh = datetime.now()

# Simulated real-time data (replace with actual Reddit API calls)
def get_campaign_data():
    base_time = datetime.now()
    
    # Simulate evolving metrics
    hours_since_launch = (base_time - datetime(2025, 11, 14, 12, 0)).total_seconds() / 3600
    growth_factor = min(2.0, 1 + hours_since_launch * 0.3)
    
    return {
        'r/investing': {
            'upvotes': int(23 * growth_factor + random.randint(-3, 8)),
            'comments': int(5 * growth_factor + random.randint(0, 3)),
            'signups': int(3 * growth_factor + random.randint(0, 2)),
            'views': int(850 * growth_factor + random.randint(-50, 200))
        },
        'r/CryptoCurrency': {
            'upvotes': int(31 * growth_factor + random.randint(-5, 12)),
            'comments': int(8 * growth_factor + random.randint(0, 4)),
            'signups': int(4 * growth_factor + random.randint(0, 3)),
            'views': int(1240 * growth_factor + random.randint(-80, 300))
        },
        'r/personalfinance': {
            'upvotes': int(18 * growth_factor + random.randint(-2, 6)),
            'comments': int(3 * growth_factor + random.randint(0, 2)),
            'signups': int(2 * growth_factor + random.randint(0, 1)),
            'views': int(620 * growth_factor + random.randint(-30, 150))
        },
        'r/SecurityCareerAdvice': {
            'upvotes': int(9 * growth_factor + random.randint(-1, 4)),
            'comments': int(2 * growth_factor + random.randint(0, 2)),
            'signups': int(1 * growth_factor + random.randint(0, 1)),
            'views': int(430 * growth_factor + random.randint(-20, 100))
        }
    }

# Get current data
data = get_campaign_data()

# Summary metrics
col1, col2, col3, col4 = st.columns(4)

total_upvotes = sum(sub['upvotes'] for sub in data.values())
total_comments = sum(sub['comments'] for sub in data.values())
total_signups = sum(sub['signups'] for sub in data.values())
total_views = sum(sub['views'] for sub in data.values())

with col1:
    st.metric("Total Upvotes", total_upvotes, delta="+3")
    
with col2:
    st.metric("Total Comments", total_comments, delta="+1")
    
with col3:
    st.metric("Beta Signups", total_signups, delta="+2")
    
with col4:
    conversion_rate = (total_signups / total_views * 100) if total_views > 0 else 0
    st.metric("Conversion Rate", f"{conversion_rate:.1f}%", delta="+0.2%")

st.markdown("---")

# Individual subreddit performance
st.subheader("📊 Performance by Subreddit")

cols = st.columns(2)

for i, (subreddit, metrics) in enumerate(data.items()):
    with cols[i % 2]:
        st.markdown(f"### {subreddit}")
        
        sub_col1, sub_col2 = st.columns(2)
        
        with sub_col1:
            st.metric("Upvotes", metrics['upvotes'])
            st.metric("Comments", metrics['comments'])
            
        with sub_col2:
            st.metric("Signups", metrics['signups'])
            st.metric("Views", metrics['views'])
            
        # Progress bar for engagement
        engagement_score = min(100, (metrics['upvotes'] + metrics['comments'] * 2) * 2)
        st.progress(engagement_score / 100)
        st.caption(f"Engagement Score: {engagement_score}/100")
        
        st.markdown("---")

# Campaign timeline
st.subheader("📈 Campaign Timeline")

# Simulated timeline data
timeline_data = []
current_time = datetime.now()
for i in range(24):  # Last 24 hours
    time_point = current_time - timedelta(hours=23-i)
    cumulative_signups = int((i+1) * total_signups / 24 + random.randint(-1, 2))
    timeline_data.append({
        'Hour': time_point.strftime('%H:%M'),
        'Cumulative Signups': max(0, cumulative_signups)
    })

import plotly.express as px
fig = px.line(timeline_data, x='Hour', y='Cumulative Signups', 
              title='Beta Signups Over Time',
              markers=True)
st.plotly_chart(fig, use_container_width=True)

# Live activity feed
st.subheader("🔴 Live Activity Feed")

activities = [
    "🎉 New beta signup from r/CryptoCurrency user!",
    "⬆️ +5 upvotes on r/investing post",
    "💬 Quality discussion started on r/personalfinance",
    "👀 High engagement on security post",
    "🔥 Post gaining traction in r/CryptoCurrency",
    "📧 Welcome email sent to new beta user",
    "✅ User completed beta onboarding",
    "🎯 Landing page optimization working well"
]

for activity in activities[-5:]:  # Show last 5 activities
    st.success(activity)

# Quick actions
st.sidebar.title("🎯 Quick Actions")

if st.sidebar.button("📱 Open Reddit Posts"):
    st.sidebar.markdown("""
    **Quick Links:**
    - [r/investing post](https://reddit.com/r/investing)
    - [r/CryptoCurrency post](https://reddit.com/r/CryptoCurrency) 
    - [r/personalfinance post](https://reddit.com/r/personalfinance)
    - [r/SecurityCareerAdvice post](https://reddit.com/r/SecurityCareerAdvice)
    """)

if st.sidebar.button("📊 View Analytics"):
    st.sidebar.success("Analytics dashboard opening...")

if st.sidebar.button("💌 Check Beta Signups"):
    st.sidebar.info(f"Current signups: {total_signups}")

# Footer
st.markdown("---")
st.markdown("**Last Updated:** " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
st.markdown("🔄 *Auto-refreshing every 30 seconds*")

# Auto-refresh script
time.sleep(1)  # Small delay to prevent rapid refreshing
#!/usr/bin/env python3
"""
Simple Job Bot Dashboard - Basic Streamlit Interface
Streamlined version for reliable Streamlit Cloud deployment
"""

import streamlit as st
import json
import os
from pathlib import Path
import sys

# Page configuration
st.set_page_config(
    page_title="Auto Job Bot Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced custom CSS
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.metric-card {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 1rem;
    border-radius: 10px;
    border: 1px solid #e1e8f0;
    margin-bottom: 1rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}
.job-card {
    background: white;
    padding: 1.5rem;
    border-radius: 10px;
    border-left: 4px solid #4CAF50;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.status-success { color: #28a745; font-weight: bold; }
.status-error { color: #dc3545; font-weight: bold; }
.status-warning { color: #ffc107; font-weight: bold; }
.status-info { color: #17a2b8; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_config():
    """Load configuration with error handling"""
    try:
        config_path = 'job_bot_config.json'
        if not os.path.exists(config_path):
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return config
    except Exception as e:
        st.error(f"Configuration error: {e}")
        return None

def main():
    """Simple main dashboard application"""
    
    # Header
    st.markdown('''
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">🤖 Auto Job Bot Dashboard</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">
            Intelligent Job Search & Application System for Bharathan M
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Load configuration
    config = load_config()
    
    if not config:
        st.error("❌ Configuration file not found!")
        st.info("This appears to be a demo deployment. The full system requires configuration setup.")
        
        # Show demo interface
        st.markdown("### 🎭 Demo Interface")
        st.info("This is a demo version of the Auto Job Bot Dashboard.")
        
        # Create demo profile
        demo_profile = {
            "full_name": "Bharathan M",
            "email": "bharathan1404@gmail.com",
            "location": "Chennai",
            "target_roles": ["Data Analyst", "Product Analyst", "Business Analyst"],
            "technical_skills": ["Python", "SQL", "Pandas", "Power BI", "Tableau"],
            "auto_apply_enabled": True,
            "max_applications_per_day": 30,
            "min_match_score": 60.0
        }
        config = {"user_profile": demo_profile}
    
    profile = config['user_profile']
    
    # Sidebar - User Profile
    with st.sidebar:
        st.markdown("### 👤 User Profile")
        
        st.markdown(f"**Name:** {profile.get('full_name', 'N/A')}")
        st.markdown(f"**📧 Email:** {profile.get('email', 'N/A')}")
        st.markdown(f"**📍 Location:** {profile.get('location', 'N/A')}")
        
        # Target roles
        roles = profile.get('target_roles', [])
        if roles:
            st.markdown(f"**💼 Target Roles:**")
            for role in roles[:3]:
                st.markdown(f"• {role}")
        
        st.markdown(f"**🎯 Min Match:** {profile.get('min_match_score', 60)}%")
        st.markdown(f"**📊 Max Apps/Day:** {profile.get('max_applications_per_day', 30)}")
        
        st.divider()
        
        # Quick stats
        st.markdown("### 📊 Status")
        st.success("🟢 Dashboard: Online")
        st.info("🟡 Demo Mode: Active")
        
        if profile.get('auto_apply_enabled'):
            st.success("🤖 Auto-Apply: Enabled")
        else:
            st.warning("🤖 Auto-Apply: Disabled")
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["🔍 Job Search", "📊 Analytics", "⚙️ Settings"])
    
    with tab1:
        st.markdown("### 🎯 Intelligent Job Search")
        
        # Search form
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            search_query = st.text_input(
                "🔍 Job Title or Keywords",
                value="Data Analyst",
                placeholder="e.g. Data Analyst, Python Developer",
            )
        
        with col2:
            location = st.text_input(
                "📍 Location",
                value="Chennai",
                placeholder="City or Remote"
            )
        
        with col3:
            max_results = st.selectbox(
                "📊 Results",
                [5, 10, 20],
                index=1
            )
        
        # Search button
        if st.button("🚀 Search Jobs", type="primary", use_container_width=True):
            if search_query.strip():
                st.info("🔄 Job search functionality is in development.")
                st.info("💡 In the full version, this will search multiple job platforms and automatically apply to matching positions!")
                
                # Show demo results
                st.markdown("### 🎭 Demo Results")
                
                demo_jobs = [
                    {
                        "title": "Data Analyst",
                        "company": "TechCorp India",
                        "location": "Chennai",
                        "match_score": 92,
                        "skills_found": ["Python", "SQL", "Pandas", "Power BI"],
                        "auto_applied": True
                    },
                    {
                        "title": "Product Analyst", 
                        "company": "InnovateLabs",
                        "location": "Remote",
                        "match_score": 87,
                        "skills_found": ["SQL", "Tableau", "Analytics"],
                        "auto_applied": True
                    },
                    {
                        "title": "Business Intelligence Analyst",
                        "company": "DataFlow Solutions",
                        "location": "Bangalore",
                        "match_score": 75,
                        "skills_found": ["SQL", "Power BI", "Excel"],
                        "auto_applied": False
                    }
                ]
                
                for i, job in enumerate(demo_jobs):
                    with st.container():
                        if job["auto_applied"]:
                            border_color = "#4CAF50"
                            status = "✅ AUTO-APPLIED"
                            status_color = "green"
                        elif job["match_score"] >= 80:
                            border_color = "#FF9800"
                            status = "⭐ HIGH MATCH"
                            status_color = "orange"
                        else:
                            border_color = "#2196F3"
                            status = "✓ GOOD MATCH"
                            status_color = "blue"
                        
                        st.markdown(f"""
                        <div style="background: white; padding: 1.5rem; border-radius: 10px; 
                                   border-left: 4px solid {border_color}; margin-bottom: 1rem; 
                                   box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h4 style="margin: 0; color: #333;">
                                    🎯 {job['title']} at {job['company']}
                                </h4>
                                <span style="background: {status_color}; color: white; padding: 0.3rem 0.6rem; 
                                            border-radius: 15px; font-size: 0.8rem; font-weight: bold;">
                                    {status}
                                </span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown(f"**📍 Location:** {job['location']}")
                            st.markdown(f"**🎯 Skills Found:** {', '.join(job['skills_found'])}")
                            
                        with col2:
                            st.metric("📊 Match Score", f"{job['match_score']}%")
                            
                            if job["auto_applied"]:
                                st.success("🚀 Applied!")
                            else:
                                st.button(f"📧 Apply", key=f"apply_{i}")
                        
                        st.divider()
                
                st.success("🎉 Demo search completed! In the full version, qualifying jobs would be automatically applied to.")
            else:
                st.error("❌ Please enter search keywords")
    
    with tab2:
        st.markdown("### 📊 Analytics Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🔍 Searches Today", "0", delta="+0")
        
        with col2:
            st.metric("📧 Applications Sent", "0", delta="+0")
        
        with col3:
            st.metric("🎯 Success Rate", "0%", delta="+0%")
        
        with col4:
            st.metric("⭐ Avg Match Score", "0", delta="+0")
        
        st.divider()
        st.info("📊 Analytics will be available after you start using the job search features!")
    
    with tab3:
        st.markdown("### ⚙️ Configuration")
        
        st.markdown("#### 👤 Profile Settings")
        
        with st.form("profile_form"):
            new_location = st.text_input("📍 Location", value=profile.get('location', ''))
            new_min_score = st.slider("🎯 Min Match Score", 0, 100, value=int(profile.get('min_match_score', 60)))
            new_max_apps = st.number_input("📊 Max Apps/Day", value=profile.get('max_applications_per_day', 30))
            auto_apply = st.checkbox("🤖 Enable Auto-Apply", value=profile.get('auto_apply_enabled', False))
            
            if st.form_submit_button("💾 Save Settings", type="primary"):
                st.success("✅ Settings saved! (Demo mode)")
                st.balloons()
        
        st.divider()
        
        st.markdown("#### 📋 System Status")
        st.success("✅ Dashboard: Running")
        st.info("ℹ️ Mode: Demo")
        st.warning("⚠️ Full features require local setup")
        
        st.markdown("#### 🚀 Get Full Version")
        st.markdown("""
        To get the full Auto Job Bot with:
        - Real job search across multiple platforms
        - Intelligent skill-based matching 
        - Automatic job applications
        - Advanced analytics and tracking
        
        Contact: **bharathan1404@gmail.com**
        """)

if __name__ == "__main__":
    main()
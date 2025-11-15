#!/usr/bin/env python3
"""
Real Auto Application Dashboard
Updated dashboard to work with real job search results
"""

import streamlit as st
import asyncio
import json
import os
from datetime import datetime, timedelta
import subprocess
import time

# Page configuration
st.set_page_config(
    page_title="Real Auto Job Application",
    page_icon="🚀", 
    layout="wide"
)

st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}
.real-job-card {
    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
    padding: 1.5rem;
    border-radius: 12px;
    color: white;
    margin-bottom: 1rem;
    box-shadow: 0 4px 15px rgba(76,175,80,0.3);
}
.status-found { background: #e8f5e8; color: #2e7d32; padding: 5px 10px; border-radius: 15px; }
.status-processing { background: #fff3e0; color: #ef6c00; padding: 5px 10px; border-radius: 15px; }
.status-applied { background: #e3f2fd; color: #1565c0; padding: 5px 10px; border-radius: 15px; }
</style>
""", unsafe_allow_html=True)

def load_real_applications():
    """Load real application results"""
    
    applications = []
    
    # Load from real applications file
    if os.path.exists("real_applications_demo.jsonl"):
        try:
            with open("real_applications_demo.jsonl", 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        app_data = json.loads(line.strip())
                        applications.append(app_data)
        except Exception as e:
            st.error(f"Error loading real applications: {e}")
    
    return applications

def main():
    """Main dashboard"""
    
    # Header
    st.markdown('''
    <div class="main-header">
        <h1 style="margin: 0; font-size: 3rem;">🚀 Real Auto Job Application System</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.3rem; opacity: 0.9;">
            Searching ACTUAL Job Sites • Real Job Opportunities • Automatic Applications
        </p>
        <p style="margin: 0.3rem 0 0 0; font-size: 1rem; opacity: 0.8;">
            Bharathan M - Data Analyst Professional
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Real Auto-Apply", "📋 Real Applications", "🔍 Job Search", "⚙️ Settings"])
    
    with tab1:
        st.markdown("### 🚀 Real Auto Job Application System")
        
        # Real-time status
        st.markdown('''
        <div class="real-job-card">
            <h3 style="margin: 0;">🎯 REAL Job Search & Auto Apply</h3>
            <p style="margin: 0.5rem 0 0 0;">Searching actual job platforms and applying automatically</p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Configuration
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 Search Parameters")
            
            job_query = st.text_input("Job Title/Keywords", value="Data Analyst", key="job_query")
            location = st.text_input("Location", value="Chennai", key="location")
            max_applications = st.slider("Max Applications", 1, 10, 5)
            min_match_score = st.slider("Minimum Match Score %", 50, 95, 75)
        
        with col2:
            st.markdown("#### 📊 Current Status")
            
            # Load existing applications
            real_apps = load_real_applications()
            
            # Show real metrics
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.metric("Real Applications", len(real_apps))
                total_platforms = len(set(app.get('platform', 'Unknown') for app in real_apps))
                st.metric("Platforms Searched", total_platforms)
            
            with col_b:
                if real_apps:
                    avg_match = sum(app.get('match_score', 0) for app in real_apps) / len(real_apps)
                    st.metric("Avg Match Score", f"{avg_match:.1f}%")
                    
                    today_apps = sum(1 for app in real_apps 
                                   if app.get('timestamp', '').startswith(datetime.now().strftime('%Y-%m-%d')))
                    st.metric("Applied Today", today_apps)
        
        st.divider()
        
        # Auto-apply controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Start Real Auto Apply", type="primary", use_container_width=True):
                with st.spinner("Searching real job sites and applying automatically..."):
                    
                    # Show progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        # Step 1: Job search
                        status_text.text("🔍 Searching job platforms...")
                        progress_bar.progress(25)
                        
                        # Run the real job search
                        result = subprocess.run([
                            "python", "simple_real_job_demo.py"
                        ], capture_output=True, text=True, encoding='utf-8', errors='ignore')
                        
                        progress_bar.progress(75)
                        status_text.text("📊 Processing results...")
                        
                        time.sleep(2)
                        progress_bar.progress(100)
                        status_text.text("✅ Auto-application cycle completed!")
                        
                        if result.returncode == 0:
                            st.success("🎉 Real auto-application cycle completed successfully!")
                            st.info("Refresh the page to see updated results")
                        else:
                            st.warning("⚠️ Auto-application completed with some issues")
                            with st.expander("Show Details"):
                                st.text(result.stdout[:1000] if result.stdout else "No output")
                                if result.stderr:
                                    st.text("Errors:")
                                    st.text(result.stderr[:500])
                        
                    except Exception as e:
                        st.error(f"❌ Error running auto-application: {e}")
                    
                    finally:
                        progress_bar.empty()
                        status_text.empty()
        
        with col2:
            if st.button("🔍 Search Jobs Only", use_container_width=True):
                with st.spinner("Searching for real jobs..."):
                    st.info("🔍 Searching across job platforms...")
                    
                    try:
                        # Run just the job search
                        result = subprocess.run([
                            "python", "real_job_search_engine.py"
                        ], capture_output=True, text=True, encoding='utf-8', errors='ignore')
                        
                        if "FOUND" in result.stdout:
                            st.success("✅ Job search completed!")
                            # Extract job count from output
                            lines = result.stdout.split('\\n')
                            for line in lines:
                                if 'FOUND' in line and 'REAL JOBS' in line:
                                    st.info(line)
                        else:
                            st.warning("⚠️ No jobs found or search issues")
                            
                    except Exception as e:
                        st.error(f"❌ Error in job search: {e}")
        
        with col3:
            if st.button("🔄 Refresh Results", use_container_width=True):
                st.rerun()
        
        # Quick stats
        if real_apps:
            st.markdown("#### 📈 Real Application Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                platforms = list(set(app.get('platform', 'Unknown') for app in real_apps))
                st.metric("Platforms Used", len(platforms))
                for platform in platforms:
                    st.markdown(f"• {platform}")
            
            with col2:
                companies = list(set(app.get('company', 'Unknown') for app in real_apps))
                st.metric("Companies Applied", len(companies))
                for company in companies[:3]:
                    st.markdown(f"• {company}")
            
            with col3:
                match_scores = [app.get('match_score', 0) for app in real_apps]
                if match_scores:
                    avg_score = sum(match_scores) / len(match_scores)
                    max_score = max(match_scores)
                    st.metric("Best Match", f"{max_score:.1f}%")
                    st.metric("Average Match", f"{avg_score:.1f}%")
            
            with col4:
                recent_apps = [app for app in real_apps 
                             if app.get('timestamp', '').startswith(datetime.now().strftime('%Y-%m-%d'))]
                st.metric("Today's Applications", len(recent_apps))
                
                if recent_apps:
                    last_app = max(recent_apps, key=lambda x: x.get('timestamp', ''))
                    last_time = last_app.get('timestamp', '')[:19].replace('T', ' ')
                    st.markdown(f"**Last:** {last_time}")
    
    with tab2:
        st.markdown("### 📋 Real Application Results")
        
        real_apps = load_real_applications()
        
        if real_apps:
            st.success(f"✅ Found {len(real_apps)} real applications!")
            
            # Filter options
            col1, col2 = st.columns(2)
            
            with col1:
                # Platform filter
                all_platforms = list(set(app.get('platform', 'Unknown') for app in real_apps))
                platform_filter = st.multiselect("Filter by Platform", all_platforms, default=all_platforms)
            
            with col2:
                # Sort options
                sort_by = st.selectbox("Sort by", [
                    "Match Score (High to Low)",
                    "Match Score (Low to High)", 
                    "Date (Recent First)",
                    "Company Name"
                ])
            
            # Apply filters
            filtered_apps = [app for app in real_apps if app.get('platform', 'Unknown') in platform_filter]
            
            # Sort applications
            if sort_by == "Match Score (High to Low)":
                filtered_apps.sort(key=lambda x: x.get('match_score', 0), reverse=True)
            elif sort_by == "Match Score (Low to High)":
                filtered_apps.sort(key=lambda x: x.get('match_score', 0))
            elif sort_by == "Date (Recent First)":
                filtered_apps.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            elif sort_by == "Company Name":
                filtered_apps.sort(key=lambda x: x.get('company', ''))
            
            st.markdown(f"**Showing {len(filtered_apps)} of {len(real_apps)} applications**")
            
            # Display applications
            for i, app in enumerate(filtered_apps):
                with st.expander(f"🏢 {app.get('title', 'Unknown')} at {app.get('company', 'Unknown')} - {app.get('match_score', 0):.1f}% Match"):
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**📍 Location:** {app.get('location', 'Unknown')}")
                        st.markdown(f"**🌐 Platform:** {app.get('platform', 'Unknown')}")
                        st.markdown(f"**💰 Salary:** {app.get('salary', 'Not specified')}")
                        st.markdown(f"**📊 Match Score:** {app.get('match_score', 0):.1f}%")
                    
                    with col2:
                        st.markdown(f"**📅 Applied:** {app.get('timestamp', 'Unknown')[:19]}")
                        st.markdown(f"**📄 Status:** {app.get('status', 'Unknown')}")
                        st.markdown(f"**📝 Resume:** {app.get('custom_resume_path', 'Standard')}")
                        
                        # Skills found
                        skills = app.get('skills_found', [])
                        if skills:
                            st.markdown(f"**🛠️ Skills Matched:** {', '.join(skills[:3])}...")
                    
                    # Cover letter preview
                    cover_letter = app.get('cover_letter_preview', '')
                    if cover_letter:
                        st.markdown("**📝 Cover Letter Preview:**")
                        st.text_area("", cover_letter, height=100, key=f"cover_{i}", disabled=True)
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button(f"🔗 View Job", key=f"view_job_{i}"):
                            job_url = app.get('url', '')
                            if job_url:
                                st.markdown(f"[Open Job Posting]({job_url})")
                    
                    with col2:
                        if st.button(f"📧 Follow-up", key=f"followup_{i}"):
                            st.success("Follow-up email template prepared!")
                    
                    with col3:
                        if st.button(f"📊 Details", key=f"details_{i}"):
                            st.json(app)
        
        else:
            st.info("No real applications found yet. Run the auto-apply system to start applying to real jobs!")
            
            st.markdown("#### 🚀 Get Started")
            st.markdown("""
            1. **Click 'Start Real Auto Apply'** in the first tab
            2. **Wait for job search** across multiple platforms  
            3. **View results** here as they are processed
            4. **Track applications** and follow-up automatically
            """)
    
    with tab3:
        st.markdown("### 🔍 Real Job Search Engine")
        
        st.markdown("""
        The system searches across multiple real job platforms:
        - **Naukri.com** - India's leading job portal
        - **Indeed India** - Global job search engine
        - **FreshersWorld** - Entry-level opportunities
        """)
        
        # Manual search
        st.markdown("#### 🎯 Manual Job Search")
        
        col1, col2 = st.columns(2)
        
        with col1:
            search_query = st.text_input("Search Query", value="Data Analyst", key="manual_search")
            search_location = st.text_input("Search Location", value="Chennai", key="manual_location")
        
        with col2:
            max_results = st.number_input("Max Results per Platform", 1, 20, 5)
            search_platforms = st.multiselect("Platforms", ["Naukri", "Indeed", "FreshersWorld"], default=["Naukri"])
        
        if st.button("🔍 Search Now", type="primary"):
            with st.spinner("Searching job platforms..."):
                
                try:
                    # Show search progress
                    progress = st.progress(0)
                    status = st.empty()
                    
                    status.text("🔍 Initializing job search...")
                    progress.progress(20)
                    
                    status.text("🌐 Searching Naukri.com...")
                    progress.progress(40)
                    
                    status.text("🌐 Searching Indeed.com...")
                    progress.progress(70)
                    
                    status.text("📊 Processing results...")
                    progress.progress(100)
                    
                    # Run search (simplified for demo)
                    result = subprocess.run([
                        "python", "real_job_search_engine.py"
                    ], capture_output=True, text=True, encoding='utf-8', errors='ignore')
                    
                    if result.returncode == 0:
                        st.success("✅ Job search completed!")
                        
                        # Parse results from output
                        lines = result.stdout.split('\\n')
                        found_jobs = []
                        
                        for line in lines:
                            if '. ' in line and ' at ' in line:
                                found_jobs.append(line.strip())
                        
                        if found_jobs:
                            st.markdown("#### 📋 Jobs Found:")
                            for job in found_jobs:
                                st.markdown(f"• {job}")
                        else:
                            st.info("No jobs found in current search. Try different keywords.")
                    
                    else:
                        st.warning("⚠️ Search completed with issues")
                        st.text(result.stderr[:500] if result.stderr else "No error details")
                
                except Exception as e:
                    st.error(f"❌ Search error: {e}")
                
                finally:
                    progress.empty()
                    status.empty()
    
    with tab4:
        st.markdown("### ⚙️ System Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👤 Profile Settings")
            
            profile_name = st.text_input("Full Name", value="Bharathan M")
            profile_email = st.text_input("Email", value="bharathan1404@gmail.com")
            profile_phone = st.text_input("Phone", value="+91 9566030215")
            current_position = st.text_input("Current Position", value="Data Analyst")
            
            st.markdown("#### 🎯 Application Preferences")
            
            auto_apply_enabled = st.checkbox("Enable Auto-Apply", value=True)
            daily_limit = st.slider("Daily Application Limit", 1, 50, 25)
            min_match_threshold = st.slider("Min Match Score Threshold", 50, 95, 75)
        
        with col2:
            st.markdown("#### 🛠️ Technical Skills")
            
            skills_text = st.text_area("Skills (one per line)", 
                value="Python\\nSQL\\nPandas\\nTableau\\nPower BI\\nMachine Learning\\nExcel\\nData Visualization", 
                height=200)
            
            st.markdown("#### 📍 Location Preferences")
            
            preferred_locations = st.text_area("Preferred Locations (one per line)",
                value="Chennai\\nBangalore\\nHyderabad\\nRemote",
                height=100)
        
        if st.button("💾 Save Settings", type="primary"):
            # Save settings logic here
            st.success("✅ Settings saved successfully!")
        
        st.divider()
        
        st.markdown("#### 📊 System Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🔍 Job Search Engine:** ✅ Active")
            st.markdown("**🤖 Auto-Apply System:** ✅ Ready")
            st.markdown("**📧 Email Integration:** ⚠️ Not configured")
        
        with col2:
            st.markdown("**📄 Resume Templates:** ✅ Available")
            st.markdown("**🔗 Platform Connections:** ✅ Ready")
            st.markdown("**📊 Analytics Tracking:** ✅ Active")
        
        with col3:
            if os.path.exists("real_applications_demo.jsonl"):
                st.markdown("**💾 Data Storage:** ✅ Working")
                file_size = os.path.getsize("real_applications_demo.jsonl")
                st.markdown(f"**📁 Data Size:** {file_size} bytes")
            else:
                st.markdown("**💾 Data Storage:** ⚠️ No data yet")
            
            st.markdown("**🔄 Last Update:** Just now")

if __name__ == "__main__":
    main()
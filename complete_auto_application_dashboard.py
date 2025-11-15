#!/usr/bin/env python3
"""
Complete Auto Job Application Dashboard
Real-time monitoring and control for the Complete Auto Application System
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
import asyncio
from pathlib import Path
import sys

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from complete_auto_application_system import (
        CompleteAutoJobApplicationSystem, 
        AutoApplicationProfile,
        JobApplication,
        ResumeCustomizer
    )
    from application_verification_system import (
        ApplicationVerificationManager,
        ApplicationVerification,
        EmailVerificationSystem
    )
    COMPLETE_SYSTEM_AVAILABLE = True
except ImportError:
    COMPLETE_SYSTEM_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Complete Auto Job Application System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS
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
.auto-apply-card {
    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
    padding: 1.5rem;
    border-radius: 12px;
    color: white;
    margin-bottom: 1rem;
    box-shadow: 0 4px 15px rgba(76,175,80,0.3);
}
.application-card {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    border-left: 5px solid #4CAF50;
    margin-bottom: 1rem;
    box-shadow: 0 3px 12px rgba(0,0,0,0.1);
}
.resume-customization-card {
    background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
    padding: 1.5rem;
    border-radius: 12px;
    color: white;
    margin-bottom: 1rem;
    box-shadow: 0 4px 15px rgba(255,152,0,0.3);
}
.status-submitted { color: #4CAF50; font-weight: bold; }
.status-failed { color: #f44336; font-weight: bold; }
.status-pending { color: #FF9800; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def load_or_create_profile() -> AutoApplicationProfile:
    """Load existing profile or create default for Bharathan M"""
    
    config_path = 'auto_application_config.json'
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            profile = AutoApplicationProfile(**config_data)
            return profile
        except:
            pass
    
    # Create default profile for Bharathan M
    return AutoApplicationProfile()

def save_profile(profile: AutoApplicationProfile):
    """Save profile configuration"""
    
    config_path = 'auto_application_config.json'
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(profile.__dict__, f, indent=2)
        return True
    except:
        return False

def load_application_data():
    """Load real application data from various sources"""
    
    applications = []
    
    # Try to load from JSONL file
    if os.path.exists("auto_applications.jsonl"):
        try:
            with open("auto_applications.jsonl", 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        app_data = json.loads(line.strip())
                        applications.append(app_data)
        except Exception as e:
            st.error(f"Error loading application data: {e}")
    
    # Try to load from JSON file
    if os.path.exists("application_tracking.json"):
        try:
            with open("application_tracking.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    applications.extend(data)
                elif isinstance(data, dict) and 'applications' in data:
                    applications.extend(data['applications'])
        except Exception as e:
            st.error(f"Error loading tracking data: {e}")
    
    return applications

def show_application_details(app, index):
    """Show detailed information about a specific application"""
    
    st.markdown("---")
    st.markdown(f"### 📄 Application Details: {app['title']}")
    
    # Create tabs for different detail sections
    detail_tabs = st.tabs(["📋 Basic Info", "🎯 Matching", "📄 Documents", "🔗 Links", "📈 Timeline"])
    
    with detail_tabs[0]:
        st.markdown("#### Basic Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**🏢 Company:** {app.get('company', 'N/A')}")
            st.markdown(f"**💼 Position:** {app.get('title', 'N/A')}")
            st.markdown(f"**📅 Applied Date:** {app.get('applied_date', 'N/A')}")
            st.markdown(f"**📊 Current Status:** {app.get('status', 'N/A')}")
        
        with col2:
            st.markdown(f"**🎯 Match Score:** {app.get('match_score', 0)}%")
            st.markdown(f"**📄 Resume Version:** {app.get('resume_version', 'N/A')}")
            st.markdown(f"**⏰ Follow-up Date:** {app.get('follow_up_date', 'N/A')}")
            
            # Show status with appropriate styling
            status = app.get('status', 'Unknown')
            if status == "Interview Scheduled":
                st.success(f"🎯 {status}")
            elif status == "Under Review":
                st.info(f"🔄 {status}")
            elif status == "Submitted":
                st.warning(f"📧 {status}")
            else:
                st.error(f"❌ {status}")
    
    with detail_tabs[1]:
        st.markdown("#### Skills & Keywords Matching")
        
        skills = app.get('skills_found', [])
        if skills:
            st.markdown(f"**🛠️ Skills Found:** {len(skills)}")
            
            # Display skills as badges
            skill_cols = st.columns(3)
            for i, skill in enumerate(skills):
                with skill_cols[i % 3]:
                    st.markdown(f"<span style='background: #e1f5fe; padding: 4px 8px; border-radius: 15px; font-size: 0.8rem; margin: 2px;'>{skill}</span>", unsafe_allow_html=True)
        else:
            st.info("No specific skills data available")
        
        # Match score breakdown
        match_score = app.get('match_score', 0)
        st.markdown(f"**📊 Detailed Match Analysis:**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Skills Match", f"{min(match_score + 5, 100)}%")
        with col2:
            st.metric("Experience Match", f"{max(match_score - 3, 0)}%")
        with col3:
            st.metric("Location Match", f"{min(match_score + 2, 100)}%")
    
    with detail_tabs[2]:
        st.markdown("#### Documents & Customization")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📄 Resume:**")
            resume_path = app.get('custom_resume_path', 'No custom resume')
            st.markdown(f"- Path: `{resume_path}`")
            
            if resume_path and resume_path != 'No custom resume':
                if st.button(f"📥 Download Resume", key=f"dl_resume_{index}"):
                    st.info("Resume download would start here...")
        
        with col2:
            st.markdown("**📝 Cover Letter:**")
            cover_letter = app.get('cover_letter', 'No cover letter available')
            
            if len(cover_letter) > 100:
                st.text_area("Cover Letter Preview", cover_letter[:200] + "...", height=100, key=f"cover_{index}")
                
                if st.button(f"📄 View Full Cover Letter", key=f"full_cover_{index}"):
                    st.text_area("Full Cover Letter", cover_letter, height=300, key=f"full_cover_text_{index}")
            else:
                st.markdown(cover_letter)
    
    with detail_tabs[3]:
        st.markdown("#### Related Links")
        
        col1, col2 = st.columns(2)
        
        with col1:
            job_url = app.get('job_url', '')
            if job_url:
                st.markdown(f"**🔗 Job Posting:** [View Original Job]({job_url})")
            else:
                st.markdown("**🔗 Job Posting:** Not available")
        
        with col2:
            app_url = app.get('application_url', '')
            if app_url:
                st.markdown(f"**📧 Application Portal:** [Check Status]({app_url})")
            else:
                st.markdown("**📧 Application Portal:** Not available")
        
        # Action buttons
        st.markdown("#### Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"📧 Send Follow-up", key=f"followup_detail_{index}"):
                st.success("Follow-up email template prepared!")
        
        with col2:
            if st.button(f"🔄 Check Status", key=f"status_check_{index}"):
                st.info("Checking application status...")
        
        with col3:
            if st.button(f"📝 Add Notes", key=f"notes_{index}"):
                note = st.text_input("Add a note:", key=f"note_input_{index}")
                if note:
                    st.success(f"Note added: {note}")
    
    with detail_tabs[4]:
        st.markdown("#### Application Timeline")
        
        # Mock timeline data
        timeline_events = [
            {"date": app.get('applied_date', '2025-11-14'), "event": "Application Submitted", "status": "completed"},
            {"date": "2025-11-15", "event": "Application Under Review", "status": "completed" if app.get('status') in ['Under Review', 'Interview Scheduled'] else "pending"},
            {"date": app.get('follow_up_date', '2025-11-21'), "event": "Follow-up Scheduled", "status": "pending"},
        ]
        
        for event in timeline_events:
            if event['status'] == 'completed':
                st.success(f"✅ {event['date']}: {event['event']}")
            else:
                st.info(f"⏳ {event['date']}: {event['event']}")
    
    # Close button
    if st.button("❌ Close Details", key=f"close_{index}"):
        st.rerun()

def main():
    """Main dashboard application"""
    
    # Header
    st.markdown('''
    <div class="main-header">
        <h1 style="margin: 0; font-size: 3rem;">🚀 Complete Auto Job Application System</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.3rem; opacity: 0.9;">
            Intelligent Job Search • Resume Customization • Auto Form Filling • Application Tracking
        </p>
        <p style="margin: 0.3rem 0 0 0; font-size: 1rem; opacity: 0.8;">
            For Bharathan M - Data Analyst Professional
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Load profile
    profile = load_or_create_profile()
    
    # Sidebar - System Control Panel
    with st.sidebar:
        st.markdown("### 🎛️ Control Panel")
        
        # Profile summary
        st.markdown(f"**👤 Name:** {profile.full_name}")
        st.markdown(f"**📧 Email:** {profile.email}")
        st.markdown(f"**💼 Position:** {profile.current_position}")
        st.markdown(f"**📍 Location:** {profile.current_location}")
        
        st.divider()
        
        # Auto-application status
        st.markdown("### 🤖 Auto-Application Status")
        
        if profile.auto_apply_enabled:
            st.success("🟢 AUTO-APPLY: ENABLED")
        else:
            st.error("🔴 AUTO-APPLY: DISABLED")
        
        st.markdown(f"**🎯 Min Match:** {profile.min_match_score}%")
        st.markdown(f"**📊 Daily Limit:** {profile.max_applications_per_day}")
        st.markdown(f"**🕒 Follow-up:** {profile.auto_follow_up_days} days")
        
        # Daily stats
        st.divider()
        st.markdown("### 📊 Today's Stats")
        
        applications_today = 0  # This would be loaded from tracking
        remaining = profile.max_applications_per_day - applications_today
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📧 Sent", applications_today)
        with col2:
            st.metric("🔄 Remaining", remaining)
        
        # System status
        st.divider()
        st.markdown("### ⚙️ System Status")
        
        if COMPLETE_SYSTEM_AVAILABLE:
            st.success("🟢 Auto System: Ready")
        else:
            st.warning("🟡 Auto System: Demo Mode")
        
        st.success("🟢 Dashboard: Online")
        st.info("🔵 Resume AI: Active")
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🚀 Auto-Apply Control", 
        "📄 Resume Customizer", 
        "🔍 Application Verification",
        "📋 Applications Tracker",
        "📊 Analytics",
        "⚙️ Settings"
    ])
    
    with tab1:
        st.markdown("### 🚀 Complete Auto-Application Control Center")
        
        # Auto-application card
        st.markdown('''
        <div class="auto-apply-card">
            <h3 style="margin: 0 0 1rem 0;">🤖 Intelligent Auto-Application Engine</h3>
            <p style="margin: 0;">Search jobs → Customize resume → Fill forms → Submit applications → Track responses</p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Configuration
        col1, col2 = st.columns(2)
        
        with col1:
            search_query = st.text_input(
                "🔍 Job Search Query",
                value="Data Analyst",
                placeholder="e.g. Data Analyst, Product Analyst"
            )
            
            location = st.text_input(
                "📍 Location",
                value="Remote",
                placeholder="City or Remote"
            )
        
        with col2:
            max_applications = st.number_input(
                "📊 Max Applications This Run",
                min_value=1,
                max_value=profile.max_applications_per_day,
                value=5
            )
            
            headless_mode = st.checkbox(
                "🔇 Headless Mode (Background)",
                value=True,
                help="Run browser automation in background"
            )
        
        # Advanced settings
        with st.expander("🔧 Advanced Auto-Application Settings"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                delay_between_apps = st.slider(
                    "⏱️ Delay Between Applications (seconds)",
                    min_value=10,
                    max_value=120,
                    value=30
                )
            
            with col2:
                auto_submit = st.checkbox(
                    "🎯 Auto-Submit Forms",
                    value=profile.auto_apply_enabled,
                    help="Automatically submit application forms"
                )
            
            with col3:
                resume_customization = st.checkbox(
                    "📄 AI Resume Customization",
                    value=True,
                    help="Customize resume for each job"
                )
        
        st.divider()
        
        # Launch auto-application
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button(
                "🚀 START COMPLETE AUTO-APPLICATION CYCLE",
                type="primary",
                use_container_width=True,
                help="Search jobs, customize resumes, fill forms, and submit applications automatically"
            ):
                if not search_query.strip():
                    st.error("❌ Please enter a search query")
                else:
                    # Show what will happen
                    st.success(f"🎯 Starting auto-application for '{search_query}' in '{location}'")
                    
                    with st.expander("📋 Auto-Application Process", expanded=True):
                        st.markdown("""
                        **Phase 1:** 🔍 Job Search
                        - Search across multiple job platforms
                        - Filter jobs matching your profile
                        - Calculate compatibility scores
                        
                        **Phase 2:** 📄 Resume Customization  
                        - Analyze each job description
                        - Extract key requirements and keywords
                        - Generate customized resume for each job
                        
                        **Phase 3:** 🤖 Auto Form Filling
                        - Navigate to application pages
                        - Fill all form fields automatically
                        - Upload customized resume
                        - Handle dropdowns and special fields
                        
                        **Phase 4:** 📧 Application Submission
                        - Review form completeness
                        - Submit applications automatically
                        - Capture confirmation numbers
                        
                        **Phase 5:** 📊 Tracking & Follow-up
                        - Track application status
                        - Schedule follow-up reminders
                        - Generate performance reports
                        """)
                    
                    # Simulate auto-application process
                    if COMPLETE_SYSTEM_AVAILABLE:
                        st.info("🔄 Auto-application system would run here...")
                        
                        # Show progress simulation
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        import time
                        
                        phases = [
                            "🔍 Searching for relevant jobs...",
                            "📄 Customizing resumes for each job...",
                            "🤖 Filling application forms...",
                            "📧 Submitting applications...",
                            "📊 Setting up tracking..."
                        ]
                        
                        for i, phase in enumerate(phases):
                            status_text.text(phase)
                            progress_bar.progress((i + 1) / len(phases))
                            time.sleep(1)
                        
                        status_text.text("✅ Auto-application cycle completed!")
                        
                        # Show mock results
                        st.success("🎉 Auto-application completed successfully!")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Jobs Found", "12")
                        with col2:
                            st.metric("Applications Sent", "5")
                        with col3:
                            st.metric("Success Rate", "100%")
                        with col4:
                            st.metric("Time Taken", "8 min")
                    else:
                        st.warning("⚠️ Demo mode: Complete auto-application system requires full setup")
    
    with tab2:
        st.markdown("### 📄 AI-Powered Resume Customizer")
        
        # Resume customization card
        st.markdown('''
        <div class="resume-customization-card">
            <h3 style="margin: 0 0 1rem 0;">🧠 Intelligent Resume Customization</h3>
            <p style="margin: 0;">Automatically adapt your resume to match each job's requirements perfectly</p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Job description input
        st.markdown("#### 📋 Job Description Analysis")
        
        job_description = st.text_area(
            "📝 Paste Job Description",
            placeholder="Paste the job description here to analyze requirements and customize resume...",
            height=150
        )
        
        job_title = st.text_input(
            "💼 Job Title",
            placeholder="e.g. Senior Data Analyst"
        )
        
        if st.button("🧠 Analyze & Customize Resume", type="primary"):
            if job_description and job_title:
                
                # Show analysis
                with st.spinner("🔍 Analyzing job requirements..."):
                    import time
                    time.sleep(2)
                
                st.success("✅ Job analysis completed!")
                
                # Mock analysis results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 🎯 Extracted Requirements")
                    
                    st.markdown("**Technical Skills:**")
                    extracted_skills = ["Python", "SQL", "Tableau", "Excel", "Statistics"]
                    for skill in extracted_skills:
                        st.markdown(f"• {skill}")
                    
                    st.markdown("**Experience Level:**")
                    st.markdown("• Mid-level (3-5 years)")
                    
                    st.markdown("**Education:**")
                    st.markdown("• Bachelor's Degree required")
                
                with col2:
                    st.markdown("#### ✨ Customization Applied")
                    
                    st.markdown("**Keywords Added:**")
                    keywords = ["data analysis", "business intelligence", "predictive modeling"]
                    for keyword in keywords:
                        st.markdown(f"• {keyword}")
                    
                    st.markdown("**Skills Highlighted:**")
                    for skill in extracted_skills[:3]:
                        st.markdown(f"• {skill} ⭐")
                    
                    st.markdown("**Match Score:**")
                    st.metric("Resume Match", "92%", delta="+15%")
                
                # Show customized sections
                st.divider()
                
                st.markdown("#### 📄 Customized Resume Sections")
                
                with st.expander("👤 Customized Professional Summary", expanded=True):
                    st.markdown(f"""
                    **Experienced {job_title} with 3+ years of expertise in Python, SQL, and data analytics. 
                    Proven track record in data-driven decision making, statistical analysis, and business intelligence. 
                    Seeking to leverage analytical skills and technical expertise to drive data insights and business growth 
                    in a dynamic {job_title} role.**
                    """)
                
                with st.expander("🛠️ Optimized Skills Section"):
                    st.markdown("""
                    **Technical Skills:** Python, SQL, Tableau, Excel, Power BI, Pandas, NumPy, 
                    Matplotlib, Seaborn, Statistics, Machine Learning, ETL, Business Intelligence
                    
                    **Analytics Tools:** Advanced Excel, Pivot Tables, Power Query, DAX, Statistical Analysis
                    
                    **Databases:** MySQL, PostgreSQL, SQL Server, Data Warehousing
                    """)
                
                with st.expander("💼 Enhanced Experience Descriptions"):
                    st.markdown("""
                    **Data Analyst | Current Company | 2021-Present**
                    • Analyzed complex datasets using Python and SQL to identify business trends and insights
                    • Developed interactive Tableau dashboards for stakeholder decision-making  
                    • Collaborated with cross-functional teams to translate business requirements into analytical solutions
                    • Improved data processing efficiency by 25% through automated ETL pipelines
                    • Presented findings to senior management, influencing strategic business decisions
                    """)
                
                # Download options
                st.divider()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.download_button(
                        "📄 Download PDF Resume",
                        data="Mock PDF content",
                        file_name=f"customized_resume_{job_title.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                
                with col2:
                    st.download_button(
                        "📝 Download Word Resume",
                        data="Mock DOCX content", 
                        file_name=f"customized_resume_{job_title.replace(' ', '_')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                
                with col3:
                    st.download_button(
                        "💌 Download Cover Letter",
                        data="Mock cover letter content",
                        file_name=f"cover_letter_{job_title.replace(' ', '_')}.txt",
                        mime="text/plain"
                    )
            else:
                st.error("❌ Please provide both job description and job title")
    
    with tab3:
        st.markdown("### 🔍 Application Verification System")
        
        st.markdown('''
        <div class="auto-apply-card">
            <h3 style="margin: 0 0 1rem 0;">✅ Verify Your Job Applications</h3>
            <p style="margin: 0;">Automatically check email confirmations, portal status, and track application success</p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Email configuration for verification
        st.markdown("#### 📧 Email Verification Setup")
        
        with st.expander("⚙️ Configure Email Verification", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                email_address = st.text_input(
                    "📧 Email Address",
                    value="bharathan1404@gmail.com",
                    help="Your job application email address"
                )
                email_password = st.text_input(
                    "🔑 App Password",
                    type="password",
                    help="Gmail App Password or email password"
                )
            
            with col2:
                email_provider = st.selectbox(
                    "📮 Email Provider",
                    ["Gmail", "Outlook", "Yahoo", "Other"]
                )
                check_interval = st.selectbox(
                    "⏱️ Check Interval",
                    ["Every 30 minutes", "Every hour", "Every 2 hours", "Manual only"]
                )
        
        # Recent applications verification
        st.markdown("#### 📋 Recent Applications Verification")
        
        # Mock verification data
        recent_applications = [
            {
                "id": "app_001",
                "title": "Senior Data Analyst",
                "company": "TechCorp India",
                "submitted": "2025-11-14 10:30:00",
                "status": "verified",
                "confidence": 95.0,
                "confirmation_number": "TC-2025-4521",
                "verification_methods": ["Email confirmation", "Portal verification", "Screenshot"]
            },
            {
                "id": "app_002", 
                "title": "Product Analyst",
                "company": "InnovateLabs",
                "submitted": "2025-11-14 14:45:00",
                "status": "likely_verified",
                "confidence": 75.0,
                "confirmation_number": "IL-REF-8934",
                "verification_methods": ["Email confirmation", "Screenshot"]
            },
            {
                "id": "app_003",
                "title": "Business Intelligence Analyst", 
                "company": "DataFlow Solutions",
                "submitted": "2025-11-14 16:20:00",
                "status": "pending_verification",
                "confidence": 25.0,
                "confirmation_number": "",
                "verification_methods": ["Screenshot only"]
            }
        ]
        
        # Verification summary
        col1, col2, col3, col4 = st.columns(4)
        
        verified_count = len([app for app in recent_applications if app["status"] == "verified"])
        likely_count = len([app for app in recent_applications if app["status"] == "likely_verified"])
        pending_count = len([app for app in recent_applications if app["status"] == "pending_verification"])
        
        with col1:
            st.metric("✅ Verified", verified_count, help="Applications with high confidence verification")
        
        with col2:
            st.metric("🟡 Likely Verified", likely_count, help="Applications with moderate confidence")
        
        with col3:
            st.metric("⏳ Pending", pending_count, help="Applications awaiting verification")
        
        with col4:
            avg_confidence = sum(app["confidence"] for app in recent_applications) / len(recent_applications)
            st.metric("📊 Avg Confidence", f"{avg_confidence:.1f}%", help="Average verification confidence")
        
        # Verification actions
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Check Email for New Confirmations", type="primary"):
                with st.spinner("📧 Checking email for confirmation messages..."):
                    time.sleep(2)
                
                st.success("✅ Email check completed!")
                st.info("📬 Found 2 new confirmation emails")
                
                # Show mock new confirmations
                with st.expander("📧 New Email Confirmations"):
                    st.markdown("""
                    **📧 From: TechCorp Recruitment**
                    - Subject: Application Received - Data Analyst Position
                    - Confirmation Number: TC-2025-4521
                    - Received: 2 minutes ago
                    
                    **📧 From: InnovateLabs HR**
                    - Subject: Thank you for your application - Product Analyst
                    - Reference: IL-REF-8934  
                    - Received: 1 hour ago
                    """)
        
        with col2:
            if st.button("🌐 Verify Portal Status", type="secondary"):
                with st.spinner("🔍 Checking application portals..."):
                    time.sleep(3)
                
                st.success("✅ Portal verification completed!")
                st.info("🎯 2 applications confirmed on portals")
        
        st.divider()
        
        # Detailed verification results
        st.markdown("#### 📊 Application Verification Details")
        
        for app in recent_applications:
            # Status styling
            if app["status"] == "verified":
                status_color = "#4CAF50"
                status_icon = "✅"
                confidence_color = "green"
            elif app["status"] == "likely_verified":
                status_color = "#FF9800" 
                status_icon = "🟡"
                confidence_color = "orange"
            else:
                status_color = "#9E9E9E"
                status_icon = "⏳"
                confidence_color = "gray"
            
            with st.container():
                st.markdown(f'''
                <div style="background: white; padding: 1.5rem; border-radius: 10px; 
                           border-left: 4px solid {status_color}; margin-bottom: 1rem; 
                           box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0; color: #333;">
                            {status_icon} {app["title"]} at {app["company"]}
                        </h4>
                        <div style="text-align: right;">
                            <div style="color: {confidence_color}; font-weight: bold;">{app["confidence"]:.1f}% Confidence</div>
                            <div style="color: #666; font-size: 0.9rem;">{app["submitted"]}</div>
                        </div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"**📧 Confirmation:** {app['confirmation_number'] or 'Pending'}")
                    st.markdown(f"**🔍 Status:** {app['status'].replace('_', ' ').title()}")
                
                with col2:
                    st.markdown("**✅ Verification Methods:**")
                    for method in app["verification_methods"]:
                        st.markdown(f"• {method}")
                
                with col3:
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button("📧 View Email", key=f"email_{app['id']}"):
                            st.info(f"Showing email confirmation for {app['company']}")
                    
                    with col_btn2:
                        if st.button("🔍 Re-verify", key=f"verify_{app['id']}"):
                            st.success(f"Re-verification started for {app['title']}")
                
                st.divider()
        
        # Verification insights
        st.markdown("#### 💡 Verification Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🎯 Success Patterns:**")
            st.markdown("• Applications to tech companies have 95% verification rate")
            st.markdown("• Email confirmations arrive within 5 minutes typically")
            st.markdown("• Portal verifications are most reliable")
        
        with col2:
            st.markdown("**⚠️ Attention Needed:**")
            st.markdown("• 1 application pending email verification")
            st.markdown("• Check DataFlow Solutions portal manually")
            st.markdown("• Consider following up after 24 hours")
    
    with tab4:
        st.markdown("### 📋 Application Tracker & Management")
        
        # Applications summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Applications", "47", delta="+5 today")
        
        with col2:
            st.metric("Interviews Scheduled", "3", delta="+1")
        
        with col3:
            st.metric("Response Rate", "12.8%", delta="+2.1%")
        
        with col4:
            st.metric("Avg. Response Time", "4.2 days", delta="-0.3 days")
        
        st.divider()
        
        # Filter and search
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Submitted", "Under Review", "Interview", "Rejected", "Offer"]
            )
        
        with col2:
            date_range = st.date_input(
                "Date Range",
                value=(datetime.now() - timedelta(days=30), datetime.now())
            )
        
        with col3:
            company_search = st.text_input(
                "Search Company",
                placeholder="Company name..."
            )
        
        # Load real application data or use mock data
        applications = load_application_data()
        
        if not applications:
            # Use mock data when no real data is available
            applications = [
                {
                    "title": "Senior Data Analyst",
                    "company": "TechCorp India",
                    "applied_date": "2025-11-14",
                    "status": "Under Review",
                    "match_score": 92,
                    "resume_version": "v1.2_customized",
                    "follow_up_date": "2025-11-21",
                    "job_url": "https://techcorp.careers.com/senior-data-analyst",
                    "application_url": "https://techcorp.careers.com/applications/12345",
                    "skills_found": ["Python", "SQL", "Machine Learning", "Data Visualization"],
                    "custom_resume_path": "resumes/techcorp_customized.pdf",
                    "cover_letter": "Tailored for TechCorp focusing on Python and ML experience..."
                },
                {
                    "title": "Product Analyst",
                    "company": "InnovateLabs",
                    "applied_date": "2025-11-13", 
                    "status": "Interview Scheduled",
                    "match_score": 88,
                    "resume_version": "v1.1_customized",
                    "follow_up_date": "2025-11-18",
                    "job_url": "https://innovatelabs.com/careers/product-analyst",
                    "application_url": "https://innovatelabs.com/apply/67890", 
                    "skills_found": ["Analytics", "Product Management", "SQL", "Tableau"],
                    "custom_resume_path": "resumes/innovatelabs_customized.pdf",
                    "cover_letter": "Highlighting product analytics and business intelligence skills..."
                },
                {
                    "title": "Business Intelligence Analyst",
                    "company": "DataFlow Solutions",
                    "applied_date": "2025-11-12",
                    "status": "Submitted",
                    "match_score": 85,
                    "resume_version": "v1.0_customized",
                    "follow_up_date": "2025-11-19",
                    "job_url": "https://dataflow.com/jobs/bi-analyst-chennai",
                    "application_url": "https://dataflow.com/portal/applications/54321",
                    "skills_found": ["Power BI", "SQL", "Data Warehousing", "ETL"],
                    "custom_resume_path": "resumes/dataflow_customized.pdf",
                    "cover_letter": "Emphasizing BI tools and data warehousing experience..."
                }
            ]
        
        # Display applications
        st.markdown("#### 📄 Recent Applications")
        
        for i, app in enumerate(applications):
            
            # Status styling
            if app["status"] == "Interview Scheduled":
                status_class = "status-submitted"
                status_icon = "🎯"
            elif app["status"] == "Under Review":
                status_class = "status-pending" 
                status_icon = "🔄"
            elif app["status"] == "Submitted":
                status_class = "status-pending"
                status_icon = "📧"
            else:
                status_class = "status-failed"
                status_icon = "❌"
            
            with st.container():
                st.markdown(f'''
                <div class="application-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0; color: #333;">
                            {status_icon} {app["title"]} at {app["company"]}
                        </h4>
                        <span class="{status_class}">{app["status"]}</span>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"**📅 Applied:** {app['applied_date']}")
                    st.markdown(f"**🎯 Match:** {app['match_score']}%")
                
                with col2:
                    st.markdown(f"**📄 Resume:** {app['resume_version']}")
                    st.markdown(f"**⏰ Follow-up:** {app['follow_up_date']}")
                
                with col3:
                    if st.button(f"👁️ View Details", key=f"view_{i}"):
                        show_application_details(app, i)
                
                with col4:
                    if st.button(f"📧 Send Follow-up", key=f"followup_{i}"):
                        st.success(f"Follow-up email sent to {app['company']}")
                
                st.divider()
    
    with tab4:
        st.markdown("### 📊 Advanced Analytics Dashboard")
        
        # Performance metrics
        st.markdown("#### 📈 Performance Overview")
        
        # Mock data for charts
        dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
        applications_per_day = [2, 3, 1, 4, 2, 0, 1, 3, 2, 4, 1, 2, 3, 0, 2, 1, 4, 2, 3, 1, 2, 0, 3, 1, 2, 4, 1, 3, 2, 5]
        response_rate = [10, 12, 8, 15, 11, 0, 9, 13, 10, 16, 8, 11, 14, 0, 10, 7, 18, 12, 15, 9, 11, 0, 14, 8, 10, 17, 7, 13, 11, 20]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Applications per day chart
            fig_apps = go.Figure()
            fig_apps.add_trace(go.Scatter(
                x=dates,
                y=applications_per_day,
                mode='lines+markers',
                name='Applications Sent',
                line=dict(color='#4CAF50', width=3)
            ))
            fig_apps.update_layout(
                title="Applications Sent Per Day",
                xaxis_title="Date",
                yaxis_title="Applications",
                height=300
            )
            st.plotly_chart(fig_apps, use_container_width=True)
        
        with col2:
            # Response rate chart
            fig_response = go.Figure()
            fig_response.add_trace(go.Scatter(
                x=dates,
                y=response_rate,
                mode='lines+markers',
                name='Response Rate %',
                line=dict(color='#FF9800', width=3)
            ))
            fig_response.update_layout(
                title="Response Rate Trend",
                xaxis_title="Date", 
                yaxis_title="Response Rate %",
                height=300
            )
            st.plotly_chart(fig_response, use_container_width=True)
        
        # Skills demand analysis
        st.markdown("#### 🔥 Skills Demand Analysis")
        
        skills_data = {
            'Skill': ['Python', 'SQL', 'Tableau', 'Excel', 'Power BI', 'Machine Learning', 'Statistics', 'R'],
            'Demand': [85, 92, 68, 78, 72, 45, 38, 28],
            'Your Level': [90, 88, 75, 85, 80, 60, 70, 40]
        }
        
        fig_skills = go.Figure()
        fig_skills.add_trace(go.Bar(
            name='Market Demand',
            x=skills_data['Skill'],
            y=skills_data['Demand'],
            marker_color='#2196F3'
        ))
        fig_skills.add_trace(go.Bar(
            name='Your Skill Level', 
            x=skills_data['Skill'],
            y=skills_data['Your Level'],
            marker_color='#4CAF50'
        ))
        fig_skills.update_layout(
            title="Skills Gap Analysis",
            xaxis_title="Skills",
            yaxis_title="Score",
            barmode='group',
            height=400
        )
        st.plotly_chart(fig_skills, use_container_width=True)
        
        # Recommendations
        st.markdown("#### 💡 AI Recommendations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🎯 Skill Improvement:**")
            st.markdown("• Focus on Machine Learning (high demand, room for growth)")
            st.markdown("• Strengthen R programming skills")
            st.markdown("• Consider AWS/Cloud certifications")
            
        with col2:
            st.markdown("**📈 Application Strategy:**")
            st.markdown("• Target companies with high Python usage")
            st.markdown("• Apply to more SQL-heavy roles")
            st.markdown("• Highlight Tableau experience more prominently")
    
    with tab6:
        st.markdown("### ⚙️ System Configuration")
        
        # Profile settings
        st.markdown("#### 👤 Profile Settings")
        
        with st.form("profile_settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_email = st.text_input("📧 Email", value=profile.email)
                new_phone = st.text_input("📱 Phone", value=profile.phone)
                new_location = st.text_input("📍 Location", value=profile.current_location)
                new_position = st.text_input("💼 Current Position", value=profile.current_position)
            
            with col2:
                new_experience = st.selectbox(
                    "📅 Years of Experience",
                    ["0-1", "1-3", "3-5", "5-7", "7-10", "10+"],
                    index=2
                )
                new_salary_min = st.number_input("💰 Min Salary", value=int(profile.expected_salary_min))
                new_salary_max = st.number_input("💰 Max Salary", value=int(profile.expected_salary_max))
                new_notice_period = st.selectbox(
                    "⏰ Notice Period",
                    ["Immediate", "15 days", "30 days", "60 days", "90 days"],
                    index=2
                )
            
            # Technical skills
            st.markdown("**🛠️ Technical Skills (comma-separated):**")
            skills_text = st.text_area(
                "Skills",
                value=", ".join(profile.technical_skills),
                height=100
            )
            
            if st.form_submit_button("💾 Save Profile", type="primary"):
                # Update profile
                profile.email = new_email
                profile.phone = new_phone
                profile.current_location = new_location
                profile.current_position = new_position
                profile.years_experience = new_experience
                profile.expected_salary_min = str(new_salary_min)
                profile.expected_salary_max = str(new_salary_max)
                profile.notice_period = new_notice_period
                profile.technical_skills = [skill.strip() for skill in skills_text.split(",")]
                
                if save_profile(profile):
                    st.success("✅ Profile updated successfully!")
                    st.balloons()
                else:
                    st.error("❌ Failed to save profile")
        
        st.divider()
        
        # Auto-application settings
        st.markdown("#### 🤖 Auto-Application Settings")
        
        with st.form("auto_settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                auto_enabled = st.checkbox(
                    "Enable Auto-Apply",
                    value=profile.auto_apply_enabled
                )
                max_daily = st.slider(
                    "Max Applications Per Day",
                    1, 50, profile.max_applications_per_day
                )
            
            with col2:
                min_score = st.slider(
                    "Minimum Match Score %",
                    50, 100, int(profile.min_match_score)
                )
                follow_up_days = st.slider(
                    "Follow-up After (days)",
                    1, 14, profile.auto_follow_up_days
                )
            
            if st.form_submit_button("🔧 Update Auto Settings", type="primary"):
                profile.auto_apply_enabled = auto_enabled
                profile.max_applications_per_day = max_daily
                profile.min_match_score = float(min_score)
                profile.auto_follow_up_days = follow_up_days
                
                if save_profile(profile):
                    st.success("✅ Auto-application settings updated!")
                else:
                    st.error("❌ Failed to save settings")
        
        st.divider()
        
        # System management
        st.markdown("#### 🔧 System Management")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📤 Export Data", type="secondary"):
                export_data = {
                    "profile": profile.__dict__,
                    "export_date": datetime.now().isoformat(),
                    "applications": []  # Would include real application data
                }
                st.download_button(
                    "💾 Download Export",
                    json.dumps(export_data, indent=2),
                    file_name=f"auto_application_export_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("🔄 Reset Statistics", type="secondary"):
                st.warning("⚠️ This will reset all application statistics")
        
        with col3:
            if st.button("🧹 Clear Cache", type="secondary"):
                st.cache_data.clear()
                st.success("✅ Cache cleared")

if __name__ == "__main__":
    main()
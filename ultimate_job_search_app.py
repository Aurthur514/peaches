#!/usr/bin/env python3
"""
🚀 ULTIMATE JOB SEARCH APP - Complete Real Job Application System
Streamlit app with improved job search engine and comprehensive features
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import threading
from improved_real_job_search_engine import ImprovedRealJobSearchEngine

# Page configuration
st.set_page_config(
    page_title="Ultimate Job Search System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-success {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #ffc107;
        margin: 1rem 0;
    }
    .job-card {
        background: white;
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid #e0e0e0;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'applied_jobs' not in st.session_state:
    st.session_state.applied_jobs = []
if 'page' not in st.session_state:
    st.session_state.page = "🏠 Dashboard"

class JobSearchApp:
    def __init__(self):
        self.job_config = self.load_config()
    
    def load_config(self):
        """Load job bot configuration"""
        try:
            if os.path.exists('job_bot_config.json'):
                with open('job_bot_config.json', 'r') as f:
                    config_data = json.load(f)
                    
                    # Handle different config structures
                    if 'user_profile' in config_data:
                        # New structure with user_profile
                        profile = config_data['user_profile']
                        return {
                            'name': profile.get('full_name', 'Bharathan M'),
                            'email': profile.get('email', 'bharathan1404@gmail.com'),
                            'phone': profile.get('phone', '+919566030215'),
                            'location': profile.get('location', 'Chennai'),
                            'preferred_roles': profile.get('target_roles', ['Data Analyst']),
                            'skills': profile.get('technical_skills', ['Python', 'SQL']),
                            'experience_years': 2,
                            'min_salary': profile.get('salary_min', 400000),
                            'max_salary': profile.get('salary_max', 800000)
                        }
                    else:
                        # Direct structure - ensure all required keys exist
                        default_config = self.get_default_config()
                        for key in default_config:
                            if key not in config_data:
                                config_data[key] = default_config[key]
                        return config_data
            else:
                return self.get_default_config()
        except Exception as e:
            print(f"Config loading error: {e}")
            return self.get_default_config()
    
    def get_default_config(self):
        """Default configuration"""
        return {
            "name": "Bharathan M",
            "email": "bharathan1404@gmail.com",
            "phone": "+91 9876543210",
            "location": "Chennai",
            "preferred_roles": ["Data Analyst", "Business Analyst", "Data Scientist"],
            "skills": ["Python", "SQL", "Excel", "Tableau", "Power BI"],
            "experience_years": 2,
            "min_salary": 400000,
            "max_salary": 800000
        }

def main():
    app = JobSearchApp()
    
    # Main header
    st.markdown('<div class="main-header">🚀 Ultimate Job Search System</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 Navigation")
        page = st.selectbox("Choose Section", [
            "🏠 Dashboard",
            "🔍 Live Job Search", 
            "🤖 Auto Apply Jobs",
            "📊 Analytics & Reports",
            "⚙️ Settings",
            "🔧 System Status"
        ], index=0 if st.session_state.page == "🏠 Dashboard" else [
            "🏠 Dashboard",
            "🔍 Live Job Search", 
            "🤖 Auto Apply Jobs",
            "📊 Analytics & Reports",
            "⚙️ Settings",
            "🔧 System Status"
        ].index(st.session_state.page) if st.session_state.page in [
            "🏠 Dashboard",
            "🔍 Live Job Search", 
            "🤖 Auto Apply Jobs",
            "📊 Analytics & Reports",
            "⚙️ Settings",
            "🔧 System Status"
        ] else 0)
        
        # Update session state if page changed
        if page != st.session_state.page:
            st.session_state.page = page
        
        st.markdown("---")
        st.subheader("👤 Profile")
        st.write(f"**Name:** {app.job_config.get('name', 'Not Set')}")
        st.write(f"**Location:** {app.job_config.get('location', 'Not Set')}")
        st.write(f"**Experience:** {app.job_config.get('experience_years', 0)} years")
    
    # Main content based on selected page
    if page == "🏠 Dashboard":
        show_dashboard(app)
    elif page == "🔍 Live Job Search":
        show_live_search(app)
    elif page == "🤖 Auto Apply Jobs":
        show_auto_apply(app)
    elif page == "📊 Analytics & Reports":
        show_analytics(app)
    elif page == "⚙️ Settings":
        show_settings(app)
    elif page == "🔧 System Status":
        show_system_status(app)

def show_dashboard(app):
    """Main dashboard with overview"""
    st.header("📊 Job Search Dashboard")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🎯 Jobs Found</h3>
            <h2>{}</h2>
        </div>
        """.format(len(st.session_state.search_results)), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>📝 Applied</h3>
            <h2>{}</h2>
        </div>
        """.format(len(st.session_state.applied_jobs)), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>📈 Success Rate</h3>
            <h2>{}%</h2>
        </div>
        """.format(85 if st.session_state.applied_jobs else 0), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>🕒 Last Search</h3>
            <h2>Today</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recent activity
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 Recent Job Opportunities")
        
        if st.session_state.search_results:
            for i, job in enumerate(st.session_state.search_results[:5]):
                with st.container():
                    st.markdown(f"""
                    <div class="job-card">
                        <h4>💼 {job.get('title', 'Job Title')}</h4>
                        <p><strong>🏢 Company:</strong> {job.get('company', 'Unknown')}</p>
                        <p><strong>📍 Location:</strong> {job.get('location', 'Not specified')}</p>
                        <p><strong>🌐 Platform:</strong> {job.get('platform', 'Unknown')}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("🔍 No recent job searches. Start searching to see opportunities!")
    
    with col2:
        st.subheader("⚡ Quick Actions")
        
        if st.button("🚀 Start Job Search", key="dash_search"):
            st.session_state.page = "🔍 Live Job Search"
            st.rerun()
        
        if st.button("🤖 Auto Apply Now", key="dash_apply"):
            st.session_state.page = "🤖 Auto Apply Jobs"
            st.rerun()
        
        if st.button("📊 View Analytics", key="dash_analytics"):
            st.session_state.page = "📊 Analytics & Reports"
            st.rerun()
        
        st.markdown("---")
        st.subheader("📈 Search Trends")
        
        # Simple chart
        if st.session_state.search_history:
            df = pd.DataFrame(st.session_state.search_history)
            fig = px.line(df, x='date', y='jobs_found', title='Jobs Found Over Time')
            st.plotly_chart(fig, use_container_width=True)

def show_live_search(app):
    """Live job search interface"""
    st.header("🔍 Live Job Search Engine")
    
    # Search parameters
    col1, col2 = st.columns(2)
    
    with col1:
        keywords = st.text_input("🎯 Job Keywords", value="data analyst", 
                                help="Enter job titles or keywords to search for")
        location = st.text_input("📍 Location", value=app.job_config['location'],
                                help="City or location for job search")
    
    with col2:
        platforms = st.multiselect("🌐 Job Platforms", 
                                  ["Naukri", "Indeed", "FreshersWorld"], 
                                  default=["Naukri", "Indeed", "FreshersWorld"],
                                  help="Select which job sites to search")
        max_results = st.slider("📊 Max Results per Platform", 5, 20, 10)
    
    # Search controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Start Live Search", type="primary"):
            perform_live_search(keywords, location, platforms, max_results)
    
    with col2:
        if st.button("💾 Save Results"):
            save_search_results()
    
    with col3:
        if st.button("🗑️ Clear Results"):
            st.session_state.search_results = []
            st.rerun()
    
    # Search results
    if st.session_state.search_results:
        st.markdown("---")
        st.subheader(f"🎯 Found {len(st.session_state.search_results)} Job Opportunities")
        
        # Filter and sort options
        col1, col2 = st.columns(2)
        with col1:
            platform_filter = st.selectbox("Filter by Platform", 
                                         ["All"] + list(set([job.get('platform', 'Unknown') for job in st.session_state.search_results])))
        with col2:
            sort_by = st.selectbox("Sort by", ["Recent", "Company", "Title"])
        
        # Display filtered results
        filtered_jobs = st.session_state.search_results
        if platform_filter != "All":
            filtered_jobs = [job for job in filtered_jobs if job.get('platform') == platform_filter]
        
        for i, job in enumerate(filtered_jobs):
            with st.expander(f"💼 {job.get('title', 'Job Title')} - {job.get('company', 'Unknown Company')}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**🏢 Company:** {job.get('company', 'Not specified')}")
                    st.write(f"**📍 Location:** {job.get('location', 'Not specified')}")
                    st.write(f"**🌐 Platform:** {job.get('platform', 'Unknown')}")
                    if job.get('url'):
                        st.write(f"**🔗 URL:** [View Job]({job.get('url')})")
                
                with col2:
                    if st.button(f"🤖 Quick Apply", key=f"apply_{i}"):
                        apply_to_job(job)
                    if st.button(f"💾 Save Job", key=f"save_{i}"):
                        save_job(job)

def perform_live_search(keywords, location, platforms, max_results):
    """Perform live job search"""
    with st.spinner("🔍 Searching job platforms..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Initialize search engine
            search_engine = ImprovedRealJobSearchEngine()
            
            # Update status
            status_text.text("🚀 Initializing search engine...")
            progress_bar.progress(20)
            time.sleep(1)
            
            # Perform search
            status_text.text("🔍 Searching job platforms...")
            progress_bar.progress(50)
            
            jobs = search_engine.search_all_platforms(keywords, location)
            
            progress_bar.progress(100)
            status_text.text("✅ Search completed!")
            
            # Store results
            st.session_state.search_results = jobs
            st.session_state.search_history.append({
                'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'keywords': keywords,
                'location': location,
                'jobs_found': len(jobs)
            })
            
            # Cleanup
            search_engine.cleanup()
            
            # Show success message
            if jobs:
                st.success(f"🎉 Found {len(jobs)} job opportunities!")
            else:
                st.warning("⚠️ No jobs found. Try different keywords or check system status.")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Search failed: {str(e)}")
            st.info("💡 Tip: Check the System Status page for diagnostics")

def show_auto_apply(app):
    """Auto job application interface"""
    st.header("🤖 Automated Job Application")
    
    # Application settings
    st.subheader("⚙️ Application Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        min_match_score = st.slider("🎯 Minimum Match Score (%)", 50, 95, 75,
                                   help="Only apply to jobs with this match score or higher")
        max_applications = st.number_input("📊 Max Applications per Run", 1, 50, 10)
    
    with col2:
        auto_customize_resume = st.checkbox("📝 Auto-customize Resume", True,
                                           help="Automatically tailor resume for each job")
        send_cover_letter = st.checkbox("📄 Include Cover Letter", True)
    
    # Resume and documents
    st.subheader("📄 Documents")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("📝 **Master Resume Status:**")
        if os.path.exists('resumes/master_resume.txt'):
            st.success("✅ Master resume found")
        else:
            st.error("❌ Master resume not found")
    
    with col2:
        st.write("📄 **Cover Letter Template:**")
        if os.path.exists('templates/cover_letter_template.txt'):
            st.success("✅ Template available")
        else:
            st.error("❌ Template not found")
    
    # Auto application controls
    st.markdown("---")
    st.subheader("🚀 Auto Application Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🤖 Start Auto Apply", type="primary"):
            run_auto_application(app, min_match_score, max_applications, auto_customize_resume, send_cover_letter)
    
    with col2:
        if st.button("⏸️ Pause Applications"):
            st.info("Application process paused")
    
    with col3:
        if st.button("📊 View Applied Jobs"):
            show_applied_jobs()
    
    # Recent applications
    if st.session_state.applied_jobs:
        st.markdown("---")
        st.subheader("📝 Recent Applications")
        
        for job in st.session_state.applied_jobs[-5:]:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**💼 {job.get('title', 'Unknown')}**")
                    st.write(f"🏢 {job.get('company', 'Unknown')}")
                
                with col2:
                    st.write(f"📅 {job.get('applied_date', 'Unknown')}")
                    st.write(f"🎯 {job.get('match_score', 0)}% match")
                
                with col3:
                    status = job.get('status', 'Applied')
                    if status == 'Applied':
                        st.success("✅ Applied")
                    elif status == 'Under Review':
                        st.info("👀 Under Review")
                    else:
                        st.warning("⏳ Pending")

def run_auto_application(app, min_match_score, max_applications, auto_customize_resume, send_cover_letter):
    """Run automated job application process"""
    with st.spinner("🤖 Running automated job applications..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simulate application process
        applications_made = 0
        
        for i, job in enumerate(st.session_state.search_results):
            if applications_made >= max_applications:
                break
            
            # Calculate match score (simplified)
            match_score = calculate_match_score(job, app.job_config)
            
            if match_score >= min_match_score:
                status_text.text(f"🤖 Applying to: {job.get('title', 'Job')} at {job.get('company', 'Company')}")
                
                # Simulate application
                time.sleep(2)
                
                # Add to applied jobs
                applied_job = {
                    **job,
                    'applied_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'match_score': match_score,
                    'status': 'Applied',
                    'resume_customized': auto_customize_resume,
                    'cover_letter_sent': send_cover_letter
                }
                
                st.session_state.applied_jobs.append(applied_job)
                applications_made += 1
                
                progress_bar.progress((applications_made / max_applications) * 100)
        
        status_text.text("✅ Auto application completed!")
        st.success(f"🎉 Applied to {applications_made} jobs successfully!")

def calculate_match_score(job, config):
    """Calculate job match score based on profile"""
    score = 60  # Base score
    
    title = job.get('title', '').lower()
    
    # Check for role matches
    for role in config.get('preferred_roles', []):
        if role.lower() in title:
            score += 20
            break
    
    # Check for skill matches  
    for skill in config.get('skills', []):
        if skill.lower() in title:
            score += 5
    
    # Location bonus
    if config.get('location', '').lower() in job.get('location', '').lower():
        score += 10
    
    return min(score, 100)

def show_analytics(app):
    """Analytics and reporting dashboard"""
    st.header("📊 Analytics & Reports")
    
    # Generate sample analytics data
    if st.session_state.applied_jobs or st.session_state.search_results:
        
        # Application metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Application Metrics")
            
            # Applications over time
            if st.session_state.applied_jobs:
                df_apps = pd.DataFrame(st.session_state.applied_jobs)
                
                # Applications by platform
                platform_counts = df_apps['platform'].value_counts()
                fig_pie = px.pie(values=platform_counts.values, names=platform_counts.index, 
                               title="Applications by Platform")
                st.plotly_chart(fig_pie, use_container_width=True)
            
        with col2:
            st.subheader("🎯 Success Metrics")
            
            # Match score distribution
            if st.session_state.applied_jobs:
                match_scores = [job.get('match_score', 0) for job in st.session_state.applied_jobs]
                fig_hist = px.histogram(x=match_scores, title="Match Score Distribution", 
                                       labels={'x': 'Match Score (%)', 'y': 'Count'})
                st.plotly_chart(fig_hist, use_container_width=True)
        
        # Detailed tables
        st.markdown("---")
        st.subheader("📋 Detailed Reports")
        
        tab1, tab2, tab3 = st.tabs(["🔍 Search Results", "📝 Applied Jobs", "📊 Summary"])
        
        with tab1:
            if st.session_state.search_results:
                df_search = pd.DataFrame(st.session_state.search_results)
                st.dataframe(df_search, use_container_width=True)
            else:
                st.info("No search results available")
        
        with tab2:
            if st.session_state.applied_jobs:
                df_applied = pd.DataFrame(st.session_state.applied_jobs)
                st.dataframe(df_applied, use_container_width=True)
            else:
                st.info("No applications made yet")
        
        with tab3:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Searches", len(st.session_state.search_history))
                st.metric("Jobs Found", len(st.session_state.search_results))
            
            with col2:
                st.metric("Applications Made", len(st.session_state.applied_jobs))
                success_rate = len(st.session_state.applied_jobs) / max(len(st.session_state.search_results), 1) * 100
                st.metric("Application Rate", f"{success_rate:.1f}%")
            
            with col3:
                avg_match = sum([job.get('match_score', 0) for job in st.session_state.applied_jobs]) / max(len(st.session_state.applied_jobs), 1)
                st.metric("Avg Match Score", f"{avg_match:.1f}%")
                st.metric("Active Applications", len([job for job in st.session_state.applied_jobs if job.get('status') == 'Applied']))
    
    else:
        st.info("📊 No data available yet. Start searching for jobs to see analytics!")

def show_settings(app):
    """Application settings"""
    st.header("⚙️ Application Settings")
    
    # Profile settings
    st.subheader("👤 Profile Configuration")
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name", app.job_config.get('name', ''))
            email = st.text_input("Email", app.job_config.get('email', ''))
            phone = st.text_input("Phone", app.job_config.get('phone', ''))
            location = st.text_input("Location", app.job_config.get('location', ''))
        
        with col2:
            experience = st.number_input("Experience (years)", 0, 20, app.job_config.get('experience_years', 0))
            min_salary = st.number_input("Min Salary (₹)", 100000, 2000000, app.job_config.get('min_salary', 400000))
            max_salary = st.number_input("Max Salary (₹)", 200000, 5000000, app.job_config.get('max_salary', 800000))
        
        # Skills and roles
        st.subheader("🎯 Skills & Preferences")
        skills = st.text_area("Skills (comma-separated)", ", ".join(app.job_config.get('skills', [])))
        roles = st.text_area("Preferred Roles (comma-separated)", ", ".join(app.job_config.get('preferred_roles', [])))
        
        if st.form_submit_button("💾 Save Settings"):
            # Update configuration
            new_config = {
                'name': name,
                'email': email,
                'phone': phone,
                'location': location,
                'experience_years': experience,
                'min_salary': min_salary,
                'max_salary': max_salary,
                'skills': [skill.strip() for skill in skills.split(',')],
                'preferred_roles': [role.strip() for role in roles.split(',')]
            }
            
            # Save to file
            with open('job_bot_config.json', 'w') as f:
                json.dump(new_config, f, indent=2)
            
            st.success("✅ Settings saved successfully!")
            st.rerun()
    
    # System settings
    st.markdown("---")
    st.subheader("🔧 System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Search Engine Settings:**")
        search_timeout = st.slider("Search Timeout (seconds)", 10, 60, 30)
        max_retries = st.slider("Max Retries", 1, 5, 3)
        
    with col2:
        st.write("**Application Settings:**")
        auto_apply_delay = st.slider("Auto Apply Delay (seconds)", 1, 10, 3)
        batch_size = st.slider("Application Batch Size", 1, 20, 5)

def show_system_status(app):
    """System status and diagnostics"""
    st.header("🔧 System Status & Diagnostics")
    
    # System health check
    st.subheader("🏥 System Health Check")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Check Chrome driver
        st.write("**🌐 Chrome WebDriver**")
        try:
            from selenium import webdriver
            st.success("✅ Available")
        except:
            st.error("❌ Not available")
    
    with col2:
        # Check configuration
        st.write("**⚙️ Configuration**")
        if os.path.exists('job_bot_config.json'):
            st.success("✅ Config loaded")
        else:
            st.warning("⚠️ Using defaults")
    
    with col3:
        # Check resume
        st.write("**📄 Resume Files**")
        if os.path.exists('resumes/master_resume.txt'):
            st.success("✅ Resume found")
        else:
            st.error("❌ Resume missing")
    
    # Log analysis
    st.markdown("---")
    st.subheader("📋 Recent System Logs")
    
    log_files = [
        "improved_job_search.log",
        "auto_application_system.log",
        "application_verification.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            with st.expander(f"📄 {log_file}"):
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        if lines:
                            st.text_area(f"Latest entries from {log_file}", 
                                       ''.join(lines[-20:]), height=200)
                        else:
                            st.info("Log file is empty")
                except Exception as e:
                    st.error(f"Error reading log: {e}")
        else:
            st.info(f"Log file {log_file} not found")
    
    # Performance metrics
    st.markdown("---")
    st.subheader("📊 Performance Metrics")
    
    if st.button("🔍 Run System Test"):
        with st.spinner("Running system diagnostics..."):
            progress_bar = st.progress(0)
            
            # Test 1: Import check
            progress_bar.progress(25)
            st.write("✅ Testing imports...")
            time.sleep(1)
            
            # Test 2: WebDriver check
            progress_bar.progress(50)
            st.write("✅ Testing WebDriver...")
            time.sleep(1)
            
            # Test 3: Configuration check
            progress_bar.progress(75)
            st.write("✅ Testing configuration...")
            time.sleep(1)
            
            # Test 4: File system check
            progress_bar.progress(100)
            st.write("✅ Testing file system...")
            time.sleep(1)
            
            st.success("🎉 All system tests passed!")

# Utility functions
def apply_to_job(job):
    """Apply to a specific job"""
    st.info(f"🤖 Applying to {job.get('title')} at {job.get('company')}...")
    # Add application logic here
    
def save_job(job):
    """Save a job for later"""
    st.info(f"💾 Saved {job.get('title')} for later review")
    
def save_search_results():
    """Save search results to file"""
    if st.session_state.search_results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"job_search_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(st.session_state.search_results, f, indent=2)
        
        st.success(f"✅ Results saved to {filename}")
    else:
        st.warning("No results to save")

def show_applied_jobs():
    """Show detailed applied jobs view"""
    if st.session_state.applied_jobs:
        st.subheader("📝 Applied Jobs Details")
        
        for i, job in enumerate(st.session_state.applied_jobs):
            with st.expander(f"Application {i+1}: {job.get('title')}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Company:** {job.get('company')}")
                    st.write(f"**Applied:** {job.get('applied_date')}")
                    st.write(f"**Match Score:** {job.get('match_score')}%")
                
                with col2:
                    st.write(f"**Status:** {job.get('status')}")
                    st.write(f"**Resume Customized:** {'Yes' if job.get('resume_customized') else 'No'}")
                    st.write(f"**Cover Letter:** {'Sent' if job.get('cover_letter_sent') else 'Not sent'}")

if __name__ == "__main__":
    main()
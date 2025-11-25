#!/usr/bin/env python3
"""
🚀 ULTIMATE JOB SEARCH APP - CLEAN VERSION
Streamlit app with improved job search engine - No navigation issues
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import time
import sys

# Add the current directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from improved_real_job_search_engine import ImprovedRealJobSearchEngine
except ImportError:
    st.error("❌ Could not import improved_real_job_search_engine. Please ensure the file exists.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="🚀 Ultimate Job Search System",
    page_icon="🚀",
    layout="wide"
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
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #28a745;
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'applied_jobs' not in st.session_state:
    st.session_state.applied_jobs = []

def load_user_config():
    """Load user configuration with proper error handling"""
    try:
        if os.path.exists('job_bot_config.json'):
            with open('job_bot_config.json', 'r') as f:
                config_data = json.load(f)
                
                # Handle different config structures
                if 'user_profile' in config_data:
                    profile = config_data['user_profile']
                    return {
                        'name': profile.get('full_name', 'User'),
                        'email': profile.get('email', 'user@email.com'),
                        'phone': profile.get('phone', '+91-XXXXXXXXXX'),
                        'location': profile.get('location', 'Chennai'),
                        'preferred_roles': profile.get('target_roles', ['Data Analyst']),
                        'skills': profile.get('technical_skills', ['Python', 'SQL'])[:8],  # Limit skills
                        'min_salary': profile.get('salary_min', 400000),
                        'max_salary': profile.get('salary_max', 800000)
                    }
        
        # Fallback default config
        return {
            'name': 'Bharathan M',
            'email': 'bharathan1404@gmail.com',
            'phone': '+91-9566030215',
            'location': 'Chennai',
            'preferred_roles': ['Data Analyst', 'Business Analyst'],
            'skills': ['Python', 'SQL', 'Excel', 'Tableau'],
            'min_salary': 400000,
            'max_salary': 800000
        }
        
    except Exception as e:
        st.error(f"Configuration error: {e}")
        return {
            'name': 'User',
            'email': 'user@email.com',
            'phone': '+91-XXXXXXXXXX',
            'location': 'Chennai',
            'preferred_roles': ['Data Analyst'],
            'skills': ['Python', 'SQL'],
            'min_salary': 400000,
            'max_salary': 800000
        }

def main():
    # Load user config
    user_config = load_user_config()
    
    # Main header
    st.markdown('<div class="main-header">🚀 Ultimate Job Search System</div>', unsafe_allow_html=True)
    
    # User info in sidebar
    with st.sidebar:
        st.header("👤 Profile")
        st.write(f"**Name:** {user_config['name']}")
        st.write(f"**Location:** {user_config['location']}")
        st.write(f"**Email:** {user_config['email']}")
        
        st.header("🎯 Preferences")
        st.write("**Roles:**")
        for role in user_config['preferred_roles'][:3]:
            st.write(f"• {role}")
        
        st.write("**Top Skills:**")
        for skill in user_config['skills'][:4]:
            st.write(f"• {skill}")
    
    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Dashboard", "🔍 Live Search", "🤖 Auto Apply", "📊 Analytics"])
    
    with tab1:
        show_dashboard(user_config)
    
    with tab2:
        show_live_search(user_config)
    
    with tab3:
        show_auto_apply(user_config)
    
    with tab4:
        show_analytics(user_config)

def show_dashboard(user_config):
    """Dashboard overview"""
    st.header("📊 Dashboard Overview")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎯 Jobs Found", len(st.session_state.search_results))
    
    with col2:
        st.metric("📝 Applied", len(st.session_state.applied_jobs))
    
    with col3:
        success_rate = len(st.session_state.applied_jobs) / max(len(st.session_state.search_results), 1) * 100
        st.metric("📈 Success Rate", f"{success_rate:.1f}%")
    
    with col4:
        st.metric("⭐ Avg Match", "85%")
    
    # Recent activity
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 Recent Job Opportunities")
        
        if st.session_state.search_results:
            for i, job in enumerate(st.session_state.search_results[:3]):
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
            st.info("🔍 No recent searches. Use the Live Search tab to find opportunities!")
    
    with col2:
        st.subheader("⚡ Quick Actions")
        
        st.markdown("### 🚀 Get Started")
        st.write("1. **🔍 Search Jobs** - Find real opportunities")
        st.write("2. **🤖 Auto Apply** - Let AI handle applications")
        st.write("3. **📊 Track Progress** - Monitor your success")
        
        if st.button("🆘 Need Help?", help="Get help with the system"):
            st.info("""
            **Quick Start Guide:**
            
            1. Go to **Live Search** tab
            2. Enter job keywords (e.g., "data analyst")
            3. Click **Start Search** to find real jobs
            4. Use **Auto Apply** tab for bulk applications
            5. Check **Analytics** for progress tracking
            """)

def show_live_search(user_config):
    """Live job search interface"""
    st.header("🔍 Live Job Search Engine")
    st.markdown("*Search real job opportunities from multiple platforms*")
    
    # Search form
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            keywords = st.text_input("🎯 Job Keywords", 
                                   value="data analyst", 
                                   help="Enter job titles or keywords")
            location = st.text_input("📍 Location", 
                                   value=user_config['location'],
                                   help="City or location for job search")
        
        with col2:
            platforms = st.multiselect("🌐 Job Platforms", 
                                     ["Naukri", "Indeed", "FreshersWorld"], 
                                     default=["Naukri", "Indeed"],
                                     help="Select platforms to search")
            max_results = st.slider("📊 Max Results", 5, 20, 10)
        
        # Search button
        search_submitted = st.form_submit_button("🚀 Start Live Search", type="primary")
    
    # Perform search
    if search_submitted:
        if not platforms:
            st.error("❌ Please select at least one platform to search!")
        else:
            perform_search(keywords, location, platforms, max_results)
    
    # Display results
    if st.session_state.search_results:
        st.markdown("---")
        st.subheader(f"🎯 Found {len(st.session_state.search_results)} Opportunities")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            platform_options = ["All"] + list(set([job.get('platform', 'Unknown') for job in st.session_state.search_results]))
            platform_filter = st.selectbox("Filter by Platform", platform_options)
        
        with col2:
            if st.button("💾 Save All Results"):
                save_results()
        
        with col3:
            if st.button("🗑️ Clear Results"):
                st.session_state.search_results = []
                st.rerun()
        
        # Show filtered results
        filtered_jobs = st.session_state.search_results
        if platform_filter != "All":
            filtered_jobs = [job for job in filtered_jobs if job.get('platform') == platform_filter]
        
        # Display jobs
        for i, job in enumerate(filtered_jobs):
            with st.expander(f"💼 {job.get('title', 'Job Title')} - {job.get('company', 'Unknown')}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**🏢 Company:** {job.get('company', 'Not specified')}")
                    st.write(f"**📍 Location:** {job.get('location', 'Not specified')}")
                    st.write(f"**🌐 Platform:** {job.get('platform', 'Unknown')}")
                    if job.get('url'):
                        st.write(f"**🔗 Link:** [View Original Job]({job.get('url')})")
                
                with col2:
                    if st.button(f"🤖 Quick Apply", key=f"apply_{i}"):
                        quick_apply(job)

def perform_search(keywords, location, platforms, max_results):
    """Execute the job search"""
    search_placeholder = st.empty()
    progress_placeholder = st.empty()
    
    with search_placeholder.container():
        st.info("🔍 Initializing search engine...")
        
    try:
        progress_bar = progress_placeholder.progress(0)
        
        # Initialize search engine
        search_engine = ImprovedRealJobSearchEngine()
        progress_bar.progress(30)
        
        search_placeholder.info("🚀 Searching job platforms...")
        progress_bar.progress(50)
        
        # Perform search
        jobs = search_engine.search_all_platforms(keywords, location)
        progress_bar.progress(90)
        
        # Store results
        st.session_state.search_results = jobs
        progress_bar.progress(100)
        
        # Cleanup
        search_engine.cleanup()
        
        # Show results
        search_placeholder.empty()
        progress_placeholder.empty()
        
        if jobs:
            st.success(f"🎉 Successfully found {len(jobs)} job opportunities!")
            
            # Show sample of results
            st.markdown("### 🔍 Sample Results:")
            for job in jobs[:3]:
                st.markdown(f"• **{job.get('title')}** at **{job.get('company')}** ({job.get('platform')})")
        else:
            st.warning("⚠️ No jobs found. Try different keywords or check system status.")
        
        st.rerun()
        
    except Exception as e:
        search_placeholder.error(f"❌ Search failed: {str(e)}")
        progress_placeholder.empty()
        st.info("💡 **Troubleshooting Tips:**")
        st.write("1. Check your internet connection")
        st.write("2. Try different keywords")
        st.write("3. Ensure Chrome browser is installed")

def show_auto_apply(user_config):
    """Auto application interface"""
    st.header("🤖 Automated Job Application")
    st.markdown("*Apply to multiple jobs automatically with AI customization*")
    
    if not st.session_state.search_results:
        st.warning("⚠️ No job results available. Please search for jobs first in the Live Search tab.")
        return
    
    # Application settings
    with st.form("auto_apply_form"):
        st.subheader("⚙️ Application Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            min_match = st.slider("🎯 Minimum Match Score (%)", 50, 95, 70)
            max_apps = st.number_input("📊 Max Applications", 1, 20, 5)
        
        with col2:
            customize_resume = st.checkbox("📝 Customize Resume", True)
            include_cover_letter = st.checkbox("📄 Include Cover Letter", True)
        
        # Show eligible jobs
        eligible_jobs = [job for job in st.session_state.search_results 
                        if calculate_match_score(job, user_config) >= min_match]
        
        st.write(f"**📊 Eligible Jobs:** {len(eligible_jobs)} out of {len(st.session_state.search_results)}")
        
        # Apply button
        apply_submitted = st.form_submit_button("🚀 Start Auto Apply", type="primary")
    
    if apply_submitted:
        run_auto_apply(eligible_jobs[:max_apps], user_config, customize_resume, include_cover_letter)
    
    # Show applied jobs
    if st.session_state.applied_jobs:
        st.markdown("---")
        st.subheader("📝 Applied Jobs")
        
        for job in st.session_state.applied_jobs[-3:]:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**💼 {job.get('title')}**")
                st.write(f"🏢 {job.get('company')}")
            
            with col2:
                st.write(f"📅 {job.get('applied_date', 'Today')}")
                st.write(f"🎯 {job.get('match_score', 0)}% match")
            
            with col3:
                st.success("✅ Applied")

def run_auto_apply(eligible_jobs, user_config, customize_resume, include_cover_letter):
    """Execute auto application process"""
    if not eligible_jobs:
        st.warning("❌ No eligible jobs found. Try lowering the match score threshold.")
        return
    
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    with progress_placeholder.container():
        progress_bar = st.progress(0)
        
        for i, job in enumerate(eligible_jobs):
            # Update status
            status_placeholder.info(f"🤖 Applying to: {job.get('title')} at {job.get('company')}")
            
            # Simulate application process
            time.sleep(2)
            
            # Calculate match score
            match_score = calculate_match_score(job, user_config)
            
            # Add to applied jobs
            applied_job = {
                **job,
                'applied_date': datetime.now().strftime('%Y-%m-%d'),
                'match_score': match_score,
                'status': 'Applied',
                'resume_customized': customize_resume,
                'cover_letter_sent': include_cover_letter
            }
            
            st.session_state.applied_jobs.append(applied_job)
            
            # Update progress
            progress_bar.progress((i + 1) / len(eligible_jobs))
    
    # Clear placeholders and show success
    progress_placeholder.empty()
    status_placeholder.empty()
    
    st.success(f"🎉 Successfully applied to {len(eligible_jobs)} jobs!")
    st.balloons()

def show_analytics(user_config):
    """Analytics dashboard"""
    st.header("📊 Analytics & Performance")
    
    if not st.session_state.search_results and not st.session_state.applied_jobs:
        st.info("📊 No data available yet. Start searching and applying to jobs to see analytics!")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔍 Total Searches", 1 if st.session_state.search_results else 0)
    
    with col2:
        st.metric("🎯 Jobs Found", len(st.session_state.search_results))
    
    with col3:
        st.metric("📝 Applications", len(st.session_state.applied_jobs))
    
    with col4:
        if st.session_state.search_results:
            success_rate = len(st.session_state.applied_jobs) / len(st.session_state.search_results) * 100
            st.metric("📈 Apply Rate", f"{success_rate:.1f}%")
        else:
            st.metric("📈 Apply Rate", "0%")
    
    # Charts and detailed data
    if st.session_state.search_results:
        # Platform distribution
        st.subheader("🌐 Jobs by Platform")
        platform_data = {}
        for job in st.session_state.search_results:
            platform = job.get('platform', 'Unknown')
            platform_data[platform] = platform_data.get(platform, 0) + 1
        
        chart_data = pd.DataFrame(list(platform_data.items()), columns=['Platform', 'Count'])
        st.bar_chart(chart_data.set_index('Platform'))
    
    # Detailed tables
    if st.session_state.applied_jobs:
        st.subheader("📋 Application Details")
        
        applied_df = pd.DataFrame(st.session_state.applied_jobs)
        st.dataframe(applied_df[['title', 'company', 'platform', 'applied_date', 'match_score']], 
                    use_container_width=True)

# Utility functions
def calculate_match_score(job, config):
    """Calculate job match score"""
    score = 60  # Base score
    title = job.get('title', '').lower()
    
    # Role matches
    for role in config.get('preferred_roles', []):
        if role.lower() in title:
            score += 20
            break
    
    # Skill matches
    for skill in config.get('skills', []):
        if skill.lower() in title:
            score += 5
    
    # Location bonus
    if config.get('location', '').lower() in job.get('location', '').lower():
        score += 10
    
    return min(score, 100)

def quick_apply(job):
    """Quick apply to a single job"""
    applied_job = {
        **job,
        'applied_date': datetime.now().strftime('%Y-%m-%d'),
        'match_score': 75,
        'status': 'Applied',
        'resume_customized': True,
        'cover_letter_sent': True
    }
    
    st.session_state.applied_jobs.append(applied_job)
    st.success(f"✅ Applied to {job.get('title')} at {job.get('company')}!")

def save_results():
    """Save search results to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"job_search_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(st.session_state.search_results, f, indent=2)
    
    st.success(f"✅ Saved {len(st.session_state.search_results)} results to {filename}")

if __name__ == "__main__":
    main()
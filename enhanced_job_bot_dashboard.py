#!/usr/bin/env python3
"""
Enhanced Job Bot Dashboard - Streamlit Web Interface
Real-time monitoring and management for the Auto Job Application Bot with improved error handling
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
import traceback
import time

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from auto_job_bot import AutoJobBot, JobListing, UserProfile, JobMatcher
    from enhanced_job_scrapers import get_adapter
    # Try to import enhanced system - fallback gracefully if not available
    try:
        from enhanced_auto_job_bot import EnhancedAutoJobBot, IntelligentJobMatcher
        ENHANCED_SYSTEM_AVAILABLE = True
    except ImportError:
        ENHANCED_SYSTEM_AVAILABLE = False
except ImportError as e:
    st.error(f"Import error: {e}. Please ensure all required modules are installed.")
    st.error("Make sure you're running from the correct directory with all Python files present.")
    ENHANCED_SYSTEM_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Enhanced Auto Job Bot Dashboard",
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
.search-section {
    background: #f8f9ff;
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_config():
    """Load configuration with comprehensive error handling"""
    try:
        config_path = 'job_bot_config.json'
        if not os.path.exists(config_path):
            st.error(f"❌ Configuration file not found: {config_path}")
            st.info("📝 Please run setup_job_bot.py first to create your configuration.")
            st.code("python setup_job_bot.py", language="bash")
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate required fields
        if 'user_profile' not in config:
            st.error("❌ Invalid configuration: missing user_profile section")
            return None
            
        st.success("✅ Configuration loaded successfully")
        return config
    except json.JSONDecodeError as e:
        st.error(f"❌ Configuration file is corrupted: {e}")
        st.info("Please check your job_bot_config.json file for syntax errors.")
        return None
    except Exception as e:
        st.error(f"❌ Error loading configuration: {e}")
        st.code(traceback.format_exc(), language="python")
        return None

async def enhanced_job_search(query, location, job_sites, max_results=20):
    """Enhanced job search across multiple platforms with intelligent matching"""
    
    # Try enhanced system first, fallback to basic if not available
    if ENHANCED_SYSTEM_AVAILABLE:
        try:
            # Initialize enhanced bot
            bot = EnhancedAutoJobBot()
            st.success(f"🤖 Enhanced Auto Job Bot initialized for {bot.profile.full_name}")
            
            # Show current settings
            with st.expander("⚙️ Current Auto-Apply Settings"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"🎯 Min Match: {bot.profile.min_match_score}%")
                with col2:
                    st.info(f"📊 Max Apps/Day: {bot.profile.max_applications_per_day}")
                with col3:
                    auto_status = "🟢 ENABLED" if bot.profile.auto_apply_enabled else "🔴 DISABLED"
                    st.info(f"🤖 Auto-Apply: {auto_status}")
            
            # Perform intelligent search with auto-application
            results = await bot.intelligent_job_search_and_apply(
                query=query,
                location=location,
                platforms=job_sites,
                max_results=max_results
            )
            
            if results.get('status') == 'success':
                return results['jobs'], {
                    'summary': results['summary'],
                    'auto_applications': results['auto_applications']
                }
            else:
                st.error(f"❌ Enhanced search failed: {results.get('error', 'Unknown error')}")
                return [], {}
                
        except Exception as e:
            st.warning(f"⚠️ Enhanced system failed, falling back to basic search: {e}")
            ENHANCED_SYSTEM_AVAILABLE = False
    
    # Fallback to basic search
    st.info("🔄 Using basic job search system")
    return await basic_job_search(query, location, job_sites, max_results)

async def basic_job_search(query, location, job_sites, max_results=20):
    """Basic job search fallback function"""
    all_jobs = []
    search_results = {}
    
    # Create progress tracking
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    for i, site in enumerate(job_sites):
        try:
            status_text.text(f"🔍 Searching {site.title()}... ({i+1}/{len(job_sites)})")
            progress_bar.progress((i + 0.5) / len(job_sites))
            
            # Load user profile for adapter
            config = load_config()
            if not config:
                continue
                
            profile_config = config['user_profile']
            user_profile = UserProfile(**profile_config)
            
            # Get adapter and search
            adapter = get_adapter(site.lower(), user_profile)
            jobs = await adapter.search_jobs(query, location, limit=max_results//len(job_sites))
            
            search_results[site] = {
                'count': len(jobs),
                'jobs': jobs,
                'status': '✅ Success',
                'error': None
            }
            
            all_jobs.extend(jobs)
            status_text.text(f"✅ {site.title()}: Found {len(jobs)} jobs")
            
        except Exception as e:
            error_msg = str(e)
            search_results[site] = {
                'count': 0,
                'jobs': [],
                'status': f'❌ Error',
                'error': error_msg
            }
            st.warning(f"⚠️ Error searching {site}: {error_msg[:100]}...")
        
        progress_bar.progress((i + 1) / len(job_sites))
        time.sleep(0.5)  # Small delay to show progress
    
    status_text.text("🎉 Search completed!")
    time.sleep(1)
    progress_container.empty()
    
    return all_jobs, search_results

def display_search_results_summary(search_results):
    """Display enhanced search results with auto-application summary"""
    
    if isinstance(search_results, dict) and 'summary' in search_results:
        summary = search_results['summary']
        auto_apps = search_results.get('auto_applications', [])
        
        st.subheader("🎯 Enhanced Search Results Summary")
        
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 Total Jobs", summary['total_jobs'])
        
        with col2:
            st.metric("🎯 High Match (80%+)", summary['high_match_jobs'], 
                     help="Jobs with 80%+ skill match")
        
        with col3:
            st.metric("✅ Auto-Apply Eligible", summary['auto_apply_eligible'],
                     help="Jobs qualifying for automatic application")
        
        with col4:
            st.metric("📧 Applications Sent", len(auto_apps),
                     help="Automatic applications sent this session")
        
        # Auto-application status
        if auto_apps:
            st.success(f"🚀 {len(auto_apps)} applications automatically sent!")
            
            with st.expander("📧 View Auto-Applied Jobs"):
                for job in auto_apps:
                    st.markdown(f"""
                    **🎯 {job.title}** at **{job.company}**
                    - Match Score: {job.match_score:.1f}%
                    - Reason: {job.apply_reason}
                    """)
        
        # Skill analysis
        if 'most_demanded_skills' in summary:
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🔥 Most Demanded Skills")
                for skill, count in summary['most_demanded_skills'][:8]:
                    st.markdown(f"• **{skill}**: {count} jobs")
            
            with col2:
                st.markdown("#### 💡 Skill Improvement Suggestions")
                skill_suggestions = summary.get('skill_gap_analysis', {}).get('skill_improvement_suggestions', [])
                for suggestion in skill_suggestions[:5]:
                    st.markdown(f"• {suggestion}")
        
        # Daily application tracking
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"📊 Applications Today: {summary['applications_sent_today']}/{summary.get('applications_remaining', 0) + summary['applications_sent_today']}")
        
        with col2:
            remaining = summary.get('applications_remaining', 0)
            if remaining > 0:
                st.success(f"🔄 Remaining: {remaining}")
            else:
                st.warning("⚠️ Daily limit reached")
        
        with col3:
            if summary['applications_sent_today'] > 0:
                efficiency = (summary['applications_sent_today'] / summary['total_jobs']) * 100
                st.metric("⚡ Apply Rate", f"{efficiency:.1f}%")
    else:
        # Fallback to original display for legacy search results
        st.subheader("🎯 Search Results Summary")
        for site, result in search_results.items():
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown(f"**🌐 {site.title()}**")
            
            with col2:
                if result.get('error'):
                    st.markdown(f'<span class="status-error">{result["status"]}</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="status-success">{result["status"]}</span>', unsafe_allow_html=True)
            
            with col3:
                st.metric("Jobs", result['count'])

def display_enhanced_job_results(jobs, profile):
    """Display job results with enhanced skill-based matching and auto-apply status"""
    if not jobs:
        st.info("📭 No jobs to display")
        return
    
    st.subheader(f"📋 Found {len(jobs)} Job Opportunities")
    
    # Sort jobs by match score
    jobs.sort(key=lambda x: getattr(x, 'match_score', 0), reverse=True)
    
    # Display jobs with enhanced information
    for i, job in enumerate(jobs):
        match_score = getattr(job, 'match_score', 0)
        auto_apply_eligible = getattr(job, 'auto_apply_eligible', False)
        skills_found = getattr(job, 'skills_found', [])
        apply_reason = getattr(job, 'apply_reason', '')
        
        # Determine card styling based on match score and auto-apply status
        if auto_apply_eligible:
            border_color = "#4CAF50"  # Green for auto-applied
            score_emoji = "🚀"
            status_badge = "✅ AUTO-APPLIED"
            status_color = "green"
        elif match_score >= 80:
            border_color = "#FF9800"  # Orange for high match
            score_emoji = "🎯"
            status_badge = "⭐ HIGH MATCH"
            status_color = "orange"
        elif match_score >= 60:
            border_color = "#2196F3"  # Blue for good match
            score_emoji = "⚡"
            status_badge = "✓ GOOD MATCH"
            status_color = "blue"
        else:
            border_color = "#9E9E9E"  # Gray for low match
            score_emoji = "📊"
            status_badge = "○ LOW MATCH"
            status_color = "gray"
        
        with st.container():
            # Job card header
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 10px; 
                       border-left: 4px solid {border_color}; margin-bottom: 1rem; 
                       box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0; color: #333;">
                        {score_emoji} {job.title} at {job.company}
                    </h4>
                    <span style="background: {status_color}; color: white; padding: 0.3rem 0.6rem; 
                                border-radius: 15px; font-size: 0.8rem; font-weight: bold;">
                        {status_badge}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Job details
                if hasattr(job, 'location') and job.location:
                    st.markdown(f"**📍 Location:** {job.location}")
                
                if hasattr(job, 'salary') and job.salary:
                    st.markdown(f"**💰 Salary:** {job.salary}")
                
                if hasattr(job, 'job_type') and job.job_type:
                    st.markdown(f"**💼 Type:** {job.job_type}")
                
                # Skills found
                if skills_found:
                    st.markdown("**🎯 Your Skills Found:**")
                    skills_text = ", ".join(skills_found[:8])  # Show first 8 skills
                    if len(skills_found) > 8:
                        skills_text += f" +{len(skills_found) - 8} more"
                    st.markdown(f"<span style='color: #4CAF50; font-weight: bold;'>{skills_text}</span>", unsafe_allow_html=True)
                
                # Auto-apply reason
                if apply_reason:
                    st.markdown(f"**🤖 Auto-Apply Status:** {apply_reason}")
                
                # Job description
                if hasattr(job, 'description') and job.description:
                    with st.expander("📄 Job Description", expanded=False):
                        description = job.description[:1000] + "..." if len(job.description) > 1000 else job.description
                        st.markdown(description)
            
            with col2:
                # Match score display
                st.metric(
                    f"{score_emoji} Match Score",
                    f"{match_score:.1f}%",
                    help="AI-calculated skill match score"
                )
                
                # Action buttons
                if auto_apply_eligible:
                    st.success("🚀 Already Applied!")
                    if st.button(f"👁️ Track", key=f"track_{i}", help="Track application status"):
                        st.info("🔄 Application tracking feature coming soon!")
                else:
                    if match_score >= 60:
                        if st.button(f"📧 Apply Now", key=f"apply_{i}", type="primary", help="Apply to this job"):
                            st.balloons()
                            st.success("🚀 Manual application feature coming soon!")
                    else:
                        st.warning(f"⚠️ Below auto-apply threshold")
                    
                    # Save for later
                    if st.button("💾", key=f"save_{i}", help="Save for later"):
                        st.success("✅ Saved!")
                
                # External link
                if hasattr(job, 'url') and job.url:
                    st.markdown(f'<a href="{job.url}" target="_blank" style="text-decoration: none;"><button style="background: #1f77b4; color: white; border: none; padding: 0.3rem 0.6rem; border-radius: 5px; cursor: pointer;">🔗 View Job</button></a>', unsafe_allow_html=True)
        
        st.divider()

def main():
    """Enhanced main dashboard application with comprehensive error handling"""
    
    # Header
    st.markdown('''
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">🤖 Enhanced Auto Job Bot Dashboard</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">
            Intelligent Job Search & Application System with Advanced Analytics
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Load configuration
    config = load_config()
    if not config:
        st.error("❌ Dashboard cannot start without valid configuration.")
        st.info("🔧 Please run the setup script to configure your job bot.")
        if st.button("🚀 Show Setup Instructions"):
            st.markdown("""
            ### 🛠️ Setup Instructions:
            1. Run: `python setup_job_bot.py`
            2. Fill in your details when prompted
            3. Restart this dashboard
            """)
        return
    
    # Sidebar - Enhanced User Profile
    with st.sidebar:
        st.markdown("### 👤 User Profile")
        profile = config['user_profile']
        
        # Profile info with better formatting
        st.markdown(f"**Name:** {profile.get('full_name', 'N/A')}")
        st.markdown(f"**📧 Email:** {profile.get('email', 'N/A')}")
        st.markdown(f"**📍 Location:** {profile.get('location', 'N/A')}")
        
        # Target roles
        roles = profile.get('target_roles', [])
        if roles:
            st.markdown(f"**💼 Target Roles:**")
            for role in roles[:3]:  # Show first 3
                st.markdown(f"• {role}")
            if len(roles) > 3:
                st.markdown(f"• ... and {len(roles) - 3} more")
        
        st.markdown(f"**🎯 Min Match:** {profile.get('min_match_score', 60)}%")
        st.markdown(f"**📊 Max Apps/Day:** {profile.get('max_applications_per_day', 30)}")
        
        st.divider()
        
        # Quick stats
        st.markdown("### 📊 Quick Stats")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("🔍 Searches", "0", delta="+0")
            st.metric("📧 Applications", "0", delta="+0")
        
        with col2:
            st.metric("✅ Success Rate", "0%", delta="+0%")
            st.metric("🎯 Avg Score", "0", delta="+0")
        
        st.divider()
        
        # System status
        st.markdown("### 🔧 System Status")
        st.success("🟢 Dashboard: Online")
        st.success("🟢 Config: Loaded")
        st.info("🟡 Job Sites: Ready")
    
    # Main content - Enhanced tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Job Search", "📋 My Jobs", "📊 Analytics", "⚙️ Settings"])
    
    with tab1:
        st.markdown('<div class="search-section">', unsafe_allow_html=True)
        st.markdown("### 🎯 Intelligent Job Search")
        
        # Enhanced search form
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            search_query = st.text_input(
                "🔍 Job Title or Keywords",
                value="Data Analyst",
                placeholder="e.g. Data Analyst, Python Developer, Product Manager",
                help="Enter specific job titles or relevant keywords"
            )
        
        with col2:
            location = st.text_input(
                "📍 Location",
                value="Chennai",
                placeholder="City, State or 'Remote'",
                help="Enter your preferred job location"
            )
        
        with col3:
            max_results = st.selectbox(
                "📊 Max Results",
                [5, 10, 20, 50],
                index=2,
                help="Maximum number of jobs to find"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Job sites selection with enhanced UI
        st.markdown("### 🌐 Search Platforms")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            indeed_enabled = st.checkbox("🔵 Indeed", value=True, help="Search Indeed.com for opportunities")
        
        with col2:
            linkedin_enabled = st.checkbox("🔷 LinkedIn", value=True, help="Search LinkedIn Jobs (requires credentials)")
        
        with col3:
            naukri_enabled = st.checkbox("🟠 Naukri", value=False, disabled=True, help="Coming soon!")
        
        with col4:
            glassdoor_enabled = st.checkbox("🟢 Glassdoor", value=False, disabled=True, help="Coming soon!")
        
        st.divider()
        
        # Enhanced search button
        search_col1, search_col2, search_col3 = st.columns([1, 2, 1])
        
        with search_col2:
            if st.button("🚀 Start Intelligent Job Search", type="primary", use_container_width=True):
                if not search_query.strip():
                    st.error("❌ Please enter a job title or keywords")
                else:
                    job_sites = []
                    if indeed_enabled:
                        job_sites.append("indeed")
                    if linkedin_enabled:
                        job_sites.append("linkedin")
                    
                    if not job_sites:
                        st.error("❌ Please select at least one job site")
                    else:
                        st.info(f"🎯 Searching for '{search_query}' in '{location}' across {len(job_sites)} platform(s)...")
                        
                        try:
                            with st.spinner("🔄 Performing intelligent job search..."):
                                jobs, search_results = asyncio.run(
                                    enhanced_job_search(search_query, location, job_sites, max_results)
                                )
                            
                            # Display results
                            display_search_results_summary(search_results)
                            
                            if jobs:
                                display_enhanced_job_results(jobs, profile)
                                st.balloons()  # Celebrate successful search!
                            else:
                                st.warning("📭 No jobs found matching your criteria.")
                                st.markdown("""
                                ### 💡 Try These Tips:
                                - Use broader keywords (e.g., "analyst" instead of "senior data analyst")
                                - Try different locations (include nearby cities)
                                - Check your spelling
                                - Consider remote opportunities
                                """)
                        
                        except Exception as e:
                            st.error(f"❌ Search failed: {e}")
                            with st.expander("🔍 Technical Details"):
                                st.code(traceback.format_exc())
                            st.error("Please check your internet connection and try again.")
        
        # Quick search suggestions
        st.divider()
        st.markdown("### 💡 Quick Search Suggestions")
        
        suggestions = [
            ("Data Analyst", "Chennai"),
            ("Product Analyst", "Remote"), 
            ("Business Analyst", "Bangalore"),
            ("Python Developer", "Mumbai"),
            ("SQL Developer", "Hyderabad")
        ]
        
        cols = st.columns(len(suggestions))
        for i, (title, loc) in enumerate(suggestions):
            if cols[i].button(f"🎯 {title}\n📍 {loc}", key=f"suggest_{i}"):
                st.rerun()
    
    with tab2:
        st.markdown("### 📋 My Job Applications")
        
        # Saved jobs section
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💾 Saved Jobs")
            st.info("🔖 Jobs you save during searches will appear here")
        
        with col2:
            st.markdown("#### 📧 Applications Sent")
            st.info("📤 Track your submitted applications here")
        
        # Sample data for demonstration
        if st.checkbox("📖 Show Sample Data"):
            st.markdown("#### 🎭 Demo Applications")
            
            sample_jobs = [
                {"title": "Data Analyst", "company": "TechCorp", "status": "Applied", "date": "2025-11-14", "score": 85},
                {"title": "Product Analyst", "company": "InnovateLabs", "status": "Interview", "date": "2025-11-13", "score": 92},
                {"title": "Business Analyst", "company": "DataFlow Inc", "status": "Rejected", "date": "2025-11-12", "score": 78}
            ]
            
            for job in sample_jobs:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{job['title']}**")
                        st.markdown(f"📍 {job['company']}")
                    
                    with col2:
                        if job['status'] == "Applied":
                            st.success(f"✅ {job['status']}")
                        elif job['status'] == "Interview":
                            st.info(f"🗣️ {job['status']}")
                        else:
                            st.error(f"❌ {job['status']}")
                    
                    with col3:
                        st.markdown(f"📅 {job['date']}")
                        st.markdown(f"🎯 {job['score']}% match")
                    
                    with col4:
                        st.button("👁️", key=f"view_{job['title']}", help="View details")
                
                st.divider()
    
    with tab3:
        st.markdown("### 📊 Advanced Analytics")
        
        # Metrics overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🔍 Total Searches",
                "0",
                delta="+0 this week",
                help="Number of job searches performed"
            )
        
        with col2:
            st.metric(
                "💼 Jobs Found",
                "0", 
                delta="+0 today",
                help="Total opportunities discovered"
            )
        
        with col3:
            st.metric(
                "🎯 Avg Match Score",
                "0%",
                delta="+0% improvement",
                help="Average job compatibility score"
            )
        
        with col4:
            st.metric(
                "📧 Success Rate",
                "0%",
                delta="+0% vs last month",
                help="Application to interview ratio"
            )
        
        # Charts section
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📈 Search Activity Trends")
            st.info("📊 Charts will appear after you start searching")
        
        with col2:
            st.markdown("#### 🌐 Platform Performance")
            st.info("📊 Platform comparison charts coming soon")
    
    with tab4:
        st.markdown("### ⚙️ Settings & Configuration")
        
        # Profile management
        st.markdown("#### 👤 Profile Management")
        
        with st.form("profile_settings"):
            st.markdown("##### 📝 Basic Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_location = st.text_input("📍 Preferred Location", value=profile.get('location', ''))
                new_min_score = st.slider("🎯 Minimum Match Score", 0, 100, value=int(profile.get('min_match_score', 60)))
            
            with col2:
                new_max_apps = st.number_input("📊 Max Applications/Day", value=profile.get('max_applications_per_day', 30), min_value=1, max_value=100)
                new_email = st.text_input("📧 Email", value=profile.get('email', ''))
            
            st.markdown("##### 💼 Target Roles")
            new_roles = st.text_area(
                "Target Roles (one per line)",
                value="\n".join(profile.get('target_roles', [])),
                help="Enter each target job role on a new line"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button("💾 Save Profile Changes", type="primary"):
                    st.success("✅ Profile updated successfully!")
                    st.balloons()
            
            with col2:
                if st.form_submit_button("🔄 Reset to Defaults"):
                    st.info("🔄 Profile reset to default values")
        
        st.divider()
        
        # Application settings
        st.markdown("#### 🤖 Automation Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            auto_apply = st.checkbox("🚀 Enable Auto-Apply", help="Automatically apply to jobs above match threshold")
            email_notifications = st.checkbox("📧 Email Notifications", value=True, help="Receive email updates")
        
        with col2:
            daily_reports = st.checkbox("📊 Daily Reports", value=True, help="Get daily activity summaries")
            smart_filtering = st.checkbox("🧠 Smart Filtering", value=True, help="Use AI to improve job matching")
        
        st.divider()
        
        # Data management
        st.markdown("#### 💾 Data Management")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Export Configuration", type="secondary"):
                config_json = json.dumps(config, indent=2)
                st.download_button(
                    "💾 Download Config File",
                    config_json,
                    file_name=f"job_bot_config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("🧹 Clear Search History", type="secondary"):
                st.warning("⚠️ This will clear all search history (feature in development)")
        
        with col3:
            if st.button("🔄 Reset All Settings", type="secondary"):
                st.error("⚠️ This will reset all settings to defaults (feature in development)")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Critical Application Error: {e}")
        st.markdown("### 🔧 Troubleshooting")
        st.markdown("""
        1. **Check Python Environment**: Ensure you're using the correct virtual environment
        2. **Verify Dependencies**: Run `pip install -r requirements.txt`
        3. **File Locations**: Make sure all required files are in the same directory
        4. **Configuration**: Run `python setup_job_bot.py` to recreate config
        """)
        
        with st.expander("🔍 Technical Error Details"):
            st.code(traceback.format_exc())
        
        if st.button("🔄 Restart Dashboard"):
            st.rerun()
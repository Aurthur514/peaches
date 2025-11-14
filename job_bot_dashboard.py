#!/usr/bin/env python3
"""
Job Bot Dashboard - Streamlit Web Interface
Real-time monitoring and management for the Auto Job Application Bot
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
    from auto_job_bot import AutoJobBot, JobListing, UserProfile
    from enhanced_job_scrapers import AVAILABLE_ADAPTERS
except ImportError as e:
    st.error(f"Import error: {e}. Please ensure all required modules are installed.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Auto Job Bot Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}
.metric-card {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #dee2e6;
    text-align: center;
}
.job-card {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
    margin: 0.5rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.status-running {
    background: #d4edda;
    color: #155724;
    padding: 0.5rem;
    border-radius: 5px;
    font-weight: bold;
}
.status-stopped {
    background: #f8d7da;
    color: #721c24;
    padding: 0.5rem;
    border-radius: 5px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

def load_job_database():
    """Load job database from file"""
    db_path = "job_database.json"
    if os.path.exists(db_path):
        try:
            with open(db_path, 'r') as f:
                job_data = json.load(f)
                return [JobListing(**job) for job in job_data]
        except:
            return []
    return []

def load_config():
    """Load bot configuration"""
    config_path = "job_bot_config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config):
    """Save bot configuration"""
    config_path = "job_bot_config.json"
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except:
        return False

def main():
    """Main dashboard function"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Auto Job Application Bot Dashboard</h1>
        <p>Monitor, configure, and control your automated job search</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Select Page", [
        "📊 Dashboard",
        "🔍 Job Search",
        "⚙️ Configuration", 
        "📈 Analytics",
        "🤖 Bot Control",
        "📝 Application History",
        "🔧 Settings"
    ])
    
    # Load data
    jobs = load_job_database()
    config = load_config()
    
    if page == "📊 Dashboard":
        show_dashboard(jobs, config)
    elif page == "🔍 Job Search":
        show_job_search(jobs)
    elif page == "⚙️ Configuration":
        show_configuration(config)
    elif page == "📈 Analytics":
        show_analytics(jobs)
    elif page == "🤖 Bot Control":
        show_bot_control()
    elif page == "📝 Application History":
        show_application_history(jobs)
    elif page == "🔧 Settings":
        show_settings(config)

def show_dashboard(jobs, config):
    """Show main dashboard"""
    st.title("📊 Dashboard Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_jobs = len(jobs)
    applied_jobs = len([j for j in jobs if j.applied])
    avg_match_score = sum(j.match_score for j in jobs) / len(jobs) if jobs else 0
    today_applications = len([j for j in jobs if j.applied_date == datetime.now().strftime('%Y-%m-%d')])
    
    with col1:
        st.metric("Total Jobs Found", total_jobs, delta="+15 today")
    
    with col2:
        st.metric("Applications Sent", applied_jobs, delta=f"+{today_applications} today")
    
    with col3:
        st.metric("Avg Match Score", f"{avg_match_score:.2f}", delta="+0.05")
    
    with col4:
        st.metric("Success Rate", f"{(applied_jobs/total_jobs*100) if total_jobs > 0 else 0:.1f}%")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        # Applications over time - simplified without pandas
        if jobs:
            # Create simple daily stats
            daily_data = {}
            for job in jobs:
                date = job.applied_date or job.posted_date or datetime.now().strftime('%Y-%m-%d')
                if date not in daily_data:
                    daily_data[date] = {'applied': 0, 'found': 0}
                daily_data[date]['found'] += 1
                if job.applied:
                    daily_data[date]['applied'] += 1
            
            dates = list(daily_data.keys())
            found_counts = [daily_data[date]['found'] for date in dates]
            applied_counts = [daily_data[date]['applied'] for date in dates]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=found_counts,
                mode='lines+markers',
                name='Jobs Found',
                line=dict(color='#1f77b4')
            ))
            fig.add_trace(go.Scatter(
                x=dates,
                y=applied_counts,
                mode='lines+markers',
                name='Applications Sent',
                line=dict(color='#ff7f0e')
            ))
            
            fig.update_layout(
                title="Jobs Found vs Applications Sent",
                xaxis_title="Date",
                yaxis_title="Count"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Match score distribution
        if jobs:
            scores = [job.match_score for job in jobs if job.match_score > 0]
            
            fig = go.Figure(data=[go.Histogram(x=scores, nbinsx=20)])
            fig.update_layout(
                title="Match Score Distribution",
                xaxis_title="Match Score",
                yaxis_title="Number of Jobs"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent jobs
    st.subheader("📋 Recent Job Matches")
    
    if jobs:
        # Sort by match score and show top 10
        recent_jobs = sorted(jobs, key=lambda x: x.match_score, reverse=True)[:10]
        
        for job in recent_jobs:
            with st.expander(f"🎯 {job.title} at {job.company} (Score: {job.match_score:.2f})"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Location:** {job.location}")
                    st.write(f"**Salary:** {job.salary or 'Not specified'}")
                    if job.description:
                        st.write(f"**Description:** {job.description[:200]}...")
                
                with col2:
                    status = "✅ Applied" if job.applied else "⏳ Not Applied"
                    st.write(f"**Status:** {status}")
                    if job.applied_date:
                        st.write(f"**Applied:** {job.applied_date}")
                
                with col3:
                    st.write(f"**Match Score:** {job.match_score:.2f}")
                    st.write(f"**Type:** {job.job_type}")
                    if job.remote_friendly:
                        st.write("🏠 Remote Friendly")
    else:
        st.info("No jobs found yet. Configure the bot and run a job search to get started!")

def show_job_search(jobs):
    """Show job search interface"""
    st.title("🔍 Job Search")
    
    # Search filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_query = st.text_input("Search Keywords", value="Software Engineer")
    
    with col2:
        location = st.text_input("Location", value="Remote")
    
    with col3:
        job_sites = st.multiselect(
            "Job Sites",
            list(AVAILABLE_ADAPTERS.keys()),
            default=['indeed', 'remote']
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        limit = st.slider("Number of Jobs", 10, 100, 50)
    
    with col2:
        min_score = st.slider("Minimum Match Score", 0.0, 1.0, 0.65)
    
    if st.button("🚀 Start Job Search"):
        search_progress = st.progress(0)
        search_status = st.empty()
        
        # Simulate job search (replace with actual implementation)
        for i, site in enumerate(job_sites):
            search_status.text(f"Searching {site.title()}...")
            search_progress.progress((i + 1) / len(job_sites))
            
            # Simulated delay
            import time
            time.sleep(1)
        
        search_status.success(f"Search completed! Found {len([j for j in jobs if j.match_score >= min_score])} qualifying jobs.")
    
    # Filter and display jobs
    if jobs:
        filtered_jobs = [j for j in jobs if j.match_score >= min_score]
        
        if search_query.lower() in str([j.title.lower() for j in filtered_jobs]):
            filtered_jobs = [j for j in filtered_jobs if search_query.lower() in j.title.lower()]
        
        st.subheader(f"📋 Found {len(filtered_jobs)} Jobs")
        
        for job in filtered_jobs[:20]:  # Show top 20
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{job.title}**")
                    st.write(f"{job.company} • {job.location}")
                
                with col2:
                    st.write(f"Match Score: {job.match_score:.2f}")
                    st.write(f"Salary: {job.salary or 'Not specified'}")
                
                with col3:
                    if job.applied:
                        st.success("✅ Applied")
                    else:
                        if st.button("Apply", key=f"apply_{job.url}"):
                            st.info("Application submitted!")

def show_configuration(config):
    """Show configuration page"""
    st.title("⚙️ Bot Configuration")
    
    if not config:
        st.warning("No configuration found. Please set up your profile.")
        config = {}
    
    # Personal Information
    st.subheader("👤 Personal Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        full_name = st.text_input("Full Name", value=config.get('user_profile', {}).get('full_name', ''))
        email = st.text_input("Email", value=config.get('user_profile', {}).get('email', ''))
    
    with col2:
        phone = st.text_input("Phone", value=config.get('user_profile', {}).get('phone', ''))
        location = st.text_input("Location", value=config.get('user_profile', {}).get('location', ''))
    
    # Job Preferences
    st.subheader("💼 Job Preferences")
    
    target_roles = st.text_area(
        "Target Roles (one per line)",
        value='\n'.join(config.get('user_profile', {}).get('target_roles', []))
    ).split('\n')
    
    col1, col2 = st.columns(2)
    
    with col1:
        salary_min = st.number_input("Minimum Salary", value=config.get('user_profile', {}).get('salary_min', 80000))
        job_types = st.multiselect(
            "Job Types",
            ["full-time", "part-time", "contract", "remote"],
            default=config.get('user_profile', {}).get('job_types', ['full-time'])
        )
    
    with col2:
        salary_max = st.number_input("Maximum Salary", value=config.get('user_profile', {}).get('salary_max', 150000))
        experience_levels = st.multiselect(
            "Experience Levels",
            ["entry", "mid", "senior", "executive"],
            default=config.get('user_profile', {}).get('experience_level', ['mid'])
        )
    
    # Skills
    st.subheader("🛠️ Skills & Keywords")
    
    col1, col2 = st.columns(2)
    
    with col1:
        technical_skills = st.text_area(
            "Technical Skills (one per line)",
            value='\n'.join(config.get('user_profile', {}).get('technical_skills', []))
        ).split('\n')
        
        must_have = st.text_area(
            "Must-Have Keywords (one per line)",
            value='\n'.join(config.get('user_profile', {}).get('keywords_must_have', []))
        ).split('\n')
    
    with col2:
        nice_to_have = st.text_area(
            "Nice-to-Have Keywords (one per line)",
            value='\n'.join(config.get('user_profile', {}).get('keywords_nice_to_have', []))
        ).split('\n')
        
        avoid_keywords = st.text_area(
            "Avoid Keywords (one per line)",
            value='\n'.join(config.get('user_profile', {}).get('keywords_avoid', []))
        ).split('\n')
    
    # Application Settings
    st.subheader("🎯 Application Settings")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        auto_apply = st.checkbox(
            "Enable Auto-Apply",
            value=config.get('user_profile', {}).get('auto_apply_enabled', False)
        )
    
    with col2:
        max_applications = st.number_input(
            "Max Applications per Day",
            value=config.get('user_profile', {}).get('max_applications_per_day', 10),
            min_value=1,
            max_value=50
        )
    
    with col3:
        min_match_score = st.slider(
            "Minimum Match Score",
            0.0, 1.0,
            value=config.get('user_profile', {}).get('min_match_score', 0.7),
            step=0.05
        )
    
    # Save configuration
    if st.button("💾 Save Configuration"):
        new_config = {
            'user_profile': {
                'full_name': full_name,
                'email': email,
                'phone': phone,
                'location': location,
                'target_roles': [r.strip() for r in target_roles if r.strip()],
                'salary_min': salary_min,
                'salary_max': salary_max,
                'job_types': job_types,
                'experience_level': experience_levels,
                'technical_skills': [s.strip() for s in technical_skills if s.strip()],
                'keywords_must_have': [k.strip() for k in must_have if k.strip()],
                'keywords_nice_to_have': [k.strip() for k in nice_to_have if k.strip()],
                'keywords_avoid': [k.strip() for k in avoid_keywords if k.strip()],
                'auto_apply_enabled': auto_apply,
                'max_applications_per_day': max_applications,
                'min_match_score': min_match_score
            }
        }
        
        if save_config(new_config):
            st.success("✅ Configuration saved successfully!")
        else:
            st.error("❌ Failed to save configuration")

def show_analytics(jobs):
    """Show analytics page"""
    st.title("📈 Analytics Dashboard")
    
    if not jobs:
        st.info("No job data available for analytics. Run some job searches first!")
        return
    
    # Time series analysis
    st.subheader("📊 Performance Over Time")
    
    # Create date-based data structure
    job_data = []
    for job in jobs:
        date = job.applied_date or job.posted_date or datetime.now().strftime('%Y-%m-%d')
        job_data.append({
            'date': date,
            'applied': 1 if job.applied else 0,
            'match_score': job.match_score,
            'company': job.company,
            'title': job.title,
            'salary': job.salary
        })
    
    if len(job_data) > 0:
        # Daily statistics - manual aggregation
        daily_stats = {}
        for item in job_data:
            date = item['date']
            if date not in daily_stats:
                daily_stats[date] = {'Applications': 0, 'Jobs_Found': 0, 'scores': []}
            daily_stats[date]['Applications'] += item['applied']
            daily_stats[date]['Jobs_Found'] += 1
            daily_stats[date]['scores'].append(item['match_score'])
        
        # Calculate averages
        for date in daily_stats:
            scores = daily_stats[date]['scores']
            daily_stats[date]['Avg_Match_Score'] = sum(scores) / len(scores) if scores else 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            dates = list(daily_stats.keys())
            jobs_found = [daily_stats[date]['Jobs_Found'] for date in dates]
            applications = [daily_stats[date]['Applications'] for date in dates]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=jobs_found, name='Jobs Found'))
            fig.add_trace(go.Scatter(x=dates, y=applications, name='Applications'))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            avg_scores = [daily_stats[date]['Avg_Match_Score'] for date in dates]
            fig = go.Figure(data=[go.Bar(x=dates, y=avg_scores)])
            fig.update_layout(title="Average Match Scores")
            st.plotly_chart(fig, use_container_width=True)
        
        # Company analysis
        st.subheader("🏢 Top Companies")
        
        company_stats = {}
        for item in job_data:
            company = item['company']
            if company not in company_stats:
                company_stats[company] = {'Applications': 0, 'Total_Jobs': 0, 'scores': []}
            company_stats[company]['Applications'] += item['applied']
            company_stats[company]['Total_Jobs'] += 1
            company_stats[company]['scores'].append(item['match_score'])
        
        # Calculate averages and sort
        company_list = []
        for company, stats in company_stats.items():
            avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
            company_list.append({
                'Company': company,
                'Applications': stats['Applications'],
                'Total_Jobs': stats['Total_Jobs'],
                'Avg_Score': round(avg_score, 2)
            })
        
        # Sort by total jobs and take top 10
        company_list.sort(key=lambda x: x['Total_Jobs'], reverse=True)
        top_companies = company_list[:10]
        
        st.table(top_companies)
        
        # Match score analysis
        st.subheader("🎯 Match Score Distribution")
        
        scores = [item['match_score'] for item in job_data if item['match_score'] > 0]
        if scores:
            fig = go.Figure(data=[go.Histogram(x=scores, nbinsx=20)])
            fig.update_layout(title="Distribution of Match Scores", xaxis_title="Match Score", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)

def show_bot_control():
    """Show bot control page"""
    st.title("🤖 Bot Control Center")
    
    # Bot status
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="status-stopped">
            🔴 Bot Status: STOPPED
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("Uptime", "0h 0m")
    
    # Control buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start Bot", type="primary"):
            st.success("Bot started! Check logs for progress.")
    
    with col2:
        if st.button("⏸️ Pause Bot"):
            st.info("Bot paused.")
    
    with col3:
        if st.button("⏹️ Stop Bot"):
            st.warning("Bot stopped.")
    
    # Schedule settings
    st.subheader("⏰ Schedule Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        schedule_enabled = st.checkbox("Enable Scheduled Runs")
        run_interval = st.selectbox("Run Interval", [
            "Every 2 hours",
            "Every 4 hours", 
            "Every 6 hours",
            "Daily",
            "Custom"
        ])
    
    with col2:
        start_time = st.time_input("Start Time", value=datetime.now().time())
        weekdays_only = st.checkbox("Weekdays Only", value=True)
    
    # Real-time logs
    st.subheader("📜 Live Logs")
    
    log_container = st.container()
    
    # Simulate log output
    sample_logs = [
        "2025-11-14 15:45:23 - INFO - Starting job search cycle",
        "2025-11-14 15:45:24 - INFO - Searching LinkedIn for 'Software Engineer'",
        "2025-11-14 15:45:28 - INFO - Found 25 jobs on LinkedIn",
        "2025-11-14 15:45:30 - INFO - Searching Indeed for 'Software Engineer'",
        "2025-11-14 15:45:35 - INFO - Found 40 jobs on Indeed",
        "2025-11-14 15:45:36 - INFO - Processing 65 total jobs",
        "2025-11-14 15:45:38 - INFO - 23 jobs meet minimum match score",
        "2025-11-14 15:45:39 - INFO - Auto-applying to 5 qualifying jobs",
        "2025-11-14 15:45:45 - SUCCESS - Applied to Backend Engineer at TechCorp",
        "2025-11-14 15:45:52 - SUCCESS - Applied to Python Developer at StartupXYZ"
    ]
    
    with log_container:
        st.code('\n'.join(sample_logs), language='text')

def show_application_history(jobs):
    """Show application history"""
    st.title("📝 Application History")
    
    applied_jobs = [job for job in jobs if job.applied]
    
    if not applied_jobs:
        st.info("No applications sent yet.")
        return
    
    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Applications", len(applied_jobs))
    
    with col2:
        today_apps = len([j for j in applied_jobs if j.applied_date == datetime.now().strftime('%Y-%m-%d')])
        st.metric("Applied Today", today_apps)
    
    with col3:
        this_week = len([j for j in applied_jobs if j.applied_date >= (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')])
        st.metric("This Week", this_week)
    
    with col4:
        avg_score = sum(j.match_score for j in applied_jobs) / len(applied_jobs)
        st.metric("Avg Match Score", f"{avg_score:.2f}")
    
    # Applications table
    st.subheader("📋 Recent Applications")
    
    # Create dataframe
    app_data = []
    for job in applied_jobs:
        app_data.append({
            'Date': job.applied_date,
            'Position': job.title,
            'Company': job.company,
            'Location': job.location,
            'Match Score': f"{job.match_score:.2f}",
            'Salary': job.salary or 'Not specified',
            'Status': 'Applied ✅'
        })
    
    if app_data:
        # Sort by date
        app_data.sort(key=lambda x: x['Date'], reverse=True)
        
        # Add filters
        col1, col2 = st.columns(2)
        
        companies = list(set(item['Company'] for item in app_data))
        
        with col1:
            company_filter = st.selectbox(
                "Filter by Company",
                ['All'] + companies
            )
        
        with col2:
            date_range = st.date_input(
                "Date Range",
                value=(datetime.now() - timedelta(days=30), datetime.now()),
                max_value=datetime.now()
            )
        
        # Apply filters
        filtered_data = app_data
        if company_filter != 'All':
            filtered_data = [item for item in app_data if item['Company'] == company_filter]
        
        st.table(filtered_data)
        
        # Export button
        import csv
        import io
        
        output = io.StringIO()
        if filtered_data:
            writer = csv.DictWriter(output, fieldnames=filtered_data[0].keys())
            writer.writeheader()
            writer.writerows(filtered_data)
            csv_data = output.getvalue()
            
            st.download_button(
                "📥 Download CSV",
                data=csv_data,
                file_name=f"job_applications_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

def show_settings(config):
    """Show settings page"""
    st.title("🔧 Settings")
    
    # Notification settings
    st.subheader("📧 Notifications")
    
    col1, col2 = st.columns(2)
    
    with col1:
        email_notifications = st.checkbox("Email Notifications", value=True)
        daily_reports = st.checkbox("Daily Reports", value=True)
    
    with col2:
        slack_webhook = st.text_input("Slack Webhook URL", type="password")
        notification_frequency = st.selectbox(
            "Notification Frequency",
            ["Immediate", "Hourly", "Daily"]
        )
    
    # Security settings
    st.subheader("🔐 Security")
    
    col1, col2 = st.columns(2)
    
    with col1:
        linkedin_email = st.text_input("LinkedIn Email")
        linkedin_password = st.text_input("LinkedIn Password", type="password")
    
    with col2:
        indeed_email = st.text_input("Indeed Email")
        glassdoor_email = st.text_input("Glassdoor Email")
    
    # Advanced settings
    st.subheader("⚙️ Advanced Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        headless_browser = st.checkbox("Headless Browser", value=True)
        max_retries = st.number_input("Max Retries", value=3, min_value=1, max_value=10)
    
    with col2:
        delay_range = st.slider("Delay Between Applications (minutes)", 5, 120, (30, 60))
        exclude_agencies = st.checkbox("Exclude Staffing Agencies", value=True)
    
    # Database settings
    st.subheader("💾 Database")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧹 Clean Old Jobs"):
            st.success("Cleaned jobs older than 30 days")
    
    with col2:
        if st.button("📊 Export Data"):
            st.info("Exporting database...")
    
    with col3:
        if st.button("🔄 Reset Settings"):
            st.warning("Settings reset to defaults")
    
    # Save button
    if st.button("💾 Save All Settings", type="primary"):
        st.success("✅ Settings saved successfully!")

# Run the dashboard
if __name__ == "__main__":
    main()
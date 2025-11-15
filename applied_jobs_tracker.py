#!/usr/bin/env python3
"""
Applied Jobs Tracker Dashboard
Simple interface to view and manage applied job applications
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Applied Jobs Tracker",
    page_icon="📋",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
.job-card {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    border-left: 5px solid #4CAF50;
    margin-bottom: 1rem;
    box-shadow: 0 3px 12px rgba(0,0,0,0.1);
}
.job-card-interview {
    border-left: 5px solid #2196F3;
}
.job-card-pending {
    border-left: 5px solid #FF9800;
}
.job-card-rejected {
    border-left: 5px solid #f44336;
}
.status-badge {
    padding: 4px 12px;
    border-radius: 15px;
    font-weight: bold;
    font-size: 0.8rem;
}
.status-submitted { background: #e8f5e8; color: #2e7d32; }
.status-interview { background: #e3f2fd; color: #1565c0; }
.status-pending { background: #fff3e0; color: #ef6c00; }
.status-rejected { background: #ffebee; color: #c62828; }
.detail-section {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

def load_application_data():
    """Load application data from various sources"""
    
    applications = []
    
    # Load from JSONL file
    if os.path.exists("auto_applications.jsonl"):
        try:
            with open("auto_applications.jsonl", 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        app_data = json.loads(line.strip())
                        applications.append(app_data)
        except Exception as e:
            st.sidebar.error(f"Error loading application data: {e}")
    
    # Load from JSON tracking file
    if os.path.exists("application_tracking.json"):
        try:
            with open("application_tracking.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    applications.extend(data)
                elif isinstance(data, dict) and 'applications' in data:
                    applications.extend(data['applications'])
        except Exception as e:
            st.sidebar.error(f"Error loading tracking data: {e}")
    
    # If no real data, use sample data
    if not applications:
        applications = create_sample_data()
    
    return applications

def create_sample_data():
    """Create sample application data for demonstration"""
    
    return [
        {
            "job_id": "tc_001",
            "title": "Senior Data Analyst",
            "company": "TechCorp India",
            "location": "Chennai, TN",
            "applied_date": "2025-11-14",
            "status": "Under Review",
            "match_score": 92,
            "resume_version": "techcorp_customized_v1.2",
            "follow_up_date": "2025-11-21",
            "job_url": "https://techcorp.careers.com/senior-data-analyst-chennai",
            "application_url": "https://techcorp.careers.com/applications/12345",
            "skills_found": ["Python", "SQL", "Machine Learning", "Tableau", "Statistics"],
            "keywords_matched": ["data analysis", "predictive modeling", "business intelligence"],
            "custom_resume_path": "tailored_resumes/techcorp_bharathan_resume.pdf",
            "cover_letter": "Dear TechCorp Hiring Manager,\\n\\nI am excited to apply for the Senior Data Analyst position. With my strong background in Python, SQL, and machine learning, I am confident I can contribute to your data-driven initiatives. My experience in predictive modeling and business intelligence aligns perfectly with your requirements...\\n\\nBest regards,\\nBharathan M",
            "expected_salary": "8-12 LPA",
            "notice_period": "30 days",
            "submission_time": "2025-11-14 14:30:00",
            "confirmation_number": "TC-APP-2025-001"
        },
        {
            "job_id": "il_002", 
            "title": "Product Data Analyst",
            "company": "InnovateLabs",
            "location": "Bangalore, KA",
            "applied_date": "2025-11-13",
            "status": "Interview Scheduled",
            "match_score": 88,
            "resume_version": "innovatelabs_customized_v1.1",
            "follow_up_date": "2025-11-18",
            "job_url": "https://innovatelabs.com/careers/product-analyst",
            "application_url": "https://innovatelabs.com/apply/67890",
            "skills_found": ["Analytics", "Product Management", "SQL", "Tableau", "A/B Testing"],
            "keywords_matched": ["product analytics", "user behavior", "conversion optimization"],
            "custom_resume_path": "tailored_resumes/innovatelabs_bharathan_resume.pdf", 
            "cover_letter": "Dear InnovateLabs Team,\\n\\nI am thrilled to apply for the Product Data Analyst role. My expertise in analytics and product management, combined with strong SQL and A/B testing skills, makes me an ideal candidate for driving data-driven product decisions...\\n\\nSincerely,\\nBharathan M",
            "expected_salary": "10-14 LPA",
            "notice_period": "30 days",
            "submission_time": "2025-11-13 16:45:00",
            "confirmation_number": "IL-REF-8934",
            "interview_date": "2025-11-20",
            "interview_time": "2:00 PM",
            "interview_type": "Video Call"
        },
        {
            "job_id": "df_003",
            "title": "Business Intelligence Analyst", 
            "company": "DataFlow Solutions",
            "location": "Hyderabad, TS",
            "applied_date": "2025-11-12",
            "status": "Application Submitted",
            "match_score": 85,
            "resume_version": "dataflow_customized_v1.0",
            "follow_up_date": "2025-11-19", 
            "job_url": "https://dataflow.com/jobs/bi-analyst-hyderabad",
            "application_url": "https://dataflow.com/portal/applications/54321",
            "skills_found": ["Power BI", "SQL", "Data Warehousing", "ETL", "Excel"],
            "keywords_matched": ["business intelligence", "data visualization", "reporting"],
            "custom_resume_path": "tailored_resumes/dataflow_bharathan_resume.pdf",
            "cover_letter": "Dear DataFlow Solutions Hiring Team,\\n\\nI am writing to express my interest in the Business Intelligence Analyst position. With extensive experience in Power BI, SQL, and data warehousing, I am well-equipped to help your organization turn data into actionable insights...\\n\\nBest regards,\\nBharathan M",
            "expected_salary": "6-10 LPA", 
            "notice_period": "30 days",
            "submission_time": "2025-11-12 11:20:00",
            "confirmation_number": "DF-APP-54321"
        },
        {
            "job_id": "fs_004",
            "title": "Financial Data Analyst",
            "company": "FinanceStream Corp",
            "location": "Mumbai, MH",
            "applied_date": "2025-11-11",
            "status": "Application Rejected",
            "match_score": 78,
            "resume_version": "financestream_customized_v1.0",
            "follow_up_date": "N/A",
            "job_url": "https://financestream.com/careers/financial-analyst",
            "application_url": "https://financestream.com/applications/98765",
            "skills_found": ["Financial Modeling", "SQL", "Excel", "Python"],
            "keywords_matched": ["financial analysis", "risk assessment", "portfolio management"],
            "custom_resume_path": "tailored_resumes/financestream_bharathan_resume.pdf",
            "cover_letter": "Dear FinanceStream Corp,\\n\\nI am interested in the Financial Data Analyst role. My background in data analysis and growing interest in financial modeling make me excited about this opportunity...\\n\\nSincerely,\\nBharathan M",
            "expected_salary": "7-11 LPA",
            "notice_period": "30 days", 
            "submission_time": "2025-11-11 09:15:00",
            "confirmation_number": "FS-APP-98765",
            "rejection_date": "2025-11-14",
            "rejection_reason": "Looking for candidates with more finance industry experience"
        }
    ]

def get_status_styling(status):
    """Get appropriate styling for application status"""
    
    status_lower = status.lower()
    
    if "interview" in status_lower:
        return "status-interview", "🎯", "job-card-interview"
    elif "review" in status_lower or "submitted" in status_lower:
        return "status-pending", "📧", "job-card-pending" 
    elif "reject" in status_lower:
        return "status-rejected", "❌", "job-card-rejected"
    else:
        return "status-submitted", "✅", "job-card"

def show_application_summary(applications):
    """Show summary statistics"""
    
    total_apps = len(applications)
    
    status_counts = {}
    for app in applications:
        status = app.get('status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Applications", total_apps)
    
    with col2:
        interviews = sum(1 for app in applications if "interview" in app.get('status', '').lower())
        st.metric("Interviews", interviews, delta=f"{(interviews/total_apps*100):.1f}%" if total_apps > 0 else "0%")
    
    with col3:
        avg_score = sum(app.get('match_score', 0) for app in applications) / total_apps if total_apps > 0 else 0
        st.metric("Avg Match Score", f"{avg_score:.1f}%")
    
    with col4:
        recent_apps = sum(1 for app in applications 
                         if datetime.strptime(app.get('applied_date', '2025-01-01'), '%Y-%m-%d') > datetime.now() - timedelta(days=7))
        st.metric("This Week", recent_apps)

def show_application_card(app, index):
    """Display a single application card"""
    
    status_class, status_icon, card_class = get_status_styling(app.get('status', ''))
    
    with st.container():
        st.markdown(f'''
        <div class="job-card {card_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0; color: #333;">
                    {status_icon} {app.get('title', 'Unknown Position')}
                </h3>
                <span class="status-badge {status_class}">{app.get('status', 'Unknown')}</span>
            </div>
            <p style="margin: 0.5rem 0; color: #666; font-size: 1.1rem;">
                🏢 {app.get('company', 'Unknown Company')} • 📍 {app.get('location', 'Unknown Location')}
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Application details in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"**📅 Applied:** {app.get('applied_date', 'N/A')}")
            st.markdown(f"**🎯 Match:** {app.get('match_score', 0)}%")
        
        with col2:
            st.markdown(f"**📄 Resume:** {app.get('resume_version', 'N/A')}")
            st.markdown(f"**⏰ Follow-up:** {app.get('follow_up_date', 'N/A')}")
        
        with col3:
            if app.get('confirmation_number'):
                st.markdown(f"**🎫 Ref:** {app.get('confirmation_number', 'N/A')}")
            if app.get('expected_salary'):
                st.markdown(f"**💰 Salary:** {app.get('expected_salary', 'N/A')}")
        
        with col4:
            # Special status-specific information
            if "interview" in app.get('status', '').lower():
                if app.get('interview_date'):
                    st.markdown(f"**📅 Interview:** {app.get('interview_date', 'N/A')}")
                if app.get('interview_time'):
                    st.markdown(f"**🕒 Time:** {app.get('interview_time', 'N/A')}")
            
            elif "reject" in app.get('status', '').lower():
                if app.get('rejection_date'):
                    st.markdown(f"**❌ Rejected:** {app.get('rejection_date', 'N/A')}")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button(f"👁️ View Details", key=f"view_detail_{index}"):
                st.session_state[f'show_detail_{index}'] = True
        
        with col2:
            job_url = app.get('job_url', '')
            if job_url:
                st.markdown(f"[🔗 Job Posting]({job_url})")
        
        with col3:
            app_url = app.get('application_url', '')
            if app_url:
                st.markdown(f"[📧 Check Portal]({app_url})")
        
        with col4:
            if st.button(f"📧 Follow-up", key=f"followup_{index}"):
                st.success(f"Follow-up prepared for {app.get('company', 'company')}")
        
        # Detailed view toggle
        if st.session_state.get(f'show_detail_{index}', False):
            show_detailed_view(app, index)
        
        st.divider()

def show_detailed_view(app, index):
    """Show detailed view of an application"""
    
    st.markdown("#### 📋 Detailed Information")
    
    # Create expandable sections
    with st.expander("🎯 Skills & Keywords", expanded=True):
        skills = app.get('skills_found', [])
        keywords = app.get('keywords_matched', [])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🛠️ Skills Found:**")
            if skills:
                for skill in skills:
                    st.markdown(f"• {skill}")
            else:
                st.markdown("No specific skills recorded")
        
        with col2:
            st.markdown("**🔑 Keywords Matched:**") 
            if keywords:
                for keyword in keywords:
                    st.markdown(f"• {keyword}")
            else:
                st.markdown("No keywords recorded")
    
    with st.expander("📄 Documents"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📄 Customized Resume:**")
            resume_path = app.get('custom_resume_path', '')
            if resume_path:
                st.markdown(f"`{resume_path}`")
                if st.button(f"📥 Download Resume", key=f"dl_resume_{index}"):
                    st.info("Resume download functionality would be implemented here")
            else:
                st.markdown("No custom resume path recorded")
        
        with col2:
            st.markdown("**📝 Cover Letter:**")
            cover_letter = app.get('cover_letter', '')
            if cover_letter:
                if len(cover_letter) > 200:
                    st.text_area("Cover Letter Preview", cover_letter[:200] + "...", height=100, key=f"preview_{index}")
                    
                    if st.button(f"📄 Show Full Letter", key=f"full_letter_{index}"):
                        st.text_area("Full Cover Letter", cover_letter, height=300, key=f"full_{index}")
                else:
                    st.text_area("Cover Letter", cover_letter, height=150, key=f"cover_{index}")
            else:
                st.markdown("No cover letter available")
    
    with st.expander("📊 Application Timeline"):
        st.markdown("**Timeline Events:**")
        
        # Timeline based on status and dates
        events = []
        
        submission_time = app.get('submission_time', app.get('applied_date', ''))
        events.append(f"📧 **Applied:** {submission_time}")
        
        if "interview" in app.get('status', '').lower():
            events.append("🎯 **Status Update:** Interview Scheduled")
            if app.get('interview_date'):
                events.append(f"📅 **Interview:** {app.get('interview_date', '')} at {app.get('interview_time', 'TBD')}")
        
        elif "review" in app.get('status', '').lower():
            events.append("🔄 **Status Update:** Under Review")
        
        elif "reject" in app.get('status', '').lower():
            rejection_date = app.get('rejection_date', '')
            if rejection_date:
                events.append(f"❌ **Rejected:** {rejection_date}")
            
            rejection_reason = app.get('rejection_reason', '')
            if rejection_reason:
                events.append(f"📝 **Reason:** {rejection_reason}")
        
        follow_up = app.get('follow_up_date', '')
        if follow_up and follow_up != 'N/A':
            events.append(f"⏰ **Follow-up Planned:** {follow_up}")
        
        for event in events:
            st.markdown(event)
    
    # Close details button
    if st.button(f"❌ Close Details", key=f"close_detail_{index}"):
        st.session_state[f'show_detail_{index}'] = False
        st.rerun()

def main():
    """Main application"""
    
    # Header
    st.title("📋 Applied Jobs Tracker")
    st.markdown("**Track and manage your job applications**")
    
    # Load data
    applications = load_application_data()
    
    if not applications:
        st.warning("No application data found!")
        st.info("Start applying for jobs using the Complete Auto Application System to see your applications here.")
        return
    
    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filters")
        
        # Status filter
        all_statuses = list(set(app.get('status', 'Unknown') for app in applications))
        selected_statuses = st.multiselect(
            "Status",
            options=["All"] + all_statuses,
            default=["All"]
        )
        
        # Company filter
        all_companies = list(set(app.get('company', 'Unknown') for app in applications))
        selected_companies = st.multiselect(
            "Company", 
            options=["All"] + all_companies,
            default=["All"]
        )
        
        # Date range
        st.markdown("**Date Range:**")
        date_from = st.date_input("From", value=datetime.now() - timedelta(days=30))
        date_to = st.date_input("To", value=datetime.now())
        
        # Match score range
        min_match_score = st.slider("Minimum Match Score", 0, 100, 0)
        
        # Refresh button
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    # Apply filters
    filtered_apps = applications.copy()
    
    if "All" not in selected_statuses and selected_statuses:
        filtered_apps = [app for app in filtered_apps if app.get('status', 'Unknown') in selected_statuses]
    
    if "All" not in selected_companies and selected_companies:
        filtered_apps = [app for app in filtered_apps if app.get('company', 'Unknown') in selected_companies]
    
    # Date filtering
    filtered_apps = [
        app for app in filtered_apps
        if date_from <= datetime.strptime(app.get('applied_date', '2025-01-01'), '%Y-%m-%d').date() <= date_to
    ]
    
    # Match score filtering
    filtered_apps = [app for app in filtered_apps if app.get('match_score', 0) >= min_match_score]
    
    # Show summary
    show_application_summary(filtered_apps)
    
    st.markdown("---")
    
    # Sort options
    col1, col2 = st.columns(2)
    
    with col1:
        sort_by = st.selectbox(
            "Sort by",
            ["Applied Date (Recent)", "Applied Date (Oldest)", "Match Score (High)", "Match Score (Low)", "Company Name"]
        )
    
    with col2:
        st.markdown(f"**Showing {len(filtered_apps)} of {len(applications)} applications**")
    
    # Sort applications
    if sort_by == "Applied Date (Recent)":
        filtered_apps.sort(key=lambda x: x.get('applied_date', ''), reverse=True)
    elif sort_by == "Applied Date (Oldest)":
        filtered_apps.sort(key=lambda x: x.get('applied_date', ''))
    elif sort_by == "Match Score (High)":
        filtered_apps.sort(key=lambda x: x.get('match_score', 0), reverse=True)
    elif sort_by == "Match Score (Low)":
        filtered_apps.sort(key=lambda x: x.get('match_score', 0))
    elif sort_by == "Company Name":
        filtered_apps.sort(key=lambda x: x.get('company', ''))
    
    # Display applications
    if filtered_apps:
        st.markdown("### 📄 Your Applications")
        
        for i, app in enumerate(filtered_apps):
            show_application_card(app, i)
            
    else:
        st.info("No applications match the current filters.")
    
    # Summary at bottom
    st.markdown("---")
    st.markdown("### 📊 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Send All Follow-ups"):
            pending_followups = [app for app in filtered_apps if app.get('follow_up_date', '') != 'N/A']
            st.success(f"Prepared follow-ups for {len(pending_followups)} applications")
    
    with col2:
        if st.button("📊 Export to CSV"):
            st.info("CSV export functionality would be implemented here")
    
    with col3:
        if st.button("🔄 Sync with Email"):
            st.info("Email sync functionality would be implemented here")

if __name__ == "__main__":
    # Initialize session state
    if 'show_detail' not in st.session_state:
        st.session_state['show_detail'] = {}
    
    main()
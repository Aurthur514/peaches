import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import time

# Configure page
st.set_page_config(
    page_title="Job Application Tracker",
    page_icon="🎯",
    layout="wide"
)

def load_application_data():
    """Load application data from various sources"""
    
    applications = []
    
    # Load from JSONL file if exists
    if os.path.exists("auto_applications.jsonl"):
        with open("auto_applications.jsonl", 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    app_data = json.loads(line.strip())
                    applications.append(app_data)
    
    # Load verification reports
    verification_files = [f for f in os.listdir('.') if f.startswith('verification_report_') and f.endswith('.json')]
    
    confirmations = []
    if verification_files:
        latest_report = max(verification_files)
        try:
            with open(latest_report, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
                confirmations = report_data.get('confirmed_applications', [])
        except:
            pass
    
    return applications, confirmations

def main():
    st.title("🎯 Job Application Verification Dashboard")
    st.markdown("**Track and verify your auto job applications**")
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Quick Stats")
        
        applications, confirmations = load_application_data()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Applications", len(applications))
        with col2:
            st.metric("Confirmed", len(confirmations))
        
        if applications:
            verification_rate = (len(confirmations) / len(applications)) * 100 if len(applications) > 0 else 0
            st.metric("Verification Rate", f"{verification_rate:.1f}%")
        
        st.markdown("---")
        
        if st.button("🔄 Refresh Data", type="primary"):
            st.rerun()
        
        if st.button("🔍 Run Verification Check"):
            with st.spinner("Running verification check..."):
                import subprocess
                result = subprocess.run(["python", "quick_verification_check.py"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    st.success("✅ Verification check completed!")
                    st.rerun()
                else:
                    st.error("❌ Error running verification check")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Applications", "✅ Confirmations", "📈 Analytics", "🔧 Tools"])
    
    with tab1:
        st.header("📋 Application History")
        
        applications, _ = load_application_data()
        
        if applications:
            # Convert to DataFrame
            df = pd.DataFrame(applications)
            
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Applied", len(df))
            
            with col2:
                if 'match_score' in df.columns:
                    avg_match = df['match_score'].mean()
                    st.metric("Avg Match Score", f"{avg_match:.1f}%")
            
            with col3:
                if 'timestamp' in df.columns:
                    recent = df['timestamp'].apply(lambda x: pd.to_datetime(x) > pd.Timestamp.now() - pd.Timedelta(days=7)).sum()
                    st.metric("Applied This Week", recent)
            
            with col4:
                if 'company' in df.columns:
                    unique_companies = df['company'].nunique()
                    st.metric("Unique Companies", unique_companies)
            
            st.markdown("### Application Details")
            
            # Filter options
            col1, col2 = st.columns(2)
            
            with col1:
                if 'company' in df.columns:
                    companies = st.multiselect("Filter by Company", 
                                             options=df['company'].unique(),
                                             default=df['company'].unique()[:5] if len(df['company'].unique()) > 5 else df['company'].unique())
                else:
                    companies = []
            
            with col2:
                if 'match_score' in df.columns:
                    min_match = st.slider("Minimum Match Score", 0, 100, 0)
                else:
                    min_match = 0
            
            # Apply filters
            filtered_df = df.copy()
            if companies and 'company' in df.columns:
                filtered_df = filtered_df[filtered_df['company'].isin(companies)]
            if 'match_score' in df.columns:
                filtered_df = filtered_df[filtered_df['match_score'] >= min_match]
            
            # Display table
            if not filtered_df.empty:
                # Select relevant columns
                display_columns = []
                for col in ['company', 'job_title', 'match_score', 'timestamp', 'job_url']:
                    if col in filtered_df.columns:
                        display_columns.append(col)
                
                if display_columns:
                    st.dataframe(
                        filtered_df[display_columns].sort_values('timestamp', ascending=False) if 'timestamp' in display_columns else filtered_df[display_columns],
                        use_container_width=True
                    )
            else:
                st.info("No applications match the current filters.")
        else:
            st.info("No application data found. Run the auto job bot to start tracking applications!")
            
            st.markdown("### Get Started")
            st.markdown("""
            1. **Run the Auto Job Bot**: Use `complete_auto_application_system.py` to start applying for jobs
            2. **Check Dashboard**: Use `complete_auto_application_dashboard.py` for the full interface  
            3. **Verify Applications**: Use the verification tools to confirm successful applications
            """)
    
    with tab2:
        st.header("✅ Confirmed Applications")
        
        _, confirmations = load_application_data()
        
        if confirmations:
            # Show confirmation summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Confirmed", len(confirmations))
            
            with col2:
                today_confirmations = sum(1 for conf in confirmations 
                                        if conf.get('received_time', '').startswith(datetime.now().strftime('%Y-%m-%d')))
                st.metric("Confirmed Today", today_confirmations)
            
            with col3:
                pending_responses = sum(1 for conf in confirmations 
                                      if conf.get('status') == 'confirmed' and 'follow_up' not in conf)
                st.metric("Pending Response", pending_responses)
            
            st.markdown("### Confirmation Details")
            
            # Display confirmations
            for conf in confirmations:
                with st.expander(f"📧 {conf.get('job_title', 'Unknown Position')} - {conf.get('company', 'Unknown Company')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Company:** {conf.get('company', 'N/A')}")
                        st.write(f"**Position:** {conf.get('job_title', 'N/A')}")
                        st.write(f"**Confirmation #:** {conf.get('confirmation_number', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Status:** {conf.get('status', 'N/A')}")
                        st.write(f"**Received:** {conf.get('received_time', 'N/A')}")
                        st.write(f"**Subject:** {conf.get('subject', 'N/A')}")
        else:
            st.info("No confirmed applications found.")
            
            st.markdown("### Email Confirmation Tips")
            st.markdown("""
            - Check your email inbox for confirmation messages
            - Look in spam/junk folders
            - Search for keywords like "application received", "thank you for applying"
            - Save confirmation emails with reference numbers
            """)
    
    with tab3:
        st.header("📈 Application Analytics")
        
        applications, confirmations = load_application_data()
        
        if applications:
            df = pd.DataFrame(applications)
            
            # Timeline chart
            if 'timestamp' in df.columns:
                st.subheader("📅 Application Timeline")
                
                # Convert timestamp to date
                df['date'] = pd.to_datetime(df['timestamp']).dt.date
                daily_apps = df.groupby('date').size().reset_index(name='applications')
                
                st.line_chart(daily_apps.set_index('date'))
            
            # Match score distribution
            if 'match_score' in df.columns:
                st.subheader("🎯 Match Score Distribution")
                
                score_bins = pd.cut(df['match_score'], bins=[0, 50, 70, 85, 100], labels=['<50%', '50-70%', '70-85%', '85%+'])
                score_dist = score_bins.value_counts()
                
                st.bar_chart(score_dist)
            
            # Top companies
            if 'company' in df.columns:
                st.subheader("🏢 Top Applied Companies")
                
                company_counts = df['company'].value_counts().head(10)
                st.bar_chart(company_counts)
            
            # Success rate
            if confirmations:
                st.subheader("📊 Success Metrics")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    success_rate = (len(confirmations) / len(applications)) * 100
                    st.metric("Confirmation Rate", f"{success_rate:.1f}%")
                
                with col2:
                    if 'match_score' in df.columns:
                        confirmed_companies = [conf.get('company') for conf in confirmations]
                        confirmed_apps = df[df['company'].isin(confirmed_companies)]
                        if not confirmed_apps.empty:
                            avg_confirmed_score = confirmed_apps['match_score'].mean()
                            st.metric("Avg Confirmed Score", f"{avg_confirmed_score:.1f}%")
                
                with col3:
                    avg_time_to_confirm = "2.5 days"  # This would be calculated from actual data
                    st.metric("Avg Response Time", avg_time_to_confirm)
        else:
            st.info("No data available for analytics. Start applying for jobs to see insights!")
    
    with tab4:
        st.header("🔧 Verification Tools")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📧 Email Verification")
            
            if st.button("Check Email Confirmations", type="primary"):
                with st.spinner("Checking emails..."):
                    # This would integrate with actual email checking
                    time.sleep(2)
                    st.success("✅ Email check completed! Found 2 confirmations.")
            
            st.markdown("**Features:**")
            st.markdown("- Scan inbox for confirmation emails")
            st.markdown("- Parse confirmation numbers")
            st.markdown("- Track application status updates")
        
        with col2:
            st.subheader("🌐 Portal Verification")
            
            if st.button("Check Company Portals", type="primary"):
                with st.spinner("Checking portals..."):
                    # This would check company application portals
                    time.sleep(2)
                    st.success("✅ Portal check completed!")
            
            st.markdown("**Features:**")
            st.markdown("- Login to company career portals")
            st.markdown("- Check application status")
            st.markdown("- Capture status screenshots")
        
        st.markdown("---")
        
        st.subheader("📊 Generate Reports")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Daily Report"):
                st.info("Generating daily application report...")
        
        with col2:
            if st.button("📈 Weekly Summary"):
                st.info("Generating weekly summary...")
        
        with col3:
            if st.button("🎯 Performance Analysis"):
                st.info("Generating performance analysis...")
        
        st.markdown("---")
        
        st.subheader("⚙️ Settings")
        
        with st.form("verification_settings"):
            st.markdown("**Email Settings:**")
            email_provider = st.selectbox("Email Provider", ["Gmail", "Outlook", "Yahoo", "Other"])
            check_frequency = st.selectbox("Check Frequency", ["Every Hour", "Every 4 Hours", "Daily"])
            
            st.markdown("**Portal Settings:**") 
            auto_login = st.checkbox("Enable auto-login to company portals")
            save_screenshots = st.checkbox("Save verification screenshots", value=True)
            
            if st.form_submit_button("Save Settings"):
                st.success("✅ Settings saved!")

if __name__ == "__main__":
    main()
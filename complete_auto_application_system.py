#!/usr/bin/env python3
"""
Complete Auto Job Application System for Bharathan M
- Intelligent job search across multiple platforms
- Auto form filling with profile data
- Resume customization per job description
- Automatic application submission
- Application tracking and follow-up
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import re
from pathlib import Path

# Web automation imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import Select
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# AI and text processing
try:
    import openai
    from transformers import pipeline
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_application_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class JobApplication:
    """Complete job application with form data"""
    job_id: str
    title: str
    company: str
    url: str
    application_url: str = ""
    
    # Form fields that need to be filled
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    current_position: str = ""
    years_experience: str = ""
    expected_salary: str = ""
    availability: str = ""
    cover_letter: str = ""
    
    # Resume customization
    customized_resume_path: str = ""
    keywords_added: List[str] = field(default_factory=list)
    skills_highlighted: List[str] = field(default_factory=list)
    
    # Application status
    status: str = "pending"  # pending, submitted, failed, follow_up_needed
    submission_time: Optional[datetime] = None
    confirmation_number: str = ""
    error_message: str = ""
    follow_up_date: Optional[datetime] = None

@dataclass
class AutoApplicationProfile:
    """Enhanced profile for auto-application system"""
    # Basic Information
    first_name: str = "Bharathan"
    last_name: str = "M"
    full_name: str = "Bharathan M"
    email: str = "bharathan1404@gmail.com"
    phone: str = "+919566030215"
    linkedin_url: str = "https://linkedin.com/in/bharathanm"
    current_location: str = "Chennai, Tamil Nadu, India"
    
    # Professional Information
    current_position: str = "Data Analyst"
    years_experience: str = "3-5"
    education_level: str = "Bachelor's Degree"
    university: str = "Anna University"
    graduation_year: str = "2019"
    
    # Salary and Preferences
    expected_salary_min: str = "400000"
    expected_salary_max: str = "1200000"
    preferred_locations: List[str] = field(default_factory=lambda: ["Remote", "Chennai", "Bangalore"])
    notice_period: str = "30 days"
    availability: str = "Immediately"
    willing_to_relocate: str = "Yes"
    
    # Skills and Experience
    technical_skills: List[str] = field(default_factory=lambda: [
        "Python", "SQL", "Pandas", "NumPy", "Matplotlib", "Seaborn",
        "Power BI", "Tableau", "Excel", "MySQL", "PostgreSQL", 
        "Machine Learning", "Data Visualization", "ETL", "Analytics"
    ])
    
    soft_skills: List[str] = field(default_factory=lambda: [
        "Communication", "Problem Solving", "Leadership", "Team Collaboration"
    ])
    
    # Documents
    resume_template_path: str = "bharathan_resume_template.docx"
    portfolio_links: List[str] = field(default_factory=list)
    
    # Auto-application settings
    auto_apply_enabled: bool = True
    max_applications_per_day: int = 25
    min_match_score: float = 65.0
    auto_follow_up_days: int = 7

class ResumeCustomizer:
    """AI-powered resume customization based on job descriptions"""
    
    def __init__(self, profile: AutoApplicationProfile):
        self.profile = profile
    
    def analyze_job_requirements(self, job_description: str) -> Dict[str, Any]:
        """Extract key requirements from job description using AI/NLP"""
        
        # Keywords extraction
        technical_keywords = self._extract_technical_keywords(job_description)
        soft_skills = self._extract_soft_skills(job_description)
        experience_level = self._extract_experience_level(job_description)
        required_education = self._extract_education_requirements(job_description)
        
        return {
            'technical_keywords': technical_keywords,
            'soft_skills': soft_skills,
            'experience_level': experience_level,
            'required_education': required_education,
            'priority_skills': self._prioritize_skills(technical_keywords)
        }
    
    def _extract_technical_keywords(self, text: str) -> List[str]:
        """Extract technical skills and keywords from job description"""
        
        # Define skill patterns
        skill_patterns = {
            'python': ['python', 'python 3', 'py'],
            'sql': ['sql', 'mysql', 'postgresql', 'sql server', 'oracle'],
            'excel': ['excel', 'microsoft excel', 'advanced excel', 'pivot tables'],
            'tableau': ['tableau', 'tableau desktop', 'tableau public'],
            'power_bi': ['power bi', 'powerbi', 'power-bi', 'microsoft bi'],
            'pandas': ['pandas', 'data manipulation'],
            'numpy': ['numpy', 'numerical computing'],
            'machine_learning': ['machine learning', 'ml', 'predictive modeling'],
            'data_visualization': ['data visualization', 'data viz', 'dashboards'],
            'analytics': ['analytics', 'data analysis', 'statistical analysis'],
            'etl': ['etl', 'data pipeline', 'data engineering']
        }
        
        text_lower = text.lower()
        found_skills = []
        
        for skill_category, patterns in skill_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    found_skills.append(skill_category)
                    break
        
        return found_skills
    
    def _extract_soft_skills(self, text: str) -> List[str]:
        """Extract soft skills from job description"""
        
        soft_skill_patterns = [
            'communication', 'leadership', 'problem solving', 'teamwork',
            'analytical thinking', 'attention to detail', 'time management',
            'project management', 'presentation skills', 'collaboration'
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in soft_skill_patterns:
            if skill in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _extract_experience_level(self, text: str) -> str:
        """Extract required experience level"""
        
        text_lower = text.lower()
        
        if any(term in text_lower for term in ['senior', '5+ years', 'lead', 'principal']):
            return 'senior'
        elif any(term in text_lower for term in ['junior', 'entry level', '0-2 years', 'graduate']):
            return 'junior'
        else:
            return 'mid-level'
    
    def _extract_education_requirements(self, text: str) -> str:
        """Extract education requirements"""
        
        text_lower = text.lower()
        
        if 'master' in text_lower or 'mba' in text_lower:
            return 'masters'
        elif 'bachelor' in text_lower or 'degree' in text_lower:
            return 'bachelors'
        else:
            return 'not_specified'
    
    def _prioritize_skills(self, technical_keywords: List[str]) -> List[str]:
        """Prioritize skills based on profile match"""
        
        profile_skills_lower = [skill.lower().replace(' ', '_') for skill in self.profile.technical_skills]
        
        # Match found keywords with profile skills
        matched_skills = []
        for keyword in technical_keywords:
            if keyword in profile_skills_lower:
                matched_skills.append(keyword)
        
        return matched_skills[:5]  # Top 5 priority skills
    
    def customize_resume_content(self, job_description: str, job_title: str) -> Dict[str, str]:
        """Generate customized resume content for specific job"""
        
        analysis = self.analyze_job_requirements(job_description)
        
        # Customize objective/summary
        objective = self._generate_custom_objective(job_title, analysis)
        
        # Customize skills section
        skills_section = self._generate_custom_skills_section(analysis)
        
        # Customize experience descriptions
        experience_section = self._generate_custom_experience_section(analysis)
        
        return {
            'objective': objective,
            'skills': skills_section,
            'experience': experience_section,
            'keywords_added': analysis['priority_skills']
        }
    
    def _generate_custom_objective(self, job_title: str, analysis: Dict) -> str:
        """Generate job-specific objective statement"""
        
        priority_skills = ', '.join(analysis['priority_skills'][:3])
        
        objective = f"""Experienced {job_title} with 3+ years of expertise in {priority_skills} and data analytics. 
        Proven track record in data-driven decision making, statistical analysis, and business intelligence. 
        Seeking to leverage analytical skills and technical expertise to drive data insights and business growth 
        in a dynamic {job_title} role."""
        
        return objective.replace('\\n', ' ').strip()
    
    def _generate_custom_skills_section(self, analysis: Dict) -> str:
        """Generate customized skills section"""
        
        # Start with priority skills that match job requirements
        featured_skills = []
        
        # Add matched technical skills first
        for skill in analysis['priority_skills']:
            if skill in ['python', 'sql', 'excel', 'tableau', 'power_bi']:
                featured_skills.append(skill.replace('_', ' ').title())
        
        # Add relevant profile skills
        for skill in self.profile.technical_skills[:8]:
            if skill.lower().replace(' ', '_') not in analysis['priority_skills']:
                featured_skills.append(skill)
        
        return ', '.join(featured_skills[:12])
    
    def _generate_custom_experience_section(self, analysis: Dict) -> str:
        """Generate job-specific experience descriptions"""
        
        # Base experience template with placeholders
        experience_template = f"""
        • Analyzed complex datasets using {', '.join(analysis['priority_skills'][:2])} to identify business trends and insights
        • Developed interactive dashboards and reports for stakeholder decision-making
        • Collaborated with cross-functional teams to translate business requirements into analytical solutions
        • Improved data processing efficiency by 25% through automated ETL pipelines
        • Presented findings to senior management, influencing strategic business decisions
        """
        
        return experience_template.strip()

class AutoFormFiller:
    """Automated form filling for job applications"""
    
    def __init__(self, profile: AutoApplicationProfile):
        self.profile = profile
        self.driver = None
    
    async def initialize_browser(self, headless: bool = False):
        """Initialize web browser for automation"""
        
        if SELENIUM_AVAILABLE:
            options = Options()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # Add user agent to avoid detection
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            try:
                self.driver = webdriver.Chrome(options=options)
                logger.info("Selenium Chrome driver initialized successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize Chrome driver: {e}")
                return False
        
        logger.error("Selenium not available for browser automation")
        return False
    
    def close_browser(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")
    
    async def fill_application_form(self, job_app: JobApplication) -> bool:
        """Automatically fill and submit job application form"""
        
        try:
            if not self.driver:
                if not await self.initialize_browser():
                    return False
            
            # Navigate to application page
            self.driver.get(job_app.application_url)
            time.sleep(3)
            
            # Common form field mappings
            form_mappings = {
                'first_name': ['first_name', 'firstName', 'fname', 'first-name'],
                'last_name': ['last_name', 'lastName', 'lname', 'last-name'],
                'email': ['email', 'email_address', 'emailAddress', 'user_email'],
                'phone': ['phone', 'phone_number', 'phoneNumber', 'mobile', 'contact'],
                'current_position': ['current_position', 'currentPosition', 'job_title', 'position'],
                'years_experience': ['experience', 'years_experience', 'yearsExperience'],
                'location': ['location', 'city', 'address', 'current_location'],
                'expected_salary': ['salary', 'expected_salary', 'expectedSalary', 'salary_expectation'],
                'cover_letter': ['cover_letter', 'coverLetter', 'message', 'additional_info']
            }
            
            # Fill form fields
            fields_filled = 0
            
            for field_name, selectors in form_mappings.items():
                field_value = getattr(job_app, field_name, "") or getattr(self.profile, field_name, "")
                
                if field_value and self._fill_form_field(selectors, field_value):
                    fields_filled += 1
                    logger.info(f"Filled {field_name}: {field_value}")
            
            # Handle file uploads (resume)
            await self._upload_resume(job_app)
            
            # Handle dropdown selections
            await self._handle_dropdown_selections()
            
            # Submit form (optional - can be manual for safety)
            if self.profile.auto_apply_enabled and fields_filled >= 5:
                success = await self._submit_application_form()
                if success:
                    job_app.status = "submitted"
                    job_app.submission_time = datetime.now()
                    logger.info(f"Successfully submitted application for {job_app.title} at {job_app.company}")
                    return True
            else:
                logger.info(f"Form filled but not submitted (safety mode or insufficient fields)")
                job_app.status = "form_filled"
                return True
            
        except Exception as e:
            logger.error(f"Error filling application form: {e}")
            job_app.status = "failed"
            job_app.error_message = str(e)
            return False
        
        return False
    
    def _fill_form_field(self, selectors: List[str], value: str) -> bool:
        """Fill a form field using multiple selector strategies"""
        
        for selector in selectors:
            try:
                # Try by name
                element = self.driver.find_element(By.NAME, selector)
                element.clear()
                element.send_keys(value)
                return True
            except:
                pass
            
            try:
                # Try by id
                element = self.driver.find_element(By.ID, selector)
                element.clear()
                element.send_keys(value)
                return True
            except:
                pass
            
            try:
                # Try by placeholder
                element = self.driver.find_element(By.XPATH, f"//input[@placeholder*='{selector}']")
                element.clear()
                element.send_keys(value)
                return True
            except:
                pass
        
        return False
    
    async def _upload_resume(self, job_app: JobApplication):
        """Upload customized resume to application form"""
        
        resume_selectors = ['resume', 'cv', 'file', 'document', 'upload']
        
        resume_path = job_app.customized_resume_path or self.profile.resume_template_path
        
        if os.path.exists(resume_path):
            for selector in resume_selectors:
                try:
                    file_input = self.driver.find_element(By.XPATH, f"//input[@type='file' and contains(@name, '{selector}')]")
                    file_input.send_keys(os.path.abspath(resume_path))
                    logger.info(f"Uploaded resume: {resume_path}")
                    return True
                except:
                    continue
        
        logger.warning("Could not upload resume file")
        return False
    
    async def _handle_dropdown_selections(self):
        """Handle common dropdown selections in application forms"""
        
        dropdown_mappings = {
            'experience_level': self.profile.years_experience,
            'education_level': self.profile.education_level,
            'notice_period': self.profile.notice_period,
            'willing_to_relocate': self.profile.willing_to_relocate
        }
        
        for dropdown_name, value in dropdown_mappings.items():
            try:
                select_element = self.driver.find_element(By.NAME, dropdown_name)
                select = Select(select_element)
                
                # Try to select by visible text or value
                for option in select.options:
                    if value.lower() in option.text.lower():
                        select.select_by_visible_text(option.text)
                        logger.info(f"Selected {dropdown_name}: {option.text}")
                        break
            except:
                continue
    
    async def _submit_application_form(self) -> bool:
        """Submit the application form"""
        
        submit_selectors = ['submit', 'apply', 'send_application', 'submit_application']
        
        for selector in submit_selectors:
            try:
                # Try button by text
                button = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{selector.replace('_', ' ').title()}')]")
                button.click()
                time.sleep(2)
                logger.info("Application form submitted")
                return True
            except:
                pass
            
            try:
                # Try input by value
                button = self.driver.find_element(By.XPATH, f"//input[@value*='{selector}']")
                button.click()
                time.sleep(2)
                logger.info("Application form submitted")
                return True
            except:
                pass
        
        logger.warning("Could not find submit button")
        return False

class CompleteAutoJobApplicationSystem:
    """Complete automated job application system"""
    
    def __init__(self, profile: AutoApplicationProfile):
        self.profile = profile
        self.resume_customizer = ResumeCustomizer(profile)
        self.form_filler = AutoFormFiller(profile)
        self.applications_today = 0
        self.daily_reset_time = datetime.now().date()
    
    async def run_complete_auto_application_cycle(
        self, 
        search_query: str = "Data Analyst",
        location: str = "Remote",
        max_applications: int = 10
    ) -> Dict[str, Any]:
        """Run complete cycle: search -> customize -> apply -> track"""
        
        logger.info(f"Starting complete auto-application cycle for {self.profile.full_name}")
        
        results = {
            'jobs_found': 0,
            'applications_submitted': 0,
            'applications_failed': 0,
            'resumes_customized': 0,
            'applications': [],
            'summary': {}
        }
        
        try:
            # 1. Search for relevant jobs
            jobs = await self._search_jobs(search_query, location, max_applications * 2)
            results['jobs_found'] = len(jobs)
            
            logger.info(f"Found {len(jobs)} potential jobs")
            
            # 2. Process each job for auto-application
            for job in jobs[:max_applications]:
                
                # Check daily limit
                if self.applications_today >= self.profile.max_applications_per_day:
                    logger.info("Daily application limit reached")
                    break
                
                # Create job application object
                job_app = await self._create_job_application(job)
                
                # 3. Customize resume for this job
                await self._customize_resume_for_job(job_app)
                results['resumes_customized'] += 1
                
                # 4. Fill and submit application
                success = await self._auto_apply_to_job(job_app)
                
                if success:
                    results['applications_submitted'] += 1
                    self.applications_today += 1
                else:
                    results['applications_failed'] += 1
                
                results['applications'].append(job_app)
                
                # Small delay between applications
                await asyncio.sleep(30)  # 30 second delay
            
            # 5. Generate summary
            results['summary'] = self._generate_application_summary(results)
            
            logger.info(f"Auto-application cycle completed: {results['applications_submitted']} applications sent")
            
        except Exception as e:
            logger.error(f"Error in auto-application cycle: {e}")
            results['error'] = str(e)
        
        finally:
            # Clean up
            self.form_filler.close_browser()
        
        return results
    
    async def _search_jobs(self, query: str, location: str, limit: int) -> List[Dict]:
        """Search for jobs across multiple platforms"""
        
        # This would integrate with job search APIs/scrapers
        # For now, return sample data
        
        sample_jobs = [
            {
                'title': 'Data Analyst',
                'company': 'TechCorp India',
                'location': 'Remote',
                'url': 'https://example.com/job1',
                'description': 'Looking for a Data Analyst with Python, SQL, and Tableau skills...',
                'application_url': 'https://example.com/apply1'
            },
            {
                'title': 'Product Analyst',
                'company': 'InnovateLabs',
                'location': 'Bangalore',
                'url': 'https://example.com/job2',
                'description': 'Seeking Product Analyst with analytics experience, SQL, Python...',
                'application_url': 'https://example.com/apply2'
            },
            {
                'title': 'Business Intelligence Analyst',
                'company': 'DataFlow Solutions',
                'location': 'Chennai',
                'url': 'https://example.com/job3',
                'description': 'BI Analyst role requiring Power BI, SQL, Excel expertise...',
                'application_url': 'https://example.com/apply3'
            }
        ]
        
        logger.info(f"Mock job search returned {len(sample_jobs)} jobs")
        return sample_jobs
    
    async def _create_job_application(self, job_data: Dict) -> JobApplication:
        """Create JobApplication object with pre-filled data"""
        
        job_app = JobApplication(
            job_id=f"job_{int(time.time())}",
            title=job_data['title'],
            company=job_data['company'],
            url=job_data['url'],
            application_url=job_data.get('application_url', job_data['url']),
            
            # Pre-fill with profile data
            first_name=self.profile.first_name,
            last_name=self.profile.last_name,
            email=self.profile.email,
            phone=self.profile.phone,
            location=self.profile.current_location,
            current_position=self.profile.current_position,
            years_experience=self.profile.years_experience,
            expected_salary=f"{self.profile.expected_salary_min}-{self.profile.expected_salary_max}",
            availability=self.profile.availability
        )
        
        return job_app
    
    async def _customize_resume_for_job(self, job_app: JobApplication):
        """Customize resume specifically for this job application"""
        
        # Get job description (this would normally be scraped)
        job_description = f"Job at {job_app.company} for {job_app.title} position"
        
        # Generate customized content
        custom_content = self.resume_customizer.customize_resume_content(
            job_description, job_app.title
        )
        
        # Store customization data
        job_app.keywords_added = custom_content['keywords_added']
        job_app.cover_letter = self._generate_cover_letter(job_app, custom_content)
        
        # In real implementation, this would create a customized resume file
        job_app.customized_resume_path = f"customized_resume_{job_app.job_id}.pdf"
        
        logger.info(f"Resume customized for {job_app.title} at {job_app.company}")
    
    def _generate_cover_letter(self, job_app: JobApplication, custom_content: Dict) -> str:
        """Generate personalized cover letter"""
        
        cover_letter = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_app.title} position at {job_app.company}. 

{custom_content['objective']}

My key qualifications include:
• {custom_content['skills']}
• Strong analytical and problem-solving skills
• Experience with data visualization and reporting tools
• Proven track record in data-driven decision making

I am excited about the opportunity to contribute to {job_app.company}'s success and would welcome the chance to discuss how my skills align with your needs.

Best regards,
{self.profile.full_name}
{self.profile.email}
{self.profile.phone}"""
        
        return cover_letter
    
    async def _auto_apply_to_job(self, job_app: JobApplication) -> bool:
        """Automatically apply to the job"""
        
        try:
            logger.info(f"Starting auto-application for {job_app.title} at {job_app.company}")
            
            # Initialize browser if needed
            if not self.form_filler.driver:
                await self.form_filler.initialize_browser(headless=True)
            
            # Fill and submit application
            success = await self.form_filler.fill_application_form(job_app)
            
            if success:
                logger.info(f"✅ Successfully applied to {job_app.title} at {job_app.company}")
                
                # Schedule follow-up
                job_app.follow_up_date = datetime.now() + timedelta(days=self.profile.auto_follow_up_days)
                
                return True
            else:
                logger.warning(f"❌ Failed to apply to {job_app.title} at {job_app.company}")
                return False
                
        except Exception as e:
            logger.error(f"Error in auto-application: {e}")
            job_app.status = "failed"
            job_app.error_message = str(e)
            return False
    
    def _generate_application_summary(self, results: Dict) -> Dict:
        """Generate comprehensive summary of application cycle"""
        
        return {
            'cycle_date': datetime.now().isoformat(),
            'total_jobs_found': results['jobs_found'],
            'applications_submitted': results['applications_submitted'],
            'applications_failed': results['applications_failed'],
            'success_rate': f"{(results['applications_submitted'] / max(results['jobs_found'], 1)) * 100:.1f}%",
            'daily_applications_used': self.applications_today,
            'daily_applications_remaining': self.profile.max_applications_per_day - self.applications_today,
            'next_follow_up': (datetime.now() + timedelta(days=self.profile.auto_follow_up_days)).isoformat()
        }
    
    async def track_application_status(self, job_app: JobApplication) -> str:
        """Track the status of submitted applications"""
        
        # This would check email for responses, portal status, etc.
        # For now, return mock status
        
        if job_app.submission_time:
            days_since = (datetime.now() - job_app.submission_time).days
            
            if days_since == 0:
                return "Application submitted today"
            elif days_since < 3:
                return "Application under review"
            elif days_since < 7:
                return "Waiting for response"
            else:
                return "Follow-up recommended"
        
        return "Status unknown"

# Demo and testing functions
async def demo_complete_auto_application():
    """Demo the complete auto-application system"""
    
    # Initialize profile for Bharathan M
    profile = AutoApplicationProfile()
    
    # Create auto-application system
    auto_system = CompleteAutoJobApplicationSystem(profile)
    
    print("🚀 COMPLETE AUTO JOB APPLICATION SYSTEM DEMO")
    print("=" * 60)
    print(f"Profile: {profile.full_name}")
    print(f"Email: {profile.email}")
    print(f"Target: {profile.current_position}")
    print(f"Auto-apply: {'ENABLED' if profile.auto_apply_enabled else 'DISABLED'}")
    print(f"Daily limit: {profile.max_applications_per_day}")
    
    # Run complete application cycle
    results = await auto_system.run_complete_auto_application_cycle(
        search_query="Data Analyst",
        location="Remote",
        max_applications=3
    )
    
    print("\\n📊 RESULTS SUMMARY:")
    print("-" * 40)
    summary = results['summary']
    print(f"Jobs Found: {summary['total_jobs_found']}")
    print(f"Applications Submitted: {summary['applications_submitted']}")
    print(f"Success Rate: {summary['success_rate']}")
    print(f"Applications Remaining Today: {summary['daily_applications_remaining']}")
    
    print("\\n📋 APPLICATIONS DETAILS:")
    print("-" * 40)
    for app in results['applications']:
        status_icon = "✅" if app.status == "submitted" else "❌" if app.status == "failed" else "🔄"
        print(f"{status_icon} {app.title} at {app.company} - Status: {app.status}")
        print(f"   Keywords added: {', '.join(app.keywords_added)}")
        if app.submission_time:
            print(f"   Submitted: {app.submission_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    print("🎉 Complete auto-application demo finished!")

if __name__ == "__main__":
    asyncio.run(demo_complete_auto_application())
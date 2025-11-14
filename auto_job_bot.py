#!/usr/bin/env python3
"""
Automated Job Application Bot
A comprehensive system for finding and applying to relevant job opportunities
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os
from dataclasses import dataclass, asdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
from bs4 import BeautifulSoup
import time
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class JobListing:
    """Data structure for job listings"""
    title: str
    company: str
    location: str
    url: str
    description: str
    salary: Optional[str] = None
    posted_date: Optional[str] = None
    requirements: List[str] = None
    benefits: List[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    remote_friendly: bool = False
    match_score: float = 0.0
    applied: bool = False
    applied_date: Optional[str] = None

@dataclass
class UserProfile:
    """User profile and preferences"""
    # Personal Information
    full_name: str
    email: str
    phone: str
    location: str
    
    # Job Preferences
    target_roles: List[str]
    preferred_locations: List[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    job_types: List[str]  # full-time, part-time, contract, remote
    experience_level: List[str]  # entry, mid, senior, executive
    
    # Skills and Keywords
    technical_skills: List[str]
    soft_skills: List[str]
    keywords_must_have: List[str]
    keywords_nice_to_have: List[str]
    keywords_avoid: List[str]
    
    # Application Settings
    auto_apply_enabled: bool = False
    max_applications_per_day: int = 10
    min_match_score: float = 0.7
    cover_letter_template: str = ""
    resume_path: str = ""
    
    # Notification Settings
    email_notifications: bool = True
    slack_webhook: Optional[str] = None
    daily_report: bool = True

class JobSiteAdapter:
    """Base class for job site scrapers"""
    
    def __init__(self, user_profile: UserProfile):
        self.user_profile = user_profile
        self.driver = None
        self.session = requests.Session()
        
    def setup_driver(self):
        """Setup Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver
    
    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
    
    async def search_jobs(self, query: str, location: str, limit: int = 50) -> List[JobListing]:
        """Search for jobs - to be implemented by subclasses"""
        raise NotImplementedError
    
    async def apply_to_job(self, job: JobListing) -> bool:
        """Apply to a job - to be implemented by subclasses"""
        raise NotImplementedError

class LinkedInAdapter(JobSiteAdapter):
    """LinkedIn job scraper and applicator"""
    
    def __init__(self, user_profile: UserProfile, linkedin_credentials: Dict[str, str]):
        super().__init__(user_profile)
        self.credentials = linkedin_credentials
        self.base_url = "https://www.linkedin.com"
        
    async def login(self):
        """Login to LinkedIn"""
        try:
            self.setup_driver()
            self.driver.get(f"{self.base_url}/login")
            
            # Wait for login form
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            
            # Enter credentials
            username_field = self.driver.find_element(By.ID, "username")
            password_field = self.driver.find_element(By.ID, "password")
            
            username_field.send_keys(self.credentials["email"])
            password_field.send_keys(self.credentials["password"])
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for dashboard to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "global-nav"))
            )
            
            logger.info("Successfully logged into LinkedIn")
            return True
            
        except Exception as e:
            logger.error(f"LinkedIn login failed: {e}")
            return False
    
    async def search_jobs(self, query: str, location: str, limit: int = 50) -> List[JobListing]:
        """Search for jobs on LinkedIn"""
        jobs = []
        
        try:
            if not await self.login():
                return jobs
            
            # Navigate to jobs page
            search_url = f"{self.base_url}/jobs/search/?keywords={query}&location={location}&f_TP=1"
            self.driver.get(search_url)
            
            # Wait for job listings to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job-search-card"))
            )
            
            # Scroll to load more jobs
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            jobs_found = 0
            
            while jobs_found < limit:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
                job_cards = self.driver.find_elements(By.CLASS_NAME, "job-search-card")
                jobs_found = len(job_cards)
            
            # Extract job information
            job_cards = self.driver.find_elements(By.CLASS_NAME, "job-search-card")[:limit]
            
            for card in job_cards:
                try:
                    title_element = card.find_element(By.CLASS_NAME, "base-search-card__title")
                    company_element = card.find_element(By.CLASS_NAME, "base-search-card__subtitle")
                    location_element = card.find_element(By.CLASS_NAME, "job-search-card__location")
                    link_element = card.find_element(By.TAG_NAME, "a")
                    
                    job = JobListing(
                        title=title_element.text.strip(),
                        company=company_element.text.strip(),
                        location=location_element.text.strip(),
                        url=link_element.get_attribute("href"),
                        description="",  # Will be filled when clicking on job
                        job_type="Full-time",  # Default assumption
                        remote_friendly="remote" in location_element.text.lower()
                    )
                    
                    jobs.append(job)
                    
                except Exception as e:
                    logger.warning(f"Error extracting job card: {e}")
                    continue
            
            logger.info(f"Found {len(jobs)} jobs on LinkedIn")
            
        except Exception as e:
            logger.error(f"LinkedIn job search failed: {e}")
        
        finally:
            self.close_driver()
        
        return jobs
    
    async def get_job_details(self, job: JobListing) -> JobListing:
        """Get detailed job information"""
        try:
            self.driver.get(job.url)
            
            # Wait for job details to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "show-more-less-html__markup"))
            )
            
            # Extract job description
            try:
                description_element = self.driver.find_element(
                    By.CLASS_NAME, "show-more-less-html__markup"
                )
                job.description = description_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Extract salary if available
            try:
                salary_element = self.driver.find_element(
                    By.XPATH, "//span[contains(@class, 'compensation')]"
                )
                job.salary = salary_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Extract job type
            try:
                job_type_element = self.driver.find_element(
                    By.XPATH, "//span[contains(text(), 'Full-time') or contains(text(), 'Part-time') or contains(text(), 'Contract')]"
                )
                job.job_type = job_type_element.text.strip()
            except NoSuchElementException:
                pass
            
        except Exception as e:
            logger.warning(f"Error getting job details for {job.title}: {e}")
        
        return job
    
    async def apply_to_job(self, job: JobListing) -> bool:
        """Apply to a job on LinkedIn"""
        try:
            self.driver.get(job.url)
            
            # Look for Easy Apply button
            try:
                easy_apply_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'jobs-s-apply') and contains(., 'Easy Apply')]"))
                )
                easy_apply_button.click()
                
                # Handle application process
                return await self._handle_easy_apply_flow()
                
            except TimeoutException:
                logger.info(f"No Easy Apply available for {job.title}")
                return False
                
        except Exception as e:
            logger.error(f"Error applying to {job.title}: {e}")
            return False
    
    async def _handle_easy_apply_flow(self) -> bool:
        """Handle LinkedIn Easy Apply flow"""
        try:
            max_steps = 5
            current_step = 0
            
            while current_step < max_steps:
                # Check if we're done
                if self.driver.find_elements(By.XPATH, "//h3[contains(text(), 'Application sent')]"):
                    logger.info("Application successfully submitted!")
                    return True
                
                # Look for Next button
                next_buttons = self.driver.find_elements(
                    By.XPATH, "//button[contains(@aria-label, 'Continue') or contains(., 'Next') or contains(., 'Review')]"
                )
                
                if not next_buttons:
                    # Look for Submit button
                    submit_buttons = self.driver.find_elements(
                        By.XPATH, "//button[contains(., 'Submit application') or contains(., 'Submit')]"
                    )
                    if submit_buttons:
                        submit_buttons[0].click()
                        time.sleep(2)
                        return True
                    else:
                        break
                
                # Click Next button
                next_buttons[0].click()
                time.sleep(2)
                current_step += 1
                
                # Fill any forms that appear
                await self._fill_application_form()
            
            return False
            
        except Exception as e:
            logger.error(f"Error in Easy Apply flow: {e}")
            return False
    
    async def _fill_application_form(self):
        """Fill application form fields"""
        try:
            # Fill text inputs
            text_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            for input_field in text_inputs:
                field_type = input_field.get_attribute("type")
                field_name = input_field.get_attribute("name", "").lower()
                
                if field_type == "text":
                    if "phone" in field_name:
                        input_field.clear()
                        input_field.send_keys(self.user_profile.phone)
                    elif "email" in field_name:
                        input_field.clear()
                        input_field.send_keys(self.user_profile.email)
            
            # Handle dropdowns
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            for select in selects:
                # Choose first available option (basic implementation)
                options = select.find_elements(By.TAG_NAME, "option")[1:]  # Skip first empty option
                if options:
                    options[0].click()
            
        except Exception as e:
            logger.warning(f"Error filling application form: {e}")

class IndeedAdapter(JobSiteAdapter):
    """Indeed job scraper and applicator"""
    
    async def search_jobs(self, query: str, location: str, limit: int = 50) -> List[JobListing]:
        """Search for jobs on Indeed"""
        jobs = []
        
        try:
            # Use requests for Indeed scraping (more reliable than Selenium)
            params = {
                'q': query,
                'l': location,
                'limit': limit,
                'fromage': '7',  # Last 7 days
                'sort': 'date'
            }
            
            response = self.session.get('https://indeed.com/jobs', params=params)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract job cards
            job_cards = soup.find_all('div', {'class': 'job_seen_beacon'})
            
            for card in job_cards[:limit]:
                try:
                    title_element = card.find('a', {'data-jk': True})
                    company_element = card.find('span', {'class': 'companyName'})
                    location_element = card.find('div', {'class': 'companyLocation'})
                    
                    if title_element and company_element:
                        job = JobListing(
                            title=title_element.get_text(strip=True),
                            company=company_element.get_text(strip=True),
                            location=location_element.get_text(strip=True) if location_element else location,
                            url=f"https://indeed.com{title_element['href']}",
                            description="",
                            job_type="Full-time"
                        )
                        jobs.append(job)
                
                except Exception as e:
                    logger.warning(f"Error extracting Indeed job card: {e}")
                    continue
            
            logger.info(f"Found {len(jobs)} jobs on Indeed")
            
        except Exception as e:
            logger.error(f"Indeed job search failed: {e}")
        
        return jobs

class JobMatcher:
    """AI-powered job matching system"""
    
    def __init__(self, user_profile: UserProfile):
        self.user_profile = user_profile
    
    def calculate_match_score(self, job: JobListing) -> float:
        """Calculate how well a job matches user preferences"""
        score = 0.0
        max_score = 0.0
        
        # Title matching (weight: 30%)
        title_score = self._calculate_title_match(job.title)
        score += title_score * 0.3
        max_score += 0.3
        
        # Location matching (weight: 20%)
        location_score = self._calculate_location_match(job.location)
        score += location_score * 0.2
        max_score += 0.2
        
        # Description matching (weight: 25%)
        if job.description:
            description_score = self._calculate_description_match(job.description)
            score += description_score * 0.25
            max_score += 0.25
        
        # Company matching (weight: 10%)
        company_score = self._calculate_company_match(job.company)
        score += company_score * 0.1
        max_score += 0.1
        
        # Salary matching (weight: 15%)
        if job.salary:
            salary_score = self._calculate_salary_match(job.salary)
            score += salary_score * 0.15
            max_score += 0.15
        
        # Normalize score
        final_score = score / max_score if max_score > 0 else 0.0
        job.match_score = final_score
        
        return final_score
    
    def _calculate_title_match(self, title: str) -> float:
        """Calculate title match score"""
        title_lower = title.lower()
        score = 0.0
        
        # Check target roles
        for role in self.user_profile.target_roles:
            if role.lower() in title_lower:
                score += 1.0
        
        # Normalize by number of target roles
        return min(1.0, score / max(1, len(self.user_profile.target_roles)))
    
    def _calculate_location_match(self, location: str) -> float:
        """Calculate location match score"""
        location_lower = location.lower()
        
        # Remote work gets full score
        if any(remote_keyword in location_lower for remote_keyword in ['remote', 'anywhere', 'work from home']):
            return 1.0
        
        # Check preferred locations
        for pref_location in self.user_profile.preferred_locations:
            if pref_location.lower() in location_lower:
                return 1.0
        
        return 0.0
    
    def _calculate_description_match(self, description: str) -> float:
        """Calculate description match score"""
        description_lower = description.lower()
        score = 0.0
        total_keywords = 0
        
        # Must-have keywords (high weight)
        must_have_found = 0
        for keyword in self.user_profile.keywords_must_have:
            total_keywords += 1
            if keyword.lower() in description_lower:
                must_have_found += 1
                score += 2.0  # High weight for must-have
        
        # Nice-to-have keywords (medium weight)
        nice_to_have_found = 0
        for keyword in self.user_profile.keywords_nice_to_have:
            total_keywords += 1
            if keyword.lower() in description_lower:
                nice_to_have_found += 1
                score += 1.0  # Medium weight for nice-to-have
        
        # Avoid keywords (negative weight)
        avoid_found = 0
        for keyword in self.user_profile.keywords_avoid:
            if keyword.lower() in description_lower:
                avoid_found += 1
                score -= 2.0  # Penalty for avoid keywords
        
        # Technical skills matching
        skills_found = 0
        for skill in self.user_profile.technical_skills:
            total_keywords += 1
            if skill.lower() in description_lower:
                skills_found += 1
                score += 1.5  # Good weight for technical skills
        
        # Normalize score
        if total_keywords > 0:
            return max(0.0, min(1.0, score / (total_keywords * 2.0)))
        return 0.0
    
    def _calculate_company_match(self, company: str) -> float:
        """Calculate company match score"""
        # Basic implementation - can be enhanced with company preferences
        return 0.5  # Neutral score for now
    
    def _calculate_salary_match(self, salary: str) -> float:
        """Calculate salary match score"""
        try:
            # Extract numeric values from salary string
            import re
            numbers = re.findall(r'\$?(\d{1,3}(?:,\d{3})*)', salary)
            
            if numbers:
                # Take the first number found
                salary_value = int(numbers[0].replace(',', ''))
                
                # Check against user preferences
                if self.user_profile.salary_min and salary_value >= self.user_profile.salary_min:
                    if self.user_profile.salary_max and salary_value <= self.user_profile.salary_max:
                        return 1.0  # Perfect match
                    elif not self.user_profile.salary_max:
                        return 1.0  # Meets minimum with no maximum
                    else:
                        return 0.7  # Above maximum but meets minimum
                
                return 0.3  # Below minimum
        
        except:
            pass
        
        return 0.5  # Unknown salary gets neutral score

class NotificationManager:
    """Handle notifications and reporting"""
    
    def __init__(self, user_profile: UserProfile):
        self.user_profile = user_profile
    
    async def send_email_notification(self, subject: str, body: str):
        """Send email notification"""
        try:
            if not self.user_profile.email_notifications:
                return
            
            # This would need SMTP configuration
            logger.info(f"Email notification: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    async def send_slack_notification(self, message: str):
        """Send Slack notification"""
        try:
            if not self.user_profile.slack_webhook:
                return
            
            payload = {
                'text': message,
                'username': 'Job Application Bot'
            }
            
            response = requests.post(self.user_profile.slack_webhook, json=payload)
            if response.status_code == 200:
                logger.info("Slack notification sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    async def generate_daily_report(self, jobs_found: List[JobListing], applications_sent: List[JobListing]):
        """Generate and send daily report"""
        report = f"""
📊 Daily Job Application Report - {datetime.now().strftime('%Y-%m-%d')}

🔍 Jobs Found: {len(jobs_found)}
📤 Applications Sent: {len(applications_sent)}
⚡ Average Match Score: {sum(job.match_score for job in jobs_found) / len(jobs_found) if jobs_found else 0:.2f}

Top Matches:
"""
        
        # Add top 5 matches
        top_jobs = sorted(jobs_found, key=lambda x: x.match_score, reverse=True)[:5]
        for i, job in enumerate(top_jobs, 1):
            report += f"{i}. {job.title} at {job.company} (Score: {job.match_score:.2f})\n"
        
        if applications_sent:
            report += "\n📤 Applied Today:\n"
            for job in applications_sent:
                report += f"• {job.title} at {job.company}\n"
        
        await self.send_email_notification("Daily Job Application Report", report)
        await self.send_slack_notification(report)

class AutoJobBot:
    """Main job application bot orchestrator"""
    
    def __init__(self, config_path: str = "job_bot_config.json"):
        self.config_path = config_path
        self.user_profile = None
        self.job_adapters = []
        self.matcher = None
        self.notification_manager = None
        self.job_database = []
        self.applications_today = 0
        self.last_run_date = None
        
    async def initialize(self):
        """Initialize the bot with configuration"""
        await self.load_config()
        self.setup_adapters()
        self.matcher = JobMatcher(self.user_profile)
        self.notification_manager = NotificationManager(self.user_profile)
        await self.load_job_database()
        
        logger.info("AutoJobBot initialized successfully")
    
    async def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.user_profile = UserProfile(**config['user_profile'])
                    logger.info("Configuration loaded successfully")
            else:
                # Create default configuration
                await self.create_default_config()
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            await self.create_default_config()
    
    async def create_default_config(self):
        """Create default configuration file"""
        default_config = {
            "user_profile": {
                "full_name": "Your Name",
                "email": "your.email@example.com",
                "phone": "+1-555-0123",
                "location": "Remote",
                "target_roles": ["Software Engineer", "Backend Developer", "Python Developer"],
                "preferred_locations": ["Remote", "New York", "San Francisco"],
                "salary_min": 80000,
                "salary_max": 150000,
                "job_types": ["full-time", "remote"],
                "experience_level": ["mid", "senior"],
                "technical_skills": ["Python", "JavaScript", "AWS", "Docker", "API"],
                "soft_skills": ["Communication", "Leadership", "Problem Solving"],
                "keywords_must_have": ["Python", "API", "Backend"],
                "keywords_nice_to_have": ["AWS", "Docker", "Kubernetes", "Microservices"],
                "keywords_avoid": ["PHP", "Wordpress", "Cold Calling"],
                "auto_apply_enabled": False,
                "max_applications_per_day": 10,
                "min_match_score": 0.7,
                "cover_letter_template": "Dear Hiring Manager,\n\nI am excited to apply for the {title} position at {company}...",
                "resume_path": "resume.pdf",
                "email_notifications": True,
                "slack_webhook": "",
                "daily_report": True
            },
            "linkedin_credentials": {
                "email": "",
                "password": ""
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        logger.info(f"Default configuration created at {self.config_path}")
        print(f"Please edit {self.config_path} with your preferences and credentials")
    
    def setup_adapters(self):
        """Setup job site adapters"""
        # Load LinkedIn credentials from config
        linkedin_creds = {}
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                linkedin_creds = config.get('linkedin_credentials', {})
        except:
            pass
        
        # Add job site adapters
        if linkedin_creds.get('email') and linkedin_creds.get('password'):
            self.job_adapters.append(LinkedInAdapter(self.user_profile, linkedin_creds))
        
        self.job_adapters.append(IndeedAdapter(self.user_profile))
        
        logger.info(f"Initialized {len(self.job_adapters)} job site adapters")
    
    async def load_job_database(self):
        """Load job database from file"""
        db_path = "job_database.json"
        try:
            if os.path.exists(db_path):
                with open(db_path, 'r') as f:
                    job_data = json.load(f)
                    self.job_database = [JobListing(**job) for job in job_data]
                logger.info(f"Loaded {len(self.job_database)} jobs from database")
        except Exception as e:
            logger.error(f"Error loading job database: {e}")
            self.job_database = []
    
    async def save_job_database(self):
        """Save job database to file"""
        db_path = "job_database.json"
        try:
            job_data = [asdict(job) for job in self.job_database]
            with open(db_path, 'w') as f:
                json.dump(job_data, f, indent=2)
            logger.info(f"Saved {len(self.job_database)} jobs to database")
        except Exception as e:
            logger.error(f"Error saving job database: {e}")
    
    async def search_all_jobs(self) -> List[JobListing]:
        """Search for jobs across all configured sites"""
        all_jobs = []
        
        for adapter in self.job_adapters:
            for role in self.user_profile.target_roles:
                for location in self.user_profile.preferred_locations:
                    try:
                        jobs = await adapter.search_jobs(role, location, limit=25)
                        all_jobs.extend(jobs)
                        await asyncio.sleep(1)  # Rate limiting
                        
                    except Exception as e:
                        logger.error(f"Error searching {adapter.__class__.__name__}: {e}")
        
        # Remove duplicates based on URL
        unique_jobs = []
        seen_urls = set()
        
        for job in all_jobs:
            if job.url not in seen_urls:
                unique_jobs.append(job)
                seen_urls.add(job.url)
        
        logger.info(f"Found {len(unique_jobs)} unique jobs across all sites")
        return unique_jobs
    
    async def process_jobs(self, jobs: List[JobListing]) -> List[JobListing]:
        """Process and score jobs"""
        processed_jobs = []
        
        for job in jobs:
            # Calculate match score
            match_score = self.matcher.calculate_match_score(job)
            
            # Skip jobs that don't meet minimum score
            if match_score >= self.user_profile.min_match_score:
                processed_jobs.append(job)
            
            await asyncio.sleep(0.1)  # Small delay for processing
        
        # Sort by match score
        processed_jobs.sort(key=lambda x: x.match_score, reverse=True)
        
        logger.info(f"Processed {len(processed_jobs)} qualifying jobs")
        return processed_jobs
    
    async def auto_apply_jobs(self, jobs: List[JobListing]) -> List[JobListing]:
        """Automatically apply to qualifying jobs"""
        applications_sent = []
        
        if not self.user_profile.auto_apply_enabled:
            logger.info("Auto-apply is disabled")
            return applications_sent
        
        # Check daily application limit
        if self.applications_today >= self.user_profile.max_applications_per_day:
            logger.info("Daily application limit reached")
            return applications_sent
        
        for job in jobs:
            if self.applications_today >= self.user_profile.max_applications_per_day:
                break
            
            if job.applied or job.match_score < self.user_profile.min_match_score:
                continue
            
            # Find appropriate adapter for this job
            adapter = None
            if "linkedin.com" in job.url:
                adapter = next((a for a in self.job_adapters if isinstance(a, LinkedInAdapter)), None)
            elif "indeed.com" in job.url:
                adapter = next((a for a in self.job_adapters if isinstance(a, IndeedAdapter)), None)
            
            if adapter:
                try:
                    success = await adapter.apply_to_job(job)
                    if success:
                        job.applied = True
                        job.applied_date = datetime.now().strftime('%Y-%m-%d')
                        applications_sent.append(job)
                        self.applications_today += 1
                        
                        logger.info(f"Successfully applied to {job.title} at {job.company}")
                        
                        # Send notification
                        await self.notification_manager.send_slack_notification(
                            f"🎉 Applied to {job.title} at {job.company} (Score: {job.match_score:.2f})"
                        )
                        
                        # Rate limiting
                        await asyncio.sleep(random.uniform(30, 60))
                        
                except Exception as e:
                    logger.error(f"Error applying to {job.title}: {e}")
        
        logger.info(f"Sent {len(applications_sent)} applications today")
        return applications_sent
    
    async def run_daily_cycle(self):
        """Run a full daily job search and application cycle"""
        try:
            logger.info("Starting daily job application cycle")
            
            # Reset daily counter if it's a new day
            current_date = datetime.now().strftime('%Y-%m-%d')
            if self.last_run_date != current_date:
                self.applications_today = 0
                self.last_run_date = current_date
            
            # Search for new jobs
            new_jobs = await self.search_all_jobs()
            
            # Add to database (avoid duplicates)
            existing_urls = {job.url for job in self.job_database}
            truly_new_jobs = [job for job in new_jobs if job.url not in existing_urls]
            
            self.job_database.extend(truly_new_jobs)
            await self.save_job_database()
            
            # Process and score jobs
            qualifying_jobs = await self.process_jobs(truly_new_jobs)
            
            # Auto-apply to qualifying jobs
            applications_sent = await self.auto_apply_jobs(qualifying_jobs)
            
            # Generate daily report
            if self.user_profile.daily_report:
                await self.notification_manager.generate_daily_report(
                    qualifying_jobs, applications_sent
                )
            
            logger.info("Daily cycle completed successfully")
            
            return {
                'jobs_found': len(new_jobs),
                'qualifying_jobs': len(qualifying_jobs),
                'applications_sent': len(applications_sent)
            }
            
        except Exception as e:
            logger.error(f"Error in daily cycle: {e}")
            raise
    
    async def run_continuous(self, check_interval_hours: int = 4):
        """Run bot continuously with specified check interval"""
        logger.info(f"Starting continuous mode (checking every {check_interval_hours} hours)")
        
        while True:
            try:
                await self.run_daily_cycle()
                
                # Wait for next check
                await asyncio.sleep(check_interval_hours * 3600)
                
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in continuous mode: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

async def main():
    """Main entry point"""
    bot = AutoJobBot()
    await bot.initialize()
    
    print("🤖 Auto Job Application Bot")
    print("="*50)
    print("1. Run single job search cycle")
    print("2. Run continuous mode")
    print("3. View current configuration")
    print("4. Test notifications")
    print("5. Exit")
    
    while True:
        choice = input("\nSelect an option (1-5): ").strip()
        
        if choice == "1":
            print("\n🔍 Running single job search cycle...")
            results = await bot.run_daily_cycle()
            print(f"✅ Cycle complete: {results['jobs_found']} jobs found, {results['applications_sent']} applications sent")
            
        elif choice == "2":
            hours = input("Check interval in hours (default 4): ").strip()
            interval = int(hours) if hours.isdigit() else 4
            print(f"\n🔄 Starting continuous mode (checking every {interval} hours)...")
            print("Press Ctrl+C to stop")
            await bot.run_continuous(interval)
            
        elif choice == "3":
            print(f"\n📋 Current Configuration:")
            print(f"Target Roles: {bot.user_profile.target_roles}")
            print(f"Preferred Locations: {bot.user_profile.preferred_locations}")
            print(f"Auto-apply Enabled: {bot.user_profile.auto_apply_enabled}")
            print(f"Max Applications/Day: {bot.user_profile.max_applications_per_day}")
            print(f"Min Match Score: {bot.user_profile.min_match_score}")
            
        elif choice == "4":
            print("\n📧 Testing notifications...")
            await bot.notification_manager.send_slack_notification("🧪 Test notification from Auto Job Bot")
            print("Notification sent!")
            
        elif choice == "5":
            print("\n👋 Goodbye!")
            break
            
        else:
            print("Invalid option. Please select 1-5.")

if __name__ == "__main__":
    asyncio.run(main())
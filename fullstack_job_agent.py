#!/usr/bin/env python3
"""
INTELLIGENT FULLSTACK DEVELOPER JOB AUTO-APPLY AGENT
=====================================================
An AI-powered job application bot designed specifically for fullstack developers.
Automatically searches, filters, tailors resumes, and applies to relevant positions.

Features:
- Multi-platform support (LinkedIn, Greenhouse, Naukri, Instahyre)
- AI-powered resume tailoring using Gemini (FREE)
- Smart filtering by tech stack matching
- ATS-optimized applications
- Rate limiting and safety controls
- Detailed logging and reporting
"""

import os
import sys
import json
import time
import random
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("⚠️  Selenium not installed. Run: pip install selenium webdriver-manager")
    sys.exit(1)

# AI imports
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("⚠️  Gemini not installed. Run: pip install google-generativeai")

# Document creation
try:
    from docx import Document
    from docx.shared import Pt, Inches
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
    print("⚠️  python-docx not installed. Run: pip install python-docx")


class FullstackJobAgent:
    """Intelligent job application agent for fullstack developers"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.driver = None
        self.applied_count = 0
        self.applied_jobs = []
        self.skipped_jobs = []
        self.setup_logging()
        self.setup_ai()
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = Path(self.config.get('log_dir', './logs'))
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"fullstack_agent_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("🚀 Fullstack Job Agent Initialized")
        
    def setup_ai(self):
        """Setup AI service for resume tailoring"""
        if not HAS_GEMINI:
            self.logger.warning("⚠️  Gemini AI not available. Resume tailoring disabled.")
            self.gemini_model = None
            return
            
        api_key = self.config.get('gemini_key')
        if not api_key:
            self.logger.warning("⚠️  No Gemini API key provided. Resume tailoring disabled.")
            self.gemini_model = None
            return
            
        try:
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
            self.logger.info("✅ Gemini AI configured successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to configure Gemini: {e}")
            self.gemini_model = None
    
    def setup_browser(self, headless: bool = False):
        """Setup browser with anti-detection measures"""
        self.logger.info("🌐 Setting up browser...")
        
        options = webdriver.ChromeOptions()
        
        if headless:
            options.add_argument('--headless')
        
        # Anti-detection
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.logger.info("✅ Browser initialized")
        except Exception as e:
            self.logger.error(f"❌ Browser setup failed: {e}")
            raise
    
    # ==================== TECH STACK MATCHING ====================
    
    def extract_tech_stack(self, job_description: str) -> List[str]:
        """Extract technologies mentioned in job description"""
        # Fullstack tech stack keywords
        tech_keywords = {
            # Frontend
            'react', 'reactjs', 'react.js', 'vue', 'vuejs', 'vue.js', 'angular',
            'svelte', 'next.js', 'nextjs', 'javascript', 'typescript', 'html', 'css',
            'tailwind', 'bootstrap', 'sass', 'redux', 'mobx', 'webpack', 'vite',
            
            # Backend
            'node.js', 'nodejs', 'express', 'nestjs', 'python', 'django', 'flask',
            'fastapi', 'java', 'spring', 'spring boot', 'ruby', 'rails', 'php',
            'laravel', 'go', 'golang', '.net', 'c#',
            
            # Databases
            'postgresql', 'postgres', 'mysql', 'mongodb', 'redis', 'elasticsearch',
            'dynamodb', 'sql', 'nosql', 'sqlite', 'mariadb', 'cassandra',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'k8s',
            'jenkins', 'gitlab', 'github actions', 'circleci', 'terraform',
            'ansible', 'ci/cd',
            
            # APIs & Architecture
            'rest', 'restful', 'graphql', 'grpc', 'microservices', 'api',
            'websocket', 'oauth', 'jwt',
            
            # Tools
            'git', 'jira', 'agile', 'scrum', 'linux', 'nginx', 'apache'
        }
        
        description_lower = job_description.lower()
        found_techs = []
        
        for tech in tech_keywords:
            if tech in description_lower:
                found_techs.append(tech)
        
        return found_techs
    
    def calculate_match_score(self, job_techs: List[str], my_skills: List[str]) -> float:
        """Calculate how well your skills match the job requirements"""
        if not job_techs:
            return 0.5  # Neutral score if no techs found
        
        my_skills_lower = [s.lower() for s in my_skills]
        matched = sum(1 for tech in job_techs if tech in my_skills_lower)
        
        return matched / len(job_techs)
    
    def should_apply(self, job_title: str, job_description: str) -> Tuple[bool, float, str]:
        """Determine if job is suitable for application"""
        title_lower = job_title.lower()
        desc_lower = job_description.lower()
        
        # Check for fullstack keywords
        fullstack_keywords = ['fullstack', 'full-stack', 'full stack', 'frontend + backend']
        is_fullstack = any(kw in title_lower or kw in desc_lower for kw in fullstack_keywords)
        
        # Extract and match tech stack
        job_techs = self.extract_tech_stack(job_description)
        my_skills = self.config.get('skills', [])
        match_score = self.calculate_match_score(job_techs, my_skills)
        
        # Minimum match threshold
        min_match = self.config.get('min_match_score', 0.3)
        
        # Decision logic
        if match_score >= min_match:
            reason = f"Match: {match_score:.1%} ({len(job_techs)} techs)"
            return True, match_score, reason
        else:
            reason = f"Low match: {match_score:.1%} (need {min_match:.1%})"
            return False, match_score, reason
    
    # ==================== LINKEDIN ====================
    
    def login_linkedin(self):
        """Login to LinkedIn"""
        self.logger.info("🔐 Logging into LinkedIn...")
        
        try:
            self.driver.get('https://www.linkedin.com/login')
            time.sleep(2)
            
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'username'))
            )
            email_field.send_keys(self.config['linkedin_email'])
            
            password_field = self.driver.find_element(By.ID, 'password')
            password_field.send_keys(self.config['linkedin_password'])
            password_field.send_keys(Keys.RETURN)
            
            time.sleep(5)
            
            # Check if login successful
            if "feed" in self.driver.current_url or "jobs" in self.driver.current_url:
                self.logger.info("✅ LinkedIn login successful")
                return True
            else:
                self.logger.error("❌ LinkedIn login failed")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ LinkedIn login error: {e}")
            return False
    
    def search_linkedin_jobs(self, keywords: str, location: str, remote_only: bool = False) -> List[Dict]:
        """Search for jobs on LinkedIn"""
        self.logger.info(f"🔍 Searching LinkedIn: {keywords} in {location}")
        
        filters = "f_AL=true"  # Easy Apply only
        if remote_only:
            filters += "&f_WT=2"
        
        if location.lower() == 'remote':
            url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&{filters}"
        else:
            url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}&{filters}"
        
        self.driver.get(url)
        time.sleep(3)
        
        # Scroll to load jobs
        for _ in range(3):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        jobs = []
        try:
            job_cards = self.driver.find_elements(By.CLASS_NAME, 'job-card-container')
            self.logger.info(f"📋 Found {len(job_cards)} LinkedIn jobs")
            
            for card in job_cards[:50]:  # Limit
                try:
                    card.click()
                    time.sleep(1)
                    
                    job_title = self.driver.find_element(
                        By.CSS_SELECTOR, '.job-details-jobs-unified-top-card__job-title'
                    ).text
                    
                    company = self.driver.find_element(
                        By.CSS_SELECTOR, '.job-details-jobs-unified-top-card__company-name'
                    ).text
                    
                    jobs.append({
                        'title': job_title,
                        'company': company,
                        'url': self.driver.current_url,
                        'platform': 'LinkedIn'
                    })
                    
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.error(f"❌ Error searching LinkedIn: {e}")
        
        return jobs
    
    def apply_linkedin_job(self, job: Dict) -> bool:
        """Apply to a LinkedIn job with Easy Apply"""
        self.logger.info(f"\n🎯 Applying: {job['title']} @ {job['company']}")
        
        try:
            # Check if already applied
            try:
                self.driver.find_element(By.XPATH, "//*[contains(text(), 'Applied')]")
                self.logger.info("  ⏭️  Already applied")
                return False
            except:
                pass
            
            # Get job description
            job_desc = self.get_linkedin_job_description()
            
            # Check if should apply
            should_apply, match_score, reason = self.should_apply(job['title'], job_desc)
            
            if not should_apply:
                self.logger.info(f"  ⏭️  Skipped: {reason}")
                self.skipped_jobs.append({**job, 'reason': reason, 'match_score': match_score})
                return False
            
            self.logger.info(f"  ✅ {reason}")
            
            # Tailor resume
            resume_path = self.tailor_resume(job['title'], job['company'], job_desc)
            
            # Click Easy Apply
            easy_apply_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='jobs-apply-button']"))
            )
            easy_apply_btn.click()
            time.sleep(2)
            
            # Fill application
            if self.fill_linkedin_application(resume_path):
                self.applied_count += 1
                self.save_applied_job({**job, 'match_score': match_score})
                self.logger.info(f"  🎉 Application #{self.applied_count} submitted! (Match: {match_score:.1%})")
                return True
            
        except Exception as e:
            self.logger.warning(f"  ⚠️  Application failed: {e}")
            return False
        
        return False
    
    def get_linkedin_job_description(self) -> str:
        """Extract LinkedIn job description"""
        try:
            desc = self.driver.find_element(By.CLASS_NAME, 'jobs-description-content__text').text
            return desc
        except:
            return ""
    
    def fill_linkedin_application(self, resume_path: str) -> bool:
        """Fill multi-page LinkedIn application"""
        try:
            page = 1
            max_pages = 10
            
            while page <= max_pages:
                self.logger.info(f"  📝 Page {page}...")
                
                # Auto-fill fields
                self.auto_fill_linkedin_fields()
                
                # Upload resume
                self.upload_resume(resume_path)
                
                time.sleep(1)
                
                # Find next/submit button
                try:
                    # Try Review button
                    review_btn = self.driver.find_element(
                        By.XPATH, "//button[@aria-label='Review your application']"
                    )
                    review_btn.click()
                    time.sleep(2)
                    page += 1
                    continue
                except:
                    pass
                
                try:
                    # Try Next button
                    next_btn = self.driver.find_element(
                        By.XPATH, "//button[@aria-label='Continue to next step']"
                    )
                    next_btn.click()
                    time.sleep(2)
                    page += 1
                    continue
                except:
                    pass
                
                try:
                    # Try Submit button
                    submit_btn = self.driver.find_element(
                        By.XPATH, "//button[@aria-label='Submit application']"
                    )
                    submit_btn.click()
                    time.sleep(3)
                    
                    # Close confirmation modal
                    try:
                        close_btn = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Dismiss']"))
                        )
                        close_btn.click()
                    except:
                        pass
                    
                    return True
                    
                except:
                    self.logger.warning("  ⚠️  No more buttons found")
                    return False
                    
        except Exception as e:
            self.logger.error(f"  ❌ Application error: {e}")
            return False
    
    def auto_fill_linkedin_fields(self):
        """Auto-fill all form fields"""
        # Text inputs
        inputs = self.driver.find_elements(By.TAG_NAME, 'input')
        for inp in inputs:
            try:
                if inp.get_attribute('type') in ['text', 'tel', 'email', 'number']:
                    label = self.get_field_label(inp)
                    value = self.get_field_value(label)
                    if value and inp.is_displayed():
                        inp.clear()
                        inp.send_keys(str(value))
            except:
                pass
        
        # Textareas
        textareas = self.driver.find_elements(By.TAG_NAME, 'textarea')
        for textarea in textareas:
            try:
                if textarea.is_displayed():
                    label = self.get_field_label(textarea)
                    if 'cover' in label.lower():
                        cover = self.generate_cover_letter()
                        textarea.clear()
                        textarea.send_keys(cover)
            except:
                pass
        
        # Dropdowns
        selects = self.driver.find_elements(By.TAG_NAME, 'select')
        for select_elem in selects:
            try:
                if select_elem.is_displayed():
                    label = self.get_field_label(select_elem)
                    value = self.get_dropdown_value(label)
                    if value:
                        Select(select_elem).select_by_visible_text(value)
            except:
                pass
    
    def get_field_label(self, element) -> str:
        """Get field label from element"""
        try:
            label = element.get_attribute('aria-label')
            if label:
                return label.lower()
            
            field_id = element.get_attribute('id')
            if field_id:
                label_elem = self.driver.find_element(By.XPATH, f"//label[@for='{field_id}']")
                return label_elem.text.lower()
        except:
            pass
        return ''
    
    def get_field_value(self, label: str) -> str:
        """Get appropriate value for field based on label"""
        label = label.lower()
        config = self.config
        
        if 'phone' in label or 'mobile' in label:
            return config.get('phone', '')
        elif 'email' in label:
            return config.get('email', '')
        elif 'first' in label and 'name' in label:
            return config.get('first_name', '')
        elif 'last' in label and 'name' in label:
            return config.get('last_name', '')
        elif 'city' in label:
            return config.get('city', '')
        elif 'linkedin' in label:
            return config.get('linkedin_url', '')
        elif 'github' in label or 'portfolio' in label:
            return config.get('github_url', '')
        elif 'year' in label and 'experience' in label:
            return str(config.get('years_experience', ''))
        
        return ''
    
    def get_dropdown_value(self, label: str) -> str:
        """Get dropdown value based on label"""
        label = label.lower()
        
        if 'experience' in label:
            years = self.config.get('years_experience', 0)
            if years < 2:
                return '0-2 years'
            elif years < 5:
                return '2-5 years'
            elif years < 10:
                return '5-10 years'
            else:
                return '10+ years'
        
        if 'gender' in label or 'race' in label or 'veteran' in label or 'disability' in label:
            return 'Prefer not to say'
        
        return ''
    
    def upload_resume(self, resume_path: str):
        """Upload resume file if input exists"""
        try:
            file_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
            for file_input in file_inputs:
                abs_path = os.path.abspath(resume_path)
                file_input.send_keys(abs_path)
                self.logger.info("  📎 Resume uploaded")
                time.sleep(2)
                break
        except:
            pass
    
    # ==================== AI RESUME TAILORING ====================
    
    def tailor_resume(self, job_title: str, company: str, job_desc: str) -> str:
        """Tailor resume using AI for specific job"""
        if not self.gemini_model:
            return self.config.get('master_resume_path', '')
        
        self.logger.info("  ✍️  Tailoring resume with AI...")
        
        # Load original resume
        resume_text = self.load_resume_text()
        
        # Extract key requirements
        job_techs = self.extract_tech_stack(job_desc)
        
        prompt = f"""You are an expert resume writer specializing in fullstack developer positions.

JOB TITLE: {job_title}
COMPANY: {company}

JOB DESCRIPTION (excerpt):
{job_desc[:2000]}

REQUIRED TECHNOLOGIES: {', '.join(job_techs[:15])}

ORIGINAL RESUME:
{resume_text[:3000]}

TASK: Optimize this resume for the job above. Focus on:

1. **Professional Summary**: Rewrite to highlight fullstack expertise matching the job
2. **Skills Section**: Prioritize technologies mentioned in job description
3. **Experience**: Emphasize relevant projects and achievements
4. **Keywords**: Include exact technologies from job description naturally
5. **ATS Optimization**: Use clear headers, standard formatting

IMPORTANT:
- Keep it truthful - only emphasize existing skills/experience
- Maintain 1-2 page length
- Use simple formatting (no tables/graphics)
- Include metrics and quantifiable achievements
- Front-load most important information

Return ONLY the optimized resume text with clear sections.

OPTIMIZED RESUME:"""

        try:
            response = self.gemini_model.generate_content(
                prompt,
                generation_config={'temperature': 0.7, 'max_output_tokens': 2500}
            )
            
            tailored_text = response.text
            
            # Save tailored resume
            resume_path = self.save_tailored_resume(tailored_text, job_title, company)
            self.logger.info(f"  ✅ Resume tailored successfully")
            
            return resume_path
            
        except Exception as e:
            self.logger.warning(f"  ⚠️  Resume tailoring failed: {e}")
            return self.config.get('master_resume_path', '')
    
    def load_resume_text(self) -> str:
        """Load resume text from file"""
        resume_path = self.config.get('master_resume_path', '')
        
        if not resume_path or not os.path.exists(resume_path):
            return self.config.get('resume_text', 'Resume text not provided')
        
        try:
            with open(resume_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return self.config.get('resume_text', 'Resume text not provided')
    
    def save_tailored_resume(self, text: str, job_title: str, company: str) -> str:
        """Save tailored resume as text file"""
        output_dir = Path(self.config.get('tailored_resumes_dir', './tailored_resumes'))
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r'[^\w\s-]', '', job_title)[:30].replace(' ', '_')
        safe_company = re.sub(r'[^\w\s-]', '', company)[:20].replace(' ', '_')
        
        filename = f"resume_{safe_company}_{safe_title}_{timestamp}.txt"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return str(filepath)
    
    def generate_cover_letter(self) -> str:
        """Generate brief cover letter"""
        return f"""Dear Hiring Manager,

I am excited to apply for this fullstack developer position. With {self.config.get('years_experience', 'several')} years of experience building modern web applications using technologies like {', '.join(self.config.get('skills', ['React', 'Node.js', 'Python'])[:3])}, I am confident I can contribute effectively to your team.

I am passionate about creating scalable, user-friendly applications and thrive in collaborative environments.

Looking forward to discussing this opportunity.

Best regards,
{self.config.get('first_name', '')} {self.config.get('last_name', '')}"""
    
    # ==================== TRACKING & REPORTING ====================
    
    def save_applied_job(self, job: Dict):
        """Save applied job to tracking file"""
        job['applied_at'] = datetime.now().isoformat()
        self.applied_jobs.append(job)
        
        output_file = Path('applied_jobs.json')
        
        try:
            existing = []
            if output_file.exists():
                with open(output_file, 'r') as f:
                    existing = json.load(f)
            
            existing.append(job)
            
            with open(output_file, 'w') as f:
                json.dump(existing, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save job: {e}")
    
    def generate_report(self):
        """Generate session report"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📊 SESSION REPORT")
        self.logger.info("="*60)
        self.logger.info(f"✅ Applications Submitted: {self.applied_count}")
        self.logger.info(f"⏭️  Jobs Skipped: {len(self.skipped_jobs)}")
        
        if self.applied_jobs:
            avg_match = sum(j.get('match_score', 0) for j in self.applied_jobs) / len(self.applied_jobs)
            self.logger.info(f"📈 Average Match Score: {avg_match:.1%}")
        
        if self.applied_jobs:
            self.logger.info("\n✅ Applied to:")
            for job in self.applied_jobs[-5:]:  # Show last 5
                score = job.get('match_score', 0)
                self.logger.info(f"   • {job['title']} @ {job['company']} ({score:.1%})")
        
        self.logger.info("="*60 + "\n")
    
    # ==================== MAIN EXECUTION ====================
    
    def run(self, max_applications: int = 10, dry_run: bool = False):
        """Run the job application agent"""
        self.logger.info("🚀 Starting Fullstack Job Agent")
        self.logger.info(f"Target: {max_applications} applications")
        self.logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        
        if dry_run:
            self.logger.warning("⚠️  DRY RUN MODE - No applications will be submitted")
        
        try:
            self.setup_browser(headless=False)
            
            # Login to platforms
            if not self.login_linkedin():
                self.logger.error("❌ LinkedIn login failed. Exiting.")
                return
            
            # Search for jobs
            searches = self.config.get('job_searches', [
                {'keywords': 'Fullstack Developer', 'location': 'Remote'},
                {'keywords': 'Full Stack Engineer', 'location': 'Remote'},
            ])
            
            all_jobs = []
            for search in searches:
                jobs = self.search_linkedin_jobs(
                    search['keywords'],
                    search.get('location', 'Remote'),
                    search.get('remote_only', True)
                )
                all_jobs.extend(jobs)
                
                if len(all_jobs) >= max_applications * 2:  # Get extra to filter
                    break
            
            self.logger.info(f"\n📋 Total jobs found: {len(all_jobs)}")
            
            # Apply to jobs
            for job in all_jobs:
                if self.applied_count >= max_applications:
                    self.logger.info(f"✅ Reached target of {max_applications} applications")
                    break
                
                if not dry_run:
                    self.apply_linkedin_job(job)
                    
                    # Rate limiting
                    delay = random.randint(30, 60)
                    self.logger.info(f"⏳ Waiting {delay}s...")
                    time.sleep(delay)
                else:
                    # Dry run - just analyze
                    job_desc = self.get_linkedin_job_description()
                    should_apply, score, reason = self.should_apply(job['title'], job_desc)
                    
                    self.logger.info(f"\n🔍 {job['title']} @ {job['company']}")
                    self.logger.info(f"   Decision: {'✅ APPLY' if should_apply else '⏭️  SKIP'} - {reason}")
            
            # Generate report
            self.generate_report()
            
        except KeyboardInterrupt:
            self.logger.info("\n⚠️  Interrupted by user")
            self.generate_report()
        except Exception as e:
            self.logger.error(f"❌ Fatal error: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("🔚 Browser closed")


# ==================== CONFIGURATION ====================

def load_config() -> Dict:
    """Load configuration from profile.json or use defaults"""
    config_file = Path('profile.json')
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    # Set defaults
    defaults = {
        'linkedin_email': 'your-email@gmail.com',
        'linkedin_password': 'your-password',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'your-email@gmail.com',
        'phone': '+1-234-567-8900',
        'city': 'San Francisco',
        'linkedin_url': 'https://linkedin.com/in/yourprofile',
        'github_url': 'https://github.com/yourusername',
        'years_experience': 3,
        'skills': [
            'React', 'Node.js', 'Python', 'JavaScript', 'TypeScript',
            'PostgreSQL', 'MongoDB', 'AWS', 'Docker', 'Git'
        ],
        'min_match_score': 0.3,
        'master_resume_path': './test_resume.txt',
        'tailored_resumes_dir': './tailored_resumes',
        'log_dir': './logs',
        'gemini_key': '',  # Get free key from https://makersuite.google.com/app/apikey
        'job_searches': [
            {'keywords': 'Fullstack Developer', 'location': 'Remote', 'remote_only': True},
            {'keywords': 'Full Stack Engineer', 'location': 'Remote', 'remote_only': True},
            {'keywords': 'Software Engineer Fullstack', 'location': 'Remote', 'remote_only': True},
        ]
    }
    
    # Merge with defaults
    for key, value in defaults.items():
        if key not in config:
            config[key] = value
    
    return config


# ==================== MAIN ====================

def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   🤖 FULLSTACK DEVELOPER JOB AUTO-APPLY AGENT 🚀         ║
║                                                          ║
║   Intelligent • AI-Powered • ATS-Optimized              ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Load configuration
    config = load_config()
    
    # Create agent
    agent = FullstackJobAgent(config)
    
    # Run agent
    import argparse
    parser = argparse.ArgumentParser(description='Fullstack Job Auto-Apply Agent')
    parser.add_argument('--max', type=int, default=10, help='Maximum applications')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no applications)')
    args = parser.parse_args()
    
    print(f"\n🎯 Target: {args.max} applications")
    print(f"📍 Mode: {'DRY RUN (Safe)' if args.dry_run else 'LIVE'}\n")
    
    if not args.dry_run:
        response = input("⚠️  Ready to start LIVE applications? (yes/no): ")
        if response.lower() != 'yes':
            print("👋 Exiting. Run with --dry-run first to test!")
            return
    
    # Run the agent
    agent.run(max_applications=args.max, dry_run=args.dry_run)
    
    print("\n✅ Agent completed!")


if __name__ == "__main__":
    main()

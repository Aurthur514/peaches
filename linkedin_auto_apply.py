#!/usr/bin/env python3
"""
LinkedIn Auto Apply with Credentials - Enhanced automation for LinkedIn job applications
"""

import os
import json
import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class LinkedInAutoApply:
    def __init__(self):
        self.setup_driver()
        self.credentials = self.load_credentials()
        self.user_profile = self.load_user_profile()
        self.applied_jobs = []
        
    def setup_driver(self):
        """Setup Chrome driver with LinkedIn-optimized settings"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # LinkedIn-specific optimizations
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 15)
            
            # Execute script to hide automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ Chrome driver initialized for LinkedIn")
            
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            raise
    
    def load_credentials(self):
        """Load LinkedIn credentials"""
        try:
            with open('job_site_credentials.json', 'r') as f:
                creds = json.load(f)
                return creds.get('linkedin', {})
        except:
            print("⚠️ No credentials found. Creating template...")
            return self.create_linkedin_credentials()
    
    def create_linkedin_credentials(self):
        """Create LinkedIn credentials template"""
        template = {
            "linkedin": {
                "email": "your_linkedin_email@gmail.com",
                "password": "your_linkedin_password",
                "enabled": False,
                "phone": "+91-9876543210",
                "location": "Chennai, Tamil Nadu, India"
            }
        }
        
        # Update existing file or create new one
        try:
            if os.path.exists('job_site_credentials.json'):
                with open('job_site_credentials.json', 'r') as f:
                    existing = json.load(f)
                existing.update(template)
                with open('job_site_credentials.json', 'w') as f:
                    json.dump(existing, f, indent=2)
            else:
                with open('job_site_credentials.json', 'w') as f:
                    json.dump(template, f, indent=2)
                    
            print("📝 LinkedIn credentials template created")
            print("Please update job_site_credentials.json with your LinkedIn details")
            return template['linkedin']
        except Exception as e:
            print(f"Error creating credentials: {e}")
            return {}
    
    def load_user_profile(self):
        """Load user profile for applications"""
        try:
            if os.path.exists('job_bot_config.json'):
                with open('job_bot_config.json', 'r') as f:
                    config = json.load(f)
                    if 'user_profile' in config:
                        profile = config['user_profile']
                        return {
                            'name': profile.get('full_name', 'Bharathan M'),
                            'email': profile.get('email', 'bharathan1404@gmail.com'),
                            'phone': profile.get('phone', '+919566030215'),
                            'location': profile.get('location', 'Chennai'),
                            'skills': profile.get('technical_skills', [])[:10],
                            'experience_years': 2,
                            'current_title': 'Data Analyst'
                        }
            return {
                'name': 'Bharathan M',
                'email': 'bharathan1404@gmail.com', 
                'phone': '+919566030215',
                'location': 'Chennai',
                'skills': ['Python', 'SQL', 'Data Analysis'],
                'experience_years': 2,
                'current_title': 'Data Analyst'
            }
        except Exception as e:
            print(f"Profile loading error: {e}")
            return {}
    
    def human_like_delay(self, min_seconds=1, max_seconds=3):
        """Add human-like delays"""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def human_like_typing(self, element, text, typing_speed=0.1):
        """Type text in a human-like manner"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, typing_speed))
    
    def login_to_linkedin(self):
        """Login to LinkedIn with credentials"""
        print("\n🔐 Logging into LinkedIn...")
        
        if not self.credentials.get('enabled'):
            print("❌ LinkedIn credentials not enabled")
            print("Please update job_site_credentials.json and set enabled: true")
            return False
        
        try:
            # Navigate to LinkedIn login
            self.driver.get("https://www.linkedin.com/login")
            self.human_like_delay(2, 4)
            
            # Fill email
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            self.human_like_typing(email_field, self.credentials['email'])
            
            # Fill password
            password_field = self.driver.find_element(By.ID, "password")
            self.human_like_typing(password_field, self.credentials['password'], 0.15)
            
            # Click login
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait and check for successful login
            self.human_like_delay(3, 5)
            
            # Check for various possible outcomes
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()
            
            if "feed" in current_url or "home" in current_url:
                print("✅ LinkedIn login successful!")
                return True
            elif "challenge" in current_url or "checkpoint" in current_url:
                print("⚠️ LinkedIn security challenge detected")
                print("Please complete the challenge manually in the browser")
                input("Press Enter after completing the challenge...")
                return True
            elif "captcha" in page_source:
                print("⚠️ CAPTCHA detected - please solve manually")
                input("Press Enter after solving CAPTCHA...")
                return True
            else:
                print("❌ LinkedIn login failed")
                print(f"Current URL: {current_url}")
                return False
                
        except Exception as e:
            print(f"❌ LinkedIn login error: {e}")
            return False
    
    def search_linkedin_jobs(self, keywords="data analyst", location="Chennai"):
        """Search for jobs on LinkedIn"""
        print(f"\n🔍 Searching LinkedIn for: {keywords} in {location}")
        
        try:
            # Navigate to jobs section
            jobs_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
            self.driver.get(jobs_url)
            self.human_like_delay(3, 5)
            
            # Wait for job listings to load
            job_cards = self.wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "[data-job-id]")
            ))
            
            print(f"📊 Found {len(job_cards)} job listings")
            
            jobs = []
            for i, card in enumerate(job_cards[:15]):  # Limit to first 15 jobs
                try:
                    # Extract job details
                    job_title_elem = card.find_element(By.CSS_SELECTOR, "h3 a")
                    job_title = job_title_elem.text.strip()
                    job_url = job_title_elem.get_attribute('href')
                    
                    company_elem = card.find_element(By.CSS_SELECTOR, "h4 a")
                    company_name = company_elem.text.strip()
                    
                    # Try to get location
                    try:
                        location_elem = card.find_element(By.CSS_SELECTOR, "[data-test-id='job-search-card-location']")
                        job_location = location_elem.text.strip()
                    except:
                        job_location = location
                    
                    # Try to get job ID
                    job_id = card.get_attribute('data-job-id')
                    
                    job_data = {
                        'id': job_id,
                        'title': job_title,
                        'company': company_name,
                        'location': job_location,
                        'url': job_url,
                        'platform': 'LinkedIn',
                        'found_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    jobs.append(job_data)
                    print(f"   {i+1}. {job_title} at {company_name}")
                    
                except Exception as e:
                    print(f"   ⚠️ Error extracting job {i+1}: {e}")
                    continue
            
            print(f"✅ Successfully extracted {len(jobs)} LinkedIn jobs")
            return jobs
            
        except Exception as e:
            print(f"❌ LinkedIn job search error: {e}")
            return []
    
    def apply_to_linkedin_job(self, job):
        """Apply to a specific LinkedIn job"""
        print(f"\n🤖 Applying to: {job['title']} at {job['company']}")
        
        try:
            # Navigate to job URL
            self.driver.get(job['url'])
            self.human_like_delay(2, 4)
            
            # Look for Easy Apply button
            easy_apply_buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(@aria-label, 'Easy Apply')] | //button[contains(text(), 'Easy Apply')]"
            )
            
            if not easy_apply_buttons:
                print("   ⚠️ No Easy Apply button found - external application required")
                return False
            
            # Click Easy Apply
            easy_apply_buttons[0].click()
            self.human_like_delay(2, 3)
            
            # Handle application flow
            success = self.handle_application_flow(job)
            
            if success:
                # Track successful application
                application_record = {
                    **job,
                    'applied_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'Applied',
                    'application_method': 'LinkedIn Easy Apply',
                    'match_score': self.calculate_job_match(job)
                }
                
                self.applied_jobs.append(application_record)
                print(f"   ✅ Successfully applied to {job['title']}")
                return True
            else:
                print(f"   ❌ Application failed for {job['title']}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error applying to {job['title']}: {e}")
            return False
    
    def handle_application_flow(self, job):
        """Handle the LinkedIn Easy Apply application flow"""
        try:
            step = 1
            max_steps = 5
            
            while step <= max_steps:
                print(f"   📝 Application step {step}...")
                
                # Check for different types of forms/steps
                
                # Step 1: Basic information
                if step == 1:
                    # Fill phone number if required
                    phone_fields = self.driver.find_elements(By.XPATH, 
                        "//input[@type='tel'] | //input[contains(@id, 'phone')]"
                    )
                    
                    for phone_field in phone_fields:
                        if not phone_field.get_attribute('value'):
                            self.human_like_typing(phone_field, self.user_profile['phone'])
                
                # Handle resume upload
                resume_uploads = self.driver.find_elements(By.XPATH, 
                    "//input[@type='file']"
                )
                
                for upload in resume_uploads:
                    if os.path.exists('resumes/master_resume.pdf'):
                        upload.send_keys(os.path.abspath('resumes/master_resume.pdf'))
                        self.human_like_delay(1, 2)
                
                # Fill text areas (cover letter, additional info)
                text_areas = self.driver.find_elements(By.TAG_NAME, "textarea")
                for textarea in text_areas:
                    if not textarea.get_attribute('value').strip():
                        cover_letter = f"Dear Hiring Manager,\n\nI am excited to apply for the {job['title']} position at {job['company']}. With my background in data analysis and {self.user_profile['experience_years']} years of experience, I believe I would be a great fit for this role.\n\nBest regards,\n{self.user_profile['name']}"
                        self.human_like_typing(textarea, cover_letter)
                
                # Look for next button
                next_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(@aria-label, 'Continue')] | //button[contains(text(), 'Next')] | //button[contains(@aria-label, 'Review')]"
                )
                
                if next_buttons:
                    next_buttons[0].click()
                    self.human_like_delay(2, 3)
                    step += 1
                    continue
                
                # Look for submit button
                submit_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(@aria-label, 'Submit application')] | //button[contains(text(), 'Submit')]"
                )
                
                if submit_buttons:
                    # Final confirmation before submitting
                    print(f"   🎯 Ready to submit application for {job['title']}")
                    submit_buttons[0].click()
                    self.human_like_delay(3, 5)
                    
                    # Check for confirmation
                    if "Your application was sent" in self.driver.page_source or \
                       "Application submitted" in self.driver.page_source:
                        print(f"   ✅ Application submitted successfully!")
                        return True
                    else:
                        print(f"   ⚠️ Application may have been submitted")
                        return True
                
                # If no next or submit button found, break
                break
            
            print(f"   ⚠️ Application flow incomplete after {max_steps} steps")
            return False
            
        except Exception as e:
            print(f"   ❌ Application flow error: {e}")
            return False
    
    def calculate_job_match(self, job):
        """Calculate how well the job matches user profile"""
        score = 60  # Base score
        
        title = job.get('title', '').lower()
        company = job.get('company', '').lower()
        
        # Check for role keywords
        if 'analyst' in title or 'data' in title:
            score += 20
        
        # Check for skill matches
        for skill in self.user_profile.get('skills', []):
            if skill.lower() in title:
                score += 5
        
        # Location bonus
        if 'chennai' in job.get('location', '').lower():
            score += 10
        
        # Company size/type bonus (simple heuristic)
        if any(word in company for word in ['tech', 'technologies', 'solutions', 'systems']):
            score += 5
        
        return min(score, 100)
    
    def run_linkedin_auto_apply(self, keywords="data analyst", location="Chennai", max_applications=10):
        """Run complete LinkedIn auto apply process"""
        print("🚀 STARTING LINKEDIN AUTO APPLY PROCESS")
        print("=" * 50)
        
        try:
            # Step 1: Login
            if not self.login_to_linkedin():
                return False
            
            # Step 2: Search for jobs
            jobs = self.search_linkedin_jobs(keywords, location)
            
            if not jobs:
                print("❌ No jobs found to apply to")
                return False
            
            # Step 3: Filter and apply to jobs
            print(f"\n🎯 Applying to up to {max_applications} jobs...")
            
            successful_applications = 0
            failed_applications = 0
            
            for i, job in enumerate(jobs[:max_applications]):
                print(f"\n--- Job {i+1}/{min(len(jobs), max_applications)} ---")
                
                # Calculate match score
                match_score = self.calculate_job_match(job)
                print(f"Match Score: {match_score}%")
                
                # Apply if match score is good
                if match_score >= 70:
                    success = self.apply_to_linkedin_job(job)
                    
                    if success:
                        successful_applications += 1
                    else:
                        failed_applications += 1
                    
                    # Add delay between applications
                    self.human_like_delay(10, 20)
                else:
                    print(f"   ⏭️ Skipped - match score too low ({match_score}%)")
            
            # Step 4: Save results
            self.save_application_results()
            
            # Step 5: Summary
            print(f"\n{'='*50}")
            print("📊 LINKEDIN AUTO APPLY SUMMARY")
            print("=" * 50)
            print(f"Jobs found: {len(jobs)}")
            print(f"Applications attempted: {successful_applications + failed_applications}")
            print(f"Successful applications: {successful_applications}")
            print(f"Failed applications: {failed_applications}")
            print(f"Success rate: {(successful_applications/(successful_applications + failed_applications)*100):.1f}%" if (successful_applications + failed_applications) > 0 else "0%")
            
            return True
            
        except Exception as e:
            print(f"❌ LinkedIn auto apply process failed: {e}")
            return False
    
    def save_application_results(self):
        """Save application results to file"""
        if self.applied_jobs:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"linkedin_applications_{timestamp}.json"
            
            try:
                with open(filename, 'w') as f:
                    json.dump({
                        'timestamp': timestamp,
                        'total_applications': len(self.applied_jobs),
                        'platform': 'LinkedIn',
                        'applications': self.applied_jobs
                    }, f, indent=2)
                
                print(f"💾 Application results saved to: {filename}")
                
            except Exception as e:
                print(f"⚠️ Could not save results: {e}")
    
    def cleanup(self):
        """Clean up browser resources"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
                print("🧹 Browser cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")

def main():
    """Main function to run LinkedIn auto apply"""
    print("🔗 LINKEDIN AUTO APPLY WITH CREDENTIALS")
    print("=" * 60)
    
    linkedin_auto = LinkedInAutoApply()
    
    try:
        # Check if credentials are configured
        if not linkedin_auto.credentials.get('enabled'):
            print("⚠️ LinkedIn credentials not enabled!")
            print("\nTo enable LinkedIn auto apply:")
            print("1. Edit 'job_site_credentials.json'")
            print("2. Add your LinkedIn email and password")
            print("3. Set 'enabled': true")
            print("4. Run this script again")
            return
        
        # Get search parameters
        keywords = input("Enter job keywords (default: data analyst): ").strip() or "data analyst"
        location = input("Enter location (default: Chennai): ").strip() or "Chennai"
        max_apps = input("Max applications (default: 5): ").strip()
        max_apps = int(max_apps) if max_apps.isdigit() else 5
        
        print(f"\n🎯 Configuration:")
        print(f"Keywords: {keywords}")
        print(f"Location: {location}")
        print(f"Max applications: {max_apps}")
        
        confirm = input("\nProceed with LinkedIn auto apply? (y/n): ").strip().lower()
        
        if confirm == 'y':
            success = linkedin_auto.run_linkedin_auto_apply(keywords, location, max_apps)
            
            if success:
                print("\n🎉 LinkedIn auto apply completed successfully!")
            else:
                print("\n❌ LinkedIn auto apply failed")
        else:
            print("❌ Auto apply cancelled by user")
    
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        linkedin_auto.cleanup()

if __name__ == "__main__":
    main()
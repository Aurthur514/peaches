#!/usr/bin/env python3
"""
🔐 CREDENTIAL-BASED AUTO APPLY SYSTEM
Complete automation with login capabilities
"""

import json
import os
import time
import getpass
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('credential_auto_apply.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CredentialAutoApplySystem:
    def __init__(self):
        self.credentials = {}
        self.driver = None
        self.applications_made = []
        self.setup_credentials()
    
    def setup_credentials(self):
        """Setup or load credentials securely"""
        print("🔐 CREDENTIAL-BASED AUTO APPLY SETUP")
        print("=" * 50)
        
        # Check if credentials file exists
        if os.path.exists('job_site_credentials.json'):
            choice = input("\n📋 Credentials file found. Do you want to:\n1. Use existing credentials\n2. Update credentials\n3. Add new platform\nChoice (1-3): ")
            
            if choice == '1':
                self.load_existing_credentials()
            elif choice == '2':
                self.update_credentials()
            elif choice == '3':
                self.add_new_platform()
        else:
            print("\n🆕 No credentials found. Let's set up your first platform!")
            self.setup_new_credentials()
    
    def setup_new_credentials(self):
        """Setup credentials for the first time"""
        print("\n🎯 Which platform would you like to start with?")
        print("1. Naukri.com (Recommended - Good for Indian market)")
        print("2. Indeed.com (International opportunities)")
        print("3. LinkedIn (Professional networking)")
        print("4. Set up multiple platforms")
        
        choice = input("\nChoice (1-4): ")
        
        platforms = []
        if choice == '1':
            platforms = ['naukri']
        elif choice == '2':
            platforms = ['indeed']
        elif choice == '3':
            platforms = ['linkedin']
        elif choice == '4':
            platforms = ['naukri', 'indeed', 'linkedin']
        
        credentials = {}
        
        for platform in platforms:
            print(f"\n🔑 Setting up {platform.title()} credentials:")
            
            if platform == 'naukri':
                email = input("📧 Naukri Email: ")
                password = getpass.getpass("🔒 Naukri Password: ")
                credentials['naukri'] = {
                    'email': email,
                    'password': password,
                    'enabled': True,
                    'login_url': 'https://www.naukri.com/nlogin/login',
                    'success_indicator': 'mynaukri'
                }
            
            elif platform == 'indeed':
                email = input("📧 Indeed Email: ")
                password = getpass.getpass("🔒 Indeed Password: ")
                credentials['indeed'] = {
                    'email': email,
                    'password': password,
                    'enabled': True,
                    'login_url': 'https://secure.indeed.com/account/login',
                    'success_indicator': 'account'
                }
            
            elif platform == 'linkedin':
                email = input("📧 LinkedIn Email: ")
                password = getpass.getpass("🔒 LinkedIn Password: ")
                credentials['linkedin'] = {
                    'email': email,
                    'password': password,
                    'enabled': True,
                    'login_url': 'https://www.linkedin.com/login',
                    'success_indicator': 'feed'
                }
        
        # Save credentials
        with open('job_site_credentials.json', 'w') as f:
            json.dump(credentials, f, indent=2)
        
        print("\n✅ Credentials saved successfully!")
        self.credentials = credentials
    
    def load_existing_credentials(self):
        """Load existing credentials"""
        try:
            with open('job_site_credentials.json', 'r') as f:
                self.credentials = json.load(f)
            
            enabled_platforms = [p for p, c in self.credentials.items() if c.get('enabled')]
            print(f"\n✅ Loaded credentials for: {', '.join(enabled_platforms)}")
            
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            self.setup_new_credentials()
    
    def update_credentials(self):
        """Update existing credentials"""
        self.load_existing_credentials()
        
        print("\n🔄 Which platform credentials do you want to update?")
        platforms = list(self.credentials.keys())
        
        for i, platform in enumerate(platforms, 1):
            status = "✅ Enabled" if self.credentials[platform].get('enabled') else "❌ Disabled"
            print(f"{i}. {platform.title()} - {status}")
        
        choice = input(f"\nChoice (1-{len(platforms)}): ")
        
        try:
            platform_index = int(choice) - 1
            platform = platforms[platform_index]
            
            print(f"\n🔑 Updating {platform.title()} credentials:")
            email = input(f"📧 New Email (current: {self.credentials[platform]['email']}): ") or self.credentials[platform]['email']
            password = getpass.getpass("🔒 New Password: ")
            
            self.credentials[platform]['email'] = email
            self.credentials[platform]['password'] = password
            self.credentials[platform]['enabled'] = True
            
            with open('job_site_credentials.json', 'w') as f:
                json.dump(self.credentials, f, indent=2)
            
            print(f"✅ {platform.title()} credentials updated!")
            
        except (ValueError, IndexError):
            print("❌ Invalid choice")
    
    def add_new_platform(self):
        """Add credentials for a new platform"""
        self.load_existing_credentials()
        
        existing_platforms = set(self.credentials.keys())
        available_platforms = ['naukri', 'indeed', 'linkedin', 'freshersworld'] - existing_platforms
        
        if not available_platforms:
            print("✅ All supported platforms are already configured!")
            return
        
        print(f"\n➕ Available platforms to add:")
        available_list = list(available_platforms)
        for i, platform in enumerate(available_list, 1):
            print(f"{i}. {platform.title()}")
        
        choice = input(f"\nChoice (1-{len(available_list)}): ")
        
        try:
            platform_index = int(choice) - 1
            platform = available_list[platform_index]
            
            print(f"\n🔑 Adding {platform.title()} credentials:")
            email = input("📧 Email: ")
            password = getpass.getpass("🔒 Password: ")
            
            platform_config = {
                'email': email,
                'password': password,
                'enabled': True
            }
            
            # Add platform-specific configuration
            if platform == 'naukri':
                platform_config.update({
                    'login_url': 'https://www.naukri.com/nlogin/login',
                    'success_indicator': 'mynaukri'
                })
            elif platform == 'indeed':
                platform_config.update({
                    'login_url': 'https://secure.indeed.com/account/login',
                    'success_indicator': 'account'
                })
            elif platform == 'linkedin':
                platform_config.update({
                    'login_url': 'https://www.linkedin.com/login',
                    'success_indicator': 'feed'
                })
            elif platform == 'freshersworld':
                platform_config.update({
                    'login_url': 'https://www.freshersworld.com/user/login',
                    'success_indicator': 'dashboard'
                })
            
            self.credentials[platform] = platform_config
            
            with open('job_site_credentials.json', 'w') as f:
                json.dump(self.credentials, f, indent=2)
            
            print(f"✅ {platform.title()} credentials added!")
            
        except (ValueError, IndexError):
            print("❌ Invalid choice")
    
    def setup_browser(self):
        """Setup browser with optimal settings"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Add preferences to handle file downloads and notifications
        prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "geolocation": 2,
            }
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 15)
        
        logger.info("Browser setup completed")
    
    def login_to_platform(self, platform):
        """Login to a specific platform"""
        if platform not in self.credentials or not self.credentials[platform].get('enabled'):
            logger.warning(f"Platform {platform} not configured or disabled")
            return False
        
        creds = self.credentials[platform]
        logger.info(f"Attempting login to {platform}")
        
        try:
            # Navigate to login page
            self.driver.get(creds['login_url'])
            time.sleep(3)
            
            if platform == 'naukri':
                return self.login_naukri(creds)
            elif platform == 'indeed':
                return self.login_indeed(creds)
            elif platform == 'linkedin':
                return self.login_linkedin(creds)
            
        except Exception as e:
            logger.error(f"Login failed for {platform}: {e}")
            return False
    
    def login_naukri(self, creds):
        """Login to Naukri.com"""
        try:
            # Find email field
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
            email_field.clear()
            email_field.send_keys(creds['email'])
            
            # Find password field
            password_field = self.driver.find_element(By.ID, "passwordField")
            password_field.clear()
            password_field.send_keys(creds['password'])
            
            # Click login
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
            login_button.click()
            
            # Wait for login success
            time.sleep(5)
            
            # Check if login was successful
            if creds['success_indicator'] in self.driver.current_url:
                logger.info("Naukri login successful")
                return True
            else:
                logger.warning("Naukri login may have failed")
                return False
                
        except Exception as e:
            logger.error(f"Naukri login error: {e}")
            return False
    
    def login_indeed(self, creds):
        """Login to Indeed.com"""
        try:
            # Find email field
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "login-email-input")))
            email_field.clear()
            email_field.send_keys(creds['email'])
            
            # Continue button
            continue_btn = self.driver.find_element(By.ID, "login-submit-button")
            continue_btn.click()
            time.sleep(2)
            
            # Find password field
            password_field = self.wait.until(EC.presence_of_element_located((By.ID, "login-password-input")))
            password_field.clear()
            password_field.send_keys(creds['password'])
            
            # Login button
            login_button = self.driver.find_element(By.ID, "login-submit-button")
            login_button.click()
            time.sleep(5)
            
            # Check success
            if creds['success_indicator'] in self.driver.current_url:
                logger.info("Indeed login successful")
                return True
            else:
                logger.warning("Indeed login may have failed")
                return False
                
        except Exception as e:
            logger.error(f"Indeed login error: {e}")
            return False
    
    def login_linkedin(self, creds):
        """Login to LinkedIn.com"""
        try:
            # Find email field
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field.clear()
            email_field.send_keys(creds['email'])
            
            # Find password field
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(creds['password'])
            
            # Click login
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            time.sleep(5)
            
            # Check success
            if creds['success_indicator'] in self.driver.current_url:
                logger.info("LinkedIn login successful")
                return True
            else:
                logger.warning("LinkedIn login may have failed")
                return False
                
        except Exception as e:
            logger.error(f"LinkedIn login error: {e}")
            return False
    
    def search_and_apply_jobs(self, keywords="data analyst", location="Chennai", max_applications=5):
        """Search for jobs and apply automatically"""
        logger.info(f"Starting automated job application: {keywords} in {location}")
        
        enabled_platforms = [p for p, c in self.credentials.items() if c.get('enabled')]
        
        for platform in enabled_platforms:
            print(f"\n🔍 Processing {platform.title()}...")
            
            if self.login_to_platform(platform):
                print(f"✅ Logged into {platform.title()}")
                
                if platform == 'naukri':
                    self.apply_naukri_jobs(keywords, location, max_applications)
                elif platform == 'indeed':
                    self.apply_indeed_jobs(keywords, location, max_applications)
                elif platform == 'linkedin':
                    self.apply_linkedin_jobs(keywords, location, max_applications)
                
            else:
                print(f"❌ Failed to login to {platform.title()}")
                
            time.sleep(5)  # Delay between platforms
    
    def apply_naukri_jobs(self, keywords, location, max_applications):
        """Apply to jobs on Naukri"""
        try:
            # Navigate to job search
            search_url = f"https://www.naukri.com/{keywords.replace(' ', '-')}-jobs-in-{location.lower()}"
            self.driver.get(search_url)
            time.sleep(3)
            
            # Find job listings
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-job-id]")[:max_applications]
            
            for i, job_card in enumerate(job_cards, 1):
                try:
                    # Extract job info
                    job_title = job_card.find_element(By.CSS_SELECTOR, ".title").text
                    company = job_card.find_element(By.CSS_SELECTOR, ".subTitle").text
                    
                    print(f"  📝 Applying to: {job_title} at {company}")
                    
                    # Click on job
                    job_card.click()
                    time.sleep(2)
                    
                    # Look for apply button
                    try:
                        apply_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Apply')]")
                        apply_button.click()
                        time.sleep(2)
                        
                        # Record application
                        application = {
                            'platform': 'Naukri',
                            'job_title': job_title,
                            'company': company,
                            'applied_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'status': 'Applied',
                            'method': 'Automated'
                        }
                        
                        self.applications_made.append(application)
                        print(f"  ✅ Applied successfully!")
                        
                    except:
                        print(f"  ⚠️ Apply button not found or already applied")
                    
                    time.sleep(3)  # Delay between applications
                    
                except Exception as e:
                    print(f"  ❌ Error applying to job {i}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in Naukri job application: {e}")
    
    def apply_indeed_jobs(self, keywords, location, max_applications):
        """Apply to jobs on Indeed"""
        try:
            # Navigate to job search
            search_url = f"https://in.indeed.com/jobs?q={keywords.replace(' ', '+')}&l={location}"
            self.driver.get(search_url)
            time.sleep(3)
            
            # Find job listings
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job_seen_beacon")[:max_applications]
            
            for i, job_card in enumerate(job_cards, 1):
                try:
                    # Extract job info
                    job_title = job_card.find_element(By.CSS_SELECTOR, "[data-testid='job-title']").text
                    company = job_card.find_element(By.CSS_SELECTOR, "[data-testid='company-name']").text
                    
                    print(f"  📝 Applying to: {job_title} at {company}")
                    
                    # Click on job
                    job_card.click()
                    time.sleep(2)
                    
                    # Look for apply button
                    try:
                        apply_button = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Apply')]")
                        apply_button.click()
                        time.sleep(3)
                        
                        # Handle application form if it appears
                        self.handle_indeed_application_form()
                        
                        # Record application
                        application = {
                            'platform': 'Indeed',
                            'job_title': job_title,
                            'company': company,
                            'applied_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'status': 'Applied',
                            'method': 'Automated'
                        }
                        
                        self.applications_made.append(application)
                        print(f"  ✅ Applied successfully!")
                        
                    except:
                        print(f"  ⚠️ Apply button not found or external application")
                    
                    time.sleep(3)
                    
                except Exception as e:
                    print(f"  ❌ Error applying to job {i}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in Indeed job application: {e}")
    
    def apply_linkedin_jobs(self, keywords, location, max_applications):
        """Apply to jobs on LinkedIn"""
        try:
            # Navigate to job search
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}&location={location}"
            self.driver.get(search_url)
            time.sleep(3)
            
            # Find job listings
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".jobs-search-results__list-item")[:max_applications]
            
            for i, job_card in enumerate(job_cards, 1):
                try:
                    # Extract job info
                    job_title = job_card.find_element(By.CSS_SELECTOR, ".job-card-list__title").text
                    company = job_card.find_element(By.CSS_SELECTOR, ".job-card-container__company-name").text
                    
                    print(f"  📝 Checking: {job_title} at {company}")
                    
                    # Click on job
                    job_card.click()
                    time.sleep(2)
                    
                    # Look for easy apply button
                    try:
                        easy_apply_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'jobs-apply-button')]")
                        
                        if "Easy Apply" in easy_apply_button.text:
                            easy_apply_button.click()
                            time.sleep(2)
                            
                            # Handle LinkedIn application process
                            self.handle_linkedin_application()
                            
                            # Record application
                            application = {
                                'platform': 'LinkedIn',
                                'job_title': job_title,
                                'company': company,
                                'applied_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'status': 'Applied',
                                'method': 'Easy Apply'
                            }
                            
                            self.applications_made.append(application)
                            print(f"  ✅ Easy Apply successful!")
                        else:
                            print(f"  ⚠️ External application required")
                            
                    except:
                        print(f"  ⚠️ Easy Apply not available")
                    
                    time.sleep(3)
                    
                except Exception as e:
                    print(f"  ❌ Error with job {i}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in LinkedIn job application: {e}")
    
    def handle_indeed_application_form(self):
        """Handle Indeed application form"""
        try:
            # Check if we're redirected to external site
            if "indeed.com" not in self.driver.current_url:
                print("  ⚠️ External application - manual completion required")
                time.sleep(2)
                self.driver.back()
                return
            
            # Look for resume upload
            try:
                resume_upload = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                resume_path = os.path.join(os.getcwd(), "resumes", "master_resume.pdf")
                if os.path.exists(resume_path):
                    resume_upload.send_keys(resume_path)
                    time.sleep(1)
            except:
                pass
            
            # Look for submit button
            try:
                submit_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit') or contains(text(), 'Apply')]")
                submit_button.click()
                time.sleep(2)
            except:
                print("  ⚠️ Manual submission required")
                
        except Exception as e:
            logger.error(f"Error handling Indeed form: {e}")
    
    def handle_linkedin_application(self):
        """Handle LinkedIn Easy Apply process"""
        try:
            # Handle multi-step application
            for step in range(3):  # Maximum 3 steps
                try:
                    # Look for next button
                    next_button = self.driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Continue') or contains(text(), 'Next')]")
                    next_button.click()
                    time.sleep(2)
                except:
                    break
            
            # Final submit
            try:
                submit_button = self.driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Submit application')]")
                submit_button.click()
                time.sleep(2)
            except:
                print("  ⚠️ Manual completion required")
                
        except Exception as e:
            logger.error(f"Error handling LinkedIn application: {e}")
    
    def save_application_results(self):
        """Save application results to file"""
        if not self.applications_made:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"credential_applications_{timestamp}.json"
        
        results = {
            'timestamp': timestamp,
            'total_applications': len(self.applications_made),
            'applications': self.applications_made
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📊 Application results saved to: {filename}")
    
    def show_results(self):
        """Display application results"""
        if not self.applications_made:
            print("\n⚠️ No applications were made")
            return
        
        print(f"\n🎉 APPLICATION RESULTS")
        print("=" * 40)
        print(f"📊 Total Applications: {len(self.applications_made)}")
        
        # Group by platform
        platform_stats = {}
        for app in self.applications_made:
            platform = app['platform']
            platform_stats[platform] = platform_stats.get(platform, 0) + 1
        
        print("\n📈 Applications by Platform:")
        for platform, count in platform_stats.items():
            print(f"  • {platform}: {count}")
        
        print("\n📋 Application Details:")
        for i, app in enumerate(self.applications_made, 1):
            print(f"{i}. {app['job_title']} at {app['company']} ({app['platform']})")
    
    def cleanup(self):
        """Cleanup browser and save results"""
        if self.driver:
            self.driver.quit()
        
        self.save_application_results()
        logger.info("Cleanup completed")

def main():
    print("🚀 CREDENTIAL-BASED AUTO APPLY SYSTEM")
    print("=" * 50)
    
    auto_apply = CredentialAutoApplySystem()
    
    try:
        if not auto_apply.credentials:
            print("❌ No credentials found. Please run credential_wizard.py first")
            return
        
        # Check for enabled credentials
        enabled_platforms = [p for p, c in auto_apply.credentials.items() if c.get('enabled')]
        
        if not enabled_platforms:
            print("❌ No platforms enabled. Your current credentials:")
            for platform, config in auto_apply.credentials.items():
                status = "✅ Enabled" if config.get('enabled') else "❌ Disabled"
                identifier = config.get('email', config.get('username', 'Not set'))
                print(f"   {platform.title()}: {status} ({identifier})")
            
            print(f"\n🔧 Please run credential_wizard.py to enable a platform")
            return
        
        # Get job search parameters
        print(f"\n🔍 JOB SEARCH CONFIGURATION")
        print("-" * 30)
        
        keywords = input("🎯 Job Keywords (default: data analyst): ") or "data analyst"
        location = input("📍 Location (default: Chennai): ") or "Chennai"
        max_apps = input("📊 Max applications per platform (default: 3): ") or "3"
        
        try:
            max_apps = int(max_apps)
        except:
            max_apps = 3
        
        # Setup browser
        print(f"\n🌐 Setting up browser...")
        auto_apply.setup_browser()
        
        # Start automated application process
        print(f"\n🤖 Starting automated job applications...")
        auto_apply.search_and_apply_jobs(keywords, location, max_apps)
        
        # Show results
        auto_apply.show_results()
        
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Main process error: {e}")
    finally:
        auto_apply.cleanup()
        print(f"\n✅ Process completed")

if __name__ == "__main__":
    main()
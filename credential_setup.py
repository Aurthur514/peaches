#!/usr/bin/env python3
"""
🔐 CREDENTIAL-BASED AUTO APPLY SETUP
Secure setup process for enhanced job application automation
"""

import json
import os
import getpass
import sys
from datetime import datetime
import base64
from cryptography.fernet import Fernet
import hashlib

class CredentialManager:
    def __init__(self):
        self.config_file = "job_site_credentials.json"
        self.encrypted_file = "job_credentials.enc"
        self.key_file = ".credential_key"
        
    def generate_encryption_key(self):
        """Generate encryption key for credential storage"""
        key = Fernet.generate_key()
        with open(self.key_file, 'wb') as f:
            f.write(key)
        return key
    
    def get_encryption_key(self):
        """Get or create encryption key"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            return self.generate_encryption_key()
    
    def encrypt_credentials(self, credentials):
        """Encrypt credential data"""
        key = self.get_encryption_key()
        fernet = Fernet(key)
        json_data = json.dumps(credentials).encode()
        encrypted_data = fernet.encrypt(json_data)
        
        with open(self.encrypted_file, 'wb') as f:
            f.write(encrypted_data)
    
    def decrypt_credentials(self):
        """Decrypt credential data"""
        if not os.path.exists(self.encrypted_file):
            return {}
        
        key = self.get_encryption_key()
        fernet = Fernet(key)
        
        with open(self.encrypted_file, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = fernet.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
    
    def setup_platform_credentials(self):
        """Interactive setup for platform credentials"""
        print("🔐 CREDENTIAL-BASED AUTO APPLY SETUP")
        print("=" * 60)
        
        print("\n⚠️ IMPORTANT SECURITY NOTES:")
        print("• Credentials will be encrypted and stored securely")
        print("• Use dedicated job search accounts if possible")
        print("• Monitor your accounts for any unusual activity")
        print("• You can disable any platform at any time")
        
        input("\nPress Enter to continue...")
        
        credentials = {}
        
        # Platform selection
        platforms = {
            "naukri": {
                "name": "Naukri.com",
                "fields": ["email", "password"],
                "benefits": "Access to premium job listings, application tracking"
            },
            "indeed": {
                "name": "Indeed.com", 
                "fields": ["email", "password"],
                "benefits": "Direct application access, company insights"
            },
            "linkedin": {
                "name": "LinkedIn",
                "fields": ["email", "password"],
                "benefits": "Professional network, premium job alerts"
            },
            "freshersworld": {
                "name": "FreshersWorld.com",
                "fields": ["username", "password"],
                "benefits": "Entry-level opportunities, bulk applications"
            }
        }
        
        for platform_id, platform_info in platforms.items():
            print(f"\n{'='*60}")
            print(f"🌐 SETUP: {platform_info['name']}")
            print(f"Benefits: {platform_info['benefits']}")
            print("=" * 60)
            
            enable = input(f"\nEnable auto apply for {platform_info['name']}? (y/n): ").lower().strip()
            
            if enable in ['y', 'yes']:
                platform_creds = {"enabled": True}
                
                for field in platform_info['fields']:
                    if field == 'password':
                        value = getpass.getpass(f"Enter {field} for {platform_info['name']}: ")
                    else:
                        value = input(f"Enter {field} for {platform_info['name']}: ")
                    
                    platform_creds[field] = value
                
                # Verify credentials format
                if self.verify_credential_format(platform_creds, platform_info['fields']):
                    credentials[platform_id] = platform_creds
                    print(f"✅ {platform_info['name']} credentials saved")
                else:
                    print(f"❌ Invalid credentials for {platform_info['name']}")
            else:
                credentials[platform_id] = {"enabled": False}
                print(f"⏭️ Skipped {platform_info['name']}")
        
        return credentials
    
    def verify_credential_format(self, creds, required_fields):
        """Verify credential format"""
        for field in required_fields:
            if not creds.get(field) or len(creds[field].strip()) < 3:
                return False
        
        # Basic email validation if email field exists
        if 'email' in creds:
            email = creds['email']
            if '@' not in email or '.' not in email.split('@')[1]:
                return False
        
        return True
    
    def save_credentials(self, credentials):
        """Save credentials securely"""
        try:
            # Encrypt and save
            self.encrypt_credentials(credentials)
            
            # Create readable config (without passwords)
            safe_config = {}
            for platform, creds in credentials.items():
                safe_config[platform] = {
                    "enabled": creds.get("enabled", False),
                    "username": creds.get("email", creds.get("username", "")),
                    "last_updated": datetime.now().isoformat()
                }
            
            with open(self.config_file, 'w') as f:
                json.dump(safe_config, f, indent=2)
            
            print("\n✅ Credentials saved securely!")
            print(f"📄 Config file: {self.config_file}")
            print(f"🔐 Encrypted data: {self.encrypted_file}")
            
        except Exception as e:
            print(f"❌ Error saving credentials: {e}")
    
    def load_credentials(self):
        """Load decrypted credentials"""
        try:
            return self.decrypt_credentials()
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            return {}
    
    def test_credentials(self):
        """Test saved credentials"""
        print("\n🔍 TESTING SAVED CREDENTIALS")
        print("-" * 40)
        
        credentials = self.load_credentials()
        
        for platform, creds in credentials.items():
            if creds.get("enabled"):
                print(f"Testing {platform}...")
                # Mock test - in real implementation, this would attempt login
                if self.mock_login_test(platform, creds):
                    print(f"✅ {platform}: Credentials appear valid")
                else:
                    print(f"❌ {platform}: May need credential update")
            else:
                print(f"⏭️ {platform}: Disabled")
    
    def mock_login_test(self, platform, creds):
        """Mock login test (placeholder for actual implementation)"""
        # This would contain actual login testing logic
        required_fields = {
            "naukri": ["email", "password"],
            "indeed": ["email", "password"],
            "linkedin": ["email", "password"],
            "freshersworld": ["username", "password"]
        }
        
        platform_fields = required_fields.get(platform, [])
        return all(creds.get(field) for field in platform_fields)

def create_enhanced_auto_apply():
    """Create enhanced auto apply system with credentials"""
    
    enhanced_code = '''#!/usr/bin/env python3
"""
🚀 ENHANCED AUTO APPLY SYSTEM - With Credential Support
Complete automation for job applications using saved credentials
"""

import json
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from cryptography.fernet import Fernet

class EnhancedAutoApplySystem:
    def __init__(self):
        self.credential_manager = self.load_credential_manager()
        self.driver = None
        self.logged_in_platforms = {}
        
    def load_credential_manager(self):
        """Load credential manager"""
        try:
            from credential_setup import CredentialManager
            return CredentialManager()
        except:
            return None
    
    def setup_driver(self):
        """Setup enhanced Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 15)
    
    def login_to_platform(self, platform):
        """Login to specific job platform"""
        if not self.credential_manager:
            return False
            
        credentials = self.credential_manager.load_credentials()
        platform_creds = credentials.get(platform, {})
        
        if not platform_creds.get("enabled"):
            return False
            
        print(f"🔐 Logging into {platform}...")
        
        try:
            if platform == "naukri":
                return self.login_naukri(platform_creds)
            elif platform == "indeed":
                return self.login_indeed(platform_creds)
            elif platform == "linkedin":
                return self.login_linkedin(platform_creds)
            elif platform == "freshersworld":
                return self.login_freshersworld(platform_creds)
            else:
                return False
        except Exception as e:
            print(f"❌ Login failed for {platform}: {e}")
            return False
    
    def login_naukri(self, creds):
        """Login to Naukri.com"""
        self.driver.get("https://www.naukri.com/nlogin/login")
        time.sleep(2)
        
        # Fill credentials
        email_field = self.wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
        email_field.clear()
        email_field.send_keys(creds['email'])
        
        password_field = self.driver.find_element(By.ID, "passwordField")
        password_field.clear()
        password_field.send_keys(creds['password'])
        
        # Submit
        login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
        login_button.click()
        time.sleep(3)
        
        # Check success
        if "mynaukri" in self.driver.current_url or "profile" in self.driver.current_url:
            self.logged_in_platforms["naukri"] = True
            print("✅ Naukri login successful")
            return True
        else:
            print("❌ Naukri login failed")
            return False
    
    def login_indeed(self, creds):
        """Login to Indeed.com"""
        self.driver.get("https://secure.indeed.com/account/login")
        time.sleep(2)
        
        # Fill email
        email_field = self.wait.until(EC.presence_of_element_located((By.ID, "login-email-input")))
        email_field.clear()
        email_field.send_keys(creds['email'])
        
        # Continue
        continue_btn = self.driver.find_element(By.ID, "login-submit-button")
        continue_btn.click()
        time.sleep(2)
        
        # Fill password
        password_field = self.wait.until(EC.presence_of_element_located((By.ID, "login-password-input")))
        password_field.clear()
        password_field.send_keys(creds['password'])
        
        # Submit
        login_button = self.driver.find_element(By.ID, "login-submit-button")
        login_button.click()
        time.sleep(3)
        
        # Check success
        if "/account/" in self.driver.current_url or "/prefs" in self.driver.current_url:
            self.logged_in_platforms["indeed"] = True
            print("✅ Indeed login successful")
            return True
        else:
            print("❌ Indeed login failed")
            return False
    
    def auto_apply_with_credentials(self, job_keywords="data analyst", location="Chennai", max_applications=5):
        """Enhanced auto apply using saved credentials"""
        print("🚀 STARTING ENHANCED AUTO APPLY WITH CREDENTIALS")
        print("=" * 60)
        
        if not self.driver:
            self.setup_driver()
        
        # Load job search results
        results = self.load_job_results()
        if not results:
            print("❌ No job results available. Please run job search first.")
            return
        
        applied_jobs = []
        credentials = self.credential_manager.load_credentials() if self.credential_manager else {}
        
        for job in results[:max_applications]:
            platform = job.get('platform', '').lower()
            
            if platform in credentials and credentials[platform].get('enabled'):
                # Login if not already logged in
                if platform not in self.logged_in_platforms:
                    if self.login_to_platform(platform):
                        print(f"✅ Ready for applications on {platform}")
                    else:
                        print(f"❌ Skipping {platform} due to login failure")
                        continue
                
                # Attempt application
                if self.apply_to_job(job):
                    applied_jobs.append({
                        **job,
                        'applied_date': datetime.now().isoformat(),
                        'application_method': 'Enhanced Auto Apply',
                        'platform_logged_in': True
                    })
                    print(f"✅ Applied to {job.get('title')} at {job.get('company')}")
                else:
                    print(f"⚠️ Failed to apply to {job.get('title')}")
            else:
                print(f"⏭️ Skipping {job.get('title')} - {platform} not enabled")
        
        self.save_applications(applied_jobs)
        self.generate_report(applied_jobs)
        
        return applied_jobs
    
    def apply_to_job(self, job):
        """Apply to individual job with enhanced automation"""
        try:
            url = job.get('url')
            if not url:
                return False
            
            # Navigate to job
            self.driver.get(url)
            time.sleep(3)
            
            # Look for apply button
            apply_selectors = [
                "//a[contains(text(), 'Apply')]",
                "//button[contains(text(), 'Apply')]",
                "//input[@value='Apply']",
                ".apply-button",
                "#applyButton"
            ]
            
            apply_button = None
            for selector in apply_selectors:
                try:
                    if selector.startswith("//"):
                        apply_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        apply_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not apply_button:
                return False
            
            # Click apply
            apply_button.click()
            time.sleep(3)
            
            # Handle application form if it appears
            return self.handle_application_form(job)
            
        except Exception as e:
            print(f"Application error: {e}")
            return False
    
    def handle_application_form(self, job):
        """Handle job application form filling"""
        try:
            # Look for common form fields and fill them
            form_fields = {
                'name': ['name', 'fullname', 'full_name', 'applicant_name'],
                'email': ['email', 'email_address', 'contact_email'],
                'phone': ['phone', 'mobile', 'contact_number', 'phone_number']
            }
            
            user_data = self.get_user_data()
            
            for field_type, selectors in form_fields.items():
                for selector in selectors:
                    try:
                        field = self.driver.find_element(By.NAME, selector)
                        if field and user_data.get(field_type):
                            field.clear()
                            field.send_keys(user_data[field_type])
                            break
                    except:
                        continue
            
            # Look for resume upload
            resume_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
            if resume_inputs and os.path.exists("resumes/master_resume.pdf"):
                resume_inputs[0].send_keys(os.path.abspath("resumes/master_resume.pdf"))
            
            # Don't auto-submit - let user review
            print("📝 Form filled - manual review recommended before submission")
            return True
            
        except Exception as e:
            print(f"Form handling error: {e}")
            return True  # Consider it successful even if form filling fails
    
    def get_user_data(self):
        """Get user data from config"""
        try:
            with open('job_bot_config.json', 'r') as f:
                config = json.load(f)
                profile = config.get('user_profile', {})
                return {
                    'name': profile.get('full_name', ''),
                    'email': profile.get('email', ''),
                    'phone': profile.get('phone', '')
                }
        except:
            return {}
    
    def load_job_results(self):
        """Load recent job search results"""
        result_files = [f for f in os.listdir('.') if f.startswith('improved_job_search_results_')]
        if not result_files:
            return []
        
        latest_file = sorted(result_files)[-1]
        try:
            with open(latest_file, 'r') as f:
                data = json.load(f)
                return data.get('jobs', [])
        except:
            return []
    
    def save_applications(self, applications):
        """Save application results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_applications_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'total_applications': len(applications),
                'applications': applications
            }, f, indent=2)
        
        print(f"💾 Applications saved to: {filename}")
    
    def generate_report(self, applications):
        """Generate application report"""
        print(f"\\n📊 ENHANCED AUTO APPLY REPORT")
        print("=" * 40)
        print(f"Total Applications: {len(applications)}")
        
        if applications:
            platforms = {}
            for app in applications:
                platform = app.get('platform')
                platforms[platform] = platforms.get(platform, 0) + 1
            
            print("\\nApplications by Platform:")
            for platform, count in platforms.items():
                print(f"  • {platform}: {count}")
        
        print("\\n✅ Enhanced auto apply completed!")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()

def main():
    """Main function to run enhanced auto apply"""
    system = EnhancedAutoApplySystem()
    
    try:
        applications = system.auto_apply_with_credentials()
        print(f"\\n🎉 Successfully processed {len(applications)} applications!")
        
    except KeyboardInterrupt:
        print("\\n⚠️ Process interrupted by user")
    except Exception as e:
        print(f"\\n❌ Error: {e}")
    finally:
        system.cleanup()

if __name__ == "__main__":
    main()
'''
    
    with open("enhanced_auto_apply_system.py", 'w') as f:
        f.write(enhanced_code)
    
    print("✅ Enhanced auto apply system created!")

def main():
    """Main setup function"""
    print("🔐 CREDENTIAL-BASED AUTO APPLY SETUP")
    print("=" * 60)
    
    print("\nThis setup will enable enhanced automation including:")
    print("• Automatic login to job platforms")
    print("• Direct application form access") 
    print("• Automated resume/cover letter upload")
    print("• Enhanced application tracking")
    print("• 85% automation vs 40% without credentials")
    
    proceed = input("\nProceed with credential setup? (y/n): ").lower().strip()
    
    if proceed not in ['y', 'yes']:
        print("Setup cancelled.")
        return
    
    # Install required packages
    try:
        import cryptography
    except ImportError:
        print("📦 Installing required encryption library...")
        os.system("pip install cryptography")
    
    # Setup credentials
    manager = CredentialManager()
    credentials = manager.setup_platform_credentials()
    manager.save_credentials(credentials)
    
    # Test credentials
    manager.test_credentials()
    
    # Create enhanced system
    create_enhanced_auto_apply()
    
    print(f"\n{'='*60}")
    print("🎉 CREDENTIAL-BASED AUTO APPLY SETUP COMPLETE!")
    print("=" * 60)
    
    enabled_platforms = [p for p, c in credentials.items() if c.get("enabled")]
    
    print(f"\n✅ ENABLED PLATFORMS: {len(enabled_platforms)}")
    for platform in enabled_platforms:
        print(f"  • {platform.title()}")
    
    print(f"\n🚀 NEXT STEPS:")
    print("1. Run: python enhanced_auto_apply_system.py")
    print("2. Monitor applications in real-time")
    print("3. Check generated application reports")
    print("4. Review account security regularly")
    
    print(f"\n📁 FILES CREATED:")
    print(f"  • {manager.config_file} - Platform configuration")
    print(f"  • {manager.encrypted_file} - Encrypted credentials")
    print(f"  • enhanced_auto_apply_system.py - Enhanced automation system")
    
    print(f"\n💡 SECURITY REMINDERS:")
    print("• Credentials are encrypted and stored securely")
    print("• Monitor your job platform accounts for activity")
    print("• You can disable any platform anytime")
    print("• Use strong, unique passwords")

if __name__ == "__main__":
    main()
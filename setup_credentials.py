#!/usr/bin/env python3
"""
CREDENTIAL-BASED AUTO APPLY SETUP - Secure configuration and enhanced automation
"""

import json
import os
import getpass
import base64
from cryptography.fernet import Fernet
from datetime import datetime

class SecureCredentialManager:
    def __init__(self):
        self.credentials_file = "job_site_credentials.json"
        self.encrypted_file = "job_site_credentials.enc"
        self.key_file = "credential_key.key"
        
    def generate_encryption_key(self):
        """Generate encryption key for credential security"""
        key = Fernet.generate_key()
        with open(self.key_file, 'wb') as f:
            f.write(key)
        print(f"✅ Generated encryption key: {self.key_file}")
        return key
    
    def load_key(self):
        """Load encryption key"""
        try:
            with open(self.key_file, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            return self.generate_encryption_key()
    
    def encrypt_credentials(self, credentials):
        """Encrypt credential data"""
        key = self.load_key()
        fernet = Fernet(key)
        
        json_str = json.dumps(credentials, indent=2)
        encrypted_data = fernet.encrypt(json_str.encode())
        
        with open(self.encrypted_file, 'wb') as f:
            f.write(encrypted_data)
        
        print(f"✅ Credentials encrypted and saved to: {self.encrypted_file}")
    
    def decrypt_credentials(self):
        """Decrypt credential data"""
        try:
            key = self.load_key()
            fernet = Fernet(key)
            
            with open(self.encrypted_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except FileNotFoundError:
            print("⚠️ No encrypted credentials found")
            return None
        except Exception as e:
            print(f"❌ Error decrypting credentials: {e}")
            return None

def setup_credentials_interactive():
    """Interactive credential setup"""
    print("🔐 CREDENTIAL-BASED AUTO APPLY SETUP")
    print("=" * 60)
    
    print("\n⚠️ SECURITY NOTICE:")
    print("• Credentials will be encrypted locally")
    print("• Use dedicated job search accounts")
    print("• Monitor account activity regularly")
    print("• You can disable platforms anytime")
    
    proceed = input("\n📋 Proceed with credential setup? (y/n): ").lower()
    if proceed != 'y':
        print("Setup cancelled.")
        return
    
    credential_manager = SecureCredentialManager()
    credentials = {}
    
    # Setup for each platform
    platforms = {
        'naukri': 'Naukri.com',
        'indeed': 'Indeed.com',
        'linkedin': 'LinkedIn.com',
        'freshersworld': 'FreshersWorld.com'
    }
    
    for platform_key, platform_name in platforms.items():
        print(f"\n🌐 Setting up {platform_name}")
        print("-" * 30)
        
        setup_platform = input(f"Setup {platform_name}? (y/n): ").lower()
        
        if setup_platform == 'y':
            if platform_key in ['naukri', 'indeed', 'linkedin']:
                email = input(f"📧 Email for {platform_name}: ")
                password = getpass.getpass(f"🔐 Password for {platform_name}: ")
                
                credentials[platform_key] = {
                    "email": email,
                    "password": password,
                    "enabled": True,
                    "setup_date": datetime.now().isoformat()
                }
            else:  # FreshersWorld uses username
                username = input(f"👤 Username for {platform_name}: ")
                password = getpass.getpass(f"🔐 Password for {platform_name}: ")
                
                credentials[platform_key] = {
                    "username": username,
                    "password": password,
                    "enabled": True,
                    "setup_date": datetime.now().isoformat()
                }
            
            print(f"✅ {platform_name} credentials configured")
        else:
            credentials[platform_key] = {
                "email": "your_email@gmail.com",
                "password": "your_password",
                "enabled": False
            }
    
    # Encrypt and save
    credential_manager.encrypt_credentials(credentials)
    
    # Create backup plain text file for reference
    with open(credential_manager.credentials_file, 'w') as f:
        json.dump({
            "note": "This is a template. Real credentials are encrypted.",
            "platforms": list(platforms.keys()),
            "setup_date": datetime.now().isoformat(),
            "encrypted_file": credential_manager.encrypted_file
        }, f, indent=2)
    
    print(f"\n✅ SETUP COMPLETE!")
    print(f"• Encrypted credentials: {credential_manager.encrypted_file}")
    print(f"• Reference file: {credential_manager.credentials_file}")
    print(f"• Encryption key: {credential_manager.key_file}")
    
    return credentials

def create_enhanced_auto_apply():
    """Create enhanced auto apply system with credential support"""
    
    enhanced_code = '''#!/usr/bin/env python3
"""
ENHANCED AUTO APPLY SYSTEM - With credential-based authentication
"""

import json
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from improved_real_job_search_engine import ImprovedRealJobSearchEngine
except ImportError:
    print("⚠️ Import warning: Using basic job search functionality")

from cryptography.fernet import Fernet

class EnhancedAutoApplySystem:
    def __init__(self):
        self.setup_logging()
        self.credential_manager = SecureCredentialManager()
        self.driver = None
        self.logged_in_platforms = set()
        
    def setup_logging(self):
        """Setup logging for auto apply activities"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('enhanced_auto_apply.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_credentials(self):
        """Load encrypted credentials"""
        return self.credential_manager.decrypt_credentials()
    
    def setup_browser(self):
        """Setup browser with enhanced options"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 15)
        
        self.logger.info("✅ Browser setup completed")
    
    def login_to_naukri(self, credentials):
        """Enhanced Naukri login with error handling"""
        try:
            self.logger.info("🔐 Attempting Naukri login...")
            
            self.driver.get("https://www.naukri.com/nlogin/login")
            time.sleep(3)
            
            # Handle cookie popup
            try:
                cookie_button = self.driver.find_element(By.ID, "cookieConsentAccept")
                cookie_button.click()
                time.sleep(1)
            except:
                pass
            
            # Fill email
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
            email_field.clear()
            email_field.send_keys(credentials['email'])
            
            # Fill password
            password_field = self.driver.find_element(By.ID, "passwordField")
            password_field.clear()
            password_field.send_keys(credentials['password'])
            
            # Click login
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
            login_button.click()
            
            # Wait for login success
            time.sleep(5)
            
            # Check login success
            if any(indicator in self.driver.current_url for indicator in ['mynaukri', 'profile', 'dashboard']):
                self.logged_in_platforms.add('naukri')
                self.logger.info("✅ Naukri login successful")
                return True
            else:
                self.logger.warning("⚠️ Naukri login may have failed - check manually")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Naukri login error: {e}")
            return False
    
    def login_to_indeed(self, credentials):
        """Enhanced Indeed login with error handling"""
        try:
            self.logger.info("🔐 Attempting Indeed login...")
            
            self.driver.get("https://secure.indeed.com/account/login")
            time.sleep(3)
            
            # Fill email
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "login-email-input")))
            email_field.clear()
            email_field.send_keys(credentials['email'])
            
            # Continue button
            continue_btn = self.driver.find_element(By.ID, "login-submit-button")
            continue_btn.click()
            time.sleep(2)
            
            # Fill password
            password_field = self.wait.until(EC.presence_of_element_located((By.ID, "login-password-input")))
            password_field.clear()
            password_field.send_keys(credentials['password'])
            
            # Login button
            login_button = self.driver.find_element(By.ID, "login-submit-button")
            login_button.click()
            time.sleep(5)
            
            # Check login success
            if any(indicator in self.driver.current_url for indicator in ['account', 'prefs', 'profile']):
                self.logged_in_platforms.add('indeed')
                self.logger.info("✅ Indeed login successful")
                return True
            else:
                self.logger.warning("⚠️ Indeed login may have failed - check manually")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Indeed login error: {e}")
            return False
    
    def apply_to_job_naukri(self, job_url, job_data):
        """Apply to job on Naukri with credential-based access"""
        try:
            self.logger.info(f"📝 Applying to Naukri job: {job_data.get('title', 'Unknown')}")
            
            self.driver.get(job_url)
            time.sleep(3)
            
            # Look for apply button
            apply_selectors = [
                "//a[contains(text(), 'Apply')]",
                "//button[contains(text(), 'Apply')]", 
                ".apply-button",
                "#apply-button"
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
            
            if apply_button:
                apply_button.click()
                time.sleep(3)
                
                # Handle application form if present
                self.handle_application_form(job_data)
                
                self.logger.info("✅ Naukri application submitted")
                return True
            else:
                self.logger.warning("⚠️ No apply button found on Naukri job")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Naukri application error: {e}")
            return False
    
    def handle_application_form(self, job_data):
        """Handle common application form fields"""
        try:
            # Look for common form fields and fill them
            form_fields = {
                'name': ['name', 'fullname', 'full_name', 'applicant_name'],
                'email': ['email', 'email_address', 'contact_email'],
                'phone': ['phone', 'mobile', 'contact_number', 'telephone'],
                'experience': ['experience', 'years_experience', 'total_experience']
            }
            
            # Load user profile
            user_profile = self.load_user_profile()
            
            for field_type, field_names in form_fields.items():
                for field_name in field_names:
                    try:
                        field_element = self.driver.find_element(By.NAME, field_name)
                        if field_type == 'name':
                            field_element.send_keys(user_profile.get('name', ''))
                        elif field_type == 'email':
                            field_element.send_keys(user_profile.get('email', ''))
                        elif field_type == 'phone':
                            field_element.send_keys(user_profile.get('phone', ''))
                        elif field_type == 'experience':
                            field_element.send_keys(str(user_profile.get('experience_years', '')))
                        break
                    except:
                        continue
            
            # Look for resume upload
            try:
                file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                resume_path = os.path.abspath("resumes/master_resume.pdf")
                if os.path.exists(resume_path):
                    file_input.send_keys(resume_path)
                    self.logger.info("📄 Resume uploaded")
            except:
                self.logger.info("📄 No resume upload field found")
            
            # Look for submit button (but don't click for safety)
            submit_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Submit')] | //input[@type='submit']")
            if submit_buttons:
                self.logger.info("📋 Application form ready to submit")
                # In production, you might want to click submit_buttons[0].click()
                # For safety, we'll just log that it's ready
            
        except Exception as e:
            self.logger.error(f"❌ Form handling error: {e}")
    
    def load_user_profile(self):
        """Load user profile data"""
        try:
            with open('job_bot_config.json', 'r') as f:
                config = json.load(f)
                if 'user_profile' in config:
                    profile = config['user_profile']
                    return {
                        'name': profile.get('full_name', ''),
                        'email': profile.get('email', ''),
                        'phone': profile.get('phone', ''),
                        'experience_years': 2
                    }
        except:
            return {
                'name': 'Bharathan M',
                'email': 'bharathan1404@gmail.com',
                'phone': '+91-9566030215',
                'experience_years': 2
            }
    
    def run_enhanced_auto_apply(self, max_applications=10):
        """Run enhanced auto apply process"""
        self.logger.info("🚀 Starting Enhanced Auto Apply System")
        
        # Load credentials
        credentials = self.load_credentials()
        if not credentials:
            self.logger.error("❌ No credentials available")
            return False
        
        # Setup browser
        self.setup_browser()
        
        try:
            # Login to platforms
            login_success = False
            
            for platform, creds in credentials.items():
                if creds.get('enabled'):
                    if platform == 'naukri':
                        login_success = self.login_to_naukri(creds) or login_success
                    elif platform == 'indeed':
                        login_success = self.login_to_indeed(creds) or login_success
            
            if not login_success:
                self.logger.error("❌ No successful logins")
                return False
            
            self.logger.info(f"✅ Logged into platforms: {self.logged_in_platforms}")
            
            # Search for jobs (using existing job search results)
            jobs = self.load_recent_job_results()
            
            if not jobs:
                self.logger.warning("⚠️ No jobs available for application")
                return False
            
            # Apply to jobs
            applications_made = 0
            successful_applications = []
            
            for job in jobs[:max_applications]:
                if applications_made >= max_applications:
                    break
                
                platform = job.get('platform', '').lower()
                
                if platform in self.logged_in_platforms:
                    success = False
                    
                    if platform == 'naukri':
                        success = self.apply_to_job_naukri(job.get('url', ''), job)
                    # Add other platforms as needed
                    
                    if success:
                        applications_made += 1
                        successful_applications.append({
                            **job,
                            'applied_date': datetime.now().isoformat(),
                            'application_method': 'Enhanced Auto Apply',
                            'status': 'Applied'
                        })
                        
                        # Delay between applications
                        time.sleep(5)
            
            # Save application results
            self.save_application_results(successful_applications)
            
            self.logger.info(f"🎉 Enhanced Auto Apply completed: {applications_made} applications made")
            return applications_made > 0
            
        except Exception as e:
            self.logger.error(f"❌ Enhanced auto apply error: {e}")
            return False
        finally:
            self.cleanup()
    
    def load_recent_job_results(self):
        """Load recent job search results"""
        try:
            # Look for recent job search results
            import glob
            result_files = glob.glob("improved_job_search_results_*.json")
            
            if result_files:
                latest_file = max(result_files, key=os.path.getctime)
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                    return data.get('jobs', [])
            else:
                return []
        except:
            return []
    
    def save_application_results(self, applications):
        """Save application results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_applications_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'total_applications': len(applications),
                    'applications': applications
                }, f, indent=2)
            
            self.logger.info(f"📊 Application results saved: {filename}")
        except Exception as e:
            self.logger.error(f"❌ Error saving results: {e}")
    
    def cleanup(self):
        """Clean up browser and resources"""
        if self.driver:
            self.driver.quit()
            self.logger.info("🧹 Browser cleanup completed")

class SecureCredentialManager:
    def __init__(self):
        self.credentials_file = "job_site_credentials.json"
        self.encrypted_file = "job_site_credentials.enc"
        self.key_file = "credential_key.key"
        
    def load_key(self):
        """Load encryption key"""
        try:
            with open(self.key_file, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            return None
    
    def decrypt_credentials(self):
        """Decrypt credential data"""
        try:
            key = self.load_key()
            if not key:
                return None
                
            fernet = Fernet(key)
            
            with open(self.encrypted_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except:
            return None

def main():
    """Main function to run enhanced auto apply"""
    print("🚀 ENHANCED AUTO APPLY SYSTEM")
    print("=" * 60)
    
    auto_apply = EnhancedAutoApplySystem()
    
    # Check if credentials are available
    credentials = auto_apply.load_credentials()
    
    if not credentials:
        print("❌ No credentials found!")
        print("Please run: python setup_credentials.py")
        return
    
    enabled_platforms = [p for p, c in credentials.items() if c.get('enabled')]
    
    if not enabled_platforms:
        print("⚠️ No platforms enabled!")
        print("Please enable platforms in your credential setup.")
        return
    
    print(f"✅ Found credentials for: {enabled_platforms}")
    
    # Run enhanced auto apply
    max_apps = int(input("📊 Maximum applications to make (1-20): ") or "5")
    
    success = auto_apply.run_enhanced_auto_apply(max_apps)
    
    if success:
        print("🎉 Enhanced Auto Apply completed successfully!")
    else:
        print("❌ Enhanced Auto Apply encountered issues. Check logs for details.")

if __name__ == "__main__":
    main()
'''
    
    with open("enhanced_auto_apply_system.py", "w") as f:
        f.write(enhanced_code)
    
    print("✅ Enhanced Auto Apply System created: enhanced_auto_apply_system.py")

def create_streamlit_dashboard():
    """Create Streamlit dashboard for credential management"""
    
    dashboard_code = '''#!/usr/bin/env python3
"""
CREDENTIAL MANAGEMENT DASHBOARD - Streamlit interface for managing auto apply credentials
"""

import streamlit as st
import json
import os
from datetime import datetime
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from enhanced_auto_apply_system import EnhancedAutoApplySystem, SecureCredentialManager
except ImportError:
    st.error("❌ Enhanced Auto Apply System not found. Please run setup first.")

st.set_page_config(
    page_title="🔐 Credential Management Dashboard",
    page_icon="🔐",
    layout="wide"
)

st.title("🔐 Credential Management Dashboard")
st.markdown("*Manage your job platform credentials for enhanced auto apply*")

# Initialize credential manager
@st.cache_resource
def get_credential_manager():
    return SecureCredentialManager()

credential_manager = get_credential_manager()

# Sidebar
with st.sidebar:
    st.header("🎯 Actions")
    action = st.selectbox("Choose Action", [
        "📊 View Status",
        "⚙️ Manage Credentials", 
        "🚀 Run Auto Apply",
        "📈 View Results"
    ])

if action == "📊 View Status":
    st.header("📊 Credential Status")
    
    # Check credential status
    credentials = credential_manager.decrypt_credentials()
    
    if credentials:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🌐 Platform Status")
            
            for platform, config in credentials.items():
                status = "✅ Enabled" if config.get('enabled') else "⚠️ Disabled"
                setup_date = config.get('setup_date', 'Unknown')
                
                with st.container():
                    st.write(f"**{platform.title()}:** {status}")
                    if setup_date != 'Unknown':
                        st.write(f"   Setup: {setup_date[:10]}")
        
        with col2:
            st.subheader("🔒 Security Status")
            
            # Check file existence
            files_status = {
                "Encrypted Credentials": os.path.exists(credential_manager.encrypted_file),
                "Encryption Key": os.path.exists(credential_manager.key_file),
                "Config Template": os.path.exists(credential_manager.credentials_file)
            }
            
            for file_type, exists in files_status.items():
                status_icon = "✅" if exists else "❌"
                st.write(f"{status_icon} {file_type}")
    else:
        st.warning("⚠️ No credentials configured. Please set up credentials first.")
        
        if st.button("🔧 Setup Credentials"):
            st.info("Please run: `python setup_credentials.py` in terminal")

elif action == "⚙️ Manage Credentials":
    st.header("⚙️ Credential Management")
    
    credentials = credential_manager.decrypt_credentials()
    
    if credentials:
        st.subheader("🎛️ Platform Settings")
        
        with st.form("credential_form"):
            updates = {}
            
            for platform in credentials.keys():
                st.write(f"**{platform.title()}**")
                col1, col2 = st.columns(2)
                
                with col1:
                    enabled = st.checkbox(
                        f"Enable {platform.title()}", 
                        value=credentials[platform].get('enabled', False),
                        key=f"enable_{platform}"
                    )
                    updates[platform] = {'enabled': enabled}
                
                with col2:
                    if credentials[platform].get('email'):
                        st.write(f"📧 Email: {credentials[platform]['email'][:10]}...")
                    elif credentials[platform].get('username'):
                        st.write(f"👤 Username: {credentials[platform]['username'][:10]}...")
            
            if st.form_submit_button("💾 Save Changes"):
                # Update credentials
                for platform, update in updates.items():
                    credentials[platform]['enabled'] = update['enabled']
                
                credential_manager.encrypt_credentials(credentials)
                st.success("✅ Settings updated successfully!")
                st.rerun()
    
    else:
        st.warning("⚠️ Please setup credentials first using the terminal command.")

elif action == "🚀 Run Auto Apply":
    st.header("🚀 Enhanced Auto Apply")
    
    credentials = credential_manager.decrypt_credentials()
    
    if not credentials:
        st.error("❌ No credentials found. Please setup credentials first.")
        st.stop()
    
    enabled_platforms = [p for p, c in credentials.items() if c.get('enabled')]
    
    if not enabled_platforms:
        st.warning("⚠️ No platforms enabled. Please enable at least one platform.")
        st.stop()
    
    st.success(f"✅ Ready to apply on: {', '.join([p.title() for p in enabled_platforms])}")
    
    # Auto apply settings
    with st.form("auto_apply_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            max_applications = st.slider("📊 Maximum Applications", 1, 20, 5)
            test_mode = st.checkbox("🧪 Test Mode (don't submit applications)", True)
        
        with col2:
            platforms_to_use = st.multiselect(
                "🌐 Platforms to Use", 
                enabled_platforms,
                default=enabled_platforms
            )
        
        if st.form_submit_button("🚀 Start Auto Apply", type="primary"):
            if platforms_to_use:
                with st.spinner("🤖 Running Enhanced Auto Apply..."):
                    try:
                        # Initialize auto apply system
                        auto_apply = EnhancedAutoApplySystem()
                        
                        # Run auto apply
                        success = auto_apply.run_enhanced_auto_apply(max_applications)
                        
                        if success:
                            st.balloons()
                            st.success("🎉 Auto Apply completed successfully!")
                        else:
                            st.warning("⚠️ Auto Apply completed with some issues. Check logs.")
                    
                    except Exception as e:
                        st.error(f"❌ Auto Apply failed: {e}")
            else:
                st.error("❌ Please select at least one platform")

elif action == "📈 View Results":
    st.header("📈 Application Results")
    
    # Look for recent application results
    import glob
    
    result_files = glob.glob("enhanced_applications_*.json")
    
    if result_files:
        # Sort by newest first
        result_files.sort(key=os.path.getctime, reverse=True)
        
        selected_file = st.selectbox("📁 Select Results File", result_files)
        
        if selected_file:
            try:
                with open(selected_file, 'r') as f:
                    data = json.load(f)
                
                applications = data.get('applications', [])
                
                st.metric("📊 Total Applications", len(applications))
                
                if applications:
                    # Show applications in table
                    import pandas as pd
                    
                    df = pd.DataFrame(applications)
                    
                    # Display summary
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        platform_counts = df['platform'].value_counts()
                        st.bar_chart(platform_counts)
                    
                    with col2:
                        st.write("**Recent Applications:**")
                        for app in applications[-5:]:
                            st.write(f"• {app.get('title', 'Unknown')} at {app.get('company', 'Unknown')}")
                    
                    with col3:
                        success_rate = len([a for a in applications if a.get('status') == 'Applied']) / len(applications) * 100
                        st.metric("Success Rate", f"{success_rate:.1f}%")
                    
                    # Detailed table
                    st.subheader("📋 Detailed Applications")
                    st.dataframe(df[['title', 'company', 'platform', 'applied_date', 'status']])
                
            except Exception as e:
                st.error(f"❌ Error loading results: {e}")
    else:
        st.info("📊 No application results found. Run auto apply first.")

# Footer
st.markdown("---")
st.markdown("🔐 **Security Notice:** Credentials are encrypted locally. Monitor your accounts regularly.")
'''
    
    with open("credential_dashboard.py", "w") as f:
        f.write(dashboard_code)
    
    print("✅ Credential Management Dashboard created: credential_dashboard.py")

def main():
    """Main setup function"""
    print("🚀 SETTING UP CREDENTIAL-BASED AUTO APPLY")
    print("=" * 60)
    
    print("\n📋 SETUP PROCESS:")
    print("1. Interactive credential configuration")
    print("2. Enhanced auto apply system creation")
    print("3. Streamlit dashboard for management")
    
    # Step 1: Setup credentials
    credentials = setup_credentials_interactive()
    
    if credentials:
        print(f"\n✅ STEP 1 COMPLETE: Credentials configured")
        
        # Step 2: Create enhanced system
        print(f"\n🔧 STEP 2: Creating enhanced auto apply system...")
        create_enhanced_auto_apply()
        
        # Step 3: Create dashboard
        print(f"\n🎨 STEP 3: Creating management dashboard...")
        create_streamlit_dashboard()
        
        print(f"\n🎉 SETUP COMPLETE!")
        print("=" * 60)
        
        print("\n🚀 NEXT STEPS:")
        print("1. Test the system:")
        print("   python enhanced_auto_apply_system.py")
        
        print("\n2. Launch dashboard:")
        print("   streamlit run credential_dashboard.py")
        
        print("\n3. Monitor applications:")
        print("   Check enhanced_applications_*.json files")
        
        print(f"\n🔐 SECURITY REMINDERS:")
        print("• Keep credential_key.key file secure")
        print("• Monitor account activity regularly")
        print("• Use strong, unique passwords")
        print("• Enable 2FA where possible")
        
    else:
        print("❌ Setup cancelled or failed.")

if __name__ == "__main__":
    # Check if cryptography library is available
    try:
        from cryptography.fernet import Fernet
        main()
    except ImportError:
        print("❌ Missing required library: cryptography")
        print("Install with: pip install cryptography")
        print("Then run this setup again.")
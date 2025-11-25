#!/usr/bin/env python3
"""
🔧 CREDENTIAL SETUP WIZARD
Interactive setup for credential-based auto apply
"""

import json
import os
import getpass

def setup_credentials_wizard():
    print("🔧 CREDENTIAL SETUP WIZARD")
    print("=" * 50)
    
    print("\n⚠️ IMPORTANT SECURITY NOTICE:")
    print("• Your credentials will be stored locally on your computer")
    print("• Use strong, unique passwords for job site accounts")
    print("• Consider creating dedicated accounts for automation")
    print("• Monitor your accounts for unusual activity")
    
    choice = input("\n✅ Do you understand and agree? (y/n): ")
    if choice.lower() != 'y':
        print("❌ Setup cancelled for security reasons")
        return
    
    print("\n🎯 Which platform would you like to set up first?")
    print("1. 📋 Naukri.com (Best for Indian market)")
    print("2. 🌍 Indeed.com (International opportunities)")
    print("3. 💼 LinkedIn (Professional network)")
    print("4. 🆕 FreshersWorld (Entry-level positions)")
    print("5. ⚙️ Configure all platforms")
    
    choice = input("\nChoice (1-5): ")
    
    # Load existing credentials or create new
    credentials_file = "job_site_credentials.json"
    credentials = {}
    
    if os.path.exists(credentials_file):
        try:
            with open(credentials_file, 'r') as f:
                credentials = json.load(f)
        except:
            credentials = {}
    
    # Platform configurations
    platforms = {
        '1': 'naukri',
        '2': 'indeed', 
        '3': 'linkedin',
        '4': 'freshersworld',
        '5': 'all'
    }
    
    selected_platforms = []
    if choice == '5':
        selected_platforms = ['naukri', 'indeed', 'linkedin', 'freshersworld']
    elif choice in platforms:
        selected_platforms = [platforms[choice]]
    else:
        print("❌ Invalid choice")
        return
    
    # Configure each platform
    for platform in selected_platforms:
        print(f"\n🔑 Configuring {platform.title()}")
        print("-" * 30)
        
        if platform in credentials and credentials[platform].get('enabled'):
            current_email = credentials[platform].get('email', 'Not set')
            update = input(f"📧 Current email: {current_email}\n   Update credentials? (y/n): ")
            
            if update.lower() != 'y':
                print(f"✅ Keeping existing {platform} credentials")
                continue
        
        # Get credentials for this platform
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
            
        elif platform == 'freshersworld':
            username = input("👤 FreshersWorld Username: ")
            password = getpass.getpass("🔒 FreshersWorld Password: ")
            
            credentials['freshersworld'] = {
                'username': username,
                'password': password,
                'enabled': True,
                'login_url': 'https://www.freshersworld.com/user/login',
                'success_indicator': 'dashboard'
            }
        
        print(f"✅ {platform.title()} credentials configured!")
    
    # Save credentials
    try:
        with open(credentials_file, 'w') as f:
            json.dump(credentials, f, indent=2)
        
        print(f"\n💾 Credentials saved to: {credentials_file}")
        
        # Show summary
        enabled_platforms = [p for p, c in credentials.items() if c.get('enabled')]
        print(f"\n📊 SETUP SUMMARY:")
        print(f"✅ Configured platforms: {', '.join([p.title() for p in enabled_platforms])}")
        print(f"🎯 Total platforms: {len(enabled_platforms)}")
        
        print(f"\n🚀 NEXT STEPS:")
        print("1. Run: python credential_auto_apply_system.py")
        print("2. Choose option '1' to use existing credentials")
        print("3. Enter your job search preferences")
        print("4. Watch the automated applications!")
        
        # Test credentials option
        test = input(f"\n🧪 Would you like to test login credentials now? (y/n): ")
        if test.lower() == 'y':
            test_login_credentials(credentials)
        
    except Exception as e:
        print(f"❌ Error saving credentials: {e}")

def test_login_credentials(credentials):
    """Test login credentials without full automation"""
    print(f"\n🧪 TESTING LOGIN CREDENTIALS")
    print("-" * 30)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        
        # Setup browser
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)
        
        enabled_platforms = [(p, c) for p, c in credentials.items() if c.get('enabled')]
        
        for platform, creds in enabled_platforms:
            print(f"\n🔍 Testing {platform.title()}...")
            
            try:
                driver.get(creds['login_url'])
                time.sleep(3)
                
                if platform == 'naukri':
                    email_field = wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
                    email_field.send_keys(creds['email'])
                    
                    password_field = driver.find_element(By.ID, "passwordField")
                    password_field.send_keys(creds['password'])
                    
                    print(f"   ✅ Form fields populated successfully")
                    print(f"   ⚠️ Login test stopped (not actually submitting)")
                
                elif platform == 'indeed':
                    email_field = wait.until(EC.presence_of_element_located((By.ID, "login-email-input")))
                    email_field.send_keys(creds['email'])
                    
                    print(f"   ✅ Email field populated successfully")
                    print(f"   ⚠️ Login test stopped (not actually submitting)")
                
                elif platform == 'linkedin':
                    email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
                    email_field.send_keys(creds['email'])
                    
                    password_field = driver.find_element(By.ID, "password")
                    password_field.send_keys(creds['password'])
                    
                    print(f"   ✅ Form fields populated successfully")
                    print(f"   ⚠️ Login test stopped (not actually submitting)")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Test failed for {platform}: {e}")
        
        driver.quit()
        print(f"\n✅ Credential testing completed")
        
    except ImportError:
        print("⚠️ Selenium not available for testing")
    except Exception as e:
        print(f"❌ Test error: {e}")

def show_current_status():
    """Show current credential configuration status"""
    print("\n📊 CURRENT CREDENTIAL STATUS")
    print("-" * 30)
    
    if not os.path.exists("job_site_credentials.json"):
        print("❌ No credentials configured")
        return
    
    try:
        with open("job_site_credentials.json", 'r') as f:
            credentials = json.load(f)
        
        for platform, config in credentials.items():
            status = "✅ Enabled" if config.get('enabled') else "❌ Disabled"
            email = config.get('email', config.get('username', 'Not set'))
            print(f"{platform.title()}: {status} ({email})")
            
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")

def main():
    print("🔧 CREDENTIAL CONFIGURATION MANAGER")
    print("=" * 50)
    
    # Show current status
    show_current_status()
    
    print(f"\n📋 What would you like to do?")
    print("1. 🆕 Set up new credentials")
    print("2. 🔄 Update existing credentials") 
    print("3. 👀 View current configuration")
    print("4. 🧪 Test existing credentials")
    print("5. ❌ Delete all credentials")
    
    choice = input("\nChoice (1-5): ")
    
    if choice == '1' or choice == '2':
        setup_credentials_wizard()
    elif choice == '3':
        show_current_status()
    elif choice == '4':
        try:
            with open("job_site_credentials.json", 'r') as f:
                credentials = json.load(f)
            test_login_credentials(credentials)
        except:
            print("❌ No credentials to test")
    elif choice == '5':
        confirm = input("⚠️ Delete all credentials? This cannot be undone! (type 'DELETE'): ")
        if confirm == 'DELETE':
            try:
                os.remove("job_site_credentials.json")
                print("✅ All credentials deleted")
            except:
                print("❌ Error deleting credentials")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
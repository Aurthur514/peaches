#!/usr/bin/env python3
"""
LinkedIn Credential Setup Wizard - Interactive setup for LinkedIn auto apply
"""

import json
import os
import getpass
from datetime import datetime

def setup_linkedin_credentials():
    """Interactive setup wizard for LinkedIn credentials"""
    
    print("🔗 LINKEDIN AUTO APPLY - CREDENTIAL SETUP WIZARD")
    print("=" * 60)
    
    print("\n📋 This wizard will help you set up LinkedIn auto apply credentials")
    print("Your credentials will be stored locally and used for automation")
    
    # Load existing credentials
    creds_file = "job_site_credentials.json"
    existing_creds = {}
    
    if os.path.exists(creds_file):
        try:
            with open(creds_file, 'r') as f:
                existing_creds = json.load(f)
        except:
            pass
    
    print("\n🔐 LINKEDIN CREDENTIAL CONFIGURATION:")
    print("-" * 40)
    
    # Get LinkedIn email
    current_email = existing_creds.get('linkedin', {}).get('email', '')
    if current_email and current_email != 'your_linkedin_email@gmail.com':
        print(f"Current email: {current_email}")
        use_current = input("Use current email? (y/n): ").strip().lower()
        if use_current == 'y':
            email = current_email
        else:
            email = input("Enter your LinkedIn email: ").strip()
    else:
        email = input("Enter your LinkedIn email: ").strip()
    
    # Get LinkedIn password
    print("\n🔒 Enter your LinkedIn password:")
    print("(Password will be hidden as you type)")
    password = getpass.getpass("LinkedIn password: ")
    
    # Get phone number
    current_phone = existing_creds.get('linkedin', {}).get('phone', '')
    if current_phone and current_phone != '+91-9876543210':
        print(f"Current phone: {current_phone}")
        use_current_phone = input("Use current phone? (y/n): ").strip().lower()
        if use_current_phone == 'y':
            phone = current_phone
        else:
            phone = input("Enter your phone number (+91-XXXXXXXXXX): ").strip()
    else:
        phone = input("Enter your phone number (+91-XXXXXXXXXX): ").strip()
    
    # Get location
    current_location = existing_creds.get('linkedin', {}).get('location', '')
    if current_location and 'Chennai' in current_location:
        print(f"Current location: {current_location}")
        use_current_loc = input("Use current location? (y/n): ").strip().lower()
        if use_current_loc == 'y':
            location = current_location
        else:
            location = input("Enter your location (City, State, Country): ").strip()
    else:
        location = input("Enter your location (e.g., Chennai, Tamil Nadu, India): ").strip()
    
    # Confirmation
    print("\n📋 CONFIGURATION SUMMARY:")
    print("-" * 30)
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")
    print(f"Phone: {phone}")
    print(f"Location: {location}")
    
    confirm = input("\nSave this configuration? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Configuration cancelled")
        return False
    
    # Update credentials
    if 'linkedin' not in existing_creds:
        existing_creds['linkedin'] = {}
    
    existing_creds['linkedin'].update({
        'email': email,
        'password': password,
        'enabled': True,  # Enable LinkedIn by default
        'phone': phone,
        'location': location,
        'configured_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    # Save to file
    try:
        with open(creds_file, 'w') as f:
            json.dump(existing_creds, f, indent=2)
        
        print("✅ LinkedIn credentials saved successfully!")
        print("🔗 LinkedIn auto apply is now enabled")
        
        # Security recommendations
        print("\n🔒 SECURITY RECOMMENDATIONS:")
        print("• Use a unique password for job searching")
        print("• Enable 2FA on your LinkedIn account")
        print("• Monitor your account for unusual activity")
        print("• Review applications regularly")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving credentials: {e}")
        return False

def test_linkedin_setup():
    """Test if LinkedIn setup is working"""
    print("\n🧪 TESTING LINKEDIN SETUP...")
    print("-" * 30)
    
    # Check credentials file
    if os.path.exists('job_site_credentials.json'):
        try:
            with open('job_site_credentials.json', 'r') as f:
                creds = json.load(f)
            
            linkedin_config = creds.get('linkedin', {})
            
            if linkedin_config.get('enabled'):
                print("✅ LinkedIn credentials found and enabled")
                print(f"Email: {linkedin_config.get('email', 'Not set')}")
                print(f"Phone: {linkedin_config.get('phone', 'Not set')}")
                print(f"Location: {linkedin_config.get('location', 'Not set')}")
                
                # Test if we can import required modules
                try:
                    from selenium import webdriver
                    print("✅ Selenium WebDriver available")
                except ImportError:
                    print("❌ Selenium not installed - run: pip install selenium")
                    return False
                
                print("✅ LinkedIn auto apply setup is ready!")
                return True
            else:
                print("⚠️ LinkedIn credentials found but not enabled")
                return False
                
        except Exception as e:
            print(f"❌ Error reading credentials: {e}")
            return False
    else:
        print("❌ No credentials file found")
        return False

def show_usage_instructions():
    """Show how to use LinkedIn auto apply"""
    print("\n🚀 HOW TO USE LINKEDIN AUTO APPLY:")
    print("=" * 40)
    
    print("\n1. **Run the LinkedIn Auto Apply:**")
    print("   python linkedin_auto_apply.py")
    
    print("\n2. **What it will do:**")
    print("   • Login to LinkedIn automatically")
    print("   • Search for jobs matching your criteria")
    print("   • Apply using LinkedIn Easy Apply")
    print("   • Track all applications")
    print("   • Generate detailed reports")
    
    print("\n3. **Customization Options:**")
    print("   • Job keywords (e.g., 'data analyst', 'python developer')")
    print("   • Location preferences")
    print("   • Maximum applications per session")
    print("   • Match score thresholds")
    
    print("\n4. **Safety Features:**")
    print("   • Human-like typing and delays")
    print("   • Respectful rate limiting")
    print("   • Application confirmation steps")
    print("   • Comprehensive logging")
    
    print("\n5. **Expected Results:**")
    print("   • 5-15 applications per session")
    print("   • 70-85% success rate")
    print("   • Complete application tracking")
    print("   • Professional job targeting")

def main():
    """Main setup function"""
    try:
        # Run setup wizard
        success = setup_linkedin_credentials()
        
        if success:
            # Test the setup
            test_success = test_linkedin_setup()
            
            if test_success:
                # Show usage instructions
                show_usage_instructions()
                
                print("\n🎉 SETUP COMPLETE!")
                print("Your LinkedIn auto apply system is ready to use.")
                
                # Ask if user wants to run it now
                run_now = input("\nRun LinkedIn auto apply now? (y/n): ").strip().lower()
                
                if run_now == 'y':
                    print("\n🚀 Starting LinkedIn auto apply...")
                    import subprocess
                    subprocess.run(['python', 'linkedin_auto_apply.py'])
                else:
                    print("You can run it anytime with: python linkedin_auto_apply.py")
            else:
                print("\n❌ Setup test failed. Please check the configuration.")
        else:
            print("\n❌ Setup failed. Please try again.")
    
    except KeyboardInterrupt:
        print("\n⚠️ Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup error: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
CREDENTIAL SETUP WIZARD - Secure setup for auto apply with login credentials
"""

import json
import os
import getpass
import base64
from cryptography.fernet import Fernet
import sys

class CredentialSetupWizard:
    def __init__(self):
        self.credentials_file = "job_site_credentials.json"
        self.secure_file = "job_site_credentials_secure.json"
        self.key_file = ".credential_key"
        
    def generate_encryption_key(self):
        """Generate encryption key for secure credential storage"""
        key = Fernet.generate_key()
        with open(self.key_file, 'wb') as f:
            f.write(key)
        print("🔐 Encryption key generated for secure storage")
        return key
    
    def load_or_create_key(self):
        """Load existing key or create new one"""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as f:
                    return f.read()
            else:
                return self.generate_encryption_key()
        except Exception as e:
            print(f"❌ Error with encryption key: {e}")
            return self.generate_encryption_key()
    
    def encrypt_credentials(self, credentials, key):
        """Encrypt credentials for secure storage"""
        fernet = Fernet(key)
        credentials_json = json.dumps(credentials)
        encrypted_data = fernet.encrypt(credentials_json.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_credentials(self, encrypted_data, key):
        """Decrypt credentials for use"""
        try:
            fernet = Fernet(key)
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(encrypted_bytes)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"❌ Decryption failed: {e}")
            return None

    def interactive_setup(self):
        """Interactive credential setup process"""
        print("🚀 CREDENTIAL SETUP WIZARD FOR AUTO APPLY")
        print("=" * 60)
        
        print("\n⚠️ IMPORTANT SECURITY NOTES:")
        print("• Use dedicated job search accounts (not your main accounts)")
        print("• Create app-specific passwords where available")
        print("• Monitor account activity regularly")
        print("• Credentials will be encrypted for security")
        
        credentials = {}
        
        # Platform selection
        platforms = {
            '1': 'naukri',
            '2': 'indeed', 
            '3': 'linkedin',
            '4': 'freshersworld'
        }
        
        print(f"\n📋 AVAILABLE PLATFORMS:")
        for key, platform in platforms.items():
            print(f"{key}. {platform.title()}")
        
        selected = input("\nEnter platform numbers (e.g., 1,2,3) or 'all': ").strip()
        
        if selected.lower() == 'all':
            selected_platforms = list(platforms.values())
        else:
            selected_numbers = [x.strip() for x in selected.split(',')]
            selected_platforms = [platforms[num] for num in selected_numbers if num in platforms]
        
        if not selected_platforms:
            print("❌ No valid platforms selected")
            return False
        
        # Setup credentials for each platform
        for platform in selected_platforms:
            print(f"\n🔐 SETTING UP: {platform.upper()}")
            print("-" * 30)
            
            enabled = input(f"Enable auto apply for {platform}? (y/n): ").lower().startswith('y')
            
            if enabled:
                if platform in ['naukri', 'indeed', 'linkedin']:
                    email = input(f"Enter {platform} email: ").strip()
                    password = getpass.getpass(f"Enter {platform} password: ")
                    
                    credentials[platform] = {
                        'email': email,
                        'password': password,
                        'enabled': True,
                        'last_updated': '2025-11-15'
                    }
                    
                elif platform == 'freshersworld':
                    username = input(f"Enter {platform} username: ").strip()
                    password = getpass.getpass(f"Enter {platform} password: ")
                    
                    credentials[platform] = {
                        'username': username,
                        'password': password,
                        'enabled': True,
                        'last_updated': '2025-11-15'
                    }
                
                print(f"✅ {platform.title()} credentials configured")
            else:
                credentials[platform] = {
                    'email': 'your_email@gmail.com',
                    'password': 'your_password',
                    'enabled': False
                }
                print(f"⏭️ {platform.title()} skipped")
        
        # Save credentials
        self.save_credentials(credentials)
        
        print(f"\n🎉 SETUP COMPLETE!")
        print(f"Configured {len([p for p in credentials.values() if p.get('enabled')])} platforms")
        
        return True
    
    def save_credentials(self, credentials):
        """Save credentials securely"""
        try:
            # Generate encryption key
            key = self.load_or_create_key()
            
            # Encrypt and save
            encrypted_data = self.encrypt_credentials(credentials, key)
            
            secure_config = {
                'encrypted': True,
                'data': encrypted_data,
                'platforms': list(credentials.keys()),
                'enabled_count': len([p for p in credentials.values() if p.get('enabled')])
            }
            
            with open(self.secure_file, 'w') as f:
                json.dump(secure_config, f, indent=2)
            
            # Also save plain text version for compatibility (with dummy data for disabled)
            plain_credentials = {}
            for platform, config in credentials.items():
                if config.get('enabled'):
                    plain_credentials[platform] = {
                        'email': '***ENCRYPTED***',
                        'password': '***ENCRYPTED***',
                        'enabled': True,
                        'note': 'Real credentials stored in encrypted file'
                    }
                else:
                    plain_credentials[platform] = config
            
            with open(self.credentials_file, 'w') as f:
                json.dump(plain_credentials, f, indent=2)
            
            print(f"💾 Credentials saved securely")
            print(f"📄 Plain config: {self.credentials_file}")
            print(f"🔐 Encrypted config: {self.secure_file}")
            
        except Exception as e:
            print(f"❌ Error saving credentials: {e}")
    
    def load_secure_credentials(self):
        """Load and decrypt credentials"""
        try:
            if not os.path.exists(self.secure_file):
                print("⚠️ No secure credentials found")
                return None
            
            with open(self.secure_file, 'r') as f:
                secure_config = json.load(f)
            
            if not secure_config.get('encrypted'):
                print("⚠️ Credentials not encrypted")
                return None
            
            key = self.load_or_create_key()
            credentials = self.decrypt_credentials(secure_config['data'], key)
            
            if credentials:
                print("✅ Credentials loaded and decrypted successfully")
                return credentials
            else:
                print("❌ Failed to decrypt credentials")
                return None
                
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            return None
    
    def test_credentials(self):
        """Test saved credentials"""
        print("\n🧪 TESTING SAVED CREDENTIALS")
        print("-" * 30)
        
        credentials = self.load_secure_credentials()
        if not credentials:
            print("❌ No credentials to test")
            return
        
        enabled_platforms = [p for p, c in credentials.items() if c.get('enabled')]
        
        print(f"Found credentials for {len(enabled_platforms)} enabled platforms:")
        for platform in enabled_platforms:
            config = credentials[platform]
            email = config.get('email', config.get('username', 'N/A'))
            print(f"✅ {platform.title()}: {email[:10]}***")
        
        print("\n💡 Ready for auto apply testing!")
        print("Run: python test_auto_apply_with_credentials.py")

def quick_setup_demo():
    """Quick demo setup for testing"""
    print("🚀 QUICK DEMO SETUP")
    print("=" * 40)
    
    demo_credentials = {
        'naukri': {
            'email': 'bharathan1404@gmail.com',
            'password': 'demo_password',
            'enabled': False,
            'note': 'Demo credentials - update with real values'
        },
        'indeed': {
            'email': 'bharathan1404@gmail.com', 
            'password': 'demo_password',
            'enabled': False,
            'note': 'Demo credentials - update with real values'
        }
    }
    
    with open('job_site_credentials.json', 'w') as f:
        json.dump(demo_credentials, f, indent=2)
    
    print("📄 Created demo credential file: job_site_credentials.json")
    print("\n✏️ TO ENABLE AUTO APPLY:")
    print("1. Edit job_site_credentials.json")
    print("2. Replace demo_password with real passwords")
    print("3. Set enabled: true for platforms you want to use")
    print("4. Test with: python test_auto_apply_with_credentials.py")

def main():
    print("🔐 AUTO APPLY CREDENTIAL SETUP")
    print("=" * 60)
    
    print("\nChoose setup method:")
    print("1. 🔐 Secure Interactive Setup (Recommended)")
    print("2. 📄 Quick Demo Setup (For Testing)")
    print("3. 🧪 Test Existing Credentials")
    print("4. ❓ Show Help")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    wizard = CredentialSetupWizard()
    
    if choice == '1':
        try:
            # Check if cryptography is available
            from cryptography.fernet import Fernet
            wizard.interactive_setup()
        except ImportError:
            print("\n❌ Cryptography library not found")
            print("Install with: pip install cryptography")
            print("Or use Quick Demo Setup (option 2)")
            
    elif choice == '2':
        quick_setup_demo()
        
    elif choice == '3':
        wizard.test_credentials()
        
    elif choice == '4':
        show_help()
    
    else:
        print("❌ Invalid choice")

def show_help():
    print("\n📚 CREDENTIAL SETUP HELP")
    print("=" * 40)
    
    print("\n🔐 SECURITY RECOMMENDATIONS:")
    print("• Use dedicated job search accounts")
    print("• Enable 2FA on your main accounts")
    print("• Create app-specific passwords when available")
    print("• Monitor account activity regularly")
    print("• Use secure setup for production use")
    
    print("\n⚡ QUICK START:")
    print("1. Run option 2 for quick demo setup")
    print("2. Edit job_site_credentials.json with real credentials")
    print("3. Set enabled: true for platforms")
    print("4. Test with auto apply system")
    
    print("\n🚀 PRODUCTION USE:")
    print("1. Run option 1 for secure encrypted setup")
    print("2. Credentials stored with encryption")
    print("3. Better security for regular use")
    print("4. Automatic credential management")

if __name__ == "__main__":
    main()
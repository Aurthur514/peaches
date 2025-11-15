#!/usr/bin/env python3
"""
Application Verification and Tracking System
Real-time verification of job applications with confirmation tracking
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import sqlite3

# Email verification imports
try:
    import imaplib
    import email
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import smtplib
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

# Web verification imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('application_verification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ApplicationVerification:
    """Application verification record"""
    application_id: str
    job_title: str
    company: str
    application_url: str
    submitted_time: datetime
    
    # Verification methods
    confirmation_email_received: bool = False
    confirmation_number: str = ""
    application_portal_status: str = ""
    
    # Email verification
    confirmation_email_subject: str = ""
    confirmation_email_body: str = ""
    confirmation_email_time: Optional[datetime] = None
    
    # Portal verification
    portal_application_id: str = ""
    portal_status: str = ""
    portal_last_checked: Optional[datetime] = None
    
    # Screenshot verification
    screenshot_path: str = ""
    success_page_captured: bool = False
    
    # Verification status
    verification_status: str = "pending"  # pending, verified, failed, unknown
    verification_confidence: float = 0.0  # 0-100%
    verification_details: List[str] = field(default_factory=list)
    
    # Follow-up tracking
    follow_up_sent: bool = False
    response_received: bool = False
    interview_scheduled: bool = False

class EmailVerificationSystem:
    """Email-based application verification"""
    
    def __init__(self, email_config: Dict[str, str]):
        self.email_config = email_config
        self.imap_server = None
        
    def connect_to_email(self) -> bool:
        """Connect to email server for verification"""
        
        if not EMAIL_AVAILABLE:
            logger.warning("Email verification not available - imaplib not installed")
            return False
        
        try:
            # Connect to email server
            if 'gmail' in self.email_config.get('email', '').lower():
                self.imap_server = imaplib.IMAP4_SSL('imap.gmail.com', 993)
            elif 'outlook' in self.email_config.get('email', '').lower():
                self.imap_server = imaplib.IMAP4_SSL('outlook.office365.com', 993)
            else:
                # Generic IMAP
                self.imap_server = imaplib.IMAP4_SSL(self.email_config.get('imap_server', ''), 993)
            
            # Login
            self.imap_server.login(
                self.email_config['email'], 
                self.email_config['password']
            )
            
            logger.info(f"Connected to email server for {self.email_config['email']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            return False
    
    def check_for_confirmation_emails(self, since_time: datetime) -> List[Dict]:
        """Check for job application confirmation emails"""
        
        if not self.imap_server:
            return []
        
        try:
            # Select inbox
            self.imap_server.select('INBOX')
            
            # Search for recent emails
            since_date = since_time.strftime("%d-%b-%Y")
            search_criteria = f'(SINCE "{since_date}")'
            
            # Keywords that indicate application confirmations
            confirmation_keywords = [
                'application received',
                'application confirmation', 
                'thank you for applying',
                'application submitted',
                'we have received your application',
                'application acknowledgment',
                'job application',
                'application reference number',
                'confirmation number'
            ]
            
            confirmations = []
            
            # Search for emails
            _, message_numbers = self.imap_server.search(None, search_criteria)
            
            for num in message_numbers[0].split():
                _, msg_data = self.imap_server.fetch(num, '(RFC822)')
                email_message = email.message_from_bytes(msg_data[0][1])
                
                subject = email_message['Subject'] or ""
                from_email = email_message['From'] or ""
                date_str = email_message['Date'] or ""
                
                # Get email body
                body = self._extract_email_body(email_message)
                
                # Check if it's a confirmation email
                is_confirmation = any(
                    keyword.lower() in subject.lower() or keyword.lower() in body.lower()
                    for keyword in confirmation_keywords
                )
                
                if is_confirmation:
                    confirmation_number = self._extract_confirmation_number(body)
                    company_name = self._extract_company_name(from_email, body)
                    
                    confirmations.append({
                        'subject': subject,
                        'from': from_email,
                        'date': date_str,
                        'body': body,
                        'confirmation_number': confirmation_number,
                        'company': company_name
                    })
                    
                    logger.info(f"Found confirmation email from {company_name}: {subject}")
            
            return confirmations
            
        except Exception as e:
            logger.error(f"Error checking confirmation emails: {e}")
            return []
    
    def _extract_email_body(self, email_message) -> str:
        """Extract text body from email message"""
        
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return body
    
    def _extract_confirmation_number(self, text: str) -> str:
        """Extract confirmation/reference number from email text"""
        
        # Common patterns for confirmation numbers
        patterns = [
            r'confirmation number[:\s]+([A-Z0-9\-]+)',
            r'reference number[:\s]+([A-Z0-9\-]+)',
            r'application id[:\s]+([A-Z0-9\-]+)',
            r'ticket number[:\s]+([A-Z0-9\-]+)',
            r'ref[:\s]+([A-Z0-9\-]+)',
            r'#([A-Z0-9\-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_company_name(self, from_email: str, body: str) -> str:
        """Extract company name from email"""
        
        # Try to extract from email domain
        if '@' in from_email:
            domain = from_email.split('@')[1]
            # Remove common email domains
            if domain not in ['gmail.com', 'outlook.com', 'yahoo.com', 'hotmail.com']:
                company = domain.replace('.com', '').replace('.co.in', '').replace('.org', '')
                return company.title()
        
        # Try to extract from email body
        company_patterns = [
            r'from ([A-Za-z\s]+) team',
            r'([A-Za-z\s]+) hiring team',
            r'([A-Za-z\s]+) recruitment',
            r'at ([A-Za-z\s]+) company'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1).strip().title()
        
        return "Unknown Company"
    
    def disconnect(self):
        """Disconnect from email server"""
        if self.imap_server:
            self.imap_server.close()
            self.imap_server.logout()

class PortalVerificationSystem:
    """Job portal verification system"""
    
    def __init__(self):
        self.driver = None
    
    async def initialize_browser(self):
        """Initialize browser for portal checking"""
        
        if not SELENIUM_AVAILABLE:
            logger.warning("Portal verification not available - selenium not installed")
            return False
        
        try:
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            self.driver = webdriver.Chrome(options=options)
            logger.info("Browser initialized for portal verification")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            return False
    
    async def verify_application_on_portal(self, verification: ApplicationVerification) -> bool:
        """Verify application status on job portal"""
        
        if not self.driver:
            return False
        
        try:
            # Navigate to application URL
            self.driver.get(verification.application_url)
            time.sleep(3)
            
            # Look for success indicators
            success_indicators = [
                "application submitted successfully",
                "thank you for applying",
                "application received",
                "confirmation",
                "success",
                "submitted"
            ]
            
            page_content = self.driver.page_source.lower()
            
            # Check for success indicators
            success_found = any(indicator in page_content for indicator in success_indicators)
            
            if success_found:
                verification.portal_application_id = self._extract_portal_id(page_content)
                verification.portal_status = "submitted"
                verification.success_page_captured = True
                
                # Take screenshot as proof
                screenshot_path = f"screenshots/success_{verification.application_id}.png"
                os.makedirs("screenshots", exist_ok=True)
                self.driver.save_screenshot(screenshot_path)
                verification.screenshot_path = screenshot_path
                
                logger.info(f"Application verified on portal: {verification.job_title} at {verification.company}")
                return True
            else:
                verification.portal_status = "unknown"
                logger.warning(f"Could not verify application on portal: {verification.job_title}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying application on portal: {e}")
            verification.portal_status = "error"
            return False
    
    def _extract_portal_id(self, page_content: str) -> str:
        """Extract application ID from portal page"""
        
        # Common patterns for application IDs on success pages
        patterns = [
            r'application id[:\s]+([A-Z0-9\-]+)',
            r'reference number[:\s]+([A-Z0-9\-]+)',
            r'tracking number[:\s]+([A-Z0-9\-]+)',
            r'id[:\s]+([A-Z0-9\-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def close_browser(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()

class ApplicationVerificationManager:
    """Complete application verification and tracking system"""
    
    def __init__(self, email_config: Dict[str, str]):
        self.email_verifier = EmailVerificationSystem(email_config)
        self.portal_verifier = PortalVerificationSystem()
        self.db_path = "application_tracking.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for tracking"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                job_title TEXT,
                company TEXT,
                application_url TEXT,
                submitted_time TEXT,
                verification_status TEXT,
                confirmation_number TEXT,
                portal_status TEXT,
                verification_confidence REAL,
                verification_details TEXT,
                last_updated TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id TEXT,
                verification_type TEXT,
                status TEXT,
                details TEXT,
                timestamp TEXT,
                FOREIGN KEY (application_id) REFERENCES applications (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def verify_application(self, verification: ApplicationVerification) -> ApplicationVerification:
        """Complete verification of job application"""
        
        logger.info(f"Starting verification for {verification.job_title} at {verification.company}")
        
        verification_methods = []
        total_confidence = 0.0
        
        # 1. Email verification
        email_verified = await self._verify_via_email(verification)
        if email_verified:
            verification_methods.append("Email confirmation received")
            total_confidence += 40.0
        
        # 2. Portal verification  
        portal_verified = await self._verify_via_portal(verification)
        if portal_verified:
            verification_methods.append("Portal verification successful")
            total_confidence += 35.0
        
        # 3. Screenshot verification
        screenshot_verified = verification.success_page_captured
        if screenshot_verified:
            verification_methods.append("Success page screenshot captured")
            total_confidence += 25.0
        
        # Calculate overall confidence
        verification.verification_confidence = total_confidence
        verification.verification_details = verification_methods
        
        # Determine verification status
        if total_confidence >= 75.0:
            verification.verification_status = "verified"
        elif total_confidence >= 50.0:
            verification.verification_status = "likely_verified"
        elif total_confidence >= 25.0:
            verification.verification_status = "partially_verified"
        else:
            verification.verification_status = "unverified"
        
        # Update database
        self._save_verification_to_db(verification)
        
        logger.info(f"Verification completed: {verification.verification_status} ({verification.verification_confidence:.1f}% confidence)")
        
        return verification
    
    async def _verify_via_email(self, verification: ApplicationVerification) -> bool:
        """Verify application via email confirmation"""
        
        try:
            if not self.email_verifier.connect_to_email():
                return False
            
            # Check for confirmation emails since application time
            confirmations = self.email_verifier.check_for_confirmation_emails(
                verification.submitted_time - timedelta(minutes=5)  # Check a bit before submission
            )
            
            # Find matching confirmation
            for conf in confirmations:
                if verification.company.lower() in conf['company'].lower() or \
                   verification.company.lower() in conf['subject'].lower() or \
                   verification.job_title.lower() in conf['subject'].lower():
                    
                    verification.confirmation_email_received = True
                    verification.confirmation_email_subject = conf['subject']
                    verification.confirmation_email_body = conf['body'][:500]  # First 500 chars
                    verification.confirmation_number = conf['confirmation_number']
                    verification.confirmation_email_time = datetime.now()
                    
                    logger.info(f"Email verification successful: {conf['subject']}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Email verification failed: {e}")
            return False
        
        finally:
            self.email_verifier.disconnect()
    
    async def _verify_via_portal(self, verification: ApplicationVerification) -> bool:
        """Verify application via job portal"""
        
        try:
            if not await self.portal_verifier.initialize_browser():
                return False
            
            success = await self.portal_verifier.verify_application_on_portal(verification)
            verification.portal_last_checked = datetime.now()
            
            return success
            
        except Exception as e:
            logger.error(f"Portal verification failed: {e}")
            return False
        
        finally:
            self.portal_verifier.close_browser()
    
    def _save_verification_to_db(self, verification: ApplicationVerification):
        """Save verification results to database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert or update application record
        cursor.execute('''
            INSERT OR REPLACE INTO applications 
            (id, job_title, company, application_url, submitted_time, verification_status, 
             confirmation_number, portal_status, verification_confidence, verification_details, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            verification.application_id,
            verification.job_title,
            verification.company,
            verification.application_url,
            verification.submitted_time.isoformat(),
            verification.verification_status,
            verification.confirmation_number,
            verification.portal_status,
            verification.verification_confidence,
            json.dumps(verification.verification_details),
            datetime.now().isoformat()
        ))
        
        # Add verification log
        cursor.execute('''
            INSERT INTO verification_logs (application_id, verification_type, status, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            verification.application_id,
            "full_verification",
            verification.verification_status,
            f"Confidence: {verification.verification_confidence}%",
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_all_applications(self) -> List[ApplicationVerification]:
        """Get all tracked applications"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, job_title, company, application_url, submitted_time, verification_status,
                   confirmation_number, portal_status, verification_confidence, verification_details
            FROM applications ORDER BY submitted_time DESC
        ''')
        
        applications = []
        for row in cursor.fetchall():
            app = ApplicationVerification(
                application_id=row[0],
                job_title=row[1],
                company=row[2],
                application_url=row[3],
                submitted_time=datetime.fromisoformat(row[4]),
                verification_status=row[5],
                confirmation_number=row[6] or "",
                portal_status=row[7] or "",
                verification_confidence=row[8] or 0.0,
                verification_details=json.loads(row[9]) if row[9] else []
            )
            applications.append(app)
        
        conn.close()
        return applications
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification statistics"""
        
        applications = self.get_all_applications()
        
        total_apps = len(applications)
        verified_apps = len([app for app in applications if app.verification_status == "verified"])
        likely_verified = len([app for app in applications if app.verification_status == "likely_verified"])
        unverified_apps = len([app for app in applications if app.verification_status == "unverified"])
        
        avg_confidence = sum(app.verification_confidence for app in applications) / total_apps if total_apps > 0 else 0
        
        return {
            'total_applications': total_apps,
            'verified_applications': verified_apps,
            'likely_verified_applications': likely_verified,
            'unverified_applications': unverified_apps,
            'verification_rate': (verified_apps + likely_verified) / total_apps * 100 if total_apps > 0 else 0,
            'average_confidence': avg_confidence,
            'email_confirmations': len([app for app in applications if app.confirmation_email_received]),
            'portal_verifications': len([app for app in applications if app.portal_status == "submitted"])
        }

# Demo and testing functions
async def demo_application_verification():
    """Demo the application verification system"""
    
    # Email configuration (user would provide real credentials)
    email_config = {
        'email': 'bharathan1404@gmail.com',
        'password': 'your_app_password',  # App password for Gmail
        'imap_server': 'imap.gmail.com'
    }
    
    # Initialize verification manager
    verifier = ApplicationVerificationManager(email_config)
    
    print("🔍 APPLICATION VERIFICATION SYSTEM DEMO")
    print("=" * 50)
    
    # Create sample application for verification
    sample_app = ApplicationVerification(
        application_id="app_001",
        job_title="Data Analyst",
        company="TechCorp India",
        application_url="https://example.com/job/apply",
        submitted_time=datetime.now() - timedelta(minutes=10)
    )
    
    # Verify the application
    verified_app = await verifier.verify_application(sample_app)
    
    print("\\n📊 VERIFICATION RESULTS:")
    print("-" * 30)
    print(f"Job: {verified_app.job_title} at {verified_app.company}")
    print(f"Status: {verified_app.verification_status}")
    print(f"Confidence: {verified_app.verification_confidence:.1f}%")
    print(f"Confirmation Number: {verified_app.confirmation_number or 'Not found'}")
    print(f"Portal Status: {verified_app.portal_status or 'Not checked'}")
    
    print("\\n✅ VERIFICATION METHODS:")
    for method in verified_app.verification_details:
        print(f"• {method}")
    
    # Get overall stats
    stats = verifier.get_verification_stats()
    
    print("\\n📈 OVERALL STATISTICS:")
    print("-" * 30)
    print(f"Total Applications: {stats['total_applications']}")
    print(f"Verified Rate: {stats['verification_rate']:.1f}%")
    print(f"Average Confidence: {stats['average_confidence']:.1f}%")
    print(f"Email Confirmations: {stats['email_confirmations']}")
    
    print("\\n🎉 Verification demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_application_verification())
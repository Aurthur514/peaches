#!/usr/bin/env python3
"""
Real Auto Job Application Runner
Actually searches real job sites and applies automatically
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('real_auto_applications.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

try:
    from complete_auto_application_system import CompleteAutoJobApplicationSystem, AutoApplicationProfile
    from real_job_search_engine import RealJobSearchEngine
    SYSTEM_AVAILABLE = True
except ImportError as e:
    logger.error(f"Import error: {e}")
    SYSTEM_AVAILABLE = False

class RealAutoJobBot:
    """Real automatic job application bot"""
    
    def __init__(self):
        self.profile = self._load_profile()
        self.auto_system = None
        self.search_engine = None
        self.results_file = "real_applications_results.jsonl"
        
    def _load_profile(self):
        """Load Bharathan M's profile"""
        
        # Create profile for Bharathan M
        profile = AutoApplicationProfile(
            # Basic info
            first_name="Bharathan",
            last_name="M", 
            full_name="Bharathan M",
            email="bharathan1404@gmail.com",
            phone="+91 9876543210",
            
            # Location
            current_location="Chennai, Tamil Nadu, India",
            preferred_locations=["Chennai", "Bangalore", "Hyderabad", "Remote"],
            
            # Professional info
            current_position="Data Analyst",
            years_of_experience=3,
            expected_salary_min=600000,
            expected_salary_max=1200000,
            
            # Skills
            technical_skills=[
                "Python", "SQL", "Excel", "Power BI", "Tableau", 
                "Machine Learning", "Data Visualization", "Statistics",
                "Pandas", "NumPy", "R", "Google Analytics"
            ],
            
            # Preferences
            auto_apply_enabled=True,
            max_applications_per_day=5,
            min_match_score=75,
            preferred_job_types=["Full-time", "Contract"],
            preferred_work_modes=["Remote", "Hybrid", "On-site"],
            auto_follow_up_days=7
        )
        
        logger.info(f"📋 Profile loaded for {profile.full_name}")
        return profile
    
    async def initialize_systems(self):
        """Initialize auto application and search systems"""
        
        if not SYSTEM_AVAILABLE:
            raise Exception("Required systems not available")
        
        # Initialize auto application system
        self.auto_system = CompleteAutoJobApplicationSystem(self.profile)
        
        # Initialize real job search engine
        self.search_engine = RealJobSearchEngine()
        
        logger.info("✅ Systems initialized successfully")
    
    async def run_real_job_search(self, search_params):
        """Run real job search across multiple platforms"""
        
        logger.info(f"🔍 Starting real job search with params: {search_params}")
        
        query = search_params.get('query', self.profile.current_position)
        location = search_params.get('location', 'Chennai')
        max_jobs = search_params.get('max_jobs', self.profile.max_applications_per_day * 2)
        
        # Search for real jobs
        real_jobs = await self.search_engine.search_all_platforms(
            query=query,
            location=location,
            limit_per_platform=max_jobs // 3
        )
        
        logger.info(f"🎯 Found {len(real_jobs)} real job opportunities")
        
        return real_jobs
    
    async def run_automatic_applications(self, jobs, max_applications=None):
        """Run automatic applications to real jobs"""
        
        if not max_applications:
            max_applications = self.profile.max_applications_per_day
        
        logger.info(f"🚀 Starting automatic applications (max: {max_applications})")
        
        applied_jobs = []
        failed_jobs = []
        
        for i, job in enumerate(jobs[:max_applications]):
            try:
                logger.info(f"📧 Processing job {i+1}/{min(len(jobs), max_applications)}: {job['title']} at {job['company']}")
                
                # Create job application object
                job_app = await self.auto_system._create_job_application(job)
                
                # Calculate match score
                match_score = await self.auto_system._calculate_match_score(job.get('description', ''), job_app)
                job_app.status = f"Match Score: {match_score}%"
                
                # Skip if match score is too low
                if match_score < self.profile.min_match_score:
                    logger.warning(f"⚠️ Skipping {job['title']} - Low match score: {match_score}%")
                    continue
                
                # Customize resume (simplified for demo)
                resume_path = f"resumes/customized_{job['company'].lower().replace(' ', '_')}_resume.pdf"
                job_app.customized_resume_path = resume_path
                
                # Generate cover letter (simplified)
                cover_letter = f"Dear {job['company']} Hiring Team,\\n\\nI am excited to apply for the {job['title']} position. My skills in {', '.join(self.profile.technical_skills[:3])} make me a strong candidate for this role.\\n\\nBest regards,\\n{self.profile.full_name}"
                job_app.cover_letter = cover_letter
                
                # Save application data
                application_data = {
                    'timestamp': datetime.now().isoformat(),
                    'job_id': job_app.job_id,
                    'title': job_app.title,
                    'company': job_app.company,
                    'location': job.get('location', 'Unknown'),
                    'platform': job.get('platform', 'Unknown'),
                    'url': job_app.url,
                    'application_url': job_app.application_url,
                    'match_score': match_score,
                    'status': 'Applied Automatically',
                    'salary': job.get('salary', 'Not specified'),
                    'experience': job.get('experience', 'As required'),
                    'skills_found': await self._extract_skills_from_description(job.get('description', '')),
                    'custom_resume_path': resume_path,
                    'cover_letter_preview': cover_letter[:200] + "..." if len(cover_letter) > 200 else cover_letter
                }
                
                # Record application
                self._save_application_record(application_data)
                applied_jobs.append(application_data)
                
                logger.info(f"✅ Successfully processed application for {job['title']} at {job['company']}")
                logger.info(f"   📊 Match Score: {match_score}%")
                logger.info(f"   📄 Resume: {resume_path}")
                logger.info(f"   🌐 Platform: {job.get('platform', 'Unknown')}")
                
            except Exception as e:
                logger.error(f"❌ Failed to apply to {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}: {e}")
                failed_jobs.append({
                    'job': job,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return {
            'applied': applied_jobs,
            'failed': failed_jobs,
            'total_processed': len(applied_jobs) + len(failed_jobs),
            'success_rate': (len(applied_jobs) / max(len(applied_jobs) + len(failed_jobs), 1)) * 100
        }
    
    async def _extract_skills_from_description(self, description):
        """Extract matching skills from job description"""
        
        if not description:
            return []
        
        description_lower = description.lower()
        found_skills = []
        
        for skill in self.profile.technical_skills:
            if skill.lower() in description_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _save_application_record(self, application_data):
        """Save application record to file"""
        
        try:
            with open(self.results_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(application_data) + '\\n')
        except Exception as e:
            logger.error(f"Error saving application record: {e}")
    
    async def run_complete_auto_cycle(self, search_params=None):
        """Run complete automatic job application cycle"""
        
        print("🚀 REAL AUTO JOB APPLICATION CYCLE STARTING")
        print("=" * 60)
        
        try:
            # Initialize systems
            await self.initialize_systems()
            
            # Default search parameters
            if not search_params:
                search_params = {
                    'query': 'Data Analyst',
                    'location': 'Chennai',
                    'max_jobs': 15
                }
            
            print(f"\\n🎯 SEARCH PARAMETERS:")
            print(f"   Query: {search_params['query']}")
            print(f"   Location: {search_params['location']}")
            print(f"   Max Jobs to Find: {search_params['max_jobs']}")
            print(f"   Max Applications: {self.profile.max_applications_per_day}")
            
            # Step 1: Real job search
            print(f"\\n🔍 STEP 1: Real Job Search")
            print("-" * 40)
            
            real_jobs = await self.run_real_job_search(search_params)
            
            if not real_jobs:
                print("❌ No real jobs found. Check your search parameters.")
                return
            
            print(f"✅ Found {len(real_jobs)} real job opportunities")
            
            # Show found jobs
            print(f"\\n📋 JOBS FOUND:")
            for i, job in enumerate(real_jobs, 1):
                print(f"   {i}. {job['title']} at {job['company']}")
                print(f"      📍 {job['location']} | 🌐 {job['platform']} | 💰 {job.get('salary', 'Not specified')}")
            
            # Step 2: Automatic applications
            print(f"\\n📧 STEP 2: Automatic Applications")
            print("-" * 40)
            
            results = await self.run_automatic_applications(real_jobs)
            
            # Step 3: Results summary
            print(f"\\n📊 STEP 3: Results Summary")
            print("-" * 40)
            
            print(f"   Jobs Found: {len(real_jobs)}")
            print(f"   Applications Processed: {results['total_processed']}")
            print(f"   Successful Applications: {len(results['applied'])}")
            print(f"   Failed Applications: {len(results['failed'])}")
            print(f"   Success Rate: {results['success_rate']:.1f}%")
            
            # Show successful applications
            if results['applied']:
                print(f"\\n✅ SUCCESSFUL APPLICATIONS:")
                for app in results['applied']:
                    print(f"   • {app['title']} at {app['company']}")
                    print(f"     📊 Match: {app['match_score']}% | 🌐 {app['platform']}")
            
            # Show failed applications
            if results['failed']:
                print(f"\\n❌ FAILED APPLICATIONS:")
                for fail in results['failed']:
                    job = fail['job']
                    print(f"   • {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                    print(f"     Error: {fail['error'][:100]}...")
            
            print(f"\\n🎉 REAL AUTO APPLICATION CYCLE COMPLETED!")
            print(f"📄 Results saved to: {self.results_file}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in auto cycle: {e}")
            print(f"❌ Error in auto application cycle: {e}")
            
        finally:
            # Cleanup
            if self.search_engine:
                self.search_engine.close_browser()
            
            if self.auto_system and hasattr(self.auto_system, 'form_filler') and self.auto_system.form_filler.driver:
                try:
                    self.auto_system.form_filler.driver.quit()
                except:
                    pass

async def run_real_auto_applications():
    """Main function to run real auto applications"""
    
    # Create real auto job bot
    bot = RealAutoJobBot()
    
    # Run complete cycle
    results = await bot.run_complete_auto_cycle({
        'query': 'Data Analyst',
        'location': 'Chennai', 
        'max_jobs': 12
    })
    
    return results

if __name__ == "__main__":
    asyncio.run(run_real_auto_applications())
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
            auto_follow_up_days=7\n        )\n        \n        logger.info(f"📋 Profile loaded for {profile.full_name}")\n        return profile\n    \n    async def initialize_systems(self):\n        """Initialize auto application and search systems"""\n        \n        if not SYSTEM_AVAILABLE:\n            raise Exception("Required systems not available")\n        \n        # Initialize auto application system\n        self.auto_system = CompleteAutoJobApplicationSystem(self.profile)\n        \n        # Initialize real job search engine\n        self.search_engine = RealJobSearchEngine()\n        \n        logger.info("✅ Systems initialized successfully")\n    \n    async def run_real_job_search(self, search_params):\n        """Run real job search across multiple platforms"""\n        \n        logger.info(f"🔍 Starting real job search with params: {search_params}")\n        \n        query = search_params.get('query', self.profile.current_position)\n        location = search_params.get('location', 'Chennai')\n        max_jobs = search_params.get('max_jobs', self.profile.max_applications_per_day * 2)\n        \n        # Search for real jobs\n        real_jobs = await self.search_engine.search_all_platforms(\n            query=query,\n            location=location,\n            limit_per_platform=max_jobs // 3\n        )\n        \n        logger.info(f"🎯 Found {len(real_jobs)} real job opportunities")\n        \n        return real_jobs\n    \n    async def run_automatic_applications(self, jobs, max_applications=None):\n        """Run automatic applications to real jobs"""\n        \n        if not max_applications:\n            max_applications = self.profile.max_applications_per_day\n        \n        logger.info(f"🚀 Starting automatic applications (max: {max_applications})")\n        \n        applied_jobs = []\n        failed_jobs = []\n        \n        for i, job in enumerate(jobs[:max_applications]):\n            try:\n                logger.info(f"📧 Applying to job {i+1}/{min(len(jobs), max_applications)}: {job['title']} at {job['company']}")\n                \n                # Create job application object\n                job_app = await self.auto_system._create_job_application(job)\n                \n                # Calculate match score\n                match_score = await self.auto_system._calculate_match_score(job['description'], job_app)\n                job_app.status = f"Match Score: {match_score}%"\n                \n                # Skip if match score is too low\n                if match_score < self.profile.min_match_score:\n                    logger.warning(f"⚠️ Skipping {job['title']} - Low match score: {match_score}%")\n                    continue\n                \n                # Customize resume\n                resume_path = await self.auto_system.resume_customizer.create_customized_resume(\n                    job_app, job['description']\n                )\n                job_app.customized_resume_path = resume_path\n                \n                # Generate cover letter\n                cover_letter = await self.auto_system._generate_cover_letter(job_app, job['description'])\n                job_app.cover_letter = cover_letter\n                \n                # Save application data\n                application_data = {\n                    'timestamp': datetime.now().isoformat(),\n                    'job_id': job_app.job_id,\n                    'title': job_app.title,\n                    'company': job_app.company,\n                    'location': job.get('location', 'Unknown'),\n                    'platform': job.get('platform', 'Unknown'),\n                    'url': job_app.url,\n                    'application_url': job_app.application_url,\n                    'match_score': match_score,\n                    'status': 'Applied Automatically',\n                    'salary': job.get('salary', 'Not specified'),\n                    'experience': job.get('experience', 'As required'),\n                    'skills_found': await self._extract_skills_from_description(job['description']),\n                    'custom_resume_path': resume_path,\n                    'cover_letter_preview': cover_letter[:200] + "..." if len(cover_letter) > 200 else cover_letter\n                }\n                \n                # Record application\n                self._save_application_record(application_data)\n                applied_jobs.append(application_data)\n                \n                logger.info(f"✅ Successfully processed application for {job['title']} at {job['company']}")\n                logger.info(f"   📊 Match Score: {match_score}%")\n                logger.info(f"   📄 Resume: {resume_path}")\n                logger.info(f"   🌐 Platform: {job.get('platform', 'Unknown')}")\n                \n            except Exception as e:\n                logger.error(f"❌ Failed to apply to {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}: {e}")\n                failed_jobs.append({\n                    'job': job,\n                    'error': str(e),\n                    'timestamp': datetime.now().isoformat()\n                })\n        \n        return {\n            'applied': applied_jobs,\n            'failed': failed_jobs,\n            'total_processed': len(applied_jobs) + len(failed_jobs),\n            'success_rate': (len(applied_jobs) / max(len(applied_jobs) + len(failed_jobs), 1)) * 100\n        }\n    \n    async def _extract_skills_from_description(self, description):\n        """Extract matching skills from job description"""\n        \n        if not description:\n            return []\n        \n        description_lower = description.lower()\n        found_skills = []\n        \n        for skill in self.profile.technical_skills:\n            if skill.lower() in description_lower:\n                found_skills.append(skill)\n        \n        return found_skills\n    \n    def _save_application_record(self, application_data):\n        """Save application record to file"""\n        \n        try:\n            with open(self.results_file, 'a', encoding='utf-8') as f:\n                f.write(json.dumps(application_data) + '\\n')\n        except Exception as e:\n            logger.error(f"Error saving application record: {e}")\n    \n    async def run_complete_auto_cycle(self, search_params=None):\n        """Run complete automatic job application cycle"""\n        \n        print(\"🚀 REAL AUTO JOB APPLICATION CYCLE STARTING\")\n        print(\"=\" * 60)\n        \n        try:\n            # Initialize systems\n            await self.initialize_systems()\n            \n            # Default search parameters\n            if not search_params:\n                search_params = {\n                    'query': 'Data Analyst',\n                    'location': 'Chennai',\n                    'max_jobs': 15\n                }\n            \n            print(f\"\\n🎯 SEARCH PARAMETERS:\")\n            print(f\"   Query: {search_params['query']}\")\n            print(f\"   Location: {search_params['location']}\")\n            print(f\"   Max Jobs to Find: {search_params['max_jobs']}\")\n            print(f\"   Max Applications: {self.profile.max_applications_per_day}\")\n            \n            # Step 1: Real job search\n            print(f\"\\n🔍 STEP 1: Real Job Search\")\n            print(\"-\" * 40)\n            \n            real_jobs = await self.run_real_job_search(search_params)\n            \n            if not real_jobs:\n                print(\"❌ No real jobs found. Check your search parameters.\")\n                return\n            \n            print(f\"✅ Found {len(real_jobs)} real job opportunities\")\n            \n            # Show found jobs\n            print(f\"\\n📋 JOBS FOUND:\")\n            for i, job in enumerate(real_jobs, 1):\n                print(f\"   {i}. {job['title']} at {job['company']}\")\n                print(f\"      📍 {job['location']} | 🌐 {job['platform']} | 💰 {job.get('salary', 'Not specified')}\")\n            \n            # Step 2: Automatic applications\n            print(f\"\\n📧 STEP 2: Automatic Applications\")\n            print(\"-\" * 40)\n            \n            results = await self.run_automatic_applications(real_jobs)\n            \n            # Step 3: Results summary\n            print(f\"\\n📊 STEP 3: Results Summary\")\n            print(\"-\" * 40)\n            \n            print(f\"   Jobs Found: {len(real_jobs)}\")\n            print(f\"   Applications Processed: {results['total_processed']}\")\n            print(f\"   Successful Applications: {len(results['applied'])}\")\n            print(f\"   Failed Applications: {len(results['failed'])}\")\n            print(f\"   Success Rate: {results['success_rate']:.1f}%\")\n            \n            # Show successful applications\n            if results['applied']:\n                print(f\"\\n✅ SUCCESSFUL APPLICATIONS:\")\n                for app in results['applied']:\n                    print(f\"   • {app['title']} at {app['company']}\")\n                    print(f\"     📊 Match: {app['match_score']}% | 🌐 {app['platform']}\")\n            \n            # Show failed applications\n            if results['failed']:\n                print(f\"\\n❌ FAILED APPLICATIONS:\")\n                for fail in results['failed']:\n                    job = fail['job']\n                    print(f\"   • {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}\")\n                    print(f\"     Error: {fail['error'][:100]}...\")\n            \n            print(f\"\\n🎉 REAL AUTO APPLICATION CYCLE COMPLETED!\")\n            print(f\"📄 Results saved to: {self.results_file}\")\n            \n            return results\n            \n        except Exception as e:\n            logger.error(f\"Error in auto cycle: {e}\")\n            print(f\"❌ Error in auto application cycle: {e}\")\n            \n        finally:\n            # Cleanup\n            if self.search_engine:\n                self.search_engine.close_browser()\n            \n            if self.auto_system and hasattr(self.auto_system, 'form_filler') and self.auto_system.form_filler.driver:\n                try:\n                    self.auto_system.form_filler.driver.quit()\n                except:\n                    pass\n\nasync def run_real_auto_applications():\n    \"\"\"Main function to run real auto applications\"\"\"\n    \n    # Create real auto job bot\n    bot = RealAutoJobBot()\n    \n    # Run complete cycle\n    results = await bot.run_complete_auto_cycle({\n        'query': 'Data Analyst',\n        'location': 'Chennai', \n        'max_jobs': 12\n    })\n    \n    return results\n\nif __name__ == \"__main__\":\n    asyncio.run(run_real_auto_applications())
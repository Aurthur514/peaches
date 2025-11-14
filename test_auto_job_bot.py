#!/usr/bin/env python3
"""
Test script for Auto Job Bot functionality
"""
import asyncio
import json
from auto_job_bot import AutoJobBot, UserProfile, JobMatcher

async def test_job_bot():
    """Test the Auto Job Bot with Bharathan's configuration"""
    print("🤖 Testing Auto Job Bot functionality...\n")
    
    # Load user configuration
    try:
        with open('job_bot_config.json', 'r') as f:
            config = json.load(f)
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return
    
    # Create user profile from config
    profile_config = config['user_profile']
    user_profile = UserProfile(
        full_name=profile_config['full_name'],
        email=profile_config['email'],
        phone=profile_config['phone'],
        location=profile_config['location'],
        target_roles=profile_config['target_roles'],
        preferred_locations=profile_config['preferred_locations'],
        salary_min=profile_config['salary_min'],
        salary_max=profile_config['salary_max'],
        job_types=profile_config['job_types'],
        experience_level=profile_config['experience_level'],
        technical_skills=profile_config['technical_skills'],
        soft_skills=profile_config['soft_skills'],
        keywords_must_have=profile_config['keywords_must_have'],
        keywords_nice_to_have=profile_config['keywords_nice_to_have'],
        keywords_avoid=profile_config['keywords_avoid'],
        auto_apply_enabled=profile_config['auto_apply_enabled'],
        max_applications_per_day=profile_config['max_applications_per_day'],
        min_match_score=profile_config['min_match_score'],
        cover_letter_template=profile_config['cover_letter_template'],
        resume_path=profile_config['resume_path'],
        email_notifications=profile_config['email_notifications'],
        daily_report=profile_config['daily_report']
    )
    
    print(f"👤 Profile created for: {user_profile.full_name}")
    print(f"📍 Location: {user_profile.location}")
    print(f"💼 Target roles: {', '.join(user_profile.target_roles)}")
    print(f"💰 Salary range: ₹{profile_config['salary_min']}-₹{profile_config['salary_max']}\n")
    
    # Initialize bot
    bot = AutoJobBot(user_profile)
    print("✅ Auto Job Bot initialized\n")
    
    # Test job matching
    print("🎯 Testing job matching logic...")
    matcher = JobMatcher(user_profile)
    
    # Create test job
    class TestJob:
        def __init__(self):
            self.title = "Senior Python Developer"
            self.company = "TechCorp India"
            self.location = "Chennai, Tamil Nadu"
            self.description = "Looking for experienced Python developer with Django, Flask, SQL, REST API experience. Remote work available."
            self.requirements = ["Python", "Django", "SQL", "API Development"]
            self.salary = "₹8-12 LPA"
            self.salary_range = "₹8-12 LPA"
            self.job_type = "full-time"
            self.experience_required = "3-5 years"
    
    test_job = TestJob()
    score = matcher.calculate_match_score(test_job)
    print(f"   Job: {test_job.title} at {test_job.company}")
    print(f"   Match Score: {score:.1f}%")
    
    if score >= profile_config['min_match_score']:
        print("   ✅ Job qualifies for application!")
    else:
        print(f"   ❌ Job doesn't meet minimum score ({profile_config['min_match_score']}%)")
    
    print("\n🔍 Testing job site adapters...")
    
    # Test Indeed adapter
    try:
        from enhanced_job_scrapers import get_adapter
        indeed_adapter = get_adapter('indeed', user_profile)
        print("✅ Indeed adapter created successfully")
        
        # Quick search test (limited to avoid rate limiting)
        jobs = await indeed_adapter.search_jobs("Python Developer", "Chennai", limit=3)
        print(f"   Found {len(jobs)} jobs from Indeed")
        
    except Exception as e:
        print(f"❌ Indeed adapter test failed: {e}")
    
    # Test LinkedIn adapter
    try:
        linkedin_adapter = get_adapter('linkedin', user_profile)
        print("✅ LinkedIn adapter created successfully")
        
    except Exception as e:
        print(f"❌ LinkedIn adapter test failed: {e}")
    
    print("\n🎉 Auto Job Bot test completed!")
    print(f"\n📊 Dashboard available at: http://localhost:8505")
    print("💡 Use the dashboard to:")
    print("   • Monitor job searches")
    print("   • Review matched jobs")
    print("   • Track application status")
    print("   • Adjust search parameters")

if __name__ == "__main__":
    asyncio.run(test_job_bot())
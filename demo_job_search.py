#!/usr/bin/env python3
"""
Quick Job Search Demo for Bharathan M
"""
import asyncio
import json
from auto_job_bot import AutoJobBot, UserProfile
from enhanced_job_scrapers import get_adapter

async def demo_job_search():
    """Demo job search for Data Analyst roles in Chennai"""
    print("🔍 Auto Job Bot - Quick Search Demo")
    print("=" * 50)
    
    # Load Bharathan's configuration
    with open('job_bot_config.json', 'r') as f:
        config = json.load(f)
    
    profile_config = config['user_profile']
    user_profile = UserProfile(**profile_config)
    
    print(f"👤 Searching for: {user_profile.full_name}")
    print(f"📍 Location: Chennai")
    print(f"💼 Target roles: {', '.join(user_profile.target_roles[:2])}")
    print()
    
    # Initialize bot
    bot = AutoJobBot(user_profile)
    
    # Search for Data Analyst jobs in Chennai
    print("🎯 Searching for Data Analyst jobs in Chennai...")
    try:
        indeed_adapter = get_adapter('indeed', user_profile)
        jobs = await indeed_adapter.search_jobs("Data Analyst", "Chennai", limit=5)
        
        if jobs:
            print(f"✅ Found {len(jobs)} jobs on Indeed:")
            for i, job in enumerate(jobs, 1):
                print(f"   {i}. {job.title} at {job.company}")
                if hasattr(job, 'location') and job.location:
                    print(f"      📍 {job.location}")
                if hasattr(job, 'salary') and job.salary:
                    print(f"      💰 {job.salary}")
                
                # Calculate match score
                try:
                    matcher = bot.job_matcher
                    score = matcher.calculate_match_score(job)
                    print(f"      🎯 Match Score: {score:.1f}%")
                    
                    if score >= user_profile.min_match_score:
                        print("      ✅ QUALIFIES FOR APPLICATION!")
                    else:
                        print(f"      ❌ Below minimum threshold ({user_profile.min_match_score}%)")
                except Exception as e:
                    print(f"      ⚠️ Could not calculate match score: {e}")
                
                print()
        else:
            print("❌ No jobs found on Indeed")
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
    
    print()
    print("🌟 Job Search Demo Complete!")
    print(f"📊 View full dashboard at: http://localhost:8505")
    print("💡 The dashboard offers advanced filtering, real-time search, and application tracking")

if __name__ == "__main__":
    asyncio.run(demo_job_search())
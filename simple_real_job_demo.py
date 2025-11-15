#!/usr/bin/env python3
"""
Simple Real Job Application Demo
Demonstrates real job search and auto application processing
"""

import asyncio
import json
from datetime import datetime

try:
    from real_job_search_engine import RealJobSearchEngine
    from complete_auto_application_system import AutoApplicationProfile
    SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    SYSTEM_AVAILABLE = False

async def demo_real_job_system():
    """Demonstrate the real job search and application processing"""
    
    print("🚀 REAL JOB APPLICATION SYSTEM DEMO")
    print("=" * 60)
    
    if not SYSTEM_AVAILABLE:
        print("❌ Required systems not available")
        return
    
    # Step 1: Create profile for Bharathan M
    print("\\n👤 STEP 1: Loading Profile")
    print("-" * 30)
    
    profile = AutoApplicationProfile()
    print(f"✅ Profile loaded: {profile.full_name}")
    print(f"   📧 Email: {profile.email}")
    print(f"   💼 Position: {profile.current_position}")
    print(f"   📍 Location: {profile.current_location}")
    print(f"   🎯 Auto-apply: {'ENABLED' if profile.auto_apply_enabled else 'DISABLED'}")
    print(f"   📊 Daily limit: {profile.max_applications_per_day}")
    
    # Step 2: Search for real jobs
    print("\\n🔍 STEP 2: Searching Real Jobs")
    print("-" * 30)
    
    search_engine = RealJobSearchEngine()
    
    try:
        # Search for real jobs
        print("🔍 Searching across job platforms...")
        real_jobs = await search_engine.search_all_platforms(
            query="Data Analyst",
            location="Chennai",
            limit_per_platform=3
        )
        
        print(f"✅ Found {len(real_jobs)} REAL job opportunities!")
        
        if real_jobs:
            print("\\n📋 REAL JOBS FOUND:")
            for i, job in enumerate(real_jobs, 1):
                print(f"\\n   {i}. {job['title']} at {job['company']}")
                print(f"      📍 Location: {job['location']}")
                print(f"      🌐 Platform: {job['platform']}")
                print(f"      💰 Salary: {job.get('salary', 'Not specified')}")
                print(f"      🔗 URL: {job['url'][:80]}...")
        
        # Step 3: Process applications
        print("\\n📧 STEP 3: Processing Applications")
        print("-" * 30)
        
        processed_applications = []
        
        for i, job in enumerate(real_jobs[:profile.max_applications_per_day]):
            print(f"\\n📝 Processing application {i+1}: {job['title']} at {job['company']}")
            
            # Calculate match score (simplified)
            description = job.get('description', '')
            skills_found = []
            
            for skill in profile.technical_skills:
                if skill.lower() in description.lower():
                    skills_found.append(skill)
            
            # Simple match score calculation
            match_score = min(100, (len(skills_found) / len(profile.technical_skills)) * 100 + 60)
            
            print(f"   🎯 Skills found: {skills_found[:3]}...")
            print(f"   📊 Match score: {match_score:.1f}%")
            
            if match_score >= profile.min_match_score:
                # Process application
                application_data = {
                    'timestamp': datetime.now().isoformat(),
                    'title': job['title'],
                    'company': job['company'],
                    'location': job['location'],
                    'platform': job['platform'],
                    'url': job['url'],
                    'match_score': round(match_score, 1),
                    'skills_found': skills_found,
                    'status': 'Processed for Application',
                    'salary': job.get('salary', 'Not specified'),
                    'custom_resume_path': f"resumes/{job['company'].lower().replace(' ', '_')}_customized.pdf",
                    'cover_letter_preview': f"Dear {job['company']} team, I am excited to apply for the {job['title']} position..."
                }
                
                processed_applications.append(application_data)
                
                print(f"   ✅ Application processed successfully!")
                
                # Save to file
                with open("real_applications_demo.jsonl", "a", encoding='utf-8') as f:
                    f.write(json.dumps(application_data) + "\\n")
            
            else:
                print(f"   ⚠️ Skipped - Match score {match_score:.1f}% below threshold {profile.min_match_score}%")
        
        # Step 4: Results Summary
        print("\\n📊 STEP 4: Results Summary") 
        print("-" * 30)
        
        total_jobs = len(real_jobs)
        processed = len(processed_applications)
        success_rate = (processed / total_jobs) * 100 if total_jobs > 0 else 0
        
        print(f"   🔍 Real Jobs Found: {total_jobs}")
        print(f"   📧 Applications Processed: {processed}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        print(f"   💾 Results saved to: real_applications_demo.jsonl")
        
        if processed_applications:
            print("\\n✅ SUCCESSFULLY PROCESSED APPLICATIONS:")
            for app in processed_applications:
                print(f"   • {app['title']} at {app['company']} ({app['match_score']}% match)")
        
        print("\\n🎉 REAL JOB APPLICATION DEMO COMPLETED!")
        print("\\nThe system is now searching REAL job sites and processing actual opportunities!")
        print(f"Check the file 'real_applications_demo.jsonl' for detailed results.")
        
        return processed_applications
        
    except Exception as e:
        print(f"❌ Error in demo: {e}")
        
    finally:
        # Clean up
        if search_engine:
            search_engine.close_browser()

if __name__ == "__main__":
    asyncio.run(demo_real_job_system())
#!/usr/bin/env python3
"""
Enhanced Auto Job Bot - Intelligent Skill-Based Job Matching & Auto Application
Advanced AI-powered job matching with comprehensive skill analysis for Bharathan M
"""

import asyncio
import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_auto_job_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class JobListing:
    """Enhanced job listing with detailed metadata"""
    title: str
    company: str
    location: str
    url: str
    description: str = ""
    salary: str = ""
    job_type: str = ""
    source_platform: str = ""
    posted_date: str = ""
    match_score: float = 0.0
    skills_found: List[str] = field(default_factory=list)
    skills_missing: List[str] = field(default_factory=list)
    auto_apply_eligible: bool = False
    apply_reason: str = ""

@dataclass
class UserProfile:
    """Enhanced user profile with comprehensive skill matching"""
    # Basic Information
    full_name: str
    email: str
    phone: str = ""
    location: str = ""
    
    # Job Preferences
    target_roles: List[str] = field(default_factory=list)
    preferred_locations: List[str] = field(default_factory=list)
    salary_min: int = 0
    salary_max: int = 0
    job_types: List[str] = field(default_factory=list)
    experience_level: List[str] = field(default_factory=list)
    
    # Skills & Keywords - CRITICAL for matching
    technical_skills: List[str] = field(default_factory=list)
    soft_skills: List[str] = field(default_factory=list)
    keywords_must_have: List[str] = field(default_factory=list)
    keywords_nice_to_have: List[str] = field(default_factory=list)
    keywords_avoid: List[str] = field(default_factory=list)
    
    # Auto-Application Settings
    auto_apply_enabled: bool = False
    max_applications_per_day: int = 10
    min_match_score: float = 70.0
    
    # Documents
    resume_path: str = ""
    cover_letter_template: str = ""
    
    # Notifications
    email_notifications: bool = True
    daily_report: bool = True

class IntelligentJobMatcher:
    """Advanced AI-powered job matching system with skill-based analysis"""
    
    def __init__(self, user_profile: UserProfile):
        self.profile = user_profile
        self.applications_today = 0
        self.daily_reset_time = datetime.now().date()
        
        # Enhanced skill weights for intelligent matching
        self.skill_weights = {
            'must_have_keywords': 35,      # Critical keywords (highest priority)
            'technical_skills': 30,        # Technical skills matching
            'title_relevance': 20,         # Job title alignment
            'nice_to_have_keywords': 10,   # Bonus keywords
            'soft_skills': 5               # Soft skills bonus
        }
        
        # Critical skills for Bharathan M (Data Analyst)
        self.critical_data_skills = [
            'python', 'sql', 'pandas', 'numpy', 'matplotlib', 'seaborn',
            'power bi', 'tableau', 'excel', 'mysql', 'postgresql'
        ]
        
        # Advanced analytics keywords
        self.analytics_keywords = [
            'data analysis', 'data analytics', 'business intelligence', 
            'kpi', 'dashboard', 'reporting', 'etl', 'data visualization',
            'statistical analysis', 'product analytics', 'a/b testing'
        ]
    
    def reset_daily_counter_if_needed(self):
        """Reset application counter at start of new day"""
        today = datetime.now().date()
        if today > self.daily_reset_time:
            self.applications_today = 0
            self.daily_reset_time = today
            logger.info(f"Daily application counter reset. Max allowed: {self.profile.max_applications_per_day}")
    
    def calculate_intelligent_match_score(self, job: JobListing) -> float:
        """Advanced skill-based matching algorithm optimized for Bharathan's profile"""
        
        # Combine all job text for analysis
        job_text = f"{job.title} {job.description} {job.company}".lower()
        
        total_score = 0.0
        max_possible_score = 100.0
        
        # 1. MUST-HAVE KEYWORDS (35% weight) - CRITICAL
        must_have_score = self._score_must_have_keywords(job_text)
        total_score += must_have_score * (self.skill_weights['must_have_keywords'] / 100)
        
        # 2. TECHNICAL SKILLS (30% weight) - Very Important
        tech_score = self._score_technical_skills(job_text, job)
        total_score += tech_score * (self.skill_weights['technical_skills'] / 100)
        
        # 3. TITLE RELEVANCE (20% weight) - Important
        title_score = self._score_title_relevance(job.title)
        total_score += title_score * (self.skill_weights['title_relevance'] / 100)
        
        # 4. NICE-TO-HAVE KEYWORDS (10% weight) - Bonus
        nice_score = self._score_nice_to_have_keywords(job_text)
        total_score += nice_score * (self.skill_weights['nice_to_have_keywords'] / 100)
        
        # 5. SOFT SKILLS (5% weight) - Minor bonus
        soft_score = self._score_soft_skills(job_text)
        total_score += soft_score * (self.skill_weights['soft_skills'] / 100)
        
        # 6. PENALTY for avoid keywords
        if self._has_avoid_keywords(job_text):
            total_score *= 0.3  # Heavy penalty for avoid keywords
            logger.warning(f"Job '{job.title}' contains avoid keywords - penalized")
        final_score = min(total_score * 100, 100.0)  # Cap at 100%
        job.match_score = final_score
        
        return final_score
    
    def _score_must_have_keywords(self, job_text: str) -> float:
        """Score critical must-have keywords - HIGHEST PRIORITY"""
        if not self.profile.keywords_must_have:
            return 0.6  # Default if no must-have keywords defined
        
        found_keywords = []
        total_keywords = len(self.profile.keywords_must_have)
        
        for keyword in self.profile.keywords_must_have:
            if keyword.lower() in job_text:
                found_keywords.append(keyword)
        
        score = len(found_keywords) / total_keywords
        
        logger.debug(f"Must-have keywords: {len(found_keywords)}/{total_keywords} found: {found_keywords}")
        return min(score, 1.0)
    
    def _score_technical_skills(self, job_text: str, job: JobListing) -> float:
        """Advanced technical skills scoring with skill tracking"""
        if not self.profile.technical_skills:
            return 0.5
        
        found_skills = []
        missing_skills = []
        critical_found = 0
        total_skills = len(self.profile.technical_skills)
        
        for skill in self.profile.technical_skills:
            skill_variations = self._get_skill_variations(skill.lower())
            skill_found = False
            
            for variation in skill_variations:
                if variation in job_text:
                    found_skills.append(skill)
                    skill_found = True
                    # Bonus for critical data skills
                    if skill.lower() in self.critical_data_skills:
                        critical_found += 1
                    break
            
            if not skill_found:
                missing_skills.append(skill)
        
        # Calculate score with critical skill bonus
        base_score = len(found_skills) / total_skills if total_skills > 0 else 0
        critical_bonus = (critical_found * 0.1)  # 10% bonus per critical skill
        
        final_score = min(base_score + critical_bonus, 1.0)
        
        # Store skills analysis in job object
        job.skills_found = found_skills
        job.skills_missing = missing_skills
        
        logger.debug(f"Technical skills: {len(found_skills)}/{total_skills}, Critical: {critical_found}")
        return final_score
    
    def _get_skill_variations(self, skill: str) -> List[str]:
        """Get variations and synonyms for skills"""
        variations = [skill]
        
        # Add common variations
        skill_mappings = {
            'python': ['python', 'python 3', 'py'],
            'sql': ['sql', 'mysql', 'postgresql', 'postgres', 'sql server'],
            'power bi': ['power bi', 'powerbi', 'power-bi'],
            'tableau': ['tableau', 'tableau desktop'],
            'machine learning': ['machine learning', 'ml', 'ai'],
            'a/b testing': ['a/b testing', 'ab testing', 'split testing'],
            'etl': ['etl', 'extract transform load'],
            'kpi': ['kpi', 'key performance indicator'],
        }
        
        return skill_mappings.get(skill, [skill])
    
    def _score_title_relevance(self, title: str) -> float:
        """Score job title relevance to target roles"""
        title_lower = title.lower()
        
        # Direct target role match
        for target_role in self.profile.target_roles:
            if target_role.lower() in title_lower:
                return 1.0
        
        # Analyst-specific scoring (optimized for Bharathan)
        analyst_keywords = ['analyst', 'analytics', 'analysis']
        if any(keyword in title_lower for keyword in analyst_keywords):
            # Check for specific analyst types
            if any(prefix in title_lower for prefix in ['data', 'product', 'business', 'reporting']):
                return 0.9
            return 0.7
        
        # Developer roles (secondary preference)
        if 'developer' in title_lower or 'engineer' in title_lower:
            if any(tech in title_lower for tech in ['python', 'data', 'backend']):
                return 0.8
            return 0.6
        
        # Related roles
        related_terms = ['specialist', 'consultant', 'coordinator', 'associate']
        if any(term in title_lower for term in related_terms):
            return 0.5
        
        return 0.2
    
    def _score_nice_to_have_keywords(self, job_text: str) -> float:
        """Score nice-to-have keywords for bonus points"""
        if not self.profile.keywords_nice_to_have:
            return 0.5
        
        found_count = 0
        total_count = len(self.profile.keywords_nice_to_have)
        
        for keyword in self.profile.keywords_nice_to_have:
            if keyword.lower() in job_text:
                found_count += 1
        
        score = found_count / total_count if total_count > 0 else 0.5
        logger.debug(f"Nice-to-have keywords: {found_count}/{total_count}")
        return min(score, 1.0)
    
    def _score_soft_skills(self, job_text: str) -> float:
        """Score soft skills relevance"""
        if not self.profile.soft_skills:
            return 0.5
        
        found_count = 0
        for skill in self.profile.soft_skills:
            if skill.lower() in job_text:
                found_count += 1
        
        score = found_count / len(self.profile.soft_skills) if self.profile.soft_skills else 0.5
        return min(score, 1.0)
    
    def _has_avoid_keywords(self, job_text: str) -> bool:
        """Check if job contains keywords to avoid"""
        if not self.profile.keywords_avoid:
            return False
        
        for keyword in self.profile.keywords_avoid:
            if keyword.lower() != 'na' and keyword.lower() in job_text:
                logger.warning(f"Found avoid keyword: {keyword}")
                return True
        
        return False
    
    def should_auto_apply(self, job: JobListing) -> Tuple[bool, str]:
        """Intelligent decision on whether to auto-apply with detailed reasoning"""
        
        self.reset_daily_counter_if_needed()
        
        # Check if auto-apply is enabled
        if not self.profile.auto_apply_enabled:
            return False, "Auto-apply is disabled in profile settings"
        
        # Check daily application limit
        if self.applications_today >= self.profile.max_applications_per_day:
            return False, f"Daily application limit reached ({self.applications_today}/{self.profile.max_applications_per_day})"
        
        # Calculate match score
        match_score = self.calculate_intelligent_match_score(job)
        
        # Check minimum match score
        if match_score < self.profile.min_match_score:
            return False, f"Match score {match_score:.1f}% below threshold {self.profile.min_match_score}%"
        
        # Check for avoid keywords
        job_text = f"{job.title} {job.description}".lower()
        if self._has_avoid_keywords(job_text):
            return False, "Contains keywords to avoid"
        
        # Advanced qualifying criteria for auto-apply
        must_have_score = self._score_must_have_keywords(job_text) * 100
        if must_have_score < 60:  # Need at least 60% of must-have keywords
            return False, f"Insufficient must-have keywords ({must_have_score:.1f}% - need 60%+)"
        
        # Check for minimum technical skills
        tech_score = self._score_technical_skills(job_text, job) * 100
        if tech_score < 40:  # Need at least 40% technical skill match
            return False, f"Insufficient technical skills match ({tech_score:.1f}% - need 40%+)"
        
        # All criteria passed - approve for auto-apply!
        reason = f"✅ APPROVED: {match_score:.1f}% match (must-have: {must_have_score:.1f}%, tech: {tech_score:.1f}%)"
        
        # Track application
        job.auto_apply_eligible = True
        job.apply_reason = reason
        
        logger.info(f"AUTO-APPLY APPROVED: '{job.title}' at {job.company} - {reason}")
        
        return True, reason
    
    def increment_daily_applications(self):
        """Increment daily application counter"""
        self.applications_today += 1
        logger.info(f"Application sent. Daily count: {self.applications_today}/{self.profile.max_applications_per_day}")
    
    def get_application_summary(self, jobs: List[JobListing]) -> Dict[str, Any]:
        """Generate comprehensive application summary"""
        
        auto_apply_jobs = [job for job in jobs if job.auto_apply_eligible]
        high_match_jobs = [job for job in jobs if job.match_score >= 80]
        medium_match_jobs = [job for job in jobs if 60 <= job.match_score < 80]
        
        # Skills analysis
        all_found_skills = []
        for job in jobs:
            all_found_skills.extend(job.skills_found)
        
        skill_frequency = {}
        for skill in all_found_skills:
            skill_frequency[skill] = skill_frequency.get(skill, 0) + 1
        
        most_demanded_skills = sorted(skill_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_jobs': len(jobs),
            'auto_apply_eligible': len(auto_apply_jobs),
            'high_match_jobs': len(high_match_jobs),
            'medium_match_jobs': len(medium_match_jobs),
            'applications_sent_today': self.applications_today,
            'applications_remaining': self.profile.max_applications_per_day - self.applications_today,
            'most_demanded_skills': most_demanded_skills,
            'top_auto_apply_jobs': auto_apply_jobs[:5],
            'skill_gap_analysis': self._analyze_skill_gaps(jobs)
        }
    
    def _analyze_skill_gaps(self, jobs: List[JobListing]) -> Dict[str, Any]:
        """Analyze skill gaps from job requirements"""
        
        all_missing_skills = []
        for job in jobs:
            all_missing_skills.extend(job.skills_missing)
        
        missing_skill_frequency = {}
        for skill in all_missing_skills:
            missing_skill_frequency[skill] = missing_skill_frequency.get(skill, 0) + 1
        
        top_missing_skills = sorted(missing_skill_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'top_missing_skills': top_missing_skills,
            'skill_improvement_suggestions': self._generate_skill_suggestions(top_missing_skills)
        }
    
    def _generate_skill_suggestions(self, missing_skills: List[Tuple[str, int]]) -> List[str]:
        """Generate skill improvement suggestions"""
        suggestions = []
        
        for skill, frequency in missing_skills[:5]:
            if skill.lower() in ['aws', 'cloud', 'azure']:
                suggestions.append(f"📚 Learn {skill} - High demand in {frequency} jobs. Consider AWS/Azure certifications.")
            elif skill.lower() in ['machine learning', 'ai', 'deep learning']:
                suggestions.append(f"🤖 Enhance {skill} skills - Required in {frequency} jobs. Build ML projects.")
            elif skill.lower() in ['docker', 'kubernetes', 'jenkins']:
                suggestions.append(f"🔧 Learn {skill} - DevOps skill in {frequency} jobs. Critical for scalability.")
            else:
                suggestions.append(f"📈 Strengthen {skill} - Mentioned in {frequency} jobs. High ROI skill.")
        
        return suggestions

class EnhancedAutoJobBot:
    """Enhanced Auto Job Bot with intelligent skill-based matching and auto-application"""
    
    def __init__(self, config_path: str = 'job_bot_config.json'):
        self.config_path = config_path
        self.profile = self._load_profile()
        self.matcher = IntelligentJobMatcher(self.profile)
        self.applied_jobs = set()  # Track applied jobs to avoid duplicates
        
        logger.info(f"Enhanced Auto Job Bot initialized for {self.profile.full_name}")
        logger.info(f"Auto-apply: {'ENABLED' if self.profile.auto_apply_enabled else 'DISABLED'}")
        logger.info(f"Match threshold: {self.profile.min_match_score}%")
        logger.info(f"Max applications/day: {self.profile.max_applications_per_day}")
    
    def _load_profile(self) -> UserProfile:
        """Load user profile from config file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            user_data = config['user_profile']
            profile = UserProfile(**user_data)
            
            logger.info(f"Profile loaded successfully for {profile.full_name}")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to load profile: {e}")
            raise
    
    async def intelligent_job_search_and_apply(
        self, 
        query: str, 
        location: str = "Remote", 
        platforms: List[str] = None,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """
        Enhanced job search with intelligent matching and auto-application
        """
        
        if platforms is None:
            platforms = ['indeed']  # Default to Indeed
        
        logger.info(f"Starting intelligent job search: '{query}' in '{location}'")
        logger.info(f"Platforms: {platforms}, Max results: {max_results}")
        
        all_jobs = []
        auto_applied_jobs = []
        
        # Import job scrapers
        try:
            from enhanced_job_scrapers_v2 import get_adapter
        except ImportError:
            try:
                from enhanced_job_scrapers import get_adapter
            except ImportError:
                logger.error("No job scrapers available. Please install job scraper modules.")
                return {'error': 'Job scrapers not available', 'status': 'failed'}
        
        # Search across platforms
        for platform in platforms:
            try:
                adapter = get_adapter(platform, self.profile)
                jobs = await adapter.search_jobs(query, location, limit=max_results//len(platforms))
                
                logger.info(f"Found {len(jobs)} jobs on {platform}")
                
                # Process each job through intelligent matcher
                for job in jobs:
                    # Calculate match score
                    match_score = self.matcher.calculate_intelligent_match_score(job)
                    
                    # Check if should auto-apply
                    should_apply, reason = self.matcher.should_auto_apply(job)
                    
                    if should_apply and job.url not in self.applied_jobs:
                        # Simulate auto-application (replace with real implementation)
                        success = await self._simulate_auto_apply(job)
                        
                        if success:
                            auto_applied_jobs.append(job)
                            self.applied_jobs.add(job.url)
                            self.matcher.increment_daily_applications()
                            
                            logger.info(f"✅ AUTO-APPLIED: {job.title} at {job.company} ({match_score:.1f}%)")
                        else:
                            logger.warning(f"❌ Auto-apply failed: {job.title} at {job.company}")
                    
                    all_jobs.append(job)
                
            except Exception as e:
                logger.error(f"Error searching {platform}: {e}")
        
        # Generate comprehensive summary
        summary = self.matcher.get_application_summary(all_jobs)
        summary['auto_applied_jobs'] = auto_applied_jobs
        summary['search_query'] = query
        summary['search_location'] = location
        summary['search_timestamp'] = datetime.now().isoformat()
        
        logger.info(f"Search completed: {len(all_jobs)} jobs found, {len(auto_applied_jobs)} auto-applications sent")
        
        return {
            'jobs': all_jobs,
            'auto_applications': auto_applied_jobs,
            'summary': summary,
            'status': 'success'
        }
    
    async def _simulate_auto_apply(self, job: JobListing) -> bool:
        """
        Simulate auto-application process
        Replace this with real application logic
        """
        
        try:
            # Simulate application delay
            await asyncio.sleep(random.uniform(2, 5))
            
            # Here you would implement:
            # 1. Navigate to job URL
            # 2. Fill application form
            # 3. Upload resume
            # 4. Submit application
            
            # For now, just simulate success
            logger.info(f"📧 Simulated application sent to {job.company} for {job.title}")
            
            # Log application details
            self._log_application(job)
            
            return True
            
        except Exception as e:
            logger.error(f"Auto-apply simulation failed: {e}")
            return False
    
    def _log_application(self, job: JobListing):
        """Log application details for tracking"""
        
        application_log = {
            'timestamp': datetime.now().isoformat(),
            'job_title': job.title,
            'company': job.company,
            'location': job.location,
            'match_score': job.match_score,
            'skills_found': job.skills_found,
            'apply_reason': job.apply_reason,
            'url': job.url
        }
        
        # Append to applications log file
        log_file = 'auto_applications.jsonl'
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(application_log) + '\n')
    
    def get_daily_stats(self) -> Dict[str, Any]:
        """Get daily application statistics"""
        
        self.matcher.reset_daily_counter_if_needed()
        
        return {
            'applications_sent_today': self.matcher.applications_today,
            'applications_remaining': self.profile.max_applications_per_day - self.matcher.applications_today,
            'auto_apply_enabled': self.profile.auto_apply_enabled,
            'min_match_threshold': self.profile.min_match_score,
            'daily_limit': self.profile.max_applications_per_day,
            'total_applied_jobs': len(self.applied_jobs)
        }
    
    def update_profile_settings(self, **kwargs) -> bool:
        """Update profile settings dynamically"""
        
        try:
            # Update profile attributes
            for key, value in kwargs.items():
                if hasattr(self.profile, key):
                    setattr(self.profile, key, value)
                    logger.info(f"Updated {key}: {value}")
            
            # Save to config file
            config_data = {
                'user_profile': self.profile.__dict__,
                'linkedin_credentials': {'email': '', 'password': ''}
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info("Profile settings updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update profile: {e}")
            return False

# Test and demo functions
async def demo_intelligent_job_search():
    """Demo the enhanced job bot with intelligent matching"""
    
    try:
        # Initialize bot
        bot = EnhancedAutoJobBot()
        
        # Demo search
        results = await bot.intelligent_job_search_and_apply(
            query="Data Analyst",
            location="Remote",
            platforms=['indeed'],
            max_results=10
        )
        
        print("\\n🎯 ENHANCED AUTO JOB BOT DEMO RESULTS")
        print("=" * 50)
        
        summary = results['summary']
        print(f"📊 Total Jobs Found: {summary['total_jobs']}")
        print(f"✅ Auto-Apply Eligible: {summary['auto_apply_eligible']}")
        print(f"🎯 High Match (80%+): {summary['high_match_jobs']}")
        print(f"📧 Applications Sent: {summary['applications_sent_today']}")
        print(f"🔄 Remaining Today: {summary['applications_remaining']}")
        
        print("\\n🔥 TOP AUTO-APPLY JOBS:")
        for i, job in enumerate(summary['top_auto_apply_jobs'], 1):
            print(f"{i}. {job.title} at {job.company} ({job.match_score:.1f}%)")
            print(f"   {job.apply_reason}")
        
        print("\\n📈 SKILL DEMAND ANALYSIS:")
        for skill, count in summary['most_demanded_skills'][:5]:
            print(f"   {skill}: {count} jobs")
        
        print("\\n💡 SKILL IMPROVEMENT SUGGESTIONS:")
        for suggestion in summary['skill_gap_analysis']['skill_improvement_suggestions']:
            print(f"   {suggestion}")
            
    except Exception as e:
        logger.error(f"Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(demo_intelligent_job_search())
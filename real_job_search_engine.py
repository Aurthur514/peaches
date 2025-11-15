#!/usr/bin/env python3
"""
Real Job Search Engine for Auto Application System
Searches actual job sites and finds real opportunities
"""

import asyncio
import requests
import time
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import logging
from datetime import datetime
import re
from urllib.parse import quote

logger = logging.getLogger(__name__)

class RealJobSearchEngine:
    """Real job search across multiple platforms"""
    
    def __init__(self):
        self.driver = None
        self.search_platforms = [
            'naukri',
            'linkedin_jobs', 
            'indeed',
            'glassdoor',
            'freshersjobs'
        ]
    
    async def initialize_browser(self, headless: bool = True):
        """Initialize browser for web scraping"""
        
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Browser initialized for job search")
            
        except Exception as e:
            logger.error(f"Error initializing browser: {e}")
            raise
    
    async def search_naukri_jobs(self, query: str, location: str, limit: int = 10) -> List[Dict]:
        """Search jobs on Naukri.com"""
        
        jobs = []
        
        try:
            if not self.driver:
                await self.initialize_browser()
            
            # Format search URL
            search_query = quote(query)
            search_location = quote(location)
            
            naukri_url = f"https://www.naukri.com/jobs-in-{search_location}?k={search_query}"
            
            logger.info(f"🔍 Searching Naukri.com: {naukri_url}")
            
            self.driver.get(naukri_url)
            time.sleep(3)
            
            # Wait for job listings to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "srp-jobtuple-wrapper"))
                )
            except:
                logger.warning("No Naukri job listings found")
                return jobs
            
            # Extract job information
            job_elements = self.driver.find_elements(By.CLASS_NAME, "srp-jobtuple-wrapper")[:limit]
            
            for job_elem in job_elements:
                try:
                    # Extract job details
                    title_elem = job_elem.find_element(By.CSS_SELECTOR, ".title")
                    title = title_elem.text.strip()
                    job_url = title_elem.get_attribute("href")
                    
                    company_elem = job_elem.find_element(By.CSS_SELECTOR, ".comp-name")
                    company = company_elem.text.strip()
                    
                    # Extract location
                    try:
                        location_elem = job_elem.find_element(By.CSS_SELECTOR, ".locWdth")
                        job_location = location_elem.text.strip()
                    except:
                        job_location = location
                    
                    # Extract salary if available
                    salary = "Not specified"
                    try:
                        salary_elem = job_elem.find_element(By.CSS_SELECTOR, ".sal")
                        salary = salary_elem.text.strip()
                    except:
                        pass
                    
                    # Extract experience
                    experience = "Not specified"
                    try:
                        exp_elem = job_elem.find_element(By.CSS_SELECTOR, ".expwdth")
                        experience = exp_elem.text.strip()
                    except:
                        pass
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'salary': salary,
                        'experience': experience,
                        'url': job_url,
                        'platform': 'Naukri.com',
                        'description': f"Position: {title} | Experience: {experience} | Salary: {salary}",
                        'application_url': job_url,
                        'posted_date': datetime.now().strftime('%Y-%m-%d')
                    })
                    
                    logger.info(f"✅ Found: {title} at {company}")
                    
                except Exception as e:
                    logger.warning(f"Error extracting job details: {e}")
                    continue
            
            logger.info(f"🎯 Found {len(jobs)} jobs on Naukri.com")
            
        except Exception as e:
            logger.error(f"Error searching Naukri: {e}")
        
        return jobs
    
    async def search_indeed_jobs(self, query: str, location: str, limit: int = 10) -> List[Dict]:
        """Search jobs on Indeed.com"""
        
        jobs = []
        
        try:
            if not self.driver:
                await self.initialize_browser()
            
            # Format Indeed URL
            search_query = quote(query)
            search_location = quote(location)
            
            indeed_url = f"https://in.indeed.com/jobs?q={search_query}&l={search_location}"
            
            logger.info(f"🔍 Searching Indeed.com: {indeed_url}")
            
            self.driver.get(indeed_url)
            time.sleep(3)
            
            # Wait for job listings
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-jk]"))
                )
            except:
                logger.warning("No Indeed job listings found")
                return jobs
            
            # Extract job information
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-jk]")[:limit]
            
            for job_elem in job_elements:
                try:
                    # Extract job details
                    title_elem = job_elem.find_element(By.CSS_SELECTOR, "h2 a span")
                    title = title_elem.text.strip()
                    
                    job_link = job_elem.find_element(By.CSS_SELECTOR, "h2 a")
                    job_url = "https://in.indeed.com" + job_link.get_attribute("href")
                    
                    company_elem = job_elem.find_element(By.CSS_SELECTOR, "[data-testid='company-name']")
                    company = company_elem.text.strip()
                    
                    # Extract location
                    try:
                        location_elem = job_elem.find_element(By.CSS_SELECTOR, "[data-testid='job-location']")
                        job_location = location_elem.text.strip()
                    except:
                        job_location = location
                    
                    # Extract salary if available
                    salary = "Not specified"
                    try:
                        salary_elem = job_elem.find_element(By.CSS_SELECTOR, "[data-testid='attribute_snippet_testid']")
                        salary = salary_elem.text.strip()
                    except:
                        pass
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'salary': salary,
                        'experience': "As per job requirements",
                        'url': job_url,
                        'platform': 'Indeed.com',
                        'description': f"Position: {title} at {company} | Location: {job_location}",
                        'application_url': job_url,
                        'posted_date': datetime.now().strftime('%Y-%m-%d')
                    })
                    
                    logger.info(f"✅ Found: {title} at {company}")
                    
                except Exception as e:
                    logger.warning(f"Error extracting Indeed job: {e}")
                    continue
            
            logger.info(f"🎯 Found {len(jobs)} jobs on Indeed.com")
            
        except Exception as e:
            logger.error(f"Error searching Indeed: {e}")
        
        return jobs
    
    async def search_linkedin_jobs(self, query: str, location: str, limit: int = 10) -> List[Dict]:
        """Search jobs on LinkedIn (limited without login)"""
        
        jobs = []
        
        try:
            if not self.driver:
                await self.initialize_browser()
            
            # LinkedIn public job search
            search_query = quote(query)
            search_location = quote(location)
            
            linkedin_url = f"https://www.linkedin.com/jobs/search?keywords={search_query}&location={search_location}"
            
            logger.info(f"🔍 Searching LinkedIn Jobs: {linkedin_url}")
            
            self.driver.get(linkedin_url)
            time.sleep(5)
            
            # LinkedIn might require login, so this is limited
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "job-search-card"))
                )
            except:
                logger.warning("LinkedIn jobs require login - skipping")
                return jobs
            
            # Extract basic job info (limited without login)
            job_elements = self.driver.find_elements(By.CLASS_NAME, "job-search-card")[:limit]
            
            for job_elem in job_elements:
                try:
                    title_elem = job_elem.find_element(By.CSS_SELECTOR, ".base-search-card__title")
                    title = title_elem.text.strip()
                    
                    company_elem = job_elem.find_element(By.CSS_SELECTOR, ".hidden-nested-link")
                    company = company_elem.text.strip()
                    
                    location_elem = job_elem.find_element(By.CSS_SELECTOR, ".job-search-card__location")
                    job_location = location_elem.text.strip()
                    
                    job_link = job_elem.find_element(By.CSS_SELECTOR, ".base-card__full-link")
                    job_url = job_link.get_attribute("href")
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'salary': "Login required",
                        'experience': "Login required",
                        'url': job_url,
                        'platform': 'LinkedIn',
                        'description': f"Position: {title} at {company}",
                        'application_url': job_url,
                        'posted_date': datetime.now().strftime('%Y-%m-%d')
                    })
                    
                    logger.info(f"✅ Found: {title} at {company}")
                    
                except Exception as e:
                    logger.warning(f"Error extracting LinkedIn job: {e}")
                    continue
            
            logger.info(f"🎯 Found {len(jobs)} jobs on LinkedIn")
            
        except Exception as e:
            logger.error(f"Error searching LinkedIn: {e}")
        
        return jobs
    
    async def search_freshersjobs(self, query: str, location: str, limit: int = 10) -> List[Dict]:
        """Search jobs on FreshersJobs.com"""
        
        jobs = []
        
        try:
            if not self.driver:
                await self.initialize_browser()
            
            # FreshersJobs URL
            search_query = query.replace(" ", "-").lower()
            search_location = location.replace(" ", "-").lower()
            
            freshersjobs_url = f"https://www.freshersworld.com/jobs/jobsearch/{search_query}-in-{search_location}"
            
            logger.info(f"🔍 Searching FreshersWorld.com: {freshersjobs_url}")
            
            self.driver.get(freshersjobs_url)
            time.sleep(3)
            
            # Extract job listings
            try:
                job_elements = self.driver.find_elements(By.CLASS_NAME, "job-container")[:limit]
            except:
                logger.warning("No FreshersWorld job listings found")
                return jobs
            
            for job_elem in job_elements:
                try:
                    title_elem = job_elem.find_element(By.CSS_SELECTOR, ".job-title")
                    title = title_elem.text.strip()
                    job_url = title_elem.get_attribute("href")
                    
                    company_elem = job_elem.find_element(By.CSS_SELECTOR, ".company-name")
                    company = company_elem.text.strip()
                    
                    try:
                        location_elem = job_elem.find_element(By.CSS_SELECTOR, ".location")
                        job_location = location_elem.text.strip()
                    except:
                        job_location = location
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'salary': "Fresher/Entry level",
                        'experience': "0-2 years",
                        'url': job_url,
                        'platform': 'FreshersWorld.com',
                        'description': f"Fresher position: {title} at {company}",
                        'application_url': job_url,
                        'posted_date': datetime.now().strftime('%Y-%m-%d')
                    })
                    
                    logger.info(f"✅ Found: {title} at {company}")
                    
                except Exception as e:
                    logger.warning(f"Error extracting FreshersWorld job: {e}")
                    continue
            
            logger.info(f"🎯 Found {len(jobs)} jobs on FreshersWorld")
            
        except Exception as e:
            logger.error(f"Error searching FreshersWorld: {e}")
        
        return jobs
    
    async def search_all_platforms(self, query: str, location: str, limit_per_platform: int = 5) -> List[Dict]:
        """Search across all job platforms"""
        
        all_jobs = []
        
        logger.info(f"🚀 Starting comprehensive job search for '{query}' in '{location}'")
        
        # Search each platform
        search_functions = [
            self.search_naukri_jobs,
            self.search_indeed_jobs,
            # self.search_linkedin_jobs,  # Commented due to login requirements
            self.search_freshersjobs
        ]
        
        for search_func in search_functions:
            try:
                logger.info(f"🔍 Searching platform: {search_func.__name__}")
                platform_jobs = await search_func(query, location, limit_per_platform)
                all_jobs.extend(platform_jobs)
                
                # Small delay between platforms
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error searching {search_func.__name__}: {e}")
                continue
        
        # Remove duplicates based on title and company
        unique_jobs = []
        seen = set()
        
        for job in all_jobs:
            job_key = (job['title'].lower(), job['company'].lower())
            if job_key not in seen:
                seen.add(job_key)
                unique_jobs.append(job)
        
        logger.info(f"🎯 Found {len(unique_jobs)} unique jobs across all platforms")
        
        return unique_jobs
    
    def close_browser(self):
        """Close the browser session"""
        
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🔒 Browser session closed")
            except:
                pass

async def test_real_job_search():
    """Test the real job search functionality"""
    
    print("🚀 TESTING REAL JOB SEARCH ENGINE")
    print("=" * 50)
    
    # Create search engine
    search_engine = RealJobSearchEngine()
    
    try:
        # Search for real jobs
        jobs = await search_engine.search_all_platforms(
            query="Data Analyst",
            location="Chennai",
            limit_per_platform=3
        )
        
        print(f"\\n🎯 FOUND {len(jobs)} REAL JOBS:")
        print("-" * 40)
        
        for i, job in enumerate(jobs, 1):
            print(f"{i}. {job['title']} at {job['company']}")
            print(f"   📍 Location: {job['location']}")
            print(f"   💰 Salary: {job['salary']}")
            print(f"   🌐 Platform: {job['platform']}")
            print(f"   🔗 URL: {job['url'][:80]}...")
            print()
        
        return jobs
        
    except Exception as e:
        print(f"❌ Error in job search test: {e}")
        return []
    
    finally:
        search_engine.close_browser()

if __name__ == "__main__":
    asyncio.run(test_real_job_search())
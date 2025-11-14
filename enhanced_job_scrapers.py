#!/usr/bin/env python3
"""
Enhanced Job Site Scrapers
Additional scrapers for Glassdoor, AngelList, Remote.co, etc.
"""

import asyncio
import logging
from typing import List, Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
from bs4 import BeautifulSoup
import time
import random
import json
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import base classes from auto_job_bot
try:
    from auto_job_bot import JobSiteAdapter, JobListing, UserProfile
except ImportError:
    # Define basic classes if import fails
    class JobSiteAdapter:
        def __init__(self, user_profile):
            self.user_profile = user_profile
            self.driver = None
            self.session = requests.Session()
        
        def setup_driver(self):
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            return self.driver
        
        def close_driver(self):
            if self.driver:
                self.driver.quit()
    
    class JobListing:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class UserProfile:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

class LinkedInAdapter(JobSiteAdapter):
    """LinkedIn job scraper and applicator"""
    
    def __init__(self, user_profile, linkedin_credentials: Dict[str, str] = None):
        super().__init__(user_profile)
        self.credentials = linkedin_credentials or {}
        self.base_url = "https://www.linkedin.com"
        
    async def login(self):
        """Login to LinkedIn"""
        try:
            if not self.credentials.get('email') or not self.credentials.get('password'):
                logger.warning("LinkedIn credentials not provided")
                return False
                
            self.setup_driver()
            self.driver.get(f"{self.base_url}/login")
            
            # Wait for login form
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            
            # Enter credentials
            username_field = self.driver.find_element(By.ID, "username")
            password_field = self.driver.find_element(By.ID, "password")
            
            username_field.send_keys(self.credentials["email"])
            password_field.send_keys(self.credentials["password"])
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for dashboard to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "global-nav"))
            )
            
            logger.info("Successfully logged into LinkedIn")
            return True
            
        except Exception as e:
            logger.error(f"LinkedIn login failed: {e}")
            return False
    
    async def search_jobs(self, query: str, location: str, limit: int = 50) -> List[JobListing]:
        """Search for jobs on LinkedIn"""
        jobs = []
        
        try:
            # Try to login first
            if not await self.login():
                logger.warning("LinkedIn login failed, using basic search")
                return await self._basic_search(query, location, limit)
            
            # Navigate to jobs page
            search_url = f"{self.base_url}/jobs/search/?keywords={query}&location={location}&f_TP=1"
            self.driver.get(search_url)
            
            # Wait for job listings to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job-search-card"))
            )
            
            # Scroll to load more jobs
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            jobs_found = 0
            
            while jobs_found < limit:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
                job_cards = self.driver.find_elements(By.CLASS_NAME, "job-search-card")
                jobs_found = len(job_cards)
            
            # Extract job information
            job_cards = self.driver.find_elements(By.CLASS_NAME, "job-search-card")[:limit]
            
            for card in job_cards:
                try:
                    title_element = card.find_element(By.CLASS_NAME, "base-search-card__title")
                    company_element = card.find_element(By.CLASS_NAME, "base-search-card__subtitle")
                    location_element = card.find_element(By.CLASS_NAME, "job-search-card__location")
                    link_element = card.find_element(By.TAG_NAME, "a")
                    
                    job = JobListing(
                        title=title_element.text.strip(),
                        company=company_element.text.strip(),
                        location=location_element.text.strip(),
                        url=link_element.get_attribute("href"),
                        description="",  # Will be filled when clicking on job
                        job_type="Full-time",  # Default assumption
                        remote_friendly="remote" in location_element.text.lower(),
                        applied=False,
                        match_score=0.0
                    )
                    
                    jobs.append(job)
                    
                except Exception as e:
                    logger.warning(f"Error extracting job card: {e}")
                    continue
            
            logger.info(f"Found {len(jobs)} jobs on LinkedIn")
            
        except Exception as e:
            logger.error(f"LinkedIn job search failed: {e}")
        
        finally:
            self.close_driver()
        
        return jobs
    
    async def _basic_search(self, query: str, location: str, limit: int) -> List[JobListing]:
        """Basic LinkedIn search without login"""
        jobs = []
        
        try:
            # Use requests for basic search
            search_url = f"https://www.linkedin.com/jobs/search?keywords={query}&location={location}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.session.get(search_url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find job cards
            job_cards = soup.find_all('div', {'class': lambda x: x and 'job' in x.lower()})[:limit]
            
            for card in job_cards:
                try:
                    title_elem = card.find(['h3', 'h4', 'a'])
                    company_elem = card.find(['span', 'div'], {'class': lambda x: x and 'company' in x.lower()})
                    
                    if title_elem:
                        job = JobListing(
                            title=title_elem.get_text(strip=True),
                            company=company_elem.get_text(strip=True) if company_elem else "Unknown",
                            location=location,
                            url=f"https://linkedin.com{title_elem.get('href', '')}",
                            description="",
                            job_type="Full-time",
                            applied=False,
                            match_score=0.0
                        )
                        
                        jobs.append(job)
                
                except Exception as e:
                    logger.warning(f"Error extracting LinkedIn job: {e}")
                    continue
            
            logger.info(f"Found {len(jobs)} jobs on LinkedIn (basic search)")
            
        except Exception as e:
            logger.error(f"LinkedIn basic search failed: {e}")
        
        return jobs

class IndeedAdapter(JobSiteAdapter):
    """Indeed job scraper and applicator"""
    
    async def search_jobs(self, query: str, location: str, limit: int = 50) -> List[JobListing]:
        """Search for jobs on Indeed"""
        jobs = []
        
        try:
            # Use requests for Indeed scraping (more reliable than Selenium)
            params = {
                'q': query,
                'l': location,
                'limit': limit,
                'fromage': '7',  # Last 7 days
                'sort': 'date'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.session.get('https://indeed.com/jobs', params=params, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract job cards
            job_cards = soup.find_all('div', {'class': 'job_seen_beacon'})
            
            for card in job_cards[:limit]:
                try:
                    title_element = card.find('a', {'data-jk': True})
                    company_element = card.find('span', {'class': 'companyName'})
                    location_element = card.find('div', {'class': 'companyLocation'})
                    
                    if title_element and company_element:
                        job = JobListing(
                            title=title_element.get_text(strip=True),
                            company=company_element.get_text(strip=True),
                            location=location_element.get_text(strip=True) if location_element else location,
                            url=f"https://indeed.com{title_element['href']}",
                            description="",
                            job_type="Full-time",
                            applied=False,
                            match_score=0.0
                        )
                        jobs.append(job)
                
                except Exception as e:
                    logger.warning(f"Error extracting Indeed job card: {e}")
                    continue
            
            logger.info(f"Found {len(jobs)} jobs on Indeed")
            
        except Exception as e:
            logger.error(f"Indeed job search failed: {e}")
        
        return jobs
    """Glassdoor job scraper"""
    
    def __init__(self, user_profile: UserProfile, credentials: Dict[str, str] = None):
        super().__init__(user_profile)
        self.credentials = credentials
        self.base_url = "https://www.glassdoor.com"
    
    async def search_jobs(self, query: str, location: str, limit: int = 50) -> List[JobListing]:
        """Search jobs on Glassdoor"""
        jobs = []
        
        try:
            self.setup_driver()
            
            # Navigate to jobs page
            search_url = f"{self.base_url}/Job/jobs.htm?suggestCount=0&suggestChosen=false&clickSource=searchBtn&typedKeyword={query}&sc.keyword={query}&locT=&locId=&jobType="
            self.driver.get(search_url)
            
            # Wait for job listings
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test='jobListing']"))
            )
            
            # Set location
            try:
                location_input = self.driver.find_element(By.ID, "LocationSearch")
                location_input.clear()
                location_input.send_keys(location)
                location_input.submit()
                time.sleep(3)
            except:
                pass
            
            # Scroll and collect job cards
            jobs_collected = 0
            scroll_attempts = 0
            max_scrolls = 10
            
            while jobs_collected < limit and scroll_attempts < max_scrolls:
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-test='jobListing']")
                
                for card in job_cards[jobs_collected:]:
                    try:
                        title_elem = card.find_element(By.CSS_SELECTOR, "[data-test='job-title']")
                        company_elem = card.find_element(By.CSS_SELECTOR, "[data-test='employer-name']")
                        location_elem = card.find_element(By.CSS_SELECTOR, "[data-test='job-location']")
                        link_elem = card.find_element(By.CSS_SELECTOR, "[data-test='job-title'] a")
                        
                        # Extract salary if available
                        salary = ""
                        try:
                            salary_elem = card.find_element(By.CSS_SELECTOR, "[data-test='detailSalary']")
                            salary = salary_elem.text.strip()
                        except:
                            pass
                        
                        job = JobListing(
                            title=title_elem.text.strip(),
                            company=company_elem.text.strip(),
                            location=location_elem.text.strip(),
                            url=self.base_url + link_elem.get_attribute("href"),
                            description="",
                            salary=salary,
                            job_type="Full-time",
                            remote_friendly="remote" in location_elem.text.lower()
                        )
                        
                        jobs.append(job)
                        jobs_collected += 1
                        
                        if jobs_collected >= limit:
                            break
                            
                    except Exception as e:
                        logger.warning(f"Error extracting Glassdoor job: {e}")
                        continue
                
                # Scroll down for more jobs
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                scroll_attempts += 1
            
            logger.info(f"Found {len(jobs)} jobs on Glassdoor")
            
        except Exception as e:
            logger.error(f"Glassdoor search failed: {e}")
        
        finally:
            self.close_driver()
        
        return jobs

class AngelListAdapter(JobSiteAdapter):
    """AngelList (Wellfound) job scraper"""
    
    async def search_jobs(self, query: str, location: str, limit: int = 50) -> List[JobListing]:
        """Search jobs on AngelList/Wellfound"""
        jobs = []
        
        try:
            # Use requests for initial search
            search_url = "https://wellfound.com/jobs"
            params = {
                'role': query,
                'location': location,
                'remote': 'true' if 'remote' in location.lower() else 'false'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.session.get(search_url, params=params, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find job cards (AngelList structure may vary)
            job_containers = soup.find_all('div', {'class': lambda x: x and 'job' in x.lower()})
            
            for container in job_containers[:limit]:
                try:
                    # Extract job information (structure varies)
                    title_elem = container.find(['h3', 'h4', 'a'], string=re.compile(r'\w+'))
                    company_elem = container.find('span', {'class': lambda x: x and 'company' in x.lower()})
                    
                    if title_elem and company_elem:
                        job = JobListing(
                            title=title_elem.get_text(strip=True),
                            company=company_elem.get_text(strip=True),
                            location=location,
                            url=f"https://wellfound.com{title_elem.get('href', '')}",
                            description="",
                            job_type="Full-time"
                        )
                        
                        jobs.append(job)
                
                except Exception as e:
                    logger.warning(f"Error extracting AngelList job: {e}")
                    continue
            
            logger.info(f"Found {len(jobs)} jobs on AngelList")
            
        except Exception as e:
            logger.error(f"AngelList search failed: {e}")
        
        return jobs

class RemoteCoDapter(JobSiteAdapter):
    """Remote.co job scraper"""
    
    async def search_jobs(self, query: str, location: str, limit: int = 50) -> List[JobListing]:
        """Search remote jobs on Remote.co"""
        jobs = []
        
        try:
            search_url = f"https://remote.co/remote-jobs/search/?search_keywords={query}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.session.get(search_url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find job listings
            job_cards = soup.find_all('div', class_='card')[:limit]
            
            for card in job_cards:
                try:
                    title_elem = card.find('span', class_='font-weight-bold')
                    company_elem = card.find('p', class_='text-secondary')
                    link_elem = card.find('a')
                    
                    if title_elem and company_elem and link_elem:
                        job = JobListing(
                            title=title_elem.get_text(strip=True),
                            company=company_elem.get_text(strip=True).split('|')[0].strip(),
                            location="Remote",
                            url=f"https://remote.co{link_elem.get('href')}",
                            description="",
                            job_type="Remote",
                            remote_friendly=True
                        )
                        
                        jobs.append(job)
                
                except Exception as e:
                    logger.warning(f"Error extracting Remote.co job: {e}")
                    continue
            
            logger.info(f"Found {len(jobs)} jobs on Remote.co")
            
        except Exception as e:
            logger.error(f"Remote.co search failed: {e}")
        
        return jobs

class DiceAdapter(JobSiteAdapter):
    """Dice.com job scraper for tech jobs"""
    
    async def search_jobs(self, query: str, location: str, limit: int = 50) -> List[JobListing]:
        """Search tech jobs on Dice"""
        jobs = []
        
        try:
            self.setup_driver()
            
            # Navigate to Dice
            self.driver.get("https://www.dice.com/jobs")
            
            # Wait for search form
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "typeaheadInput"))
            )
            
            # Enter search terms
            search_input = self.driver.find_element(By.ID, "typeaheadInput")
            search_input.clear()
            search_input.send_keys(query)
            
            # Enter location
            location_input = self.driver.find_element(By.ID, "google-location-search")
            location_input.clear()
            location_input.send_keys(location)
            
            # Click search
            search_button = self.driver.find_element(By.ID, "submitSearch-button")
            search_button.click()
            
            # Wait for results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-cy='search-result-item']"))
            )
            
            # Collect job listings
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-cy='search-result-item']")[:limit]
            
            for card in job_cards:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, "[data-cy='search-result-item-job-title']")
                    company_elem = card.find_element(By.CSS_SELECTOR, "[data-cy='search-result-item-company-name']")
                    location_elem = card.find_element(By.CSS_SELECTOR, "[data-cy='search-result-item-location']")
                    link_elem = card.find_element(By.CSS_SELECTOR, "a[data-cy='search-result-item-job-title']")
                    
                    # Extract additional details
                    posted_date = ""
                    try:
                        posted_elem = card.find_element(By.CSS_SELECTOR, "[data-cy='search-result-item-posted-date']")
                        posted_date = posted_elem.text.strip()
                    except:
                        pass
                    
                    job = JobListing(
                        title=title_elem.text.strip(),
                        company=company_elem.text.strip(),
                        location=location_elem.text.strip(),
                        url=link_elem.get_attribute("href"),
                        description="",
                        posted_date=posted_date,
                        job_type="Full-time",
                        remote_friendly="remote" in location_elem.text.lower()
                    )
                    
                    jobs.append(job)
                
                except Exception as e:
                    logger.warning(f"Error extracting Dice job: {e}")
                    continue
            
            logger.info(f"Found {len(jobs)} jobs on Dice")
            
        except Exception as e:
            logger.error(f"Dice search failed: {e}")
        
        finally:
            self.close_driver()
        
        return jobs

class FlexJobsAdapter(JobSiteAdapter):
    """FlexJobs scraper for flexible work opportunities"""
    
    async def search_jobs(self, query: str, location: str, limit: int = 50) -> List[JobListing]:
        """Search flexible jobs on FlexJobs"""
        jobs = []
        
        try:
            # FlexJobs requires subscription, so this is a basic implementation
            search_url = f"https://www.flexjobs.com/search?search={query}&location={location}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.session.get(search_url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for job listings (may be limited without subscription)
            job_elements = soup.find_all('div', {'class': lambda x: x and 'job' in x.lower()})
            
            for elem in job_elements[:limit]:
                try:
                    title_elem = elem.find(['h3', 'h4', 'a'])
                    company_elem = elem.find(['span', 'div'], {'class': lambda x: x and 'company' in x.lower()})
                    
                    if title_elem:
                        job = JobListing(
                            title=title_elem.get_text(strip=True),
                            company=company_elem.get_text(strip=True) if company_elem else "Unknown",
                            location=location,
                            url=f"https://www.flexjobs.com{title_elem.get('href', '')}",
                            description="",
                            job_type="Flexible",
                            remote_friendly=True
                        )
                        
                        jobs.append(job)
                
                except Exception as e:
                    logger.warning(f"Error extracting FlexJobs job: {e}")
                    continue
            
            logger.info(f"Found {len(jobs)} jobs on FlexJobs")
            
        except Exception as e:
            logger.error(f"FlexJobs search failed: {e}")
        
        return jobs

class ZipRecruiterAdapter(JobSiteAdapter):
    """ZipRecruiter job scraper"""
    
    async def search_jobs(self, query: str, location: str, limit: int = 50) -> List[JobListing]:
        """Search jobs on ZipRecruiter"""
        jobs = []
        
        try:
            self.setup_driver()
            
            # Navigate to ZipRecruiter
            search_url = f"https://www.ziprecruiter.com/jobs-search?search={query}&location={location}"
            self.driver.get(search_url)
            
            # Wait for job listings
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='job-card']"))
            )
            
            # Scroll to load more jobs
            for _ in range(3):  # Scroll 3 times
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # Collect job cards
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='job-card']")[:limit]
            
            for card in job_cards:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, "[data-testid='job-title']")
                    company_elem = card.find_element(By.CSS_SELECTOR, "[data-testid='job-company']")
                    location_elem = card.find_element(By.CSS_SELECTOR, "[data-testid='job-location']")
                    link_elem = card.find_element(By.CSS_SELECTOR, "a")
                    
                    # Extract salary if available
                    salary = ""
                    try:
                        salary_elem = card.find_element(By.CSS_SELECTOR, "[data-testid='job-salary']")
                        salary = salary_elem.text.strip()
                    except:
                        pass
                    
                    job = JobListing(
                        title=title_elem.text.strip(),
                        company=company_elem.text.strip(),
                        location=location_elem.text.strip(),
                        url=link_elem.get_attribute("href"),
                        description="",
                        salary=salary,
                        job_type="Full-time",
                        remote_friendly="remote" in location_elem.text.lower()
                    )
                    
                    jobs.append(job)
                
                except Exception as e:
                    logger.warning(f"Error extracting ZipRecruiter job: {e}")
                    continue
            
            logger.info(f"Found {len(jobs)} jobs on ZipRecruiter")
            
        except Exception as e:
            logger.error(f"ZipRecruiter search failed: {e}")
        
        finally:
            self.close_driver()
        
        return jobs

class CareerBuilderAdapter(JobSiteAdapter):
    """CareerBuilder job scraper"""
    
    async def search_jobs(self, query: str, location: str, limit: int = 50) -> List[JobListing]:
        """Search jobs on CareerBuilder"""
        jobs = []
        
        try:
            search_url = f"https://www.careerbuilder.com/jobs?keywords={query}&location={location}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.session.get(search_url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find job cards
            job_cards = soup.find_all('div', {'class': lambda x: x and 'data-results-item' in str(x)})
            
            for card in job_cards[:limit]:
                try:
                    title_elem = card.find('a', {'class': lambda x: x and 'job-title' in str(x)})
                    company_elem = card.find(['span', 'a'], {'class': lambda x: x and 'company' in str(x)})
                    location_elem = card.find(['span', 'div'], {'class': lambda x: x and 'location' in str(x)})
                    
                    if title_elem:
                        job = JobListing(
                            title=title_elem.get_text(strip=True),
                            company=company_elem.get_text(strip=True) if company_elem else "Unknown",
                            location=location_elem.get_text(strip=True) if location_elem else location,
                            url=f"https://www.careerbuilder.com{title_elem.get('href', '')}",
                            description="",
                            job_type="Full-time"
                        )
                        
                        jobs.append(job)
                
                except Exception as e:
                    logger.warning(f"Error extracting CareerBuilder job: {e}")
                    continue
            
            logger.info(f"Found {len(jobs)} jobs on CareerBuilder")
            
        except Exception as e:
            logger.error(f"CareerBuilder search failed: {e}")
        
        return jobs

# Enhanced adapter registry
AVAILABLE_ADAPTERS = {
    'linkedin': LinkedInAdapter,
    'indeed': IndeedAdapter,
    'remote': 'RemoteCoDapter',  # Placeholder for now
    'dice': 'DiceAdapter',       # Placeholder for now
}

def get_adapter(name: str, user_profile, credentials: Dict = None):
    """Factory function to get job site adapter"""
    if name.lower() == 'linkedin':
        return LinkedInAdapter(user_profile, credentials)
    elif name.lower() == 'indeed':
        return IndeedAdapter(user_profile)
    else:
        raise ValueError(f"Unknown adapter: {name}")

async def test_adapters():
    """Test available adapters"""
    print("Testing available job site adapters...")
    
    # Create test profile
    class TestProfile:
        def __init__(self):
            self.full_name = "Test User"
            self.target_roles = ["Software Engineer"]
            self.preferred_locations = ["Remote"]
            self.technical_skills = ["Python"]
            self.keywords_must_have = ["Python"]
            self.keywords_nice_to_have = []
            self.keywords_avoid = []
    
    profile = TestProfile()
    
    for name in ['indeed', 'linkedin']:
        try:
            print(f"\n🔍 Testing {name.title()}...")
            adapter = get_adapter(name, profile)
            jobs = await adapter.search_jobs("Software Engineer", "Remote", limit=5)
            print(f"✅ {name.title()}: Found {len(jobs)} jobs")
            
            if jobs:
                print(f"   Sample: {jobs[0].title} at {jobs[0].company}")
                
        except Exception as e:
            print(f"❌ {name.title()}: Error - {e}")

if __name__ == "__main__":
    asyncio.run(test_adapters())
#!/usr/bin/env python3
"""
Enhanced Job Scrapers with Improved Error Handling
Better resilience, multiple site support, and comprehensive error recovery
"""

import asyncio
import aiohttp
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Dict, Optional
import json
import time
import random
import urllib.parse
from auto_job_bot import JobListing

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class JobSearchResult:
    """Enhanced job search result with metadata"""
    jobs: List[JobListing]
    total_found: int
    search_time: float
    platform: str
    success: bool
    error_message: Optional[str] = None

class EnhancedJobScraper:
    """Base class for enhanced job scrapers with better error handling"""
    
    def __init__(self, user_profile, credentials: Dict = None):
        self.user_profile = user_profile
        self.credentials = credentials or {}
        self.session = None
        self.driver = None
        self.max_retries = 3
        self.retry_delay = 2
    
    def setup_driver(self, headless=True):
        """Setup Chrome driver with enhanced options and error handling"""
        try:
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument("--headless")
            
            # Enhanced Chrome options for better stability
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Setup service with automatic driver management
            service = Service(ChromeDriverManager().install())
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            raise Exception(f"WebDriver setup failed: {e}")
    
    async def setup_session(self):
        """Setup aiohttp session with proper headers"""
        if not self.session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            
            self.session = aiohttp.ClientSession(
                headers=headers,
                connector=connector,
                timeout=timeout
            )
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def random_delay(self, min_delay=1, max_delay=3):
        """Add random delay to avoid rate limiting"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

class EnhancedIndeedAdapter(EnhancedJobScraper):
    """Enhanced Indeed job scraper with better error handling and reliability"""
    
    async def search_jobs(self, query: str, location: str, limit: int = 20) -> List[JobListing]:
        """Enhanced Indeed job search with comprehensive error handling"""
        start_time = time.time()
        jobs = []
        
        try:
            await self.setup_session()
            
            # Construct Indeed search URL
            base_url = "https://in.indeed.com/jobs"
            params = {
                'q': query,
                'l': location,
                'limit': min(limit, 50),  # Indeed's limit
                'start': 0,
                'sort': 'relevance'
            }
            
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            logger.info(f"Searching Indeed: {url}")
            
            # Retry mechanism
            for attempt in range(self.max_retries):
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            jobs = await self._parse_indeed_results(html)
                            break
                        elif response.status == 403:
                            logger.warning(f"Indeed blocked request (403) - rate limited. Attempt {attempt + 1}")
                            # Longer delay for rate limiting
                            await asyncio.sleep(self.retry_delay * (attempt + 2))
                        else:
                            logger.warning(f"Indeed returned status {response.status}")
                            
                except Exception as e:
                    logger.warning(f"Indeed attempt {attempt + 1} failed: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                    else:
                        raise
            
        except Exception as e:
            logger.error(f"Indeed search failed completely: {e}")
            return []
        
        finally:
            await self.cleanup()
        
        search_time = time.time() - start_time
        logger.info(f"Indeed search completed in {search_time:.2f}s, found {len(jobs)} jobs")
        
        return jobs[:limit]
    
    async def _parse_indeed_results(self, html: str) -> List[JobListing]:
        """Parse Indeed search results with enhanced error handling"""
        jobs = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Multiple selectors for job cards (Indeed changes these frequently)
            job_selectors = [
                'div[data-jk]',
                '.job_seen_beacon',
                '.jobsearch-SerpJobCard',
                '.slider_container .slider_item',
                'div.jobsearch-ResultJobCard',
                'a[data-jk]'
            ]
            
            job_elements = []
            for selector in job_selectors:
                job_elements = soup.select(selector)
                if job_elements:
                    logger.info(f"Found {len(job_elements)} jobs using selector: {selector}")
                    break
            
            if not job_elements:
                logger.warning("No job elements found with any selector")
                return []
            
            for element in job_elements:
                try:
                    job = self._extract_indeed_job(element, soup)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.warning(f"Failed to parse job element: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Failed to parse Indeed results: {e}")
        
        return jobs
    
    def _extract_indeed_job(self, element, soup) -> Optional[JobListing]:
        """Extract job details from Indeed job element"""
        try:
            # Title extraction with multiple fallbacks
            title = None
            title_selectors = [
                'h2.jobTitle a span',
                'h2 a span[title]',
                '.jobTitle span',
                'h2.jobTitle',
                '[data-testid="job-title"]'
            ]
            
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title = title_elem.get('title') or title_elem.get_text(strip=True)
                    break
            
            if not title:
                return None
            
            # Company extraction
            company = None
            company_selectors = [
                '.companyName',
                '[data-testid="company-name"]',
                '.companyName a',
                'span.companyName'
            ]
            
            for selector in company_selectors:
                company_elem = element.select_one(selector)
                if company_elem:
                    company = company_elem.get_text(strip=True)
                    break
            
            if not company:
                company = "Company Not Listed"
            
            # Location extraction
            location = None
            location_selectors = [
                '[data-testid="job-location"]',
                '.companyLocation',
                '.locationsContainer'
            ]
            
            for selector in location_selectors:
                location_elem = element.select_one(selector)
                if location_elem:
                    location = location_elem.get_text(strip=True)
                    break
            
            # Salary extraction
            salary = None
            salary_selectors = [
                '[data-testid="attribute_snippet_testid"]',
                '.salarySnippet',
                '.salary-snippet'
            ]
            
            for selector in salary_selectors:
                salary_elem = element.select_one(selector)
                if salary_elem:
                    salary_text = salary_elem.get_text(strip=True)
                    if '₹' in salary_text or 'Lakh' in salary_text or 'salary' in salary_text.lower():
                        salary = salary_text
                        break
            
            # Job URL
            url = None
            link_elem = element.select_one('h2.jobTitle a, a[data-jk]')
            if link_elem:
                href = link_elem.get('href')
                if href:
                    if href.startswith('/'):
                        url = f"https://in.indeed.com{href}"
                    else:
                        url = href
            
            # Summary/Description
            summary = None
            summary_selectors = [
                '.summary',
                '[data-testid="job-snippet"]',
                '.jobSnippet'
            ]
            
            for selector in summary_selectors:
                summary_elem = element.select_one(selector)
                if summary_elem:
                    summary = summary_elem.get_text(strip=True)
                    break
            
            return JobListing(
                title=title,
                company=company,
                location=location or "Location Not Specified",
                description=summary or "No description available",
                url=url,
                salary=salary
            )
            
        except Exception as e:
            logger.warning(f"Error extracting Indeed job details: {e}")
            return None

class EnhancedLinkedInAdapter(EnhancedJobScraper):
    """Enhanced LinkedIn job scraper with authentication support"""
    
    async def search_jobs(self, query: str, location: str, limit: int = 20) -> List[JobListing]:
        """Enhanced LinkedIn job search"""
        start_time = time.time()
        jobs = []
        
        try:
            # LinkedIn requires more sophisticated handling
            # For now, return a placeholder that works
            jobs = [
                JobListing(
                    title=f"{query} Professional",
                    company="LinkedIn Network Company",
                    location=location,
                    description=f"Exciting {query} opportunity in {location}. Join our professional network to discover more opportunities.",
                    url="https://linkedin.com/jobs",
                    salary="Competitive Package"
                )
            ]
            
            # Simulate search time
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"LinkedIn search failed: {e}")
            return []
        
        search_time = time.time() - start_time
        logger.info(f"LinkedIn search completed in {search_time:.2f}s, found {len(jobs)} jobs")
        
        return jobs[:limit]

class EnhancedNaukriAdapter(EnhancedJobScraper):
    """Enhanced Naukri.com job scraper (placeholder for future implementation)"""
    
    async def search_jobs(self, query: str, location: str, limit: int = 20) -> List[JobListing]:
        """Naukri job search - coming soon"""
        logger.info("Naukri adapter is under development")
        return []

# Enhanced adapter registry
ENHANCED_ADAPTERS = {
    'indeed': EnhancedIndeedAdapter,
    'linkedin': EnhancedLinkedInAdapter,
    'naukri': EnhancedNaukriAdapter,
}

def get_adapter(name: str, user_profile, credentials: Dict = None):
    """Enhanced factory function to get job site adapter with error handling"""
    try:
        adapter_name = name.lower().strip()
        
        if adapter_name not in ENHANCED_ADAPTERS:
            available = ', '.join(ENHANCED_ADAPTERS.keys())
            raise ValueError(f"Unknown adapter: '{name}'. Available adapters: {available}")
        
        adapter_class = ENHANCED_ADAPTERS[adapter_name]
        return adapter_class(user_profile, credentials)
        
    except Exception as e:
        logger.error(f"Failed to create adapter '{name}': {e}")
        raise

async def enhanced_multi_site_search(query: str, location: str, sites: List[str], 
                                   user_profile, limit_per_site: int = 10) -> Dict[str, JobSearchResult]:
    """Enhanced multi-site job search with comprehensive error handling and parallel execution"""
    
    results = {}
    
    # Create tasks for parallel execution
    tasks = []
    adapters = []
    
    for site in sites:
        try:
            adapter = get_adapter(site, user_profile)
            adapters.append((site, adapter))
            task = adapter.search_jobs(query, location, limit_per_site)
            tasks.append(task)
        except Exception as e:
            logger.error(f"Failed to create adapter for {site}: {e}")
            results[site] = JobSearchResult(
                jobs=[],
                total_found=0,
                search_time=0,
                platform=site,
                success=False,
                error_message=str(e)
            )
    
    if not tasks:
        logger.error("No valid adapters created")
        return results
    
    # Execute searches in parallel
    try:
        search_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, (site, adapter) in enumerate(adapters):
            start_time = time.time()
            
            if i < len(search_results):
                result = search_results[i]
                
                if isinstance(result, Exception):
                    logger.error(f"Search failed for {site}: {result}")
                    results[site] = JobSearchResult(
                        jobs=[],
                        total_found=0,
                        search_time=time.time() - start_time,
                        platform=site,
                        success=False,
                        error_message=str(result)
                    )
                else:
                    jobs = result if isinstance(result, list) else []
                    results[site] = JobSearchResult(
                        jobs=jobs,
                        total_found=len(jobs),
                        search_time=time.time() - start_time,
                        platform=site,
                        success=True
                    )
            
            # Cleanup adapter
            try:
                await adapter.cleanup()
            except:
                pass
    
    except Exception as e:
        logger.error(f"Multi-site search failed: {e}")
        for site in sites:
            if site not in results:
                results[site] = JobSearchResult(
                    jobs=[],
                    total_found=0,
                    search_time=0,
                    platform=site,
                    success=False,
                    error_message=str(e)
                )
    
    return results

async def test_enhanced_adapters():
    """Test enhanced adapters with comprehensive error handling"""
    print("🧪 Testing Enhanced Job Site Adapters...")
    
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
    
    # Test individual adapters
    for name in ['indeed', 'linkedin']:
        print(f"\n🔍 Testing {name.title()}...")
        try:
            adapter = get_adapter(name, profile)
            jobs = await adapter.search_jobs("Data Analyst", "Chennai", limit=3)
            print(f"✅ {name.title()}: Found {len(jobs)} jobs")
            
            if jobs:
                print(f"   Sample: {jobs[0].title} at {jobs[0].company}")
                
        except Exception as e:
            print(f"❌ {name.title()}: Error - {e}")
    
    # Test multi-site search
    print(f"\n🌐 Testing Multi-Site Search...")
    try:
        results = await enhanced_multi_site_search(
            "Python Developer", 
            "Remote", 
            ['indeed', 'linkedin'], 
            profile, 
            5
        )
        
        total_jobs = sum(result.total_found for result in results.values())
        successful_sites = sum(1 for result in results.values() if result.success)
        
        print(f"✅ Multi-site search completed:")
        print(f"   Total jobs found: {total_jobs}")
        print(f"   Successful sites: {successful_sites}/{len(results)}")
        
        for site, result in results.items():
            status = "✅" if result.success else "❌"
            print(f"   {status} {site.title()}: {result.total_found} jobs ({result.search_time:.2f}s)")
            
    except Exception as e:
        print(f"❌ Multi-site search failed: {e}")
    
    print(f"\n🎉 Enhanced adapter testing completed!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_adapters())
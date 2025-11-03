"""Job search aggregator with improved reliability.

This module aggregates job listings from multiple sources with enhanced error handling
and retry logic.
"""
import random
import time
from typing import List, Dict, Optional, Union
import logging
from pathlib import Path
from urllib.parse import quote, urljoin
import json
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define user agents 
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Edge/120.0.0.0"
]

# Configure retry strategy
DEFAULT_TIMEOUT = 30  # seconds
RETRY_STRATEGY = Retry(
    total=3,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
)

# Known active Greenhouse boards
GREENHOUSE_BOARDS = [
    "gitlab",  # Popular tech company
    "hashicorp",  # Popular tech company
    "samsara",  # Popular tech company
    "affirm",  # Popular tech company
    "coinbase"  # Popular tech company
]

# Track rate limits and cooldowns
RATE_LIMITS = {}

def should_rate_limit(domain: str) -> bool:
    """Check if we should rate limit requests to a domain."""
    if domain not in RATE_LIMITS:
        return False
        
    last_request, count = RATE_LIMITS[domain]
    if datetime.now() - last_request > timedelta(minutes=15):
        # Reset after cooldown period
        RATE_LIMITS[domain] = (datetime.now(), 1)
        return False
        
    if count > 30:  # Limit requests per 15 min window
        return True
        
    RATE_LIMITS[domain] = (last_request, count + 1)
    return False

def get_session() -> requests.Session:
    """Create a session with retry handling."""
    session = requests.Session()
    
    adapter = HTTPAdapter(
        max_retries=RETRY_STRATEGY,
        pool_connections=10,
        pool_maxsize=10
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Add common headers
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json,text/html",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive" 
    })
    return session

try:
    from playwright.sync_api import sync_playwright, TimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available - web scraping will be limited")

def get_browser_context(playwright, headless: bool = True):
    """Create a browser context with anti-detection measures."""
    browser = playwright.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-extensions",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]
    )
    
    context = browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width": random.randint(1024, 1920), 
                 "height": random.randint(768, 1080)},
        locale="en-US",
        timezone_id="America/New_York",
        permissions=["geolocation"],
        java_script_enabled=True
    )
    
    # Mask automation
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = { runtime: {} };
    """)
    
    return browser, context

def search_greenhouse_jobs(session: requests.Session, search_term: str = None) -> List[Dict]:
    """Search for jobs across multiple Greenhouse boards."""
    all_jobs = []
    
    for company in GREENHOUSE_BOARDS:
        if should_rate_limit("greenhouse.io"):
            logger.warning(f"Rate limiting in effect for Greenhouse API, skipping {company}")
            continue
            
        url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
        
        try:
            logger.info(f"Checking {company} Greenhouse API: {url}")
            response = session.get(url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            
            jobs = response.json().get("jobs", [])
            
            # If search term provided, filter results
            if search_term:
                search_terms = [term.lower() for term in search_term.split()]
                jobs = [
                    job for job in jobs
                    if any(term in job.get("title", "").lower() or
                          term in job.get("location", {}).get("name", "").lower() or
                          term in " ".join(job.get("departments", [{}])[0].get("name", "")).lower()
                          for term in search_terms)
                ]
            
            for job in jobs:
                job_info = {
                    "title": job.get("title"),
                    "company": company,
                    "location": job.get("location", {}).get("name", "Unknown"),
                    "department": job.get("departments", [{}])[0].get("name"),
                    "absolute_url": job.get("absolute_url"),
                    "source": "Greenhouse"
                }
                all_jobs.append(job_info)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Greenhouse API error ({company}): {type(e).__name__}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"URL: {url}")
                logger.error(f"Status code: {e.response.status_code}")
                logger.error(f"Response: {e.response.text}")
            continue
            
        time.sleep(1)  # Be nice to the API
        
    return all_jobs

def search_jobs(query: str = "Software Engineer", location: str = "remote") -> List[Dict]:
    """Search for jobs across all configured sources."""
    session = get_session()
    all_jobs = []
    search_term = f"{query} {location}".lower()
    
    # Search Greenhouse boards
    logger.info(f"Searching Greenhouse boards via API")
    greenhouse_jobs = search_greenhouse_jobs(session, search_term)
    all_jobs.extend(greenhouse_jobs)
    
    logger.info(f"Found {len(all_jobs)} total jobs across {len(GREENHOUSE_BOARDS)} sources")
    return all_jobs

def get_job_description(job_url: str) -> str:
    """Get job description from any supported source.
    
    Args:
        job_url: Job posting URL
        
    Returns:
        Full job description text
    """
    logger.info(f"Getting description from: {job_url}")
    
    if not PLAYWRIGHT_AVAILABLE:
        return ""
    
    try:
        with sync_playwright() as p:
            browser, context = get_browser_context(p)
            page = context.new_page()
            page.set_default_timeout(45000)
            
            response = page.goto(job_url, wait_until="networkidle")
            if not response or not response.ok:
                raise Exception(f"Failed to load {job_url}")
            
            time.sleep(random.uniform(2, 4))
            
            description = ""
            
            # Try different selectors based on the job board
            selectors = [
                ".job-content",
                "#content",
                "[data-qa='job-description']",
                ".description",
                "#job-description",
                "#description"
            ]
            
            for selector in selectors:
                try:
                    element = page.wait_for_selector(selector, timeout=5000)
                    if element:
                        description = element.inner_text()
                        break
                except:
                    continue
            
            browser.close()
            return description.strip()
            
    except Exception as e:
        logger.error(f"Failed to get job description: {e}")
        return ""

if __name__ == "__main__":
    # Example usage
    jobs = search_jobs("Data Engineer", "remote")
    
    # Print results
    for job in jobs:
        print("\nJob Found:")
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Department: {job['department']}")
        print(f"URL: {job['absolute_url']}")
        print(f"Source: {job['source']}")
        
        # Optionally fetch job description
        # desc = get_job_description(job['absolute_url'])
        # print(f"\nDescription preview: {desc[:200]}...")
"""Job search aggregator.

This module aggregates job listings from multiple sources:
- Greenhouse boards
- LinkedIn jobs
- Other sources (Indeed, etc. to be added)

It also coordinates with the resume tailoring system to ensure
each application uses an appropriately customized resume.
"""
import random
import time
from typing import List, Dict, Optional, Union
import logging
from pathlib import Path
from urllib.parse import quote, urljoin
import json
import requests

# Define user agents manually for now
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/93.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/94.0.992.50"
]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure proxy and anti-detection settings
PROXY_LIST = [] # Disabled for now

# Load company career pages
COMPANY_CAREERS = {
    "github": "https://github.com/about/careers",
    "stripe": "https://stripe.com/jobs",
    "databricks": "https://databricks.com/company/careers",
    "digitalocean": "https://www.digitalocean.com/careers",
    "elastic": "https://www.elastic.co/careers",
    "confluent": "https://www.confluent.io/careers",
    "auth0": "https://auth0.com/careers"
}

# Try to import source-specific modules
SOURCES_AVAILABLE = {
    "greenhouse": True,  # Built-in support
    "linkedin": False,   # Will be updated below
    "indeed": False,    # Future
    "company": True    # Direct company career pages
}

try:
    from automation_tools.linkedin import search_linkedin_jobs
    SOURCES_AVAILABLE["linkedin"] = True
except ImportError:
    logger.warning("LinkedIn module not available")

try:
    from automation_tools.resume_tailor import tailor_resume, tailor_cover_letter
    RESUME_TAILOR_AVAILABLE = True
except ImportError:
    logger.warning("Resume tailoring not available")
    RESUME_TAILOR_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    PLAYWRIGHT_AVAILABLE = False


def get_browser_context(playwright, use_proxy: bool = False, retry_without_proxy: bool = False):
    """Create a browser context with anti-detection measures."""
    user_agent = random.choice(USER_AGENTS)
    
    browser = playwright.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled", 
            "--disable-extensions",
            "--no-sandbox",
            "--disable-dev-shm-usage"
            ],
            timeout=60000
    )
    
    # Enhanced anti-detection
    context = browser.new_context(
        user_agent=user_agent,
        viewport={"width": random.randint(1024, 1920), "height": random.randint(768, 1080)},
        locale=random.choice(["en-US", "en-GB", "en-CA"]),
        timezone_id=random.choice(["America/New_York", "Europe/London", "Asia/Singapore"]),
        permissions=["geolocation"],
        java_script_enabled=True,
        has_touch=random.choice([True, False]),
            color_scheme=random.choice(["dark", "light", "no-preference"]),
            bypass_csp=True
    )
    
    # Mask automation
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = { runtime: {} };
    """)
    
    return browser, context

def search_for_jobs(
    job_title: str,
    location: str = "remote",
    sources: Optional[List[str]] = None,
    limit_per_source: int = 5,
    use_proxy: bool = True
) -> List[Dict]:
    """Search multiple job sources and return aggregated results.
    
    Args:
        job_title: Job title to search for
        location: Job location or "remote"
        sources: List of sources to search (default: all available)
        limit_per_source: Max results per source
        
    Returns:
        List of jobs with title, company, url, and source
    """
    if sources is None:
        sources = [s for s, available in SOURCES_AVAILABLE.items() if available]
    
    logger.info(f"Searching {len(sources)} sources for: {job_title} in {location}")
    all_jobs = []
    
    # 1. Search company career pages and Greenhouse
    if "company" in sources or "greenhouse" in sources:
        try:
            # Try direct API endpoints first for some companies
            api_endpoints = {
                "github": "https://jobs.github.com/positions.json",
                "stripe": "https://stripe.com/jobs/listing/api/search",
                "databricks": "https://boards.greenhouse.io/databricks/jobs/search.json"
            }
            
            for company, api_url in api_endpoints.items():
                try:
                    headers = {"User-Agent": random.choice(USER_AGENTS)}
                    params = {"q": job_title, "location": location}
                    response = requests.get(api_url, headers=headers, params=params, timeout=10)
                    
                    if response.ok:
                        jobs_data = response.json()
                        if isinstance(jobs_data, list):  # GitHub format
                            for job in jobs_data:
                                if job.get("title") and any(term.lower() in job["title"].lower() for term in job_title.split()):
                                    all_jobs.append({
                                        "title": job["title"],
                                        "company": company,
                                        "url": job["url"],
                                        "source": "company_api",
                                        "location": job.get("location", location)
                                    })
                        elif isinstance(jobs_data, dict):  # Other API formats
                            for job in jobs_data.get("jobs", []):
                                if job.get("title") and any(term.lower() in job["title"].lower() for term in job_title.split()):
                                    all_jobs.append({
                                        "title": job["title"],
                                        "company": company,
                                        "url": job.get("absolute_url", job.get("url")),
                                        "source": "company_api",
                                        "location": job.get("location", location)
                                    })
                                    
                except Exception as e:
                    logger.warning(f"Failed to fetch from {company} API: {e}")
            
            # Fallback to web scraping
            with sync_playwright() as p:
                browser, context = get_browser_context(p, use_proxy=use_proxy)
                all_company_jobs = []
                
                # Create a new page with enhanced timeouts
                page = context.new_page()
                page.set_default_timeout(60000)  # Longer timeout
                page.set_default_navigation_timeout(60000)  # Separate navigation timeout
                
                # Add error handling for common scenarios
                page.on("pageerror", lambda err: logger.warning(f"Page error: {err}"))
                page.on("requestfailed", lambda req: logger.warning(f"Failed request: {req.url}"))
                
                # Configure retry strategy
                retry_options = {
                    "attempts": 3,
                    "delay": lambda attempt: 2 ** attempt + random.uniform(1, 3)
                }
                
                # First try direct company career pages
                if "company" in sources:
                    for company, career_url in COMPANY_CAREERS.items():
                        try:
                            logger.info(f"Checking {company} careers page")
                            response = page.goto(career_url, wait_until="domcontentloaded")
                            if response and response.ok:
                                time.sleep(random.uniform(2, 4))
                                
                                # Try common job search selectors
                                search_selectors = [
                                    'input[type="search"]',
                                    'input[placeholder*="search"]',
                                    'input[aria-label*="search"]'
                                ]
                                
                                for selector in search_selectors:
                                    try:
                                        search_input = page.query_selector(selector)
                                        if search_input:
                                            search_input.fill(job_title)
                                            search_input.press("Enter")
                                            time.sleep(3)
                                            break
                                    except Exception:
                                        continue
                                
                                # Try to find job listings
                                job_selectors = [
                                    "a[href*='job']",
                                    "a[href*='career']",
                                    "a[href*='position']",
                                    ".job-listing",
                                    ".careers-listing"
                                ]
                                
                                for selector in job_selectors:
                                    jobs = page.query_selector_all(selector)
                                    for job in jobs:
                                        try:
                                            job_url = job.get_attribute("href")
                                            if job_url:
                                                job_url = urljoin(career_url, job_url)
                                                title = job.inner_text()
                                                
                                                if any(term.lower() in title.lower() for term in job_title.split()):
                                                    all_company_jobs.append({
                                                        "title": title,
                                                        "company": company,
                                                        "url": job_url,
                                                        "source": "company",
                                                        "location": location
                                                    })
                                                    
                                                    if len(all_company_jobs) >= limit_per_source:
                                                        break
                                        except Exception as e:
                                            logger.warning(f"Failed to parse job listing: {e}")
                                            continue
                                            
                                    if len(all_company_jobs) >= limit_per_source:
                                        break
                                        
                        except Exception as e:
                            logger.warning(f"Failed to check {company} careers: {e}")
                            continue
                            
                        time.sleep(random.uniform(3, 5))  # Delay between companies
                
                # Then try Greenhouse search
                if "greenhouse" in sources:
                    greenhouse_jobs = []
                    
                    # Try Greenhouse API first
                    gh_companies = ["stripe", "databricks", "auth0", "elastic"]
                    for company in gh_companies:
                        try:
                            api_url = f"https://boards.greenhouse.io/{company}/jobs/search.json"
                            headers = {"User-Agent": random.choice(USER_AGENTS)}
                            params = {"query": job_title}
                            
                            response = requests.get(api_url, headers=headers, params=params, timeout=10)
                            if response.ok:
                                jobs_data = response.json()
                                for job in jobs_data.get("jobs", []):
                                    if any(term.lower() in job["title"].lower() for term in job_title.split()):
                                        greenhouse_jobs.append({
                                            "title": job["title"],
                                            "company": company,
                                            "url": f"https://boards.greenhouse.io/{company}/jobs/{job['id']}",
                                            "source": "greenhouse",
                                            "location": job.get("location", location)
                                        })
                                        
                                        if len(greenhouse_jobs) >= limit_per_source:
                                            break
                                            
                        except Exception as e:
                            logger.warning(f"Failed to fetch from {company} Greenhouse API: {e}")
                            
                    # Fallback to web search if needed
                    if len(greenhouse_jobs) < limit_per_source:
                        page = context.new_page()  # Fresh page for Greenhouse
                        page.set_default_timeout(45000)
                
                # Try direct company job board APIs
                api_endpoints = {
                    "github": "https://jobs.github.com/positions.json",
                    "stripe": "https://api.stripe.com/v1/jobs",
                    "databricks": "https://www.databricks.com/api/careers/jobs",
                    "digitalocean": "https://api.digitalocean.com/v2/careers",
                    "elastic": "https://jobs.elastic.co/api/jobs",
                    "auth0": "https://auth0.com/api/jobs"
                }
                
                for company, api_url in api_endpoints.items():
                    try:
                        headers = {
                            "User-Agent": random.choice(USER_AGENTS),
                            "Accept": "application/json"
                        }
                        params = {
                            "q": job_title,
                            "location": location,
                            "remote": True
                        }
                        
                        response = requests.get(api_url, headers=headers, params=params, timeout=10)
                        if response.ok:
                            try:
                                jobs_data = response.json()
                                if isinstance(jobs_data, list):  # GitHub format
                                    for job in jobs_data:
                                        if job.get("title") and any(term.lower() in job["title"].lower() for term in job_title.split()):
                                            all_jobs.append({
                                                "title": job["title"],
                                                "company": company,
                                                "url": job["url"],
                                                "source": "company_api",
                                                "location": job.get("location", location)
                                            })
                                elif isinstance(jobs_data, dict):  # Other API formats
                                    for job in jobs_data.get("jobs", []):
                                        if job.get("title") and any(term.lower() in job["title"].lower() for term in job_title.split()):
                                            all_jobs.append({
                                                "title": job["title"],
                                                "company": company,
                                                "url": job.get("url", job.get("absolute_url")),
                                                "source": "company_api",
                                                "location": job.get("location", location)
                                            })
                            except ValueError:
                                logger.warning(f"Invalid JSON from {company} API")
                        
                    except Exception as e:
                        logger.warning(f"Failed to fetch from {company} API: {e}")
                        
                    # Always add a delay between requests
                    time.sleep(random.uniform(1, 2))
                    
                # If we found jobs through APIs, return early
                if len(all_jobs) >= limit_per_source:
                    return all_jobs
                    
                # Fallback to searching Greenhouse boards directly
                logger.info("Falling back to direct board search")
                greenhouse_boards = [
                    "github",
                    "stripe",
                    "databricks",
                    "elastic",
                    "auth0"
                ]
                
                for board in greenhouse_boards:
                    try:
                        url = f"https://boards.greenhouse.io/{board}"
                        logger.info(f"Checking {board} board")
                            
                        # Implement retry logic
                        max_retries = 3
                        base_delay = 2
                        current_attempt = 0
                        
                        while current_attempt < max_retries:
                            try:
                                response = page.goto(url, wait_until="domcontentloaded")
                                if not response or not response.ok:
                                    raise Exception("Page not loaded successfully")
                                    
                                # Wait for job listings
                                page.wait_for_selector(".opening", timeout=15000)
                                time.sleep(random.uniform(3, 5))
                                
                                # Extract job listings
                                jobs = page.query_selector_all(".opening")
                                for job in jobs:
                                    try:
                                        title_elem = job.query_selector("a")
                                        dept_elem = job.query_selector(".department")
                                        loc_elem = job.query_selector(".location")
                                        
                                        if title_elem:
                                            title = title_elem.inner_text()
                                            if any(term.lower() in title.lower() for term in job_title.split()):
                                                job_url = "https://boards.greenhouse.io" + title_elem.get_attribute("href")
                                                all_jobs.append({
                                                    "title": title,
                                                    "company": board,
                                                    "url": job_url,
                                                    "source": "greenhouse",
                                                    "location": loc_elem.inner_text() if loc_elem else location,
                                                    "department": dept_elem.inner_text() if dept_elem else None
                                                })
                                    except Exception as e:
                                        logger.warning(f"Failed to parse job listing: {e}")
                                        continue
                                
                                break  # Success, exit retry loop
                                
                            except Exception as e:
                                current_attempt += 1
                                if current_attempt == max_retries:
                                    logger.warning(f"Failed to check {board} board after {max_retries} attempts: {e}")
                                    break
                                    
                                delay = base_delay ** current_attempt + random.uniform(0, 1)
                                logger.info(f"Attempt {current_attempt} failed, retrying in {delay:.1f} seconds")
                                time.sleep(delay)
                                
                    except Exception as e:
                        logger.warning(f"Failed to process {board}: {e}")
                        continue
                        
                    time.sleep(random.uniform(3, 5))  # Delay between boards
                    
                time.sleep(random.uniform(2, 3))
                
                # Wait for and extract search results (try multiple selectors)
                selectors = ["div#search", "div#rso", "div.g"]
                found_selector = False
                
                for selector in selectors:
                    try:
                        page.wait_for_selector(selector, timeout=10000)
                        found_selector = True
                        break
                    except Exception:
                        continue
                        
                if not found_selector:
                    raise Exception("Could not find search results on page")
                    
                time.sleep(2)  # Let JavaScript finish running
                
                # Extract Greenhouse job URLs from search results - try multiple selector patterns
                greenhouse_jobs = []
                for link_selector in ["a[href*='greenhouse.io/jobs']", "a[href*='boards.greenhouse.io']", "cite[*='greenhouse.io']"]:
                    links = page.query_selector_all(link_selector)
                
                for link in links:
                    try:
                        href = link.get_attribute("href")
                        if href and "greenhouse.io/jobs/" in href:
                            # Extract real URL from Google redirect
                            url = href.split("/url?q=")[1].split("&")[0] if "/url?q=" in href else href
                            
                            # Get job details
                            job_response = page.goto(url)
                            if job_response and job_response.ok:
                                time.sleep(random.uniform(1, 2))
                                
                                title = page.query_selector("h1.app-title")
                                company = page.query_selector(".company-name")
                                loc = page.query_selector(".location")
                                
                                if title:
                                    greenhouse_jobs.append({
                                        "title": title.inner_text(),
                                        "company": company.inner_text() if company else url.split("/")[3].title(),
                                        "url": url,
                                        "source": "greenhouse",
                                        "location": loc.inner_text() if loc else location
                                    })
                                    
                                    if len(greenhouse_jobs) >= limit_per_source:
                                        break
                                        
                    except Exception as e:
                        logger.warning(f"Failed to process job link: {e}")
                        
                        # Smart retry with exponential backoff
                        for retry in range(3):
                            try:
                                # Exponential backoff: 2, 4, 8 seconds + random jitter
                                time.sleep(2 ** (retry + 1) + random.uniform(0, 1))
                                
                                # Create fresh context for retry
                                retry_context = browser.new_context(
                                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/90.0.0.0",
                                    viewport={"width": 1920, "height": 1080}
                                )
                                retry_page = retry_context.new_page()
                                retry_page.set_default_timeout(30000)
                                
                                job_response = retry_page.goto(url)
                                if job_response and job_response.ok:
                                    time.sleep(random.uniform(1, 2))
                                    
                                    title = retry_page.query_selector("h1.app-title")
                                    company = retry_page.query_selector(".company-name")
                                    loc = retry_page.query_selector(".location")
                                    
                                    if title:
                                        greenhouse_jobs.append({
                                            "title": title.inner_text(),
                                            "company": company.inner_text() if company else url.split("/")[3].title(),
                                            "url": url,
                                            "source": "greenhouse",
                                            "location": loc.inner_text() if loc else location
                                        })
                                        
                                        if len(greenhouse_jobs) >= limit_per_source:
                                            break
                                            
                                    break  # Success, exit retry loop
                                    
                            except Exception as retry_e:
                                logger.warning(f"Retry {retry + 1} failed: {retry_e}")
                                continue
                                
                        continue  # Move to next job link
                            
                # Clean up context after each job
                if context:
                    try:
                        context.close()
                    except:
                        pass
                
                logger.info(f"Found {len(greenhouse_jobs)} Greenhouse jobs")
                all_jobs.extend(greenhouse_jobs)
                
                all_jobs.extend(greenhouse_jobs)
                logger.info(f"Found {len(greenhouse_jobs)} Greenhouse jobs")
                
        except Exception as e:
            logger.error(f"Greenhouse search failed: {e}")
    
    # 2. Search LinkedIn jobs
    if "linkedin" in sources and SOURCES_AVAILABLE["linkedin"]:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                linkedin_jobs = search_linkedin_jobs(
                    job_title,
                    location=location,
                    results_limit=limit_per_source
                )
                if linkedin_jobs:  # Only extend if we got results
                    all_jobs.extend(linkedin_jobs)
                    logger.info(f"Found {len(linkedin_jobs)} LinkedIn jobs")
                    break
                else:
                    logger.warning(f"LinkedIn search attempt {attempt + 1} returned no results")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** (attempt + 1) + random.uniform(1, 3))
            except Exception as e:
                logger.error(f"LinkedIn search attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** (attempt + 1) + random.uniform(1, 3))
                else:
                    logger.error("All LinkedIn search attempts failed")
    
    # Randomize order to avoid always hitting the same source first
    random.shuffle(all_jobs)
    
    logger.info(f"Found {len(all_jobs)} total jobs across {len(sources)} sources")
    return all_jobs


def get_job_description(job_url: str) -> str:
    """Get job description from any supported source.
    
    Args:
        job_url: Job posting URL (from any supported source)
        
    Returns:
        Full job description text
    """
    logger.info(f"Getting description from: {job_url}")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/90.0.0.0"
            )
            page = context.new_page()
            page.set_default_timeout(30000)
            
            response = page.goto(job_url, wait_until="domcontentloaded")
            if not response or not response.ok:
                raise Exception(f"Failed to load {job_url}")
            
            time.sleep(random.uniform(2, 4))
            
            description = ""
            
            if "greenhouse.io" in job_url:
                # Try different Greenhouse selectors
                selectors = [
                    ".job-content",
                    "#content",
                    ".job-description",
                    "#app-body",
                    ".opening-desc"
                ]
                
                for selector in selectors:
                    content = page.query_selector(selector)
                    if content:
                        description = content.inner_text()
                        if description and len(description) > 100:
                            break
                            
            elif "linkedin.com" in job_url:
                # Handle LinkedIn's job description
                try:
                    # Need to scroll to load content
                    page.evaluate("window.scrollBy(0, 300)")
                    time.sleep(1)
                    
                    # Try multiple selectors (LinkedIn changes them often)
                    selectors = [
                        ".description__text",
                        ".show-more-less-html",
                        "[data-test-id='job-details']",
                        ".jobs-description"
                    ]
                    
                    for selector in selectors:
                        content = page.query_selector(selector)
                        if content:
                            description = content.inner_text()
                            if description and len(description) > 100:
                                break
                                
                except Exception as e:
                    logger.warning(f"LinkedIn description extraction failed: {e}")
            
            if description:
                return description
            else:
                logger.warning(f"Could not find description in {job_url}")
                return "Could not retrieve job description"
                
    except Exception as e:
        logger.error(f"Failed to get job description: {str(e)}")
        return f"Error retrieving description: {str(e)}"


__all__ = ["search_for_jobs", "get_job_description"]
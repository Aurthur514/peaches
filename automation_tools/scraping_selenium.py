"""Job search aggregator using Selenium.

This module aggregates job listings from multiple sources:
- Greenhouse boards
- LinkedIn jobs
- Other sources (Indeed, etc. to be added)
"""
import random
import time
from typing import List, Dict, Optional
import logging
from pathlib import Path
from urllib.parse import quote, urljoin
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Define user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/93.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/94.0.992.50"
]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def get_webdriver():
    """Create and configure Chrome WebDriver with anti-detection measures."""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # Use new headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option('prefs', {
        'profile.default_content_setting_values.notifications': 2,
        'profile.default_content_settings.popups': 0,
        'download.prompt_for_download': False
    })
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Add anti-detection scripts
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("window.chrome = { runtime: {} };")
    
    return driver

def normalize_job_title(title: str) -> str:
    """Normalize a job title for comparison."""
    # Common substitutions
    substitutions = {
        "sr": "senior",
        "jr": "junior",
        "engg": "engineer",
        "eng": "engineer",
        "dev": "developer",
        "swe": "software engineer",
        "sw": "software"
    }
    
    # Normalize the title
    title = title.lower().strip()
    for k, v in substitutions.items():
        title = title.replace(k, v)
        
    return title

def titles_match(listing_title: str, search_title: str, strict: bool = False) -> bool:
    """Check if a job listing title matches the search title."""
    listing_title = normalize_job_title(listing_title)
    search_title = normalize_job_title(search_title)
    
    # Split into words
    listing_words = set(listing_title.split())
    search_words = set(search_title.split())
    
    if strict:
        # All search words must be present
        return all(word in listing_words for word in search_words)
    else:
        # At least 50% of search words must be present
        matches = sum(1 for word in search_words if word in listing_words)
        return matches >= len(search_words) / 2

def search_for_jobs(
    job_title: str,
    location: str = "remote",
    sources: Optional[List[str]] = None,
    limit_per_source: int = 5,
    use_proxy: bool = False,
    strict_matching: bool = True
) -> List[Dict]:
    """Search multiple job sources and return aggregated results.
    
    Args:
        job_title: Job title to search for
        location: Job location or "remote"
        sources: List of sources to search (default: all available)
        limit_per_source: Max results per source
        use_proxy: Whether to use proxy (unused in Selenium version)
        strict_matching: Whether to use strict title matching
        
    Returns:
        List of jobs with title, company, url, source, location, etc.
    """
    logger.info(f"Searching for: {job_title} in {location} (strict={strict_matching})")
    all_jobs = []
    
    # Try direct API endpoints first
    api_endpoints = {
        "github": "https://jobs.github.com/positions.json",
        "stripe": "https://stripe.com/jobs/listing/api/search",
        "databricks": "https://boards.greenhouse.io/databricks/jobs/search.json"
    }
    
    for company, api_url in api_endpoints.items():
        try:
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            params = {"q": job_title, "location": location}
            response = requests.get(api_url, headers=headers, params=params, timeout=15)
            
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
                                    "url": job.get("absolute_url", job.get("url")),
                                    "source": "company_api",
                                    "location": job.get("location", location)
                                })
                except ValueError:
                    logger.warning(f"Invalid JSON from {company} API")
                    
        except Exception as e:
            logger.warning(f"Failed to fetch from {company} API: {e}")
            
        time.sleep(random.uniform(2, 4))
        
    # Fall back to web scraping
    if len(all_jobs) < limit_per_source:
        logger.info("Falling back to direct board search")
        driver = None
        try:
            driver = get_webdriver()
            wait = WebDriverWait(driver, 15)
            
            # Check Greenhouse boards
            boards_to_check = ["stripe", "databricks", "elastic"]
            for board in boards_to_check:
                try:
                    url = f"https://boards.greenhouse.io/{board}"
                    logger.info(f"Checking {board} board")
                    
                    # Implement retry logic
                    max_retries = 3
                    base_delay = 2
                    current_attempt = 0
                    
                    while current_attempt < max_retries:
                        try:
                            logger.info(f"Loading {url}")
                            driver.get(url)
                            time.sleep(5)  # Wait longer for initial page load
                            
                            # First try scrolling to load more content
                            try:
                                last_height = driver.execute_script("return document.body.scrollHeight")
                                while True:
                                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                                    time.sleep(2)
                                    new_height = driver.execute_script("return document.body.scrollHeight")
                                    if new_height == last_height:
                                        break
                                    last_height = new_height
                            except Exception as e:
                                logger.warning(f"Scroll failed: {e}")
                            
                            # First try searching for software engineer directly
                            try:
                                search_input = driver.find_element(By.CSS_SELECTOR, "input[type='search'], input[placeholder*='Search']")
                                search_input.clear()
                                search_input.send_keys(job_title)
                                search_input.submit()
                                time.sleep(3)
                            except Exception as e:
                                logger.debug(f"Search not available: {e}")
                            
                            # Handle pagination - look for "page" or "load more" buttons
                            def try_load_more():
                                try:
                                    # Common pagination/load more selectors
                                    load_more_selectors = [
                                        "button[contains(text(), 'Load')]",
                                        "button[contains(text(), 'More')]",
                                        "button[contains(text(), 'Show')]",
                                        "*[contains(@class, 'load-more')]",
                                        "*[contains(@class, 'pagination')]",
                                        "*[contains(@class, 'next-page')]"
                                    ]
                                    
                                    for selector in load_more_selectors:
                                        elements = driver.find_elements(By.XPATH, selector)
                                        for elem in elements:
                                            if elem.is_displayed() and elem.is_enabled():
                                                elem.click()
                                                time.sleep(2)
                                                return True
                                    return False
                                except Exception as e:
                                    logger.debug(f"Load more failed: {e}")
                                    return False
                            
                            # Keep loading more until we can't
                            while try_load_more():
                                pass
                            
                            # Try multiple selectors for job listings
                            selectors = [
                                # GreenHouse specific selectors
                                (By.CLASS_NAME, "opening"),
                                (By.CSS_SELECTOR, ".opening-item"),
                                (By.CSS_SELECTOR, ".posting"),
                                (By.CSS_SELECTOR, ".role"),
                                # Generic job board selectors
                                (By.CSS_SELECTOR, ".jobs-list .job-item"),
                                (By.CSS_SELECTOR, ".job-listing"),
                                (By.CSS_SELECTOR, "[data-test='job-list'] > div"),
                                # Individual job links
                                (By.CSS_SELECTOR, "a[href*='/jobs/'][href*='engineer']"),
                                (By.CSS_SELECTOR, "a[href*='/position/'][href*='engineer']"),
                                (By.CSS_SELECTOR, "a[href*='/career/'][href*='engineer']"),
                                # Department containers
                                (By.CSS_SELECTOR, "div[data-department='Engineering'] .job"),
                                (By.CSS_SELECTOR, "section[id*='engineering'] .position"),
                                # Broader containers as fallback
                                (By.CSS_SELECTOR, ".jobs-container .job"),
                                (By.CSS_SELECTOR, ".careers-list .position"),
                                (By.CSS_SELECTOR, ".opportunities .role")
                            ]
                            
                            openings = None
                            for selector in selectors:
                                try:
                                    openings = wait.until(
                                        EC.presence_of_all_elements_located(selector)
                                    )
                                    if openings:
                                        logger.info(f"Found job listings using selector: {selector}")
                                        break
                                except TimeoutException:
                                    continue
                                    
                            if not openings:
                                raise TimeoutException("No job listings found")
                            
                            for opening in openings:
                                try:
                                    # Get the raw HTML for debugging
                                    raw_html = opening.get_attribute('outerHTML')
                                    logger.debug(f"Raw job listing HTML: {raw_html}")
                                    
                                    # Look for parent elements that might contain department info
                                    department = None
                                    try:
                                        parent = opening
                                        for _ in range(3):  # Check up to 3 levels up
                                            parent = parent.find_element(By.XPATH, "..")
                                            for attr in ["data-department", "data-team", "data-category", "data-group"]:
                                                dept = parent.get_attribute(attr)
                                                if dept:
                                                    department = dept
                                                    break
                                            if department:
                                                break
                                    except:
                                        pass  # Ignore if we can't find department info
                                    
                                    # Get text from the element itself first
                                    opening_text = opening.text or opening.get_attribute('textContent')
                                    if opening_text:
                                        logger.debug(f"Opening text: {opening_text}")
                                    
                                    # Try different title selectors
                                    title_elem = None
                                    title_selectors = [
                                        # Direct title elements
                                        (By.CSS_SELECTOR, ".job-title, .position-title, .role-title"),
                                        (By.CSS_SELECTOR, "h1, h2, h3, h4, h5"),
                                        (By.CSS_SELECTOR, ".title, .position, .role"),
                                        # Anchor tags
                                        (By.CSS_SELECTOR, "a[href*='/jobs/']"),
                                        (By.CSS_SELECTOR, "a[href*='/position/']"),
                                        # Nested elements
                                        (By.CSS_SELECTOR, "a > span"),
                                        (By.CSS_SELECTOR, "div[class*='title']"),
                                        (By.CSS_SELECTOR, "div[class*='position']"),
                                        # Broad matches
                                        (By.CSS_SELECTOR, "*[class*='title'], *[class*='position'], *[class*='role']")
                                    ]
                                    
                                    # Try each selector
                                    for title_selector in title_selectors:
                                        try:
                                            title_elem = opening.find_element(*title_selector)
                                            if title_elem:
                                                break
                                        except NoSuchElementException:
                                            continue
                                    
                                    # Try different department/location selectors
                                    dept_elem = None
                                    loc_elem = None
                                    for selector in [
                                        (By.CLASS_NAME, "department"),
                                        (By.CLASS_NAME, "team"),
                                        (By.CLASS_NAME, "group")
                                    ]:
                                        try:
                                            dept_elem = opening.find_element(*selector)
                                            break
                                        except NoSuchElementException:
                                            continue
                                            
                                    for selector in [
                                        (By.CLASS_NAME, "location"),
                                        (By.CLASS_NAME, "workplace"),
                                        (By.CLASS_NAME, "place")
                                    ]:
                                        try:
                                            loc_elem = opening.find_element(*selector)
                                            break
                                        except NoSuchElementException:
                                            continue
                                    
                                    # Try getting text in different ways
                                    title = None
                                    if title_elem:
                                        # Try multiple ways to get text
                                        title = title_elem.text or title_elem.get_attribute('textContent') or title_elem.get_attribute('innerText')
                                        
                                    if title and any(term.lower() in title.lower() for term in job_title.split()):
                                        # Try getting URL
                                        job_url = None
                                        try:
                                            if title_elem.tag_name == 'a':
                                                job_url = title_elem.get_attribute("href")
                                            else:
                                                # Look for parent or child anchor
                                                anchor = title_elem.find_element(By.XPATH, "./ancestor::a[1] | ./descendant::a[1]")
                                                if anchor:
                                                    job_url = anchor.get_attribute("href")
                                        except Exception:
                                            try:
                                                # Try finding any nearby anchor
                                                anchor = opening.find_element(By.TAG_NAME, "a")
                                                if anchor:
                                                    job_url = anchor.get_attribute("href")
                                            except Exception:
                                                pass
                                                
                                        if job_url:
                                            # Clean up URL
                                            if not job_url.startswith('http'):
                                                job_url = "https://boards.greenhouse.io" + job_url
                                                
                                            # Get location and department text safely
                                            location_text = loc_elem.text if loc_elem else None
                                            department_text = dept_elem.text if dept_elem else None
                                            
                                            if not location_text and loc_elem:
                                                location_text = loc_elem.get_attribute('textContent') or loc_elem.get_attribute('innerText')
                                                
                                            # Use department info from parent elements if available
                                            if department and not department_text:
                                                department_text = department
                                                
                                            if not department_text and dept_elem:
                                                department_text = dept_elem.get_attribute('textContent') or dept_elem.get_attribute('innerText')
                                                
                                            job = {
                                                "title": title.strip(),
                                                "company": board,
                                                "url": job_url,
                                                "source": "greenhouse",
                                                "location": location_text.strip() if location_text else location,
                                                "department": department_text.strip() if department_text else None
                                            }
                                            
                                            logger.info(f"Found job: {job['title']} at {job['company']}")
                                            all_jobs.append(job)
                                        
                                        if len(all_jobs) >= limit_per_source:
                                            break
                                except NoSuchElementException as e:
                                    logger.warning(f"Failed to parse job listing: {e}")
                                    continue
                                    
                            break  # Success, exit retry loop
                            
                        except TimeoutException as e:
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
                
        except Exception as e:
            logger.error(f"Web scraping failed: {e}")
            
        finally:
            if driver:
                driver.quit()
                
    # Final sorting and limiting
    all_jobs.sort(key=lambda x: x.get("posted_at", "") or "", reverse=True)
    logger.info(f"Found {len(all_jobs)} total jobs")
    
    return all_jobs[:limit_per_source] if limit_per_source > 0 else all_jobs

def get_job_description(url: str) -> Optional[str]:
    """Get the full job description from a job listing URL."""
    driver = None
    try:
        driver = get_webdriver()
        wait = WebDriverWait(driver, 15)
        
        driver.get(url)
        time.sleep(random.uniform(2, 4))
        
        # Common job description selectors
        selectors = [
            ".description",
            ".job-description",
            "#job-description",
            "[data-test='job-description']",
            ".job-listing",
            ".content"
        ]
        
        for selector in selectors:
            try:
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                return element.text
            except TimeoutException:
                continue
                
        # Fallback to body text
        return driver.find_element(By.TAG_NAME, "body").text
        
    except Exception as e:
        logger.warning(f"Failed to get job description from {url}: {e}")
        return None
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    # Example usage
    jobs = search_for_jobs("Software Engineer", "remote", limit_per_source=2)
    for job in jobs:
        print(f"\nTitle: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"URL: {job['url']}")
        print(f"Source: {job['source']}")
        print(f"Location: {job['location']}")
        if job.get('department'):
            print(f"Department: {job['department']}")
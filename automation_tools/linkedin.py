"""LinkedIn job application automation.

This module provides tools to:
1. Search LinkedIn jobs
2. Extract job details
3. Apply via "Easy Apply" when available
4. Handle rate limiting and anti-bot measures
"""
import time
import random
import logging
from pathlib import Path
from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_linkedin_jobs(
    title: str,
    location: str = "remote",
    results_limit: int = 10,
    filters: Optional[Dict] = None
) -> List[Dict]:
    """Search LinkedIn jobs with anti-bot measures.
    
    Args:
        title: Job title to search for
        location: Job location or "remote"
        results_limit: Maximum number of results
        filters: Optional dict of LinkedIn filters
        
    Returns:
        List of jobs with title, company, url, etc.
    """
    logger.info(f"Searching LinkedIn for: {title} in {location}")
    
    jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 1. Go to LinkedIn jobs
            # 1. Construct search URL with filters
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={title}&location={location}"
            if filters:
                # Add any filters (remote, experience level, etc.)
                filter_params = []
                if filters.get("remote"):
                    filter_params.append("f_WT=2")
                if filters.get("experience"):
                    filter_params.append(f"f_E={filters['experience']}")
                if filter_params:
                    search_url += "&" + "&".join(filter_params)
                    
            # 2. Navigate with anti-bot measures
            page.goto(search_url)
            time.sleep(random.uniform(2, 4))  # Let page load
            time.sleep(random.uniform(2, 4))  # Random delay
            
            # Extract job cards
            cards = page.query_selector_all(".job-card-container")
            for card in cards[:results_limit]:
                try:
                    job = {
                        "title": card.query_selector(".job-card-title").inner_text(),
                        "company": card.query_selector(".job-card-company").inner_text(),
                        "location": card.query_selector(".job-card-location").inner_text(),
                        "url": card.query_selector("a.job-card-title").get_attribute("href"),
                        "source": "linkedin"
                    }
                    jobs.append(job)
                except Exception as e:
                    logger.warning(f"Failed to parse job card: {e}")
                    
            logger.info(f"Found {len(jobs)} LinkedIn jobs")
            
        except Exception as e:
            logger.error(f"LinkedIn search failed: {e}")
        finally:
            browser.close()
            
    return jobs

def apply_linkedin_job(
    job_url: str,
    profile: Dict,
    resume_path: str,
    dry_run: bool = True
) -> str:
    """Apply to a LinkedIn job via Easy Apply if available.
    
    Args:
        job_url: LinkedIn job URL
        profile: Dict with personal info
        resume_path: Path to tailored resume
        dry_run: If True, don't submit
        
    Returns:
        Status message
    """
    logger.info(f"Starting LinkedIn application: {job_url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not dry_run)
        page = browser.new_page()
        
        try:
            page.goto(job_url)
            time.sleep(random.uniform(2, 4))
            
            # Look for Easy Apply button
            easy_apply = page.query_selector("button.jobs-apply-button")
            if not easy_apply:
                return "No Easy Apply button found"
                
            easy_apply.click()
            time.sleep(1)
            
            # Fill form fields (depends on the specific form)
            try:
                # Common fields
                page.fill('input[name="firstName"]', profile["first_name"])
                page.fill('input[name="lastName"]', profile["last_name"])
                page.fill('input[name="email"]', profile["email"])
                
                # Upload resume
                page.set_input_files('input[type="file"]', resume_path)
                
                if not dry_run:
                    submit = page.query_selector("button[type='submit']")
                    if submit:
                        submit.click()
                        try:
                            success = page.wait_for_selector(".application-success", timeout=5000)
                            if success:
                                return "Application submitted successfully"
                        except PlaywrightTimeoutError:
                            return "Submission may have failed - no success message"
                            
                return "Form filled (dry-run)"
                
            except Exception as e:
                logger.error(f"Error filling LinkedIn form: {e}")
                return f"Failed to fill form: {str(e)}"
                
        except Exception as e:
            logger.error(f"LinkedIn application failed: {e}")
            return f"Failed: {str(e)}"
        finally:
            browser.close()
            
    return "Application process completed"
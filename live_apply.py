"""Live application helper.

This module provides a safe way to run live (non-dry-run) applications with:
- Required profile validation
- Rate limiting between submissions
- Detailed logging
- Single-job test mode
"""
import time
import logging
from pathlib import Path
from typing import Optional

from automation_tools.scraping import search_for_jobs, get_job_description
from automation_tools.greenhouse import apply_to_greenhouse_job
import config

# Set up logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "live_apply.log"),
        logging.StreamHandler()
    ]
)


def validate_profile_for_live() -> bool:
    """Check if profile has required fields for live submission."""
    required = ["first_name", "last_name", "email", "master_resume_path"]
    missing = [k for k in required if not config.MY_PROFILE.get(k)]
    if missing:
        logging.error(f"Missing required profile fields for live run: {missing}")
        return False
    
    resume_path = config.MY_PROFILE.get("master_resume_path")
    if not Path(resume_path).exists():
        logging.error(f"Resume file not found: {resume_path}")
        return False
    
    return True


def run_live_test(
    title: str = "Data Analyst",
    location: str = "remote",
    board: str = "greenhouse",
    timeout: int = 30
) -> Optional[str]:
    """Run a single live application as a test.
    
    Args:
        title: Job title to search for
        location: Job location
        board: Only "greenhouse" supported for now
        timeout: Seconds to wait between actions
    
    Returns:
        URL of the job that was submitted to, or None if failed
    """
    if not validate_profile_for_live():
        return None
    
    # 1. Search for matching jobs
    jobs = search_for_jobs(title, location)
    if not jobs:
        logging.error("No jobs found")
        return None
    
    # 2. Find first matching job for the board
    job = None
    for j in jobs:
        if board == "greenhouse" and "greenhouse.io" in j.get("url", ""):
            job = j
            break
    
    if not job:
        logging.error(f"No {board} jobs found in results")
        return None
    
    # 3. Get full description
    url = job["url"]
    desc = get_job_description(url)
    logging.info(f"Found matching job: {job['title']} @ {job['company']}")
    
    # 4. Submit!
    if board == "greenhouse":
        status = apply_to_greenhouse_job(url, config.MY_PROFILE, dry_run=False)
        if "success" in status.lower():
            return url
    
    return None


def run_live_batch(
    title: str,
    location: str = "remote",
    limit: int = 3,
    min_delay: int = 30,
    max_delay: int = 120
) -> list[str]:
    """Run a batch of live applications with rate limiting.
    
    Args:
        title: Job title to search for
        location: Job location
        limit: Maximum number of applications to submit
        min_delay: Minimum seconds between submissions
        max_delay: Maximum seconds between submissions
    
    Returns:
        List of URLs that were successfully submitted to
    """
    if not validate_profile_for_live():
        return []
    
    jobs = search_for_jobs(title, location)
    if not jobs:
        logging.error("No jobs found")
        return []
    
    submitted = []
    for job in jobs[:limit]:
        url = job.get("url")
        if not url:
            continue
            
        if "greenhouse.io" in url.lower():
            desc = get_job_description(url)
            status = apply_to_greenhouse_job(url, config.MY_PROFILE, dry_run=False)
            if "success" in status.lower():
                submitted.append(url)
                
                # Rate limiting
                if len(submitted) < limit:
                    delay = min(max_delay, max(min_delay, 30 + len(submitted) * 15))
                    logging.info(f"Rate limiting - waiting {delay}s before next submission")
                    time.sleep(delay)
    
    return submitted


if __name__ == "__main__":
    # Quick test: try to submit one application
    result = run_live_test()
    if result:
        print(f"Success! Submitted to: {result}")
    else:
        print("Test submission failed - check logs for details")
#!/usr/bin/env python3
"""
Simple orchestrator to perform a dry-run of the job-application agent.

Usage examples:
  python auto_apply.py --title "Data Analyst" --location remote --limit 2 --dry-run

This script uses the existing automation utilities in `automation_tools`.
It defaults to dry-run mode (does not submit applications). Set --dry-run False to run headless but
note: real submissions are still intentionally disabled by default in the automation scripts.
"""
import argparse
from automation_tools.scraping_selenium import search_for_jobs, get_job_description
from automation_tools.greenhouse import apply_to_greenhouse_job
import config
import sys
from typing import List, Dict
import logging
import os
import time
import random

# configure basic logging to bot_run.log
logger = logging.getLogger("auto_apply")
logger.setLevel(logging.INFO)
bot_log = os.path.abspath(os.path.join(os.path.dirname(__file__), "bot_run.log"))
fh_bot = logging.FileHandler(bot_log)
fh_bot.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(fh_bot)


def main():
    parser = argparse.ArgumentParser(description="Auto-apply agent with resume tailoring")
    parser.add_argument("--title", required=True, help="Job title to search for")
    parser.add_argument("--location", default="remote", help="Location for the job search")
    parser.add_argument("--sources", nargs="+", default=["greenhouse", "linkedin"], 
                      help="Job sources to search")
    parser.add_argument("--limit", type=int, default=3, help="Max number of jobs to process")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                      help="Perform a safe dry-run")
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false",
                      help="Disable dry-run (not recommended)")
    args = parser.parse_args()

    if not config.validate_profile(minimal=True):
        print("ERROR: incomplete profile. Please create `profile.json` or set environment variables.")
        sys.exit(1)

    # 1. Search multiple sources
    print(f"Searching {len(args.sources)} sources for: {args.title} in {args.location}")
    jobs = search_for_jobs(
        job_title=args.title,
        location=args.location,
        sources=args.sources,
        limit_per_source=max(2, args.limit // len(args.sources))
    )
    jobs = jobs[:args.limit]

    results = []
    for j in jobs:
        print("-" * 40)
        print(f"Found: {j.get('title')} @ {j.get('company')} -> {j.get('url')}")
        
        # Get full description
        desc = get_job_description(j.get('url'))
        print(f"Description (short): {desc[:200]}")
        
        try:
            # Tailor resume for this job
            from automation_tools.resume_tailor import tailor_resume, tailor_cover_letter
            tailored_resume, match_score = tailor_resume(
                config.MY_PROFILE['master_resume_path'],
                desc,
                j.get('title', ''),
                j.get('company', '')
            )
            print(f"Created tailored resume (match score: {match_score:.2f})")
            
            # Update profile with tailored resume
            profile = dict(config.MY_PROFILE)
            profile['master_resume_path'] = tailored_resume
            
            # Create tailored cover letter
            if profile.get('master_cover_letter'):
                profile['cover_letter'] = tailor_cover_letter(
                    profile['master_cover_letter'],
                    desc,
                    j.get('title', ''),
                    j.get('company', '')
                )
            
        except ImportError:
            print("Resume tailoring not available - using master resume")
            profile = config.MY_PROFILE
            match_score = 0.0

        # Apply based on source
        status = "No automation available"
        url = j.get('url', '')
        
        if "greenhouse.io" in url:
            status = apply_to_greenhouse_job(url, profile, dry_run=args.dry_run)
        elif "linkedin.com" in url:
            try:
                from automation_tools.linkedin import apply_linkedin_job
                status = apply_linkedin_job(url, profile, profile['master_resume_path'],
                                         dry_run=args.dry_run)
            except ImportError:
                status = "LinkedIn automation not available"
                
        print(f"Result: {status}")
        results.append({
            "job": j,
            "status": status,
            "match_score": match_score
        })
        
        # Rate limiting between applications
        if len(results) < len(jobs):
            delay = random.randint(30, 60)
            print(f"Waiting {delay}s before next application...")
            time.sleep(delay)

    print("\nSummary:")
    for r in results:
        score = f" (match: {r['match_score']:.2f})" if r['match_score'] > 0 else ""
        print(f"{r['job'].get('title')} @ {r['job'].get('company')}: {r['status']}{score}")


def run_auto_apply(title: str, location: str = "remote", limit: int = 3, dry_run: bool = True) -> List[Dict]:
    """Programmatic entrypoint for running the auto-apply flow.

    Returns a list of results with keys 'job' and 'status'.
    """
    if not config.validate_profile(minimal=True):
        raise RuntimeError("incomplete profile: please create profile.json or set env vars for first_name, last_name and email")

    jobs = search_for_jobs(title, location)[:limit]
    results: List[Dict] = []

    for j in jobs:
        desc = get_job_description(j.get('url'))
        if j.get('url') and "greenhouse.io" in j.get('url'):
            status = apply_to_greenhouse_job(j.get('url'), config.MY_PROFILE, dry_run=dry_run)
        else:
            status = f"No automation available for {j.get('url')}"
        results.append({"job": j, "status": status})

    return results


def run_live_apply(title: str, location: str = "remote", limit: int = 3, rate_min: int = 30, rate_max: int = 90) -> List[Dict]:
    """Run a live (non-dry) application flow with rate-limiting and safety checks.

    - Validates that the profile contains a `master_resume_path` that exists.
    - Runs up to `limit` jobs and sleeps between submissions for a random period in [rate_min, rate_max] seconds.
    - Logs to `bot_run.log` and relies on `automation_tools/greenhouse.py` to append to `submissions.log`.
    """
    profile = config.MY_PROFILE
    resume = profile.get("master_resume_path")
    if not resume:
        raise RuntimeError("Profile does not include 'master_resume_path'. Please set it before running live.")
    if not os.path.exists(resume):
        raise RuntimeError(f"Resume path does not exist: {resume}")

    logger.info(f"Starting live apply: title={title}, location={location}, limit={limit}")

    jobs = search_for_jobs(title, location)[:limit]
    results: List[Dict] = []

    for idx, j in enumerate(jobs, start=1):
        logger.info(f"Processing job {idx}/{len(jobs)}: {j.get('url')}")
        desc = get_job_description(j.get('url'))
        if j.get('url') and "greenhouse.io" in j.get('url'):
            status = apply_to_greenhouse_job(j.get('url'), profile, dry_run=False)
        else:
            status = f"No automation available for {j.get('url')}"
        results.append({"job": j, "status": status})
        logger.info(f"Result for {j.get('url')}: {status}")

        # Rate-limit between submissions unless this was the last job
        if idx < len(jobs):
            wait = random.uniform(rate_min, rate_max)
            logger.info(f"Sleeping {wait:.1f}s before next submission")
            time.sleep(wait)

    logger.info("Live apply run complete")
    return results


if __name__ == "__main__":
    main()

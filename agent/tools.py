from langchain.tools import tool
import os
import config
from config import MY_PROFILE
from automation_tools.scraping import search_for_jobs, get_job_description
from automation_tools.greenhouse import apply_to_greenhouse_job
# from automation_tools.lever import apply_to_lever_job # You'd import this too

# --- Tool 1: Job Search ---
@tool
def tool_search_for_jobs(job_title: str, location: str = "remote") -> list[dict]:
    """
    Searches for jobs matching a title and location.
    Returns a list of dictionaries, each with 'title', 'company', and 'url'.
    This should always be the first tool you use.
    """
    return search_for_jobs(job_title, location)

# --- Tool 2: Description Scraper ---
@tool
def tool_get_job_description(job_url: str) -> str:
    """
    Given a job URL, this tool scrapes the full job description text.
    This text is required *before* you can apply, so you
    can use it to tailor the resume and answer questions.
    """
    return get_job_description(job_url)

# --- Tool 3: The "Router" Applicator ---
@tool
def tool_apply_to_job_url(job_url: str, job_description: str) -> str:
    """
    Applies to a single job using its URL and job description.
    This tool will internally decide which automation script to run.
    It returns a success or failure message.
    """
    print(f"--- Received 'apply' command for: {job_url} ---")
    
    # Here is the ROUTER logic. Decide whether we are running a dry-run.
    # Priority: profile key `dry_run` -> environment variable JOB_AGENT_DRY_RUN -> default True
    env_val = os.getenv("JOB_AGENT_DRY_RUN")
    if isinstance(MY_PROFILE, dict) and MY_PROFILE.get("dry_run") is not None:
        dry_run = bool(MY_PROFILE.get("dry_run"))
    elif env_val is not None:
        dry_run = env_val.lower() in ("1", "true", "yes")
    else:
        dry_run = True

    if "greenhouse.io" in job_url:
        print("Routing to Greenhouse script...")
        # You could also add LLM calls here to tailor resume/answer questions
        return apply_to_greenhouse_job(job_url, MY_PROFILE, dry_run=dry_run)
        
    elif "lever.co" in job_url:
        print("Routing to Lever script...")
        # return apply_to_lever_job(job_url, MY_PROFILE) # Your future function
        return "Lever script is not implemented yet."
        
    else:
        print("Unknown job board.")
        return f"Error: Cannot apply to this website. Unknown domain: {job_url}"

# --- Gather all tools in one list ---
all_tools = [
    tool_search_for_jobs,
    tool_get_job_description,
    tool_apply_to_job_url
]
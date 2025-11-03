from playwright.sync_api import sync_playwright
import time

def apply_to_greenhouse_job(job_url: str, profile: dict):
    """
    Uses Playwright to fill out a standard Greenhouse application.
    """
    print(f"--- Opening Greenhouse page: {job_url} ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # See it run
        page = browser.new_page()
        page.goto(job_url)

        try:
            page.get_by_label("First Name *").fill(profile['first_name'])
            page.get_by_label("Last Name *").fill(profile['last_name'])
            page.get_by_label("Email *").fill(profile['email'])
            page.get_by_label("Resume/CV *").set_input_files(profile['master_resume_path'])
            
            # New fields for phone, LinkedIn, GitHub
            if profile['phone']:
                page.get_by_label("Phone").fill(profile['phone'])
            if profile['linkedin_url']:
                page.get_by_label("LinkedIn URL").fill(profile['linkedin_url'])
            if profile['github_url']:
                page.get_by_label("GitHub URL").fill(profile['github_url'])

            # Handle "Are you authorized to work...?"
            page.get_by_label("Yes", exact=True).check()

            print("--- Form filled successfully! (Not submitting) ---")
            time.sleep(5) # Pause to let you see
        
        except Exception as e:
            print(f"Error on Greenhouse: {e}")
            return f"Failed to apply to Greenhouse: {e}"
        finally:
            browser.close()
            
    return "Successfully filled Greenhouse application."

# You would also create automation_tools/lever.py in the same way
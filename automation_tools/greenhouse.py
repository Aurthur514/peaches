from playwright.sync_api import sync_playwright
import time
from typing import Dict
import logging
import os
import re

# Configure logging
logger = logging.getLogger("greenhouse")
logger.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bot_run.log"))
fh = logging.FileHandler(log_file)
fh.setFormatter(log_formatter)
logger.addHandler(fh)


def _log_submission(entry: str):
    submissions_log = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "submissions.log"))
    try:
        with open(submissions_log, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception as e:
        logger.error(f"Failed to write submissions.log: {e}")


def apply_to_greenhouse_job(job_url: str, profile: Dict, dry_run: bool = True) -> str:
    """
    Uses Playwright to fill out a Greenhouse application. When dry_run=False this
    will attempt to click the submit button and log results.
    """
    logger.info(f"Opening Greenhouse page: {job_url} (dry_run={dry_run})")
    print(f"--- Opening Greenhouse page: {job_url} (dry_run={dry_run}) ---")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=dry_run)
        page = browser.new_page()
        page.goto(job_url)

        try:
            # Fill fields defensively
            if profile.get("first_name"):
                try:
                    page.get_by_label("First Name *").fill(profile["first_name"])
                except Exception:
                    pass

            if profile.get("last_name"):
                try:
                    page.get_by_label("Last Name *").fill(profile["last_name"])
                except Exception:
                    pass

            if profile.get("email"):
                try:
                    page.get_by_label("Email *").fill(profile["email"])
                except Exception:
                    pass

            resume_path = profile.get("master_resume_path")
            if resume_path:
                try:
                    page.get_by_label("Resume/CV *").set_input_files(resume_path)
                except Exception:
                    # Try alternative upload selectors
                    try:
                        page.locator('input[type="file"]').set_input_files(resume_path)
                    except Exception:
                        pass

            # Optional fields
            if profile.get("phone"):
                try:
                    page.get_by_label("Phone").fill(profile["phone"])
                except Exception:
                    pass

            # Try to check a common radio option if present
            try:
                if page.query_selector("text=Yes"):
                    page.get_by_label("Yes", exact=True).check()
            except Exception:
                pass

            # If dry_run, stop here
            if dry_run:
                logger.info(f"Dry-run completed for {job_url}")
                print("--- Form filled successfully (dry_run mode: not submitting) ---")
                time.sleep(2)
                return "Filled Greenhouse application (dry_run)."

            # Attempt to locate and click a Submit / Apply button
            clicked = False
            submit_selectors = [
                'button:has-text("Submit application")',
                'button:has-text("Submit")',
                'button:has-text("Apply")',
                'text=Submit application',
            ]

            for sel in submit_selectors:
                try:
                    btn = page.locator(sel)
                    if btn.count() > 0:
                        btn.first.click()
                        clicked = True
                        logger.info(f"Clicked submit selector '{sel}' for {job_url}")
                        break
                except Exception:
                    continue

            # Fallback: look for button role with regex
            if not clicked:
                try:
                    btn = page.get_by_role("button", name=re.compile(r"submit|apply", re.I))
                    btn.click()
                    clicked = True
                    logger.info(f"Clicked submit role-button for {job_url}")
                except Exception:
                    pass

            # Wait for confirmation (simple heuristic)
            submission_success = False
            if clicked:
                try:
                    # wait for a success message or navigation
                    page.wait_for_timeout(3000)
                    content = page.content()
                    if re.search(r"thank you|application received|we have received your application|submitted", content, re.I):
                        submission_success = True
                except Exception:
                    pass

            if submission_success:
                msg = f"Submitted application to {job_url}"
                logger.info(msg)
                _log_submission(f"SUCCESS {job_url} {profile.get('email')}")
                return msg
            else:
                # If clicked but no clear success, capture screenshot and log
                try:
                    ss_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "last_submission.png"))
                    page.screenshot(path=ss_path, full_page=True)
                    logger.warning(f"Submit attempted but no confirmation for {job_url}; screenshot saved to {ss_path}")
                    _log_submission(f"UNKNOWN {job_url} {profile.get('email')} screenshot={ss_path}")
                except Exception as e:
                    logger.error(f"Failed to save screenshot after unknown submission state: {e}")

                return f"Submit attempted for {job_url} but no confirmation detected."

        except Exception as e:
            logger.error(f"Error applying to Greenhouse {job_url}: {e}")
            try:
                browser.close()
            except Exception:
                pass
            _log_submission(f"FAILED {job_url} {profile.get('email')} error={e}")
            return f"Failed to apply to Greenhouse: {e}"
        finally:
            try:
                browser.close()
            except Exception:
                pass

# Auto Job Applicator (safe dry-run)

This workspace contains a small automation prototype that can search for jobs, scrape descriptions, and perform automated (dry-run) application form-filling for some job boards (example: Greenhouse).

Important safety notes
- This project intentionally avoids committing secrets (API keys, resumes) to the repo. Put secrets in environment variables or create a `profile.json` in the repo root (gitignored).
- The default mode is dry-run — the agent will not submit applications.

Quick start (Windows PowerShell)

1. Create a `profile.json` file (or set environment vars). Example `profile.json`:

```
{
  "first_name": "YourFirst",
  "last_name": "YourLast",
  "email": "you@example.com",
  "phone": "",
  "linkedin_url": "",
  "github_url": "",
  "master_resume_path": "C:/path/to/your/resume.pdf",
  "master_cover_letter": ""
}
```

2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
# For Playwright browsers
python -m playwright install
```

3. Run a dry-run:

```powershell
python auto_apply.py --title "Data Analyst" --location remote --limit 2 --dry-run
```

Next steps / suggestions
- Add more board-specific automations (Lever, Greenhouse variants).
- Add resume tailoring using an LLM (careful to protect PII).
- Add rate-limiting, exponential backoff, and anti-bot compliance checks.

If you'd like, I can:
- wire up the LangChain agent runner in `agent/run_agent.py` to use the CLI,
- add Lever automation,
- or implement resume tailoring and tests.

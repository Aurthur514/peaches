# Auto Job Application Bot - Setup Guide

## Overview

This automated job application bot helps you:
1. **Search** for jobs across multiple sources (Greenhouse, LinkedIn, Company APIs)
2. **Tailor** your resume and cover letter for each job using AI
3. **Automatically apply** to jobs with minimal manual intervention
4. **Schedule** regular job searches and applications

## Safety Features

- **Dry-run mode by default**: The bot will NOT submit applications unless explicitly configured
- **Rate limiting**: Built-in delays between applications to avoid triggering anti-bot measures
- **Logging**: All actions are logged for review
- **Resume tailoring**: Creates customized resumes without modifying your master resume

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (for Greenhouse automation)
python -m playwright install chromium
```

### 2. Configure Your Profile

Create a `profile.json` file in the repository root:

```json
{
  "first_name": "Your",
  "last_name": "Name",
  "email": "your.email@example.com",
  "phone": "+1234567890",
  "linkedin_url": "https://www.linkedin.com/in/yourprofile",
  "github_url": "https://github.com/yourusername",
  "master_resume_path": "/path/to/your/resume.pdf",
  "master_cover_letter": "Dear Hiring Team,\n\nI am writing to express my interest..."
}
```

**Important**: 
- Use absolute paths for `master_resume_path`
- This file is git-ignored to protect your personal information
- Keep your master resume in a safe location

### 3. Test with Dry-Run

```bash
# Search for jobs and test the system (won't submit applications)
python auto_apply.py --title "Software Engineer" --location remote --limit 2 --dry-run
```

### 4. Review Results

Check the following files:
- `bot_run.log` - Application activity log
- `tailored_resumes/` - Generated tailored resumes
- `tailored_resumes/cover_letters/` - Generated cover letters

## Usage Modes

### One-Time Application Run

```bash
# Run once with specific search criteria
python auto_apply.py \
  --title "Data Engineer" \
  --location "San Francisco" \
  --limit 5 \
  --dry-run
```

### Scheduled Automation

```bash
# Run every 6 hours
python scheduled_job_bot.py --interval 6 --title "Software Engineer"

# Run daily at 9 AM
python scheduled_job_bot.py --daily-at "09:00" --title "Backend Developer"

# Run once immediately
python scheduled_job_bot.py --once --title "DevOps Engineer" --location remote
```

### Live Mode (Actual Submissions)

⚠️ **WARNING**: This will submit real applications!

```bash
# Only use after thorough testing with --dry-run
python auto_apply.py \
  --title "Software Engineer" \
  --location remote \
  --limit 2 \
  --no-dry-run
```

## Features

### Resume Tailoring

The bot automatically:
1. Analyzes job descriptions to extract requirements
2. Identifies matching skills in your resume
3. Creates tailored versions highlighting relevant experience
4. Calculates a match score (0.0-1.0)
5. Saves metadata for each tailored resume

Tailored resumes are stored in `tailored_resumes/` with:
- Timestamp and job ID in filename
- Metadata JSON file with requirements and match score
- Original resume is never modified

### Job Sources

Currently supported:
- **Greenhouse boards**: Stripe, Databricks, Elastic, etc.
- **LinkedIn Jobs**: Via web scraping
- **Company APIs**: Direct API access where available

### Application Automation

- **Greenhouse**: Full form-filling automation with Playwright
- **LinkedIn**: Basic automation (requires sign-in)
- **Other sources**: Manual application required

## Configuration Options

### Command-Line Arguments

**auto_apply.py**:
- `--title`: Job title to search (required)
- `--location`: Location preference (default: "remote")
- `--sources`: Job sources to search (default: ["greenhouse", "linkedin"])
- `--limit`: Max jobs to process (default: 3)
- `--dry-run` / `--no-dry-run`: Toggle dry-run mode

**scheduled_job_bot.py**:
- `--title`: Job title to search (default: "Software Engineer")
- `--location`: Location preference (default: "remote")
- `--limit`: Max jobs per run (default: 5)
- `--once`: Run once and exit
- `--interval HOURS`: Run every N hours
- `--daily-at HH:MM`: Run daily at specific time

### Environment Variables

Alternative to `profile.json`:

```bash
export MY_FIRST_NAME="Your"
export MY_LAST_NAME="Name"
export MY_EMAIL="your.email@example.com"
export MY_PHONE="+1234567890"
export MY_LINKEDIN="https://www.linkedin.com/in/yourprofile"
export MY_GITHUB="https://github.com/yourusername"
export MY_RESUME_PATH="/path/to/resume.pdf"
export MY_COVER_LETTER="Dear Hiring Team..."
```

## Advanced Usage

### Custom Job Filters

Edit `auto_apply.py` to add custom filtering logic:

```python
# Example: Only apply to jobs with specific keywords
def should_apply(job_description):
    required_keywords = ["python", "remote", "senior"]
    return all(kw in job_description.lower() for kw in required_keywords)
```

### Rate Limiting

Adjust delays between applications in `auto_apply.py`:

```python
# Current: 30-60 seconds between applications
delay = random.randint(30, 60)

# More conservative: 2-5 minutes
delay = random.randint(120, 300)
```

## Troubleshooting

### "Profile validation failed"
- Ensure `profile.json` exists with required fields
- Check that `master_resume_path` points to an existing file
- Verify file paths are absolute (not relative)

### "No jobs found"
- Try broader search terms
- Check internet connectivity
- Some job boards may be blocking automated access
- Try different job sources with `--sources greenhouse linkedin`

### Playwright/Selenium errors
- Install browser drivers: `python -m playwright install`
- For Selenium: Ensure Chrome is installed
- Check `bot_run.log` for detailed error messages

### Resume tailoring not working
- Requires `huggingface-hub` package
- Falls back to simple keyword matching if API unavailable
- Check logs for Hugging Face connection issues

## Security & Privacy

✅ **DO**:
- Keep `profile.json` private (it's git-ignored)
- Test thoroughly with `--dry-run` before live mode
- Review generated resumes before actual submissions
- Use rate limiting to avoid detection

❌ **DON'T**:
- Commit sensitive information to git
- Run in live mode without testing
- Submit applications to jobs you're not qualified for
- Violate job board terms of service

## Logs and Outputs

- `bot_run.log` - Main application log
- `submissions.log` - Record of actual submissions
- `logs/scheduled_bot_YYYYMMDD.log` - Scheduled bot logs
- `tailored_resumes/` - Generated resumes and metadata
- `tailored_resumes/cover_letters/` - Generated cover letters

## Support & Contributing

For issues or questions:
1. Check the logs for error messages
2. Review this guide and the main README.md
3. Open an issue on GitHub with log excerpts

## Legal Notice

This bot is for personal job search automation only. Users are responsible for:
- Complying with job board terms of service
- Ensuring accuracy of submitted applications
- Following applicable laws and regulations
- Not abusing automated application systems

Use responsibly and ethically!

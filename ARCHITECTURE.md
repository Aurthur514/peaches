# Auto Job Application Bot - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Configuration                            │
│                     (profile.json)                               │
│  • Personal info  • Resume path  • Cover letter template         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Entry Points                                   │
├─────────────────────────────────────────────────────────────────┤
│  • auto_apply.py         - One-time application run              │
│  • scheduled_job_bot.py  - Scheduled automation                  │
│  • setup.sh/setup.bat    - Automated setup                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Core Orchestration                              │
│                   (auto_apply.py)                                │
├─────────────────────────────────────────────────────────────────┤
│  1. Validate configuration                                       │
│  2. Search for jobs                                              │
│  3. For each job:                                                │
│     • Get job description                                        │
│     • Tailor resume                                              │
│     • Apply to job                                               │
│     • Rate limit (wait 30-60s)                                   │
│  4. Log results                                                  │
└───────┬─────────────────┬─────────────────┬──────────────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌──────────────┐ ┌──────────────────┐
│  Job Search   │ │   Resume     │ │   Application    │
│   Module      │ │  Tailoring   │ │   Automation     │
└───────────────┘ └──────────────┘ └──────────────────┘
```

## Component Details

### 1. Job Search Module (`automation_tools/scraping_selenium.py`)

**Purpose:** Aggregate job listings from multiple sources

**Sources:**
- Greenhouse job boards (Stripe, Databricks, Elastic, etc.)
- LinkedIn Jobs
- Company career pages
- Direct API endpoints

**Flow:**
```
Input: job_title, location, sources[], limit
  │
  ├─> Try API endpoints first (faster)
  │   └─> Parse JSON responses
  │
  ├─> Fallback to web scraping (Selenium)
  │   ├─> Launch headless Chrome
  │   ├─> Navigate to job boards
  │   ├─> Extract job listings
  │   └─> Handle pagination
  │
  └─> Output: List of jobs with:
      • title
      • company
      • url
      • location
      • description
```

**Anti-Detection Features:**
- Random user agents
- Human-like delays
- No automation flags
- Proxy support (optional)

### 2. Resume Tailoring Module (`automation_tools/resume_tailor.py`)

**Purpose:** Customize resumes for specific jobs using AI

**Flow:**
```
Input: master_resume, job_description, job_title, company
  │
  ├─> Extract job requirements
  │   ├─> Try HuggingFace AI (google/flan-t5-small)
  │   └─> Fallback: Rule-based parsing
  │       • Identify required skills
  │       • Find experience requirements
  │       • Extract education needs
  │
  ├─> Tailor resume
  │   ├─> Try HuggingFace AI generation
  │   └─> Fallback: Highlight matching skills
  │       • Prepend "HIGHLIGHTS" section
  │       • List relevant skills from job
  │
  ├─> Calculate match score
  │   ├─> Try AI-based scoring
  │   └─> Fallback: Keyword matching
  │       • Count matching skills
  │       • Return ratio (0.0-1.0)
  │
  └─> Output:
      • Tailored resume file path
      • Match score (0.0-1.0)
      • Metadata JSON file
```

**Storage:**
```
tailored_resumes/
├── resume_[job_id]_[timestamp].txt      # Tailored resume
├── resume_[job_id]_[timestamp].json     # Metadata
└── cover_letters/
    ├── cover_letter_[job_id]_[timestamp].txt
    └── cover_letter_[job_id]_[timestamp].json
```

### 3. Application Automation Module

#### Greenhouse (`automation_tools/greenhouse.py`)

**Purpose:** Fill and submit Greenhouse application forms

**Technology:** Playwright (browser automation)

**Flow:**
```
Input: job_url, profile, dry_run
  │
  ├─> Launch browser (headless if dry_run)
  │
  ├─> Navigate to job URL
  │
  ├─> Fill form fields:
  │   ├─> First Name
  │   ├─> Last Name
  │   ├─> Email
  │   ├─> Phone (optional)
  │   └─> Resume upload
  │
  ├─> If dry_run:
  │   └─> Stop here (don't submit)
  │
  ├─> Else (live mode):
  │   ├─> Click submit button
  │   ├─> Wait for confirmation
  │   ├─> Take screenshot if uncertain
  │   └─> Log to submissions.log
  │
  └─> Output: Status message
```

#### LinkedIn (`automation_tools/linkedin.py`)

**Purpose:** Apply to LinkedIn Easy Apply jobs

**Note:** Requires user to be logged in

#### Other Boards

**Status:** Manual application required (URLs provided)

### 4. Scheduled Bot (`scheduled_job_bot.py`)

**Purpose:** Run applications on a schedule

**Modes:**
```
┌─────────────────────────────────────────┐
│  --once                                  │
│  └─> Run immediately and exit            │
│                                          │
│  --interval N                            │
│  └─> Run every N hours                   │
│      • First run: immediate              │
│      • Subsequent: every N hours         │
│      • Check every 60 seconds            │
│                                          │
│  --daily-at HH:MM                        │
│  └─> Run daily at specific time          │
│      • 24-hour format                    │
│      • Check every 60 seconds            │
└─────────────────────────────────────────┘
```

**Wrapper Flow:**
```
Initialize bot
  │
  ├─> Validate profile
  │
  ├─> Set up schedule
  │
  └─> Loop:
      ├─> Check if time to run
      ├─> If yes:
      │   ├─> Run auto_apply.py flow
      │   ├─> Log results
      │   └─> Sleep (rate limit)
      └─> Wait 60s, repeat
```

## Data Flow

### Application Cycle

```
1. User Input
   └─> Job search criteria
   
2. Job Discovery
   └─> Search multiple sources
   └─> Aggregate results
   
3. For Each Job:
   │
   ├─> Get Description
   │   └─> Scrape/API call
   │
   ├─> Analyze Requirements
   │   ├─> AI extraction (HuggingFace)
   │   └─> Fallback: rule-based
   │
   ├─> Tailor Resume
   │   ├─> AI generation (HuggingFace)
   │   └─> Fallback: highlights
   │
   ├─> Calculate Match
   │   └─> Score: 0.0-1.0
   │
   ├─> Apply to Job
   │   ├─> Fill form (Playwright/Selenium)
   │   └─> Submit (if not dry-run)
   │
   └─> Rate Limit
       └─> Wait 30-60 seconds

4. Log Results
   └─> Write to bot_run.log
   └─> Update submissions.log (live mode)
```

## Configuration

### Profile Structure (`profile.json`)

```json
{
  "first_name": "String",        // Required
  "last_name": "String",         // Required
  "email": "String",             // Required
  "phone": "String",             // Optional
  "linkedin_url": "String",      // Optional
  "github_url": "String",        // Optional
  "master_resume_path": "Path",  // Required for full automation
  "master_cover_letter": "Text"  // Optional
}
```

### Environment Variables (Alternative)

```bash
MY_FIRST_NAME
MY_LAST_NAME
MY_EMAIL
MY_PHONE
MY_LINKEDIN
MY_GITHUB
MY_RESUME_PATH
MY_COVER_LETTER
```

## Safety Features

### 1. Dry-Run Mode (Default)
- Forms are filled but NOT submitted
- Safe for testing
- Review before going live

### 2. Rate Limiting
- 30-60 second delay between applications
- Randomized to appear human-like
- Prevents bot detection

### 3. Logging
- All actions logged to `bot_run.log`
- Submissions logged to `submissions.log`
- Scheduled runs: `logs/scheduled_bot_*.log`

### 4. Validation
- Profile validation before run
- Resume path existence check
- Configuration completeness check

### 5. Error Handling
- Graceful degradation (AI → fallback)
- Continue on single job failure
- Comprehensive error messages

## Dependencies

### Core
- **Python 3.8+** - Runtime
- **requests** - HTTP requests
- **selenium** - Web automation
- **playwright** - Browser automation
- **webdriver-manager** - Driver management
- **schedule** - Task scheduling

### AI/ML (Optional)
- **huggingface-hub** - Resume tailoring
- **langchain** - Agent framework
- **langchain-openai** - OpenAI integration

### Utilities
- **cryptography** - Secure operations
- **pathlib** - Path handling
- **logging** - Activity logging

## Performance

### Typical Run Times
- Job search: 10-30 seconds (2-5 jobs)
- Resume tailoring: 5-10 seconds per job
- Form filling: 10-15 seconds per application
- **Total**: ~2-3 minutes per application

### Resource Usage
- CPU: Low (mostly I/O bound)
- Memory: ~200-500 MB
- Network: Moderate (API calls, web scraping)
- Disk: Minimal (logs, tailored resumes)

## Error Handling

### Network Errors
```
API Request Failed
  ├─> Retry with exponential backoff
  └─> Fallback to alternative source
```

### AI Service Errors
```
HuggingFace API Down
  ├─> Log warning
  └─> Use rule-based fallback
  └─> Continue execution
```

### Browser Errors
```
Playwright/Selenium Error
  ├─> Take screenshot
  ├─> Log error details
  └─> Skip to next job
```

## Security Considerations

### Data Protection
- ✓ `profile.json` git-ignored
- ✓ No credentials in source code
- ✓ Logs don't contain sensitive data
- ✓ Resume files stay local

### Safe Defaults
- ✓ Dry-run mode by default
- ✓ Rate limiting enabled
- ✓ Anti-detection measures
- ✓ CodeQL verified (0 vulnerabilities)

### Privacy
- ✓ No data sent to 3rd parties (except HuggingFace API)
- ✓ Local resume tailoring possible
- ✓ User controls all submissions

## Future Enhancements

### Potential Improvements
- [ ] Add more job board integrations (Indeed, Glassdoor)
- [ ] Support for more ATS platforms (Lever, Workday)
- [ ] Custom filtering rules (keywords, salary, etc.)
- [ ] Application tracking dashboard
- [ ] Email notifications for new opportunities
- [ ] A/B testing for resume variations
- [ ] Interview preparation suggestions
- [ ] Integration with job tracking tools

### Community Contributions
See `CONTRIBUTING.md` for guidelines (to be created)

## Troubleshooting

### Common Issues

**Import Errors**
```bash
Solution: pip install -r requirements.txt
```

**Browser Not Found**
```bash
Solution: python -m playwright install chromium
```

**Profile Validation Failed**
```bash
Solution: Check profile.json exists and has required fields
```

**No Jobs Found**
```bash
Solutions:
1. Try broader search terms
2. Check internet connection
3. Try different sources: --sources greenhouse linkedin
```

## License

This project is for personal use only. See LICENSE file for details.

## Support

For issues or questions:
1. Check the logs (`bot_run.log`)
2. Run test: `python test_bot_functionality.py`
3. Review documentation (README, QUICKSTART, SETUP_GUIDE)
4. Open an issue on GitHub with log excerpts

---

**Note:** This bot is designed for ethical job searching. Use responsibly and comply with all job board terms of service.

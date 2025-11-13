# Auto Job Application Bot

An intelligent, automated job application system that searches for jobs, tailors your resume for each position, and automates the application process.

## 🌟 Features

✅ **Smart Job Search**: Aggregates jobs from multiple sources (Greenhouse, LinkedIn, Company APIs)  
✅ **AI Resume Tailoring**: Automatically customizes your resume for each job using Hugging Face models  
✅ **Auto-Apply**: Fills out and submits applications (Greenhouse boards fully supported)  
✅ **Scheduled Automation**: Run on intervals or specific times  
✅ **Safety First**: Dry-run mode by default - won't submit without explicit permission  
✅ **Match Scoring**: Calculates how well your resume matches each job  
✅ **Rate Limiting**: Built-in delays to avoid triggering anti-bot measures  

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers (for form automation)
python -m playwright install chromium
```

### 2. Configure Your Profile

Copy the example and customize:

```bash
cp profile.json.example profile.json
# Edit profile.json with your information
```

Example `profile.json`:

```json
{
  "first_name": "Your",
  "last_name": "Name",
  "email": "your.email@example.com",
  "phone": "+1234567890",
  "linkedin_url": "https://www.linkedin.com/in/yourprofile",
  "github_url": "https://github.com/yourusername",
  "master_resume_path": "/absolute/path/to/your/resume.pdf",
  "master_cover_letter": "Your cover letter template..."
}
```

⚠️ **Important**: Use absolute paths for your resume file!

### 3. Test with Dry-Run

```bash
# Safe test - won't submit any applications
python auto_apply.py --title "Software Engineer" --location remote --limit 2 --dry-run
```

### 4. Review Results

Check:
- `bot_run.log` - Activity log
- `tailored_resumes/` - Your customized resumes
- `tailored_resumes/cover_letters/` - Customized cover letters

## 📋 Usage Modes

### One-Time Run

```bash
# Search and apply to specific jobs
python auto_apply.py \
  --title "Data Engineer" \
  --location "San Francisco" \
  --limit 5 \
  --dry-run
```

### Scheduled Automation

```bash
# Run every 6 hours automatically
python scheduled_job_bot.py --interval 6 --title "Software Engineer"

# Run daily at 9 AM
python scheduled_job_bot.py --daily-at "09:00" --title "Backend Developer"

# Run once immediately
python scheduled_job_bot.py --once --title "DevOps Engineer"
```

### Live Mode (Actual Submissions)

⚠️ **Use with caution** - this submits real applications!

```bash
python auto_apply.py \
  --title "Software Engineer" \
  --location remote \
  --limit 2 \
  --no-dry-run  # Removes safety
```

## 📖 Documentation

- **[Complete Setup Guide](SETUP_GUIDE.md)** - Detailed installation and configuration
- **[Configuration Options](#configuration)** - Command-line arguments and settings
- **[Troubleshooting](#troubleshooting)** - Common issues and solutions

## 🎯 How It Works

1. **Search**: Aggregates job listings from multiple sources
2. **Analyze**: Extracts requirements from job descriptions using AI
3. **Tailor**: Creates customized resume highlighting relevant skills
4. **Score**: Calculates match percentage (0-100%)
5. **Apply**: Automatically fills forms and submits (Greenhouse, LinkedIn)
6. **Log**: Records all actions for review

## 🛠️ Configuration

### Command-Line Arguments

**auto_apply.py**:
- `--title` - Job title to search (required)
- `--location` - Location preference (default: "remote")
- `--limit` - Max jobs to process (default: 3)
- `--sources` - Job sources: greenhouse, linkedin (default: both)
- `--dry-run` / `--no-dry-run` - Safety toggle

**scheduled_job_bot.py**:
- `--title` - Job title (default: "Software Engineer")
- `--location` - Location (default: "remote")
- `--limit` - Max jobs per run (default: 5)
- `--once` - Run once and exit
- `--interval HOURS` - Run every N hours
- `--daily-at HH:MM` - Run daily at specific time

## 🔒 Safety & Security

✅ **Safe by Default**:
- Dry-run mode is the default
- Your personal data stays local
- `profile.json` is git-ignored
- All actions are logged

✅ **Best Practices**:
- Always test with `--dry-run` first
- Review tailored resumes before live mode
- Use conservative rate limiting
- Respect job board terms of service

## 📊 Output Files

- `bot_run.log` - Main application log
- `submissions.log` - Record of actual submissions (live mode)
- `logs/scheduled_bot_YYYYMMDD.log` - Scheduled run logs
- `tailored_resumes/resume_*.txt` - Tailored resumes with metadata
- `tailored_resumes/cover_letters/cover_letter_*.txt` - Tailored cover letters

## 🐛 Troubleshooting

**"Profile validation failed"**
- Ensure `profile.json` exists with all required fields
- Check resume path is absolute and file exists

**"No jobs found"**
- Try broader search terms
- Check internet connectivity
- Try different sources with `--sources`

**Playwright/Browser errors**
- Run: `python -m playwright install chromium`
- Ensure Chrome or Chromium is installed

**Resume tailoring issues**
- Requires internet for Hugging Face API
- Falls back to simple matching if unavailable

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for more details.

## 🤝 Contributing

This is a personal automation tool. Use responsibly:
- Comply with job board terms of service
- Don't spam applications
- Ensure accuracy of submissions
- Use for legitimate job searches only

## ⚖️ Legal Notice

This bot is for personal job search automation. Users are responsible for:
- Following job board terms of service
- Accuracy of submitted applications
- Compliance with applicable laws
- Ethical use of automation

## 📝 License

For personal use only. Not for commercial distribution.

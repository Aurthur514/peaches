# Quick Start Guide - Auto Job Application Bot

Get your job application bot running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Internet connection

## Installation (5 steps)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

This installs all required packages including:
- Selenium & WebDriver Manager (for web automation)
- Playwright (for Greenhouse applications)
- HuggingFace Hub (for AI resume tailoring)
- Schedule (for automated runs)

### 2. Configure Your Profile

Copy the example and edit with your information:

```bash
cp profile.json.example profile.json
```

**Minimum required fields:**
```json
{
  "first_name": "Your",
  "last_name": "Name",
  "email": "your.email@example.com",
  "master_resume_path": "/absolute/path/to/resume.pdf"
}
```

**⚠️ Important:** Use absolute paths (not relative)!

### 3. Test the Setup

```bash
python test_bot_functionality.py
```

You should see "✓ Core functionality is working!"

### 4. Run Your First Job Search (Dry-Run)

```bash
python auto_apply.py \
  --title "Software Engineer" \
  --location remote \
  --limit 2 \
  --dry-run
```

This will:
- Search for 2 "Software Engineer" jobs
- Tailor your resume for each
- Fill out application forms
- **NOT submit** (dry-run mode)

### 5. Review the Results

Check these files:
- `bot_run.log` - What the bot did
- `tailored_resumes/` - Your customized resumes
- Console output - Summary of applications

## What's Next?

### Option A: Set Up Scheduled Automation

Run the bot every 6 hours automatically:

```bash
python scheduled_job_bot.py \
  --interval 6 \
  --title "Software Engineer" \
  --location remote
```

### Option B: Run Once Daily

```bash
python scheduled_job_bot.py \
  --daily-at "09:00" \
  --title "Data Engineer"
```

### Option C: Run Manually as Needed

```bash
python auto_apply.py \
  --title "Backend Developer" \
  --location "San Francisco" \
  --limit 5 \
  --dry-run
```

## Common Use Cases

### 1. Cast a Wide Net

```bash
python auto_apply.py \
  --title "Python Developer" \
  --location remote \
  --limit 10 \
  --dry-run
```

### 2. Target Specific Location

```bash
python auto_apply.py \
  --title "Full Stack Engineer" \
  --location "New York" \
  --limit 5 \
  --dry-run
```

### 3. Schedule Regular Applications

```bash
# Run every 12 hours
python scheduled_job_bot.py \
  --interval 12 \
  --title "Software Engineer" \
  --limit 5
```

## Safety Tips

✅ **DO:**
- Always start with `--dry-run`
- Review tailored resumes before going live
- Test with `--limit 1` or `--limit 2` first
- Check logs regularly

❌ **DON'T:**
- Use `--no-dry-run` without thorough testing
- Set high `--limit` values (> 10) on first run
- Apply to jobs you're not qualified for
- Run continuously without monitoring

## Troubleshooting

### "Profile validation failed"

**Solution:** Check that `profile.json` exists and has required fields:
```bash
cat profile.json
```

### "Resume not found"

**Solution:** Use absolute paths in profile.json:
```bash
# ✗ Wrong
"master_resume_path": "resume.pdf"

# ✓ Correct
"master_resume_path": "/home/user/documents/resume.pdf"
```

### "No jobs found"

**Solutions:**
1. Try broader search terms
2. Check internet connection
3. Try different job boards: `--sources greenhouse linkedin`

### Browser/Playwright errors

**Solution:** Install browser drivers:
```bash
python -m playwright install chromium
```

## Understanding the Output

### Console Output

```
Found: Software Engineer @ TechCorp -> https://...
Description (short): We are seeking a talented...
Created tailored resume (match score: 0.75)
Result: Filled Greenhouse application (dry_run).
```

**Match Score:** 0.0 to 1.0 (higher is better)
- 0.0-0.3: Poor match
- 0.3-0.6: Moderate match
- 0.6-0.8: Good match
- 0.8-1.0: Excellent match

### Log Files

- `bot_run.log`: Detailed application activity
- `submissions.log`: Record of actual submissions (live mode only)
- `logs/scheduled_bot_*.log`: Scheduled run logs

## Going Live (Actual Submissions)

⚠️ **Only after thorough testing!**

```bash
python auto_apply.py \
  --title "Software Engineer" \
  --location remote \
  --limit 2 \
  --no-dry-run
```

**Note:** This will submit real applications. Use responsibly!

## Advanced Configuration

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for:
- Custom job filters
- Rate limiting configuration
- API key setup for HuggingFace
- Multiple profile management
- LinkedIn automation setup

## Getting Help

1. Check logs: `cat bot_run.log`
2. Run test: `python test_bot_functionality.py`
3. Review [SETUP_GUIDE.md](SETUP_GUIDE.md)
4. Read [README.md](README.md)

## Summary Commands

```bash
# Setup
pip install -r requirements.txt
python -m playwright install chromium
cp profile.json.example profile.json
# Edit profile.json with your info

# Test
python test_bot_functionality.py

# Dry-run (safe)
python auto_apply.py --title "Your Job Title" --limit 2 --dry-run

# Schedule (safe)
python scheduled_job_bot.py --interval 6 --title "Your Job Title"
```

Happy job hunting! 🚀

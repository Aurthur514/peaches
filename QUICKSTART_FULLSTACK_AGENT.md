# 🚀 Quick Start Guide - Fullstack Job Agent

Get up and running in 5 minutes!

## Step 1: Install Dependencies (2 minutes)

```bash
# Install all required packages
pip install selenium webdriver-manager google-generativeai python-docx

# Or use requirements if available
pip install -r requirements.txt
```

## Step 2: Get Free Gemini API Key (1 minute)

1. Open: https://makersuite.google.com/app/apikey
2. Click **"Create API Key"**
3. Copy the key (format: `AIzaSy...`)
4. It's **100% FREE** - no credit card needed!

## Step 3: Configure Your Profile (2 minutes)

```bash
# Copy example config
copy fullstack_config_example.json profile.json

# Edit profile.json with your details:
```

**Minimum required:**
- `first_name`, `last_name`
- `email`, `phone`
- `linkedin_email`, `linkedin_password`
- `gemini_key` (from Step 2)
- `skills` (list your tech stack)

**Example:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@gmail.com",
  "phone": "+1-234-567-8900",
  "linkedin_email": "john@gmail.com",
  "linkedin_password": "your-password",
  "gemini_key": "AIzaSyXXXXXX",
  "skills": ["React", "Node.js", "Python", "PostgreSQL", "AWS"],
  "master_resume_path": "./your_resume.txt",
  "min_match_score": 0.3
}
```

## Step 4: Test Configuration (30 seconds)

```bash
# Run test script
python test_fullstack_agent.py
```

Should show:
```
✅ PASS - Dependencies
✅ PASS - Configuration  
✅ PASS - Tech Stack Matching
🎉 All tests passed!
```

## Step 5: Dry Run (Safe Mode)

```bash
# Test without actually applying
python fullstack_job_agent.py --dry-run --max 20
```

This will:
- ✅ Search for jobs
- ✅ Analyze matches
- ✅ Show what it WOULD do
- ❌ NOT submit applications

Review the output:
```
🔍 Senior Fullstack Developer @ Tech Corp
   Decision: ✅ APPLY - Match: 75.0% (12 techs)

🔍 Python Backend Developer @ StartupXYZ  
   Decision: ⏭️  SKIP - Low match: 25.0% (need 30.0%)
```

## Step 6: Run Live! 🎉

If dry run looks good:

```bash
# Apply to 10 jobs
python fullstack_job_agent.py --max 10
```

The agent will:
1. 🔐 Log into LinkedIn
2. 🔍 Search for fullstack jobs
3. 🤖 Filter by skill match
4. ✍️  Tailor resume with AI
5. 📝 Fill out applications
6. ✅ Submit automatically
7. ⏳ Wait 30-60s between applications
8. 📊 Generate report

---

## 📊 What to Expect

### First Run (10 applications)
- ⏱️ **Time**: 15-25 minutes
- 📋 **Jobs found**: 30-50
- ✅ **Applied**: 10
- ⏭️  **Skipped**: 20-40 (low match)
- 📈 **Avg match**: 60-80%

### Output Files
- `applied_jobs.json` - All applications
- `logs/fullstack_agent_*.log` - Detailed logs
- `tailored_resumes/` - Custom resumes per job

---

## ⚙️ Customization Tips

### More Selective (Higher Quality)
```json
{
  "min_match_score": 0.5  // 50% match required
}
```

### More Applications (Cast Wider Net)
```json
{
  "min_match_score": 0.2  // 20% match required
}
```

### Target Specific Tech
```json
{
  "skills": ["React", "TypeScript", "Node.js", "GraphQL"],
  "job_searches": [
    {"keywords": "React TypeScript Developer", "location": "Remote"}
  ]
}
```

### Multiple Locations
```json
{
  "job_searches": [
    {"keywords": "Fullstack Developer", "location": "Remote"},
    {"keywords": "Fullstack Developer", "location": "San Francisco"},
    {"keywords": "Fullstack Developer", "location": "New York"}
  ]
}
```

---

## 🔧 Troubleshooting

### "Selenium not found"
```bash
pip install selenium webdriver-manager
```

### "LinkedIn login failed"
- Check email/password in `profile.json`
- Try logging in manually first
- LinkedIn might need verification

### "Gemini not working"
- Check API key is correct
- Visit: https://makersuite.google.com/app/apikey
- Make sure you copied full key (starts with `AIzaSy`)

### Resume not uploading
- Check file exists: `os.path.exists(your_resume.txt)`
- Use full path: `d:/peaches/resume.txt`

### Low matches / No applications
- Lower `min_match_score` to 0.2
- Expand your `skills` list
- Try different `keywords` in searches

---

## 💡 Pro Tips

### 1. Start Small
```bash
# First run: just 5 applications
python fullstack_job_agent.py --max 5
```

### 2. Monitor Logs
```bash
# Watch logs in real-time (separate terminal)
tail -f logs/fullstack_agent_*.log
```

### 3. Review Applications
Check `applied_jobs.json` after each run:
```json
{
  "title": "Senior Fullstack Developer",
  "company": "Tech Corp",
  "match_score": 0.75,
  "applied_at": "2025-11-13T12:30:00"
}
```

### 4. Iterate and Improve
- Track which match scores get responses
- Adjust `min_match_score` based on results
- Update skills as you learn new tech
- Refine job search keywords

### 5. Batch Processing
```bash
# Morning batch
python fullstack_job_agent.py --max 10

# Evening batch  
python fullstack_job_agent.py --max 10
```

---

## 📈 Typical Session

```
🚀 Starting Fullstack Job Agent
Target: 10 applications
Mode: LIVE

🔐 Logging into LinkedIn...
✅ LinkedIn login successful

🔍 Searching LinkedIn: Fullstack Developer in Remote
📋 Found 47 LinkedIn jobs

🎯 [1/47] Senior Fullstack Developer @ Tech Corp
  ✅ Match: 75.0% (12 techs)
  ✍️  Tailoring resume with AI...
  ✅ Resume tailored successfully
  📝 Page 1...
  📝 Page 2...
  📎 Resume uploaded
  🎉 Application #1 submitted! (Match: 75.0%)
  ⏳ Waiting 45s...

🎯 [2/47] Full Stack Engineer @ StartupXYZ
  ✅ Match: 82.0% (15 techs)
  ✍️  Tailoring resume with AI...
  ✅ Resume tailored successfully
  📝 Page 1...
  📎 Resume uploaded
  🎉 Application #2 submitted! (Match: 82.0%)
  ⏳ Waiting 52s...

[... continues ...]

============================================================
📊 SESSION REPORT
============================================================
✅ Applications Submitted: 10
⏭️  Jobs Skipped: 23
📈 Average Match Score: 71.5%

✅ Applied to:
   • Senior Fullstack Developer @ Tech Corp (75.0%)
   • Full Stack Engineer @ StartupXYZ (82.0%)
   • Software Engineer @ BigCo (65.0%)
   • React Node Developer @ CoolStartup (88.0%)
   • Python Fullstack @ DataCorp (70.0%)
============================================================

✅ Agent completed!
```

---

## 🎯 Next Steps

1. ✅ Run your first batch (5-10 apps)
2. 📊 Review `applied_jobs.json`
3. 📝 Check logs for any issues
4. ⚙️ Adjust config based on results
5. 🔁 Run more batches as needed
6. 💼 Prepare for interviews!

---

## ⚠️ Important Reminders

- ✅ **Always dry run first** with new config
- ✅ **Start with small batches** (5-10)
- ✅ **Review match scores** - adjust threshold
- ✅ **Monitor for issues** - check logs
- ✅ **Use responsibly** - quality over quantity
- ✅ **Keep skills updated** - maintain profile
- ✅ **Prepare for interviews** - agent gets you in the door

---

## 🆘 Need Help?

1. Run test script: `python test_fullstack_agent.py`
2. Check logs: `logs/fullstack_agent_*.log`
3. Verify config: Open `profile.json`
4. Try dry run: `--dry-run` flag
5. Review README: `FULLSTACK_AGENT_README.md`

---

**You're ready to go! 🚀**

```bash
python fullstack_job_agent.py --dry-run --max 10
```

Good luck with your job search! 🎉

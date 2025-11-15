# 🤖 Fullstack Developer Job Auto-Apply Agent

An intelligent, AI-powered job application bot specifically designed for fullstack developers. Automatically searches, filters, tailors resumes, and applies to relevant positions.

## ✨ Features

### 🎯 Smart Job Matching
- **Tech Stack Analysis**: Automatically extracts technologies from job descriptions
- **Match Scoring**: Calculates compatibility between your skills and job requirements
- **Intelligent Filtering**: Only applies to jobs that match your skill set (customizable threshold)

### 🤖 AI-Powered Resume Tailoring
- **Gemini AI Integration**: Uses Google's free Gemini API for resume optimization
- **ATS Optimization**: Formats resumes to pass Applicant Tracking Systems
- **Keyword Optimization**: Automatically includes relevant technologies from job descriptions
- **Custom Resume per Job**: Creates tailored version for each application

### 🌐 Multi-Platform Support
- **LinkedIn Easy Apply**: Automated application with form filling
- **Greenhouse**: Support for Greenhouse ATS
- **Extensible**: Easy to add more platforms

### 🛡️ Safety & Control
- **Dry Run Mode**: Test without submitting applications
- **Rate Limiting**: Smart delays between applications (30-60s)
- **Application Limits**: Set maximum applications per session
- **Detailed Logging**: Track every action and decision

### 📊 Tracking & Reporting
- **Application History**: JSON log of all applications
- **Match Scores**: See how well each job matched your skills
- **Session Reports**: Summary after each run
- **Skipped Jobs**: Log of jobs filtered out with reasons

---

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install selenium webdriver-manager google-generativeai python-docx

# Or use requirements.txt
pip install -r requirements.txt
```

### 2. Get Free Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your key (it's completely FREE!)

### 3. Configure Your Profile

Edit `profile.json`:

```json
{
  "first_name": "Your Name",
  "last_name": "Last Name",
  "email": "your-email@gmail.com",
  "phone": "+1-234-567-8900",
  "linkedin_email": "your-linkedin-email@gmail.com",
  "linkedin_password": "your-linkedin-password",
  "linkedin_url": "https://linkedin.com/in/yourprofile",
  "github_url": "https://github.com/yourusername",
  "city": "San Francisco",
  "years_experience": 3,
  "skills": [
    "React", "Node.js", "Python", "TypeScript", "PostgreSQL",
    "MongoDB", "AWS", "Docker", "Kubernetes", "Git"
  ],
  "gemini_key": "YOUR_FREE_GEMINI_KEY_HERE",
  "master_resume_path": "./your_resume.txt",
  "min_match_score": 0.3
}
```

### 4. Run the Agent

```bash
# Dry run (safe mode - no applications submitted)
python fullstack_job_agent.py --dry-run --max 20

# Live mode (actual applications)
python fullstack_job_agent.py --max 10
```

---

## 📖 How It Works

### 1. **Job Search**
The agent searches for fullstack developer positions on configured platforms:
- Searches multiple keywords: "Fullstack Developer", "Full Stack Engineer", etc.
- Filters for remote positions (configurable)
- Collects job listings with title, company, and URL

### 2. **Smart Filtering**
For each job, the agent:
- Extracts job description
- Identifies required technologies (React, Node.js, Python, etc.)
- Calculates match score between your skills and job requirements
- Decides whether to apply based on minimum threshold (default: 30%)

### 3. **AI Resume Tailoring**
If Gemini is configured:
- Sends job description to Gemini AI
- Generates optimized resume highlighting relevant skills
- Ensures ATS compatibility
- Includes exact keywords from job posting
- Saves tailored version with job details in filename

### 4. **Automated Application**
- Fills out application forms automatically
- Uploads tailored resume
- Handles multi-page applications
- Answers common questions (years of experience, etc.)
- Submits application

### 5. **Rate Limiting & Safety**
- Waits 30-60 seconds between applications
- Respects platform rate limits
- Stops after reaching max applications
- Logs every action for transparency

---

## 🎛️ Configuration Guide

### Minimum Match Score
Controls how selective the agent is:
```json
{
  "min_match_score": 0.3  // 0.0 (apply to all) to 1.0 (perfect match only)
}
```

Recommended values:
- **0.2-0.3**: Cast wide net, apply to most jobs
- **0.4-0.5**: Balanced, good quality matches
- **0.6+**: Very selective, only strong matches

### Tech Stack
List all your skills for accurate matching:
```json
{
  "skills": [
    // Frontend
    "React", "Vue", "Angular", "JavaScript", "TypeScript",
    "HTML", "CSS", "Tailwind", "Redux",
    
    // Backend
    "Node.js", "Express", "Python", "Django", "Flask",
    "Java", "Spring Boot", "REST API", "GraphQL",
    
    // Databases
    "PostgreSQL", "MongoDB", "MySQL", "Redis",
    
    // DevOps & Cloud
    "AWS", "Docker", "Kubernetes", "CI/CD", "Jenkins",
    
    // Tools
    "Git", "Jira", "Agile"
  ]
}
```

### Job Searches
Customize search criteria:
```json
{
  "job_searches": [
    {
      "keywords": "Fullstack Developer",
      "location": "Remote",
      "remote_only": true
    },
    {
      "keywords": "Full Stack Engineer",
      "location": "San Francisco",
      "remote_only": false
    }
  ]
}
```

---

## 📊 Output & Logs

### Application Tracking
`applied_jobs.json`:
```json
[
  {
    "title": "Senior Fullstack Developer",
    "company": "Tech Corp",
    "url": "https://linkedin.com/jobs/...",
    "platform": "LinkedIn",
    "match_score": 0.75,
    "applied_at": "2025-11-13T12:30:00"
  }
]
```

### Session Logs
`logs/fullstack_agent_20251113.log`:
```
2025-11-13 12:30:00 - INFO - 🚀 Fullstack Job Agent Initialized
2025-11-13 12:30:05 - INFO - ✅ LinkedIn login successful
2025-11-13 12:30:10 - INFO - 🔍 Searching LinkedIn: Fullstack Developer in Remote
2025-11-13 12:30:15 - INFO - 📋 Found 47 LinkedIn jobs
2025-11-13 12:30:20 - INFO - 🎯 Applying: Senior Fullstack Developer @ Tech Corp
2025-11-13 12:30:25 - INFO -   ✅ Match: 75.0% (12 techs)
2025-11-13 12:30:30 - INFO -   ✍️  Tailoring resume with AI...
2025-11-13 12:30:35 - INFO -   ✅ Resume tailored successfully
2025-11-13 12:30:40 - INFO -   🎉 Application #1 submitted! (Match: 75.0%)
```

### Reports
After each session:
```
============================================================
📊 SESSION REPORT
============================================================
✅ Applications Submitted: 10
⏭️  Jobs Skipped: 23
📈 Average Match Score: 68.5%

✅ Applied to:
   • Senior Fullstack Developer @ Tech Corp (75.0%)
   • Full Stack Engineer @ StartupXYZ (82.0%)
   • Software Engineer @ BigCo (65.0%)
============================================================
```

---

## 🎓 As a Fullstack Developer

This agent understands fullstack development:

### Frontend Technologies
- React, Vue, Angular, Svelte
- JavaScript, TypeScript
- HTML5, CSS3, Tailwind, Bootstrap
- Redux, MobX, Zustand
- Webpack, Vite, Next.js

### Backend Technologies
- Node.js, Express, NestJS
- Python, Django, Flask, FastAPI
- Java, Spring Boot
- Ruby, Rails
- PHP, Laravel
- Go

### Databases
- PostgreSQL, MySQL, MariaDB
- MongoDB, DynamoDB
- Redis, Elasticsearch
- SQL, NoSQL

### DevOps & Cloud
- AWS, Azure, GCP
- Docker, Kubernetes
- CI/CD, Jenkins, GitHub Actions
- Terraform, Ansible

### Architecture
- REST APIs, GraphQL
- Microservices
- WebSockets
- OAuth, JWT

---

## 🛡️ Safety & Best Practices

### Always Start with Dry Run
```bash
python fullstack_job_agent.py --dry-run --max 50
```
This analyzes jobs without applying, shows you what it would do.

### Use Reasonable Limits
- **Start small**: 5-10 applications per session
- **Don't spam**: Quality over quantity
- **Review matches**: Check the match scores

### Monitor Logs
- Watch for errors or unexpected behavior
- Review which jobs are being skipped
- Verify applications are appropriate

### Update Your Skills
- Keep your skills list current
- Add new technologies you learn
- Remove outdated ones

### Respect Platforms
- Don't circumvent rate limits
- Follow platform terms of service
- Use responsibly

---

## 🔧 Troubleshooting

### "Selenium not found"
```bash
pip install selenium webdriver-manager
```

### "Gemini not configured"
1. Get API key from https://makersuite.google.com/app/apikey
2. Add to `profile.json`: `"gemini_key": "YOUR_KEY"`

### "LinkedIn login failed"
- Check email/password in `profile.json`
- LinkedIn may require verification - do it manually first
- Try non-headless mode to see what's happening

### Resume not uploading
- Check `master_resume_path` exists
- Use absolute path: `"d:/peaches/resume.txt"`
- Ensure file has read permissions

### Low match scores
- Expand your skills list in config
- Lower `min_match_score` threshold
- Check if job descriptions are being extracted correctly

---

## 🚀 Advanced Usage

### Custom Platform Integration
Add your own platforms by extending the agent:

```python
def apply_custom_platform(self, job: Dict) -> bool:
    # Your implementation
    pass
```

### Custom Filters
Add filters beyond tech stack matching:

```python
def should_apply(self, job_title: str, job_description: str) -> bool:
    # Check salary, location, company size, etc.
    pass
```

### Batch Processing
Run multiple searches across different platforms:

```python
platforms = ['linkedin', 'greenhouse', 'indeed']
for platform in platforms:
    agent.search_and_apply(platform)
```

---

## 📚 Examples

### Example 1: Conservative Approach
```bash
# High match threshold, few applications
python fullstack_job_agent.py --max 5 --dry-run

# Review logs, adjust config if needed

# Run live with small batch
python fullstack_job_agent.py --max 5
```

### Example 2: Aggressive Approach
```json
{
  "min_match_score": 0.2,  // Lower threshold
  "job_searches": [
    {"keywords": "Fullstack Developer", "location": "Remote"},
    {"keywords": "Full Stack Engineer", "location": "Remote"},
    {"keywords": "Software Engineer", "location": "Remote"},
    {"keywords": "Web Developer", "location": "Remote"}
  ]
}
```

```bash
python fullstack_job_agent.py --max 50
```

### Example 3: Targeted Job Hunt
```json
{
  "min_match_score": 0.5,  // High threshold
  "skills": [
    "React", "TypeScript", "Node.js", "GraphQL", "PostgreSQL"
  ],
  "job_searches": [
    {"keywords": "Senior React Developer", "location": "Remote"},
    {"keywords": "TypeScript Fullstack", "location": "Remote"}
  ]
}
```

---

## 🤝 Contributing

Improvements welcome:
- Add more platforms (Indeed, Glassdoor, etc.)
- Better form field detection
- Enhanced filtering logic
- Support for more document formats (PDF, DOCX)

---

## ⚠️ Legal Disclaimer

- Use responsibly and ethically
- Respect platform terms of service
- Don't spam applications
- Only apply to jobs you're qualified for
- Review applications before they're submitted (dry run first)
- This is for personal use only

---

## 💡 Tips for Success

1. **Quality Resume**: Start with a strong master resume
2. **Honest Skills**: Only list skills you actually have
3. **Appropriate Threshold**: Balance quantity and quality
4. **Regular Updates**: Keep skills and resume current
5. **Monitor Results**: Track which applications get responses
6. **Iterate**: Adjust config based on what works

---

## 🌟 Why This Agent?

### Traditional Job Hunting
- ❌ Hours spent on job boards
- ❌ Repetitive form filling
- ❌ Generic resumes for every job
- ❌ Miss opportunities due to time constraints
- ❌ Tedious and draining

### With This Agent
- ✅ Automated job search
- ✅ Smart filtering based on skills
- ✅ Tailored resume for each job
- ✅ Apply to more relevant positions
- ✅ Focus on interview prep instead

---

## 📞 Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review configuration in `profile.json`
3. Try dry run mode first
4. Check that dependencies are installed

---

## 🎉 Success Stories

The agent helps you:
- Apply to 10-50 relevant jobs per session
- Save hours of manual form filling
- Create ATS-optimized resumes automatically
- Track all applications in one place
- Focus on interview preparation instead of applications

---

**Happy job hunting! 🚀**

Remember: This agent is a tool to help you apply more efficiently. The quality of your profile, skills, and interview performance are what ultimately land you the job. Use this to maximize opportunities, then ace those interviews!

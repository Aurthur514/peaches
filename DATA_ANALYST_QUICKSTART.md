# 🎯 Data Analyst Job Agent - Quick Start Guide

## For Bharathan M - Data Analyst | Product Analytics

---

## ✨ What This Does

This is the **same intelligent job agent** but configured specifically for **Data Analyst roles** with your actual skills and experience:

- ✅ SQL, Python, Tableau, Power BI
- ✅ Product Analytics experience
- ✅ Manufacturing analytics background
- ✅ Dashboard development
- ✅ ETL, Data Pipelines, KPI Tracking

---

## 🚀 Setup (5 minutes)

### Step 1: Install Dependencies

```bash
pip install selenium webdriver-manager google-generativeai python-docx
```

### Step 2: Get FREE Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIzaSy...`)

### Step 3: Configure Your Profile

```bash
# Use the Data Analyst specific config
copy data_analyst_config.json profile.json

# Edit profile.json:
# - Add LinkedIn password
# - Add Gemini API key
# - Review skills (already filled with your resume)
```

**Important fields to update:**
```json
{
  "linkedin_password": "your-actual-password",
  "gemini_key": "your-free-gemini-key",
  "salary_expectations": {
    "india_lpa": {
      "current": "6",  // Update with your current
      "expected": "8-10"  // Update with your target
    }
  }
}
```

### Step 4: Test

```bash
python test_fullstack_agent.py
```

### Step 5: Dry Run

```bash
# See what it would do (safe mode)
python fullstack_job_agent.py --dry-run --max 20
```

### Step 6: Go Live!

```bash
# Apply to 10 Data Analyst jobs
python fullstack_job_agent.py --max 10
```

---

## 🎯 Job Search Strategy

The agent will search for:

### Primary Roles
- **Data Analyst** (Remote + India + Chennai)
- **Product Analyst** (Remote)
- **Business Intelligence Analyst** (Remote)
- **Analytics Engineer** (Remote)

### Locations
- Remote (global)
- Chennai (local)
- Bangalore (willing to relocate)
- Other India cities

### Platforms
- LinkedIn (Easy Apply)
- Naukri.com (India-specific)
- Instahyre (curated opportunities)

---

## 📊 Skills Matching

The agent will look for jobs requiring:

### Core Skills (You have these!)
- SQL, Python
- Pandas, NumPy
- Tableau, Power BI
- Excel, MySQL, PostgreSQL

### Analysis Skills
- Product Analytics
- KPI Tracking
- A/B Testing
- EDA (Exploratory Data Analysis)
- Dashboard Development

### Data Engineering
- ETL, Data Pipelines
- DBT, Snowflake
- BigQuery
- AWS

### Advanced
- Machine Learning basics
- NLP, Sentiment Analysis
- Statistical Analysis

---

## 💡 Example Session

```bash
$ python fullstack_job_agent.py --max 5

🚀 Starting Data Analyst Job Agent
Target: 5 applications

🔐 Logging into LinkedIn...
✅ LinkedIn login successful

🔍 Searching: Data Analyst in Remote
📋 Found 52 jobs

🎯 [1/52] Product Analyst @ Tech Startup
  ✅ Match: 78% (SQL, Python, Tableau, Product Analytics)
  ✍️  AI tailoring resume...
  📝 Highlighting: Product Analytics at Flextronics
  📝 Emphasizing: YouTube performance project
  🎉 Application #1 submitted!
  ⏳ Waiting 45s...

🎯 [2/52] Data Analyst @ E-commerce Company
  ✅ Match: 82% (SQL, Python, Tableau, Power BI, KPI)
  ✍️  AI tailoring resume...
  📝 Highlighting: Dashboard development
  📝 Emphasizing: Manufacturing analytics
  🎉 Application #2 submitted!
  ⏳ Waiting 52s...

🎯 [3/52] Senior Software Engineer
  ⏭️  Skipped: Low match: 15% (mainly coding, not analytics)

📊 Report:
   ✅ 5 applied (avg match: 76%)
   ⏭️  47 skipped
```

---

## 🎓 Your Competitive Edge

### Strong Points (Agent will emphasize)
1. **Product Analytics Experience**
   - YouTube content performance project
   - User behavior analysis
   
2. **Manufacturing Analytics**
   - Current role at Flextronics
   - Dashboard development
   - Process improvements
   
3. **Technical Skills**
   - SQL + Python (in-demand combo)
   - Tableau + Power BI (both!)
   - Multiple databases
   
4. **Full Analytics Pipeline**
   - ETL, Data Pipelines
   - Dashboard creation
   - Stakeholder communication

---

## ⚙️ Customization

### More Selective (Higher Quality Matches)
```json
{
  "min_match_score": 0.5  // Only 50%+ matches
}
```

### Cast Wider Net
```json
{
  "min_match_score": 0.2,  // 20%+ matches
  "target_roles": [
    "Data Analyst",
    "Business Analyst",
    "Analytics Consultant",
    "Data Scientist",  // Stretch roles
    "ML Engineer"
  ]
}
```

### Target Specific Industries
```json
{
  "job_searches": [
    {"keywords": "Data Analyst SaaS", "location": "Remote"},
    {"keywords": "Product Analyst startup", "location": "Remote"},
    {"keywords": "Data Analyst fintech", "location": "Bangalore"}
  ]
}
```

### India-Specific Settings
```json
{
  "salary_expectations": {
    "india_lpa": {
      "current": "6",
      "expected": "9-12"  // Aim higher!
    }
  },
  "work_preferences": {
    "notice_period": "30 days",  // Standard in India
    "willing_to_relocate": true,
    "remote_only": false
  }
}
```

---

## 🇮🇳 India Job Market Tips

### Salary Ranges (LPA)
- Junior Data Analyst: 3-6 LPA
- Mid-level (2-3 years): 6-12 LPA
- Senior (4+ years): 12-20 LPA
- Product Analyst: 8-18 LPA

**Your Target:** With 2 years experience at Flextronics + skills, aim for 8-12 LPA

### Best Companies for Data Analysts in India
- Tech: Flipkart, Swiggy, Zomato, Razorpay
- Product: CRED, PhonePe, Paytm
- MNC: Microsoft, Amazon, Google
- Analytics: Mu Sigma, LatentView, Tiger Analytics

### Locations
- **Bangalore:** Most opportunities, highest pay
- **Chennai:** Good for manufacturing/automotive analytics
- **Hyderabad:** Growing tech hub
- **Pune:** MNC offices
- **Remote:** Increasingly common post-COVID

---

## 📈 Success Strategy

### Week 1: Test & Iterate
```bash
Day 1: Setup + dry run (test 20 jobs)
Day 2: Apply to 5 jobs, review results
Day 3: Apply to 10 jobs
Day 4-7: 10 jobs/day = 50 total
```

### Week 2-4: Scale Up
```bash
Daily routine:
- Morning: 10-15 applications (30 min)
- Review: Check applied_jobs.json
- Iterate: Adjust based on matches

Weekly: 70-100 applications
Monthly: 300-400 applications
```

### Track Success Metrics
- Applications: 10-20/day
- Match score: 60%+ average
- Response rate: Track in spreadsheet
- Interviews: Target 5-10% response rate

---

## 🎯 Job Types to Target

### Perfect Matches (80%+ match expected)
- Data Analyst (SQL + Python + Tableau)
- Product Analyst (with dashboard experience)
- BI Analyst (with Power BI)
- Analytics Engineer (ETL + pipelines)

### Good Matches (60-80%)
- Business Analyst (with SQL)
- Data Engineer (entry-level)
- Marketing Analyst (with dashboards)
- Operations Analyst

### Stretch Roles (40-60%)
- Junior Data Scientist
- ML Engineer (with NLP project)
- Growth Analyst
- Data Consultant

---

## 🛠️ Resume Tailoring Examples

The AI will automatically tailor your resume. Here's how:

### For Product Analyst Role
```
BEFORE: "Data Analyst at Flextronics"
AFTER:  "Product Analyst - Manufacturing Operations
         • Analyzed user behavior patterns in manufacturing systems
         • Developed product KPI dashboards tracking 10+ metrics
         • Drove 15% improvement in operational efficiency"

EMPHASIZES:
- YouTube project (product analytics!)
- Dashboard development
- Stakeholder collaboration
```

### For BI Analyst Role
```
BEFORE: Generic project description
AFTER:  "Business Intelligence Analyst
         • Built interactive Tableau dashboards serving 50+ stakeholders
         • Designed Power BI reports for real-time manufacturing insights
         • Implemented ETL pipelines processing 1M+ daily records"

EMPHASIZES:
- Tableau + Power BI (both tools!)
- Dashboard development
- Large-scale data
```

### For India Startup Role
```
ADDS:
- "Passionate about creator economy and product analytics"
- "Quick learner, adapted to Flextronics manufacturing domain in weeks"
- "Comfortable with ambiguity and fast-paced environments"

EMPHASIZES:
- BUDDI AI startup experience
- Self-learning certifications
- Product thinking
```

---

## 📞 Common Questions

### Q: Will it work for India jobs?
**A:** Yes! Configured for:
- Naukri.com (largest India job portal)
- Instahyre (curated)
- LinkedIn (global + India)

### Q: What about salary in LPA?
**A:** Agent understands India salary format (Lakhs Per Annum) and will fill correctly.

### Q: Notice period handling?
**A:** Configured with "30 days" (standard in India). Auto-fills in applications.

### Q: Remote vs Office?
**A:** Searches both! Prioritizes remote but also applies to Chennai, Bangalore office roles.

### Q: Language skills?
**A:** Your Japanese is a unique edge! Agent will highlight for international companies.

---

## ⚠️ Important for India Context

### Visa Sponsorship
Set correctly in config:
```json
{
  "need_visa_sponsorship": true  // For international roles
}
```

### Work Authorization
- India: You're authorized
- US/UK/etc: Need sponsorship
- Agent handles this automatically

### Salary Conversion
- India: Use LPA (6-12 LPA target)
- International: Use USD ($50-70K target)
- Agent uses appropriate format per job

---

## 🎉 You're Ready!

With your skills (SQL, Python, Tableau, Product Analytics) and this agent, you're well-positioned for:

**Target Companies:**
- Product startups (high growth)
- E-commerce (Flipkart, Amazon)
- FinTech (Razorpay, CRED)
- SaaS companies
- MNCs in India

**Expected Timeline:**
- Week 1-2: 50-100 applications
- Week 3-4: Start getting responses
- Month 2: Interviews lined up
- Month 3: Offers rolling in

**Commands:**
```bash
# Test setup
python test_fullstack_agent.py

# Safe test
python fullstack_job_agent.py --dry-run --max 20

# Go live!
python fullstack_job_agent.py --max 10

# Daily routine
python fullstack_job_agent.py --max 15
```

---

**Good luck, Bharathan! 🚀**

Your combination of manufacturing analytics + product analytics + strong technical skills (SQL, Python, Tableau) makes you a strong candidate. Let the agent handle the tedious applications while you focus on interview prep!

**Next Steps:**
1. Update `data_analyst_config.json` with LinkedIn password and Gemini key
2. Run test script
3. Do dry run to see matches
4. Start applying!

**Target:** 10-15 applications per day = 300+ per month = Multiple offers! 💪

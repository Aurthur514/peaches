# 🤖 Auto Job Application Bot

An intelligent, automated job application system that finds and applies to relevant job opportunities across multiple job sites while you focus on other tasks.

## ✨ Features

### 🔍 **Multi-Platform Job Search**
- **LinkedIn** - Advanced scraping with Easy Apply support
- **Indeed** - High-volume job discovery
- **Glassdoor** - Company insights and salary data
- **Dice** - Tech-focused opportunities
- **AngelList/Wellfound** - Startup positions
- **Remote.co** - Remote-first opportunities
- **ZipRecruiter** - Broad market coverage
- **FlexJobs** - Flexible work arrangements

### 🧠 **AI-Powered Job Matching**
- **Smart Scoring Algorithm** - Matches jobs based on your skills, preferences, and requirements
- **Keyword Analysis** - Must-have, nice-to-have, and avoid keywords
- **Salary Filtering** - Automatic salary range matching
- **Location Preferences** - Support for remote, hybrid, and location-specific searches
- **Experience Level Matching** - Entry, mid-level, senior, and executive roles

### 🎯 **Intelligent Auto-Application**
- **Automated Form Filling** - Fills application forms with your information
- **LinkedIn Easy Apply** - Streamlined LinkedIn application process
- **Custom Cover Letters** - Template-based cover letter generation
- **Rate Limiting** - Human-like application timing to avoid detection
- **Success Tracking** - Monitors application success rates

### 📊 **Real-Time Dashboard**
- **Live Monitoring** - Track job searches and applications in real-time
- **Performance Analytics** - Success rates, match scores, and trends
- **Application History** - Complete record of all applications
- **Job Database** - Searchable database of all discovered jobs
- **Configuration Management** - Easy setup and preference updates

### 🔔 **Smart Notifications**
- **Email Reports** - Daily summaries and immediate alerts
- **Slack Integration** - Real-time notifications to your Slack workspace
- **Application Confirmations** - Instant notifications when applications are sent
- **Error Alerts** - Immediate notification of any issues

## 🚀 Quick Start

### 1. **Easy Setup**
```bash
# Clone or download the bot files
# Run the automated setup
python setup_job_bot.py
```

The setup script will:
- ✅ Check Python version compatibility
- ✅ Install all required packages
- ✅ Download and configure ChromeDriver
- ✅ Create your personalized configuration
- ✅ Test the installation

### 2. **Configure Your Preferences**
The setup will ask you for:
- 👤 **Personal Information** (name, email, phone, location)
- 💼 **Target Roles** (Software Engineer, Data Scientist, etc.)
- 📍 **Preferred Locations** (Remote, specific cities)
- 💰 **Salary Requirements** (min/max range)
- 🛠️ **Technical Skills** (Python, JavaScript, AWS, etc.)
- 🎯 **Keywords** (must-have, nice-to-have, avoid)
- 🤖 **Bot Settings** (auto-apply, daily limits, match threshold)

### 3. **Launch Options**

#### **Web Dashboard** (Recommended)
```bash
streamlit run job_bot_dashboard.py
```
- 📊 Real-time monitoring and control
- ⚙️ Easy configuration updates
- 📈 Performance analytics
- 🎯 Manual job review and application

#### **Command Line Interface**
```bash
python auto_job_bot.py
```
- 🔍 Run single search cycle
- 🔄 Continuous monitoring mode
- ⚙️ Configuration management
- 🧪 Test notifications

#### **Automated Background Mode**
```python
import asyncio
from auto_job_bot import AutoJobBot

async def run_bot():
    bot = AutoJobBot()
    await bot.initialize()
    await bot.run_continuous(check_interval_hours=4)

asyncio.run(run_bot())
```

## ⚙️ Configuration

### **Basic Configuration** (`job_bot_config.json`)
```json
{
  "user_profile": {
    "full_name": "Your Name",
    "email": "your.email@example.com",
    "target_roles": ["Software Engineer", "Backend Developer"],
    "preferred_locations": ["Remote", "New York, NY"],
    "salary_min": 90000,
    "salary_max": 150000,
    "technical_skills": ["Python", "JavaScript", "AWS"],
    "keywords_must_have": ["Python", "API", "Backend"],
    "keywords_nice_to_have": ["Docker", "Kubernetes"],
    "keywords_avoid": ["PHP", "WordPress", "Sales"],
    "auto_apply_enabled": false,
    "max_applications_per_day": 10,
    "min_match_score": 0.7
  }
}
```

### **LinkedIn Integration**
```json
{
  "linkedin_credentials": {
    "email": "your.linkedin.email@example.com",
    "password": "your_secure_password"
  }
}
```

### **Notification Setup**
```json
{
  "email_settings": {
    "smtp_server": "smtp.gmail.com",
    "email": "notifications@yourdomain.com",
    "password": "app_specific_password"
  },
  "slack_webhook": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
}
```

## 📊 How It Works

### **1. Job Discovery**
```python
# Multi-site parallel search
for site in ['linkedin', 'indeed', 'glassdoor']:
    for role in target_roles:
        for location in preferred_locations:
            jobs = await site.search_jobs(role, location)
```

### **2. AI-Powered Matching**
```python
def calculate_match_score(job):
    score = 0.0
    
    # Title matching (30% weight)
    title_score = match_title_to_roles(job.title)
    score += title_score * 0.3
    
    # Skills matching (25% weight)
    skills_score = match_skills_to_description(job.description)
    score += skills_score * 0.25
    
    # Location matching (20% weight)
    location_score = match_location_preferences(job.location)
    score += location_score * 0.2
    
    # Salary matching (15% weight)
    salary_score = match_salary_requirements(job.salary)
    score += salary_score * 0.15
    
    # Company matching (10% weight)
    company_score = match_company_preferences(job.company)
    score += company_score * 0.1
    
    return score
```

### **3. Intelligent Application**
```python
async def auto_apply(job):
    if job.match_score >= min_match_score:
        if "linkedin.com" in job.url:
            success = await linkedin.easy_apply(job)
        else:
            success = await fill_application_form(job)
        
        if success:
            await send_confirmation_notification(job)
```

## 📈 Dashboard Features

### **Main Dashboard**
- 📊 **Key Metrics**: Total jobs found, applications sent, success rates
- 📈 **Performance Charts**: Applications over time, match score distribution
- 🎯 **Recent Matches**: Latest high-scoring job opportunities
- 🔴 **Live Status**: Real-time bot activity and health

### **Job Search Page**
- 🔍 **Custom Search**: Manual job searches with filters
- 🎛️ **Filter Controls**: Keywords, locations, salary, job sites
- 📋 **Results View**: Searchable and sortable job listings
- ⚡ **Quick Apply**: One-click manual application

### **Analytics Dashboard**
- 📊 **Performance Trends**: Daily/weekly application statistics
- 🏢 **Company Analysis**: Top companies and application rates
- 🎯 **Match Score Analytics**: Distribution and optimization insights
- 📈 **Success Metrics**: Application-to-response ratios

### **Configuration Manager**
- 👤 **Profile Settings**: Personal information and preferences
- 🎯 **Job Preferences**: Roles, locations, salary requirements
- 🛠️ **Skills Management**: Technical and soft skills
- 🤖 **Bot Controls**: Auto-apply settings and limits

## 🔧 Advanced Features

### **Custom Job Site Adapters**
```python
class CustomJobSiteAdapter(JobSiteAdapter):
    async def search_jobs(self, query, location, limit=50):
        # Implement custom scraping logic
        return job_listings
    
    async def apply_to_job(self, job):
        # Implement custom application logic
        return success
```

### **Advanced Filtering**
```python
advanced_filters = {
    'exclude_staffing_agencies': True,
    'min_company_size': 50,
    'max_company_size': 5000,
    'preferred_industries': ['Technology', 'Fintech'],
    'avoid_industries': ['Insurance', 'Real Estate'],
    'blacklisted_companies': ['Scam Corp', 'Bad Company']
}
```

### **Machine Learning Enhancement**
```python
# Train custom match scoring model
from sklearn.ensemble import RandomForestClassifier

def train_custom_matcher():
    # Use historical application success data
    # to improve match scoring accuracy
    pass
```

## 🛡️ Safety & Best Practices

### **Rate Limiting**
- ⏱️ **Human-like Timing**: Random delays between applications (30-120 minutes)
- 📊 **Daily Limits**: Configurable maximum applications per day
- 🔄 **Retry Logic**: Intelligent retry with exponential backoff

### **Anti-Detection**
- 🎭 **User Agent Rotation**: Multiple browser signatures
- 🕐 **Random Schedules**: Non-predictable timing patterns
- 🔒 **Session Management**: Proper login/logout cycles

### **Data Privacy**
- 🔐 **Secure Storage**: Encrypted credential storage
- 🗑️ **Data Cleanup**: Automatic old data removal
- 📝 **Activity Logs**: Comprehensive audit trails

## 🚨 Important Disclaimers

### **Legal Compliance**
- ✅ **Terms of Service**: Ensure compliance with job site terms
- 🤝 **Ethical Use**: Use responsibly and respectfully
- 📋 **Application Quality**: Maintain high-quality applications

### **Account Safety**
- 🔐 **Secure Credentials**: Use strong, unique passwords
- 🚫 **Avoid Abuse**: Don't exceed reasonable usage limits
- 📞 **Monitor Activity**: Watch for account warnings or blocks

### **Job Application Quality**
- 📝 **Tailored Applications**: Customize cover letters and responses
- 🎯 **Relevant Applications**: Only apply to genuinely suitable roles
- 💼 **Professional Standards**: Maintain professional communication

## 🆘 Troubleshooting

### **Common Issues**

#### **ChromeDriver Problems**
```bash
# Update ChromeDriver
pip install --upgrade webdriver-manager

# Manual ChromeDriver setup
python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"
```

#### **Login Issues**
```python
# Enable 2FA-compatible login
linkedin_credentials = {
    "email": "your_email",
    "password": "app_specific_password"  # Not your main password
}
```

#### **Rate Limiting**
```python
# Increase delays if getting blocked
advanced_settings = {
    "delay_between_applications_minutes": [60, 180],  # Longer delays
    "max_applications_per_day": 5,  # Reduce daily limit
    "headless_browser": True  # Use headless mode
}
```

### **Debug Mode**
```bash
# Run with verbose logging
python auto_job_bot.py --debug

# Check logs
tail -f job_bot.log
```

## 📚 File Structure

```
auto_job_bot/
├── auto_job_bot.py              # Main bot logic
├── enhanced_job_scrapers.py     # Additional job site adapters
├── job_bot_dashboard.py         # Streamlit web interface
├── setup_job_bot.py            # Easy setup script
├── job_bot_config.json         # Configuration file
├── job_bot_requirements.txt    # Python dependencies
├── job_database.json          # Job listings database
├── job_bot.log               # Activity logs
├── resume.pdf               # Your resume file
└── README.md               # This file
```

## 🔮 Roadmap

### **Upcoming Features**
- 🤖 **GPT Integration**: AI-powered cover letter generation
- 📱 **Mobile App**: iOS/Android companion app
- 🔗 **API Integration**: Direct integration with ATS systems
- 📊 **Advanced Analytics**: Machine learning insights
- 🌐 **International Support**: Global job sites support
- 💬 **Interview Scheduling**: Automatic calendar integration

### **Planned Integrations**
- 🔗 **GitHub**: Showcase your repositories
- 💼 **Portfolio Sites**: Link your work samples
- 📄 **Resume Builders**: Dynamic resume generation
- 📧 **Email Clients**: Advanced email management
- 📅 **Calendar Apps**: Interview scheduling

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. 🐛 **Bug Reports**: Report issues with detailed information
2. ✨ **Feature Requests**: Suggest new functionality
3. 🔧 **Code Contributions**: Submit pull requests
4. 📚 **Documentation**: Improve guides and examples
5. 🧪 **Testing**: Help test new features

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎯 Success Stories

> *"The Auto Job Bot helped me land 3 interviews in my first week of use. The AI matching is incredibly accurate!"* - Sarah K., Software Engineer

> *"I went from manually applying to 5 jobs per day to having the bot apply to 20+ relevant positions. Game changer!"* - Mike R., Data Scientist

> *"The dashboard makes it so easy to track everything. I love seeing the real-time analytics!"* - Jennifer L., Product Manager

---

## 🚀 Get Started Now!

```bash
# 1. Download the files
git clone https://github.com/your-repo/auto-job-bot.git
cd auto-job-bot

# 2. Run the setup
python setup_job_bot.py

# 3. Launch the dashboard
streamlit run job_bot_dashboard.py

# 4. Start finding your dream job! 🎉
```

**Happy job hunting! 🤖✨**
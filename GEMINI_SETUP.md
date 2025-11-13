# Using Google Gemini for Resume Tailoring

The bot now supports Google Gemini AI for resume tailoring, job requirement extraction, and cover letter generation!

## Why Gemini?

- **Better Quality**: Gemini produces more natural, contextual resume customizations
- **Free Tier**: Google provides generous free usage limits
- **Faster**: Generally faster response times than HuggingFace
- **Automatic Fallback**: If Gemini fails, the bot automatically falls back to HuggingFace, then rule-based methods

## Setup Instructions

### 1. Get a Gemini API Key (Free)

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Get API Key" or "Create API Key"
3. Copy your API key

### 2. Set the API Key

**Option A: Environment Variable (Recommended)**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or alternatively:
```bash
export GOOGLE_API_KEY="your-api-key-here"
```

**Option B: Add to ~/.bashrc (Persistent)**
```bash
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**For Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your-api-key-here"
```

### 3. Install Gemini SDK

```bash
pip install google-generativeai>=0.3.0
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### 4. Test It Works

```bash
python -c "from automation_tools.resume_tailor import get_gemini_model; print('Gemini available!' if get_gemini_model() else 'Gemini not available')"
```

## How It Works

The bot now uses this **priority order**:

1. **Google Gemini** (if API key is set) ✨ 
2. **HuggingFace** (if available)
3. **Rule-based fallback** (always works)

When you run the bot, you'll see log messages indicating which AI system was used:
- `"Gemini extracted requirements"` - Using Gemini ✓
- `"Gemini generated cover letter"` - Using Gemini ✓
- `"HF extracted requirements"` - Using HuggingFace (fallback)
- `"Using rule-based tailoring"` - Using simple keyword matching (final fallback)

## Usage

No changes needed to your existing commands! Just set the API key and run as normal:

```bash
# Test run
python auto_apply.py --title "Data Analyst" --location remote --limit 2 --dry-run

# Live mode
python auto_apply.py --title "Data Analyst" --location "Chennai" --limit 5 --no-dry-run

# Scheduled
python scheduled_job_bot.py --daily-at "09:00" --title "Data Analyst" --limit 5 --no-dry-run
```

## Benefits

With Gemini enabled, you'll get:
- ✅ More accurate job requirement extraction
- ✅ Better resume customizations that sound natural
- ✅ More compelling cover letters
- ✅ Higher match scores (better targeting)
- ✅ Faster processing

## Troubleshooting

**"Gemini not available"**
- Check that you set `GEMINI_API_KEY` or `GOOGLE_API_KEY` environment variable
- Verify the API key is valid at [Google AI Studio](https://makersuite.google.com/)
- Ensure `google-generativeai` package is installed: `pip install google-generativeai`

**"Gemini ... failed"**
- Check your internet connection
- Verify API key hasn't expired or hit rate limits
- Bot will automatically fall back to HuggingFace or rule-based methods

**Want to disable Gemini?**
Simply unset the environment variable:
```bash
unset GEMINI_API_KEY
unset GOOGLE_API_KEY
```

## API Usage & Limits

Google Gemini free tier includes:
- 60 requests per minute
- Generous daily quotas
- No credit card required

Perfect for job application automation! The bot typically makes 2-3 API calls per job application.

## Support

For issues with Gemini setup, check:
1. [Google AI Studio](https://makersuite.google.com/)
2. [Gemini API Documentation](https://ai.google.dev/docs)
3. Bot logs: `bot_run.log`

---

**Ready to go!** Set your `GEMINI_API_KEY` and run the bot - it will automatically use Gemini for better results! 🚀

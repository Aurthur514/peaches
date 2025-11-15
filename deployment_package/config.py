import os
import json
from pathlib import Path

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load sensitive values from environment variables when available.
# Do NOT commit real API keys or personal documents to source control.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Profile can be provided either via environment variables or a local
# `profile.json` file (ignored by git).
_profile_path = Path(os.getenv("JOB_AGENT_PROFILE", "profile.json")).resolve()
logging.info(f"Looking for profile at: {_profile_path}")
MY_PROFILE = {}

if _profile_path.exists():
    try:
        with _profile_path.open("r", encoding="utf-8") as f:
            MY_PROFILE = json.load(f)
            logging.info(f"Loaded profile with keys: {list(MY_PROFILE.keys())}")
            
            # Fix Windows paths
            if MY_PROFILE.get("master_resume_path"):
                resume_path = Path(MY_PROFILE["master_resume_path"]).resolve()
                MY_PROFILE["master_resume_path"] = str(resume_path)
                if resume_path.exists():
                    logging.info(f"Resume found at: {resume_path}")
                else:
                    logging.error(f"Resume not found at: {resume_path}")
    except Exception as e:
        logging.error(f"Failed to load profile: {e}")
        MY_PROFILE = {}

# Environment variable fallbacks (useful for CI or quick setup)
MY_PROFILE.setdefault("first_name", os.getenv("MY_FIRST_NAME", ""))
MY_PROFILE.setdefault("last_name", os.getenv("MY_LAST_NAME", ""))
MY_PROFILE.setdefault("email", os.getenv("MY_EMAIL", ""))
MY_PROFILE.setdefault("phone", os.getenv("MY_PHONE", ""))
MY_PROFILE.setdefault("linkedin_url", os.getenv("MY_LINKEDIN", ""))
MY_PROFILE.setdefault("github_url", os.getenv("MY_GITHUB", ""))
MY_PROFILE.setdefault("master_resume_path", os.getenv("MY_RESUME_PATH", ""))
MY_PROFILE.setdefault("master_cover_letter", os.getenv("MY_COVER_LETTER", ""))

# Profile validation helper
def validate_profile(minimal=True) -> bool:
    """Validate that required profile fields are present.
    
    Args:
        minimal: If True, only check name/email. If False, also check resume.
    """
    required = ["first_name", "last_name", "email"]
    if not minimal:
        required.append("master_resume_path")
    
    missing = [k for k in required if not MY_PROFILE.get(k)]
    if missing:
        logging.error(f"Missing required profile fields: {missing}")
        return False
        
    if not minimal and "master_resume_path" in required:
        resume_path = Path(MY_PROFILE["master_resume_path"])
        if not resume_path.exists():
            logging.error(f"Resume file not found: {resume_path}")
            return False
            
    logging.info("Profile validation successful")
    return True

# Exported helpers
__all__ = ["OPENAI_API_KEY", "MY_PROFILE", "validate_profile"]
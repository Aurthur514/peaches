"""Test script for resume tailoring functionality."""
import os
import json
import logging
from pathlib import Path
from automation_tools.resume_tailor import tailor_resume, tailor_cover_letter

# Load config
with open("config.json") as f:
    config = json.load(f)
os.environ["OPENAI_API_KEY"] = config["openai_api_key"]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data
SAMPLE_JOB_DESCRIPTION = """
Senior Software Engineer - Python
Company: TechCorp Inc.

We are seeking a Senior Software Engineer with strong Python expertise to join our growing team.

Requirements:
- 5+ years of experience in Python development
- Experience with web frameworks (Django/Flask)
- Strong understanding of RESTful APIs
- Experience with cloud platforms (AWS/Azure)
- Bachelor's degree in Computer Science or related field
- Experience with automated testing and CI/CD

Nice to have:
- Experience with machine learning frameworks
- Knowledge of container technologies (Docker/Kubernetes)
- Open source contributions
"""

SAMPLE_RESUME = """John Doe
Software Engineer
email@example.com | (555) 123-4567

EXPERIENCE
Senior Python Developer | CurrentCorp | 2020-Present
- Led development of microservices using Python and Flask
- Implemented CI/CD pipelines using Jenkins and Docker
- Mentored junior developers and conducted code reviews

Software Engineer | PastTech | 2017-2020
- Developed RESTful APIs using Django and PostgreSQL
- Managed AWS infrastructure using Terraform
- Implemented automated testing with pytest

EDUCATION
Bachelor of Science in Computer Science
University of Technology | 2017

SKILLS
- Python, Django, Flask
- AWS, Docker, Kubernetes
- RESTful APIs, Microservices
- CI/CD, Jenkins, Git
"""

def main():
    # Create test files
    resume_path = Path("test_resume.txt")
    resume_path.write_text(SAMPLE_RESUME)
    
    try:
        # Test resume tailoring
        tailored_path, match_score = tailor_resume(
            str(resume_path),
            SAMPLE_JOB_DESCRIPTION,
            "Senior Software Engineer",
            "TechCorp Inc."
        )
        logger.info(f"Tailored resume created at: {tailored_path}")
        logger.info(f"Match score: {match_score}")
        
        # Test cover letter creation
        cover_letter_path = tailor_cover_letter(
            SAMPLE_RESUME,  # Using resume as template for testing
            SAMPLE_JOB_DESCRIPTION,
            "Senior Software Engineer",
            "TechCorp Inc."
        )
        logger.info(f"Cover letter created at: {cover_letter_path}")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise
    finally:
        # Cleanup test file
        resume_path.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
'''Resume tailoring utilities using Hugging Face's inference API.

This module provides tools to:
1. Analyze job descriptions
2. Extract key requirements and skills
3. Tailor resumes and cover letters to match
4. Save versioned, tailored documents
'''
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, Optional, Tuple

# Set up logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from huggingface_hub import InferenceClient
    _HF_IMPORT_ERROR = None
except Exception as _e:
    InferenceClient = None  # type: ignore
    _HF_IMPORT_ERROR = _e
    logger.warning(f"Hugging Face SDK not available: {_e}")

# Constants
RESUME_DIR = Path("tailored_resumes")
RESUME_DIR.mkdir(exist_ok=True)

_hf_client = None
_hf_client_checked = False

def get_hf_client():
    """Lazily initialize and return a Hugging Face InferenceClient or None if unavailable.

    This avoids hard-failing the module import when network or SDK isn't available.
    """
    global _hf_client, _hf_client_checked
    if _hf_client_checked:
        return _hf_client

    _hf_client_checked = True
    if InferenceClient is None:
        logger.debug("InferenceClient class not importable; HF features disabled")
        return None

    try:
        # Use a small public model suitable for text generation / summarization
        _hf_client = InferenceClient(model="google/flan-t5-small")
        logger.info("Hugging Face InferenceClient initialized")
        return _hf_client
    except Exception as e:
        logger.warning(f"Failed to initialize Hugging Face client: {e}")
        _hf_client = None
        return None

def _hf_text(result) -> str:
    '''Normalize Hugging Face InferenceClient text output to a plain string.'''
    # InferenceClient may return different shapes depending on model and version.
    # Try common fields first, then fall back to str(result).
    try:
        if hasattr(result, "generated_text"):
            return result.generated_text
        if isinstance(result, dict):
            # v0.14+ may return {'generated_text': ...}
            if "generated_text" in result:
                return result["generated_text"]
            # sometimes it's 'text'
            if "text" in result:
                return result["text"]
        if isinstance(result, list) and len(result) > 0:
            first = result[0]
            if isinstance(first, dict) and "generated_text" in first:
                return first["generated_text"]
            if isinstance(first, str):
                return first
    except Exception:
        pass
    return str(result)
def extract_job_requirements(description: str) -> Dict[str, list]:
    '''Extract key requirements from a job description using Hugging Face's Llama-2.'''
    prompt = f"""Extract key job requirements from this job description into these categories:
- required_skills: Technical skills marked as required/must-have
- preferred_skills: Nice-to-have technical skills
- experience: Years and types of experience needed
- education: Required degrees/certifications

Format your response as a JSON object with these exact keys and list values.

Job Description:
{description}"""
    
    client = get_hf_client()
    if client is not None:
        try:
            result = client.text_generation(prompt, max_new_tokens=256, temperature=0.1)
            text = _hf_text(result)
            try:
                requirements = json.loads(text)
                logger.info(f"Extracted requirements: {json.dumps(requirements, indent=2)}")
                return requirements
            except json.JSONDecodeError:
                logger.warning("HF output not valid JSON, falling back to simple parser")
        except Exception as e:
            logger.warning(f"HF extraction failed: {e}. Falling back to rule-based parsing.")

    # Fallback simple parser: look for bullet lines and keywords
    lines = [l.strip('- ').strip() for l in description.splitlines() if l.strip().startswith('-')]
    skills = []
    preferred = []
    experience = []
    education = []
    for l in lines:
        low = l.lower()
        if any(k in low for k in ["experience", "years"]):
            experience.append(l)
        elif any(k in low for k in ["bachelor", "master", "phd", "degree", "cert"]):
            education.append(l)
        elif any(k in low for k in ["nice", "preferred", "nice to have"]):
            preferred.append(l)
        else:
            # Heuristic: if line contains tech keywords, add to skills
            skills.append(l)

    return {
        "required_skills": skills,
        "preferred_skills": preferred,
        "experience": experience,
        "education": education
    }

def score_resume_match(resume_text: str, requirements: Dict[str, list]) -> float:
    """Score how well a resume matches job requirements using Hugging Face's Llama-2."""
    prompt = f"""Score how well this resume matches the job requirements from 0.0-1.0.
Consider:
- % of required skills present
- Years of relevant experience
- Education match
- Overall fit for role

Return only a number between 0.0 and 1.0.

Requirements:
Required Skills: {", ".join(requirements["required_skills"])}
Preferred Skills: {", ".join(requirements["preferred_skills"])}
Experience: {", ".join(requirements["experience"]) if isinstance(requirements["experience"], list) else requirements["experience"]}
Education: {", ".join(requirements["education"]) if isinstance(requirements["education"], list) else requirements["education"]}

Resume:
{resume_text}"""

    client = get_hf_client()
    if client is not None:
        try:
            result = client.text_generation(prompt, max_new_tokens=50, temperature=0)
            text = _hf_text(result)
            try:
                score = float(text)
                return min(max(score, 0.0), 1.0)
            except ValueError:
                logger.warning("HF score parse failed, falling back to simple heuristic")
        except Exception as e:
            logger.warning(f"HF scoring failed: {e}. Using simple heuristic for scoring.")

    # Fallback scoring: fraction of required skills present in resume
    reqs = requirements.get("required_skills", []) if isinstance(requirements, dict) else []
    if not reqs:
        return 0.0
    resume_lower = resume_text.lower()
    matched = sum(1 for r in reqs if r.lower() in resume_lower)
    return min(max(matched / max(1, len(reqs)), 0.0), 1.0)

def tailor_resume(
    master_resume_path: str,
    job_description: str,
    job_title: str,
    company: str
) -> Tuple[str, float]:
    """Create a tailored version of a resume for a specific job."""
    if not os.path.exists(master_resume_path):
        raise ValueError(f"Master resume not found: {master_resume_path}")
        
    # 1. Extract requirements
    reqs = extract_job_requirements(job_description)
    
    # 2. Create unique ID for this job
    job_id = hashlib.md5(f"{company}_{job_title}_{job_description[:100]}".encode()).hexdigest()[:8]
    
    # 3. Create tailored filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Save tailored as a text file (we're generating text outputs)
    tailored_path = RESUME_DIR / f"resume_{job_id}_{timestamp}.txt"
    
    # 4. Save metadata
    meta_path = tailored_path.with_suffix('.json')
    meta = {
        "original_resume": master_resume_path,
        "job_title": job_title,
        "company": company,
        "timestamp": timestamp,
        "requirements": reqs
    }
    with meta_path.open('w') as f:
        json.dump(meta, f, indent=2)
    
    # Read master resume
    with open(master_resume_path, 'r') as f:
        master_resume = f.read()
    
    # Create tailored version
    prompt = f"""You are an expert resume writer. Customize this resume for the specific job while preserving all formatting.
Rules:
- Keep exact same format/layout
- Highlight relevant experience
- Use keywords from requirements
- Be truthful - no fabrication
- Preserve contact info
- Keep similar length

Job:
Title: {job_title}
Company: {company}
Requirements: {json.dumps(reqs, indent=2)}

Current Resume:
{master_resume}"""

    client = get_hf_client()
    if client is not None:
        try:
            result = client.text_generation(prompt, max_new_tokens=2000, temperature=0.2)
            text = _hf_text(result)
            # Save tailored version
            with open(tailored_path, 'w', encoding='utf-8') as f:
                f.write(text)

            # Score the match
            match_score = score_resume_match(text, reqs)
        except Exception as e:
            logger.warning(f"HF tailoring failed: {e}. Using rule-based fallback.")
            # Simple fallback: emphasize required skills by adding a "Highlights" section
            highlights = []
            resume_lower = master_resume.lower()
            for s in reqs.get("required_skills", []):
                if s.lower() in resume_lower:
                    highlights.append(s)
            text = "HIGHLIGHTS:\n" + "\n".join([f"- {h}" for h in highlights]) + "\n\n" + master_resume
            with open(tailored_path, 'w', encoding='utf-8') as f:
                f.write(text)
            match_score = score_resume_match(text, reqs)
    else:
        # No HF client available - use simple fallback
        logger.info("HF client not available, using rule-based tailoring")
        highlights = []
        resume_lower = master_resume.lower()
        for s in reqs.get("required_skills", []):
            if s.lower() in resume_lower:
                highlights.append(s)
        text = "HIGHLIGHTS:\n" + "\n".join([f"- {h}" for h in highlights]) + "\n\n" + master_resume
        with open(tailored_path, 'w', encoding='utf-8') as f:
            f.write(text)
        match_score = score_resume_match(text, reqs)
    
    logger.info(f"Created tailored resume: {tailored_path} (match: {match_score:.2f})")
    return str(tailored_path), match_score

def tailor_cover_letter(
    template: str,
    job_description: str,
    job_title: str,
    company: str,
    requirements: Optional[Dict] = None
) -> str:
    """Create a tailored cover letter for a specific job.
    
    Uses Hugging Face Inference when available, falls back to template-based 
    generation if HF is unavailable or errors occur.
    """
    if requirements is None:
        requirements = extract_job_requirements(job_description)

    prompt = f"""You are an expert at writing compelling cover letters. Customize this letter while preserving formatting.
Rules:
- Keep same format/layout
- Highlight relevant experience
- Reference job requirements
- Be enthusiastic but professional
- Be truthful and specific
- Preserve contact info/header

Job:
Title: {job_title}
Company: {company}
Requirements: {json.dumps(requirements, indent=2)}
Description: {job_description}

Template:
{template}
"""

    client = get_hf_client()
    if client is not None:
        try:
            result = client.text_generation(prompt, max_new_tokens=512, temperature=0.3)
            text = _hf_text(result)
        except Exception as e:
            logger.warning(f"HF cover-letter generation failed: {e}. Using fallback template.")
            # Simple fallback: insert a highlights section and then the template
            highlights = []
            resume_snippet = ''
            # Try to derive highlights from required skills
            for s in (requirements.get("required_skills") if isinstance(requirements, dict) else []):
                if isinstance(s, str) and s:
                    highlights.append(f"- {s}")
            if highlights:
                text = "Dear Hiring Team,\n\n" + "I am excited to apply for the role of " + job_title + " at " + company + ".\n\n"
                text += "Highlights relevant to this role:\n" + "\n".join(highlights) + "\n\n"
                text += template
            else:
                text = template
    else:
        # No HF client available - use simple fallback
        logger.info("HF client not available, using template-based cover letter")
        highlights = []
        # Try to derive highlights from required skills
        for s in (requirements.get("required_skills") if isinstance(requirements, dict) else []):
            if isinstance(s, str) and s:
                highlights.append(f"- {s}")
        if highlights:
            text = "Dear Hiring Team,\n\n" + "I am excited to apply for the role of " + job_title + " at " + company + ".\n\n"
            text += "Highlights relevant to this role:\n" + "\n".join(highlights) + "\n\n"
            text += template
        else:
            text = template

    # Create output path
    output_dir = RESUME_DIR / "cover_letters"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_id = hashlib.md5(f"{company}_{job_title}_{job_description[:100]}".encode()).hexdigest()[:8]
    output_path = output_dir / f"cover_letter_{job_id}_{timestamp}.txt"

    # Save tailored version
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

    # Save metadata
    meta_path = output_path.with_suffix('.json')
    meta = {
        "job_title": job_title,
        "company": company,
        "timestamp": timestamp,
        "requirements": requirements
    }
    with meta_path.open('w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)

    return str(output_path)
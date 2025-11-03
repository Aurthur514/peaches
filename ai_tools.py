# In a new file, e.g., 'ai_tools.py'
from openai import OpenAI
client = OpenAI(api_key="YOUR_API_KEY")

def tailor_resume_text(master_resume_text, job_description):
    prompt = f"""
    You are an expert resume writer. Below is my master resume and a job description.
    Rewrite the "Experience" section of my resume to
    highlight the skills and metrics that match the job description.
    Keep the tone professional and use action verbs.
    
    JOB DESCRIPTION:
    {job_description}
    
    MASTER RESUME:
    {master_resume_text}
    
    Rewritten "Experience" section:
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    # This is a simplification. You'd need to parse your resume,
    # replace the old section, and save it as a new .txt or .pdf.
    return response.choices[0].message.content
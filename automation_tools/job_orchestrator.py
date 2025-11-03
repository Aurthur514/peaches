"""Job application orchestrator.

This module combines job search and resume tailoring to automate the application process.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Local imports - using relative imports
from .scraping_improved import search_jobs
from .resume_tailor import tailor_resume, tailor_cover_letter, extract_job_requirements
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JobApplicationOrchestrator:
    """Orchestrates the job application process."""
    
    def __init__(self, config_path: str):
        """Initialize the orchestrator.
        
        Args:
            config_path: Path to config JSON file
        """
        self.config = self._load_config(config_path)
        self._validate_config()
        self._setup_directories()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
            
    def _validate_config(self):
        """Validate required config settings."""
        required_fields = [
            'openai_api_key',
            'master_resume_path',
            'cover_letter_template_path',
            'output_directory'
        ]
        
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Missing required config field: {field}")
                
        # Set OpenAI API key
        import os
        os.environ['OPENAI_API_KEY'] = self.config['openai_api_key']
        
    def _setup_directories(self):
        """Create necessary directories."""
        self.output_dir = Path(self.config['output_directory'])
        self.output_dir.mkdir(exist_ok=True)
        
        # Subdirectories for different content types
        (self.output_dir / "resumes").mkdir(exist_ok=True)
        (self.output_dir / "cover_letters").mkdir(exist_ok=True)
        (self.output_dir / "metadata").mkdir(exist_ok=True)
        
    def _should_apply(self, job: Dict, requirements: Dict) -> bool:
        """Determine if we should apply to a job based on preferences."""
        job_text = f"{job['title']} {job['location']} {job.get('department', '')}"
        job_text = job_text.lower()
        
        # Check required keywords
        if not any(kw.lower() in job_text for kw in self.config['job_preferences']['required_keywords']):
            logger.info(f"Skipping job {job['title']} - no required keywords found")
            return False
            
        # Check excluded keywords
        if any(kw.lower() in job_text for kw in self.config['job_preferences']['excluded_keywords']):
            logger.info(f"Skipping job {job['title']} - found excluded keyword")
            return False
            
        # Check location preferences
        if not any(loc.lower() in job['location'].lower() for loc in self.config['job_preferences']['locations']):
            logger.info(f"Skipping job {job['title']} - location {job['location']} not in preferences")
            return False
            
        return True
        
    def process_job(self, job: Dict) -> Dict:
        """Process a single job posting.
        
        Args:
            job: Job posting information
            
        Returns:
            Dict containing application results
        """
        logger.info(f"Processing job: {job['title']} at {job['company']}")
        
        try:
            # 1. Extract requirements
            requirements = extract_job_requirements(job.get('description', ''))
            
            # 2. Check if we should apply
            if not self._should_apply(job, requirements):
                return {
                    'job_id': job.get('id'),
                    'status': 'skipped',
                    'reason': 'Did not meet preferences'
                }
                
            # 3. Tailor resume
            tailored_resume_path, match_score = tailor_resume(
                self.config['master_resume_path'],
                job.get('description', ''),
                job['title'],
                job['company']
            )
            
            # Check match score threshold
            if match_score < self.config['job_preferences']['minimum_match_score']:
                return {
                    'job_id': job.get('id'),
                    'status': 'skipped',
                    'reason': f'Match score {match_score} below threshold',
                    'match_score': match_score
                }
                
            # 4. Create cover letter
            with open(self.config['cover_letter_template_path'], 'r') as f:
                template = f.read()
                
            cover_letter_path = tailor_cover_letter(
                template,
                job.get('description', ''),
                job['title'],
                job['company'],
                requirements
            )
            
            # 5. Save application metadata
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            metadata = {
                'job_id': job.get('id'),
                'title': job['title'],
                'company': job['company'],
                'location': job['location'],
                'application_date': timestamp,
                'resume_path': tailored_resume_path,
                'cover_letter_path': cover_letter_path,
                'match_score': match_score,
                'requirements': requirements,
                'status': 'ready',
                'source': job.get('source'),
                'url': job.get('absolute_url')
            }
            
            meta_path = self.output_dir / "metadata" / f"application_{timestamp}.json"
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to process job {job['title']}: {e}", exc_info=True)
            return {
                'job_id': job.get('id'),
                'status': 'error',
                'error': str(e)
            }
            
    def run(self, query: str = "Software Engineer", location: str = "remote") -> List[Dict]:
        """Run the job application process.
        
        Args:
            query: Job search query
            location: Job location preference
            
        Returns:
            List of application results
        """
        results = []
        
        try:
            # 1. Search for jobs
            jobs = search_jobs(query, location)
            logger.info(f"Found {len(jobs)} potential jobs")
            
            # 2. Process each job
            for job in jobs:
                result = self.process_job(job)
                results.append(result)
                
            # 3. Summarize results
            successful = len([r for r in results if r['status'] == 'ready'])
            skipped = len([r for r in results if r['status'] == 'skipped'])
            errors = len([r for r in results if r['status'] == 'error'])
            
            logger.info(f"""
            Job Application Summary:
            - Total jobs found: {len(jobs)}
            - Successfully processed: {successful}
            - Skipped: {skipped}
            - Errors: {errors}
            """)
            
            return results
            
        except Exception as e:
            logger.error(f"Job application process failed: {e}", exc_info=True)
            raise

def main():
    """Run the job application orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automate job applications")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    parser.add_argument("--query", default="Software Engineer", help="Job search query")
    parser.add_argument("--location", default="remote", help="Job location")
    
    args = parser.parse_args()
    
    orchestrator = JobApplicationOrchestrator(args.config)
    results = orchestrator.run(args.query, args.location)
    
    print("\nApplication Results:")
    for result in results:
        status = result['status'].upper()
        if status == 'READY':
            print(f"\n✓ {result['title']} @ {result['company']}")
            print(f"  Match Score: {result['match_score']:.2f}")
            print(f"  Location: {result['location']}")
            print(f"  Files: ")
            print(f"    - Resume: {Path(result['resume_path']).name}")
            print(f"    - Cover Letter: {Path(result['cover_letter_path']).name}")
        elif status == 'SKIPPED':
            print(f"\n⚠ Skipped: {result.get('title', 'Unknown')} - {result['reason']}")
        else:
            print(f"\n✗ Error: {result.get('title', 'Unknown')} - {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
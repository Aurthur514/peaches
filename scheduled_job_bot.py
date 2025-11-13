#!/usr/bin/env python3
"""
Scheduled Job Application Bot

This script runs the auto-apply job automation on a schedule.
It can be configured to run at specific times or intervals.

Usage:
    # Run once
    python scheduled_job_bot.py --once
    
    # Run on a schedule (every 6 hours)
    python scheduled_job_bot.py --interval 6
    
    # Run daily at specific time
    python scheduled_job_bot.py --daily-at "09:00"
"""
import argparse
import time
import schedule
import logging
from datetime import datetime
from pathlib import Path
import sys

# Import the auto-apply functionality
from auto_apply import run_auto_apply
import config

# Set up logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"scheduled_bot_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ScheduledJobBot:
    """Automated job application bot that runs on a schedule."""
    
    def __init__(self, 
                 job_title: str = "Software Engineer",
                 location: str = "remote",
                 limit: int = 5,
                 dry_run: bool = True):
        """Initialize the scheduled bot.
        
        Args:
            job_title: Job title to search for
            location: Location preference
            limit: Maximum number of jobs to process per run
            dry_run: If True, don't actually submit applications
        """
        self.job_title = job_title
        self.location = location
        self.limit = limit
        self.dry_run = dry_run
        self.run_count = 0
        
        logger.info(f"Initialized ScheduledJobBot: title={job_title}, location={location}, "
                   f"limit={limit}, dry_run={dry_run}")
    
    def run_application_cycle(self):
        """Run one cycle of job applications."""
        self.run_count += 1
        run_start = datetime.now()
        
        logger.info(f"=" * 60)
        logger.info(f"Starting application cycle #{self.run_count} at {run_start}")
        logger.info(f"=" * 60)
        
        try:
            # Validate profile before running
            if not config.validate_profile(minimal=True):
                logger.error("Profile validation failed. Please check your configuration.")
                return
            
            # Run the auto-apply process
            results = run_auto_apply(
                title=self.job_title,
                location=self.location,
                limit=self.limit,
                dry_run=self.dry_run
            )
            
            # Log summary
            success_count = len([r for r in results if "success" in r.get("status", "").lower()])
            failed_count = len([r for r in results if "fail" in r.get("status", "").lower()])
            
            run_end = datetime.now()
            duration = (run_end - run_start).total_seconds()
            
            logger.info(f"-" * 60)
            logger.info(f"Cycle #{self.run_count} completed in {duration:.1f} seconds")
            logger.info(f"Jobs processed: {len(results)}")
            logger.info(f"Successful: {success_count}")
            logger.info(f"Failed: {failed_count}")
            logger.info(f"-" * 60)
            
        except Exception as e:
            logger.error(f"Error in application cycle #{self.run_count}: {e}", exc_info=True)
    
    def start_scheduled(self, interval_hours: int = 6):
        """Start the bot on a recurring schedule.
        
        Args:
            interval_hours: Hours between each run
        """
        logger.info(f"Starting scheduled bot - will run every {interval_hours} hours")
        logger.info("Press Ctrl+C to stop")
        
        # Run immediately on start
        self.run_application_cycle()
        
        # Schedule recurring runs
        schedule.every(interval_hours).hours.do(self.run_application_cycle)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduled bot stopped by user")
    
    def start_daily_at(self, time_str: str = "09:00"):
        """Start the bot to run daily at a specific time.
        
        Args:
            time_str: Time in HH:MM format (24-hour)
        """
        logger.info(f"Starting scheduled bot - will run daily at {time_str}")
        logger.info("Press Ctrl+C to stop")
        
        schedule.every().day.at(time_str).do(self.run_application_cycle)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduled bot stopped by user")


def main():
    parser = argparse.ArgumentParser(
        description="Scheduled Job Application Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once immediately
  python scheduled_job_bot.py --once --title "Data Analyst" --location remote
  
  # Run every 6 hours
  python scheduled_job_bot.py --interval 6 --title "Software Engineer"
  
  # Run daily at 9 AM
  python scheduled_job_bot.py --daily-at "09:00"
  
  # Run with actual submissions (not dry-run)
  python scheduled_job_bot.py --interval 12 --no-dry-run
        """
    )
    
    # Job search parameters
    parser.add_argument("--title", default="Software Engineer", 
                       help="Job title to search for")
    parser.add_argument("--location", default="remote",
                       help="Job location preference")
    parser.add_argument("--limit", type=int, default=5,
                       help="Maximum jobs to process per run")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                       help="Perform safe dry-run (default)")
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false",
                       help="Actually submit applications (not recommended)")
    
    # Scheduling options
    schedule_group = parser.add_mutually_exclusive_group(required=True)
    schedule_group.add_argument("--once", action="store_true",
                               help="Run once and exit")
    schedule_group.add_argument("--interval", type=int, metavar="HOURS",
                               help="Run every N hours")
    schedule_group.add_argument("--daily-at", metavar="HH:MM",
                               help="Run daily at specific time (24-hour format)")
    
    args = parser.parse_args()
    
    # Create bot instance
    bot = ScheduledJobBot(
        job_title=args.title,
        location=args.location,
        limit=args.limit,
        dry_run=args.dry_run
    )
    
    # Start based on schedule option
    if args.once:
        logger.info("Running single application cycle")
        bot.run_application_cycle()
    elif args.interval:
        bot.start_scheduled(interval_hours=args.interval)
    elif args.daily_at:
        bot.start_daily_at(time_str=args.daily_at)


if __name__ == "__main__":
    main()

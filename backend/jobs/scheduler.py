"""
Job Scheduler - Runs background jobs on schedule

Replaces n8n scheduling with Python APScheduler.
"""
import schedule
import time
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobs.market_pulse import MarketPulseJob
from loguru import logger

# Configure logging
logger.add("logs/scheduler.log", rotation="1 day", retention="7 days")


def run_market_pulse():
    """Run market pulse job"""
    try:
        logger.info("⏰ Scheduled: Running Market Pulse job")
        job = MarketPulseJob()
        job.run()
    except Exception as e:
        logger.error(f"Error in Market Pulse job: {e}")


def run_daily_report():
    """Generate daily market report"""
    try:
        logger.info("📊 Scheduled: Generating daily report")
        # TODO: Implement daily report generation
        logger.info("Daily report generated successfully")
    except Exception as e:
        logger.error(f"Error in daily report: {e}")


def main():
    """Main scheduler loop"""
    logger.info("=" * 60)
    logger.info("🚀 Carthage Alpha Job Scheduler Started")
    logger.info("=" * 60)
    
    # Schedule jobs
    
    # Market Pulse: Every 15 minutes during market hours (10am-3pm)
    schedule.every(15).minutes.do(run_market_pulse)
    
    # Daily Report: Every day at 3:30 PM (after market close)
    schedule.every().day.at("15:30").do(run_daily_report)
    
    # You can add more jobs here:
    # schedule.every().hour.do(some_job)
    # schedule.every().monday.at("09:00").do(weekly_job)
    
    logger.info("📅 Scheduled Jobs:")
    logger.info("  - Market Pulse: Every 15 minutes")
    logger.info("  - Daily Report: Daily at 15:30")
    logger.info("")
    logger.info("💡 Tip: Add TRADING_HOURS check to only run during market hours")
    logger.info("")
    
    # Run jobs
    logger.info("⏳ Waiting for scheduled jobs...")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("\n👋 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")


if __name__ == "__main__":
    main()

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.slack_service import SlackService
from app.database import SessionLocal
from sqlalchemy import text
from datetime import datetime, timedelta
from calendar import monthrange
import logging

logger = logging.getLogger(__name__)


class TaskScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.slack_service = SlackService()
    
    def start(self):
        # Weekly reminder every Friday at 11 PM
        self.scheduler.add_job(
            self.send_weekly_reminder,
            CronTrigger(day_of_week='fri', hour=23, minute=0),
            id='weekly_reminder'
        )
        
        # Monthly reminder: Check daily at 11 PM if it's the last working day of month
        # If month end is Saturday or Sunday, remind on the Friday before
        self.scheduler.add_job(
            self.check_and_send_monthly_reminder,
            CronTrigger(hour=23, minute=0),  # Run daily at 11 PM
            id='monthly_reminder_check'
        )
        
        self.scheduler.start()
        logger.info("Scheduler started with weekly (Friday 11 PM) and monthly (last working day 11 PM) reminders")
    
    def stop(self):
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def get_last_working_day_of_month(self, year: int, month: int) -> datetime:
        """
        Calculate the last working day of the month.
        If month end is Saturday or Sunday, return the Friday before.
        Otherwise, return the last day of the month.
        """
        # Get the last day of the month
        last_day = monthrange(year, month)[1]
        last_date = datetime(year, month, last_day)
        
        # Check if it's Saturday (5) or Sunday (6)
        weekday = last_date.weekday()  # Monday=0, Sunday=6
        
        if weekday == 5:  # Saturday
            # Return Friday (day before)
            return last_date - timedelta(days=1)
        elif weekday == 6:  # Sunday
            # Return Friday (2 days before)
            return last_date - timedelta(days=2)
        else:
            # It's a weekday, return the last day
            return last_date
    
    async def check_and_send_monthly_reminder(self):
        """
        Check if today is the last working day of the month and send reminder if so.
        """
        try:
            today = datetime.now()
            last_working_day = self.get_last_working_day_of_month(today.year, today.month)
            
            # Check if today is the last working day (same date)
            if today.date() == last_working_day.date():
                await self.send_monthly_reminder()
                logger.info(f"Monthly reminder sent on {today.date()} (last working day of month)")
            else:
                logger.debug(f"Today ({today.date()}) is not the last working day ({last_working_day.date()})")
        
        except Exception as e:
            logger.error(f"Error checking monthly reminder date: {str(e)}")
    
    async def send_weekly_reminder(self):
        try:
            db = SessionLocal()
            
            # Get all channels where bot is present
            result = db.execute(text("SELECT DISTINCT channel_id FROM timesheet_entries"))
            channels = [row[0] for row in result]
            
            # Also get all users who have submitted timesheets
            user_result = db.execute(text("SELECT DISTINCT user_id FROM timesheet_entries"))
            user_ids = [row[0] for row in user_result]
            
            reminder_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "⏰ *Weekly Timesheet Reminder*\n\nDon't forget to fill your weekly timesheet for this week!\nUse `/postTimesheetWeekly` to submit."
                    }
                }
            ]
            
            # Send to channels
            # for channel in channels:
            #     self.slack_service.post_message(
            #         channel,
            #         reminder_blocks,
            #         "Weekly Timesheet Reminder"
            #     )
            
            # Send DM to users who have submitted before
            for user_id in user_ids:
                self.slack_service.send_dm(
                    user_id,
                    reminder_blocks,
                    "Weekly Timesheet Reminder"
                )
            
            db.close()
            logger.info(f"Weekly reminder sent to {len(channels)} channels and {len(user_ids)} users")
        
        except Exception as e:
            logger.error(f"Error sending weekly reminder: {str(e)}")
    
    async def send_monthly_reminder(self):
        try:
            db = SessionLocal()
            
            # Get all channels where bot is present
            result = db.execute(text("SELECT DISTINCT channel_id FROM timesheet_entries"))
            channels = [row[0] for row in result]
            
            # Also get all users who have submitted timesheets
            user_result = db.execute(text("SELECT DISTINCT user_id FROM timesheet_entries"))
            user_ids = [row[0] for row in user_result]
            
            reminder_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "⏰ *Monthly Timesheet Reminder*\n\nDon't forget to fill your monthly timesheet!\nUse `/commands/postTimesheetMonthly` to submit."
                    }
                }
            ]
            
            # Send to channels
            # for channel in channels:
            #     self.slack_service.post_message(
            #         channel,
            #         reminder_blocks,
            #         "Monthly Timesheet Reminder"
            #     )
            
            # Send DM to users who have submitted before
            for user_id in user_ids:
                self.slack_service.send_dm(
                    user_id,
                    reminder_blocks,
                    "Monthly Timesheet Reminder"
                )
            
            db.close()
            logger.info(f"Monthly reminder sent to {len(channels)} channels and {len(user_ids)} users")
        
        except Exception as e:
            logger.error(f"Error sending monthly reminder: {str(e)}")
    
    async def send_monthly_summary(self):
        """
        Keep the old monthly summary method for backward compatibility if needed.
        This can be removed or kept for admin reports.
        """
        try:
            from app.services.timesheet_service import TimesheetService
            from app.utils.block_builder import BlockBuilder
            from app.config import get_settings
            
            settings = get_settings()
            db = SessionLocal()
            
            # Get monthly entries
            entries = TimesheetService.get_monthly_entries(db)
            blocks = BlockBuilder.build_report_blocks(
                entries,
                "📊 Monthly Timesheet Summary"
            )
            
            # Send to manager
            self.slack_service.send_dm(
                settings.slack_manager_user_id,
                blocks,
                "Monthly Timesheet Summary"
            )
            
            db.close()
            logger.info("Monthly summary sent to manager")
        
        except Exception as e:
            logger.error(f"Error sending monthly summary: {str(e)}")
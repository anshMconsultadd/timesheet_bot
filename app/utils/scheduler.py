from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from app.services.slack_service import SlackService
from app.services.timesheet_service import TimesheetService
from app.database import SessionLocal
from app.config import get_settings
from sqlalchemy import text
from datetime import datetime, timedelta
from calendar import monthrange
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class TaskScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.slack_service = SlackService()
    
    def start(self):
        # PRODUCTION: Weekly reminder every Friday at 11 PM
        self.scheduler.add_job(
            self.send_weekly_reminder,
            CronTrigger(day_of_week='fri', hour=23, minute=0),  # PRODUCTION: Friday 11 PM
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
        logger.info("Scheduler started - PRODUCTION MODE: Weekly (Friday 11 PM) and monthly (last working day 11 PM) reminders")
    
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

    def get_missing_users_per_channel(self, db, timesheet_type: str = 'weekly'):
        """
        Get a dictionary of {channel_id: [missing_user_ids]}.
        Missing users are those who are in the channel but haven't submitted timesheet yet.
        """
        try:
            missing_users_per_channel = {}
            
            # Get all channels
            result = db.execute(text("SELECT DISTINCT channel_id FROM timesheet_entries WHERE channel_id != 'unknown'"))
            channels = [row[0] for row in result]
            
            for channel_id in channels:
                try:
                    # Get all users in this channel (excluding bots)
                    all_users = self.slack_service.get_all_users_from_channels([channel_id])
                    
                    if not all_users:
                        continue
                    
                    # Get users who have submitted this timesheet type
                    if timesheet_type == 'weekly':
                        submitted_users = self._get_weekly_submitters(db)
                    else:
                        submitted_users = self._get_monthly_submitters(db)
                    
                    # Calculate missing users
                    missing = [uid for uid in all_users if uid not in submitted_users]
                    
                    if missing:
                        missing_users_per_channel[channel_id] = missing
                        logger.info(f"Channel {channel_id}: {len(missing)} missing users for {timesheet_type} timesheet")
                
                except Exception as e:
                    logger.warning(f"Error processing channel {channel_id}: {str(e)}")
                    continue
            
            return missing_users_per_channel
        
        except Exception as e:
            logger.error(f"Error getting missing users per channel: {str(e)}")
            return {}

    def _get_weekly_submitters(self, db):
        """Get user IDs who have submitted weekly timesheet this week."""
        try:
            from datetime import datetime, timedelta
            week_start = datetime.now() - timedelta(days=datetime.now().weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            
            result = db.execute(text("""
                SELECT DISTINCT user_id FROM timesheet_entries 
                WHERE timesheet_type = 'weekly' AND submission_date >= :week_start
            """), {"week_start": week_start})
            
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error getting weekly submitters: {str(e)}")
            return []

    def _get_monthly_submitters(self, db):
        """Get user IDs who have submitted monthly timesheet this month."""
        try:
            from datetime import datetime
            now = datetime.now()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            result = db.execute(text("""
                SELECT DISTINCT user_id FROM timesheet_entries 
                WHERE timesheet_type = 'monthly' AND submission_date >= :month_start
            """), {"month_start": month_start})
            
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error getting monthly submitters: {str(e)}")
            return []
    
    def _post_missing_users_to_channel(self, channel_id: str, missing_user_ids: list, timesheet_type: str = 'weekly'):
        """Post the missing users list to a specific channel."""
        try:
            if not missing_user_ids:
                logger.info(f"No missing users for {channel_id}, skipping post")
                return
            
            # Format user mentions
            user_mentions = "\n".join([f"<@{user_id}>" for user_id in missing_user_ids])
            
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*⚠️ Users who haven't submitted {timesheet_type} timesheet:*\n{user_mentions}"
                    }
                }
            ]
            
            success = self.slack_service.post_message(
                channel_id,
                blocks,
                f"Missing {timesheet_type} timesheet submissions"
            )
            
            if success:
                logger.info(f"Posted missing users list to {channel_id} ({len(missing_user_ids)} users)")
            else:
                logger.error(f"Failed to post missing users list to {channel_id}")
        
        except Exception as e:
            logger.error(f"Error posting missing users to channel {channel_id}: {str(e)}")
    
    async def post_missing_users_to_channels(self, timesheet_type: str = 'weekly'):
        """
        Post the list of missing users to each channel.
        This is called after the configured delay from the initial reminder.
        """
        try:
            db = SessionLocal()
            
            missing_users_per_channel = self.get_missing_users_per_channel(db, timesheet_type)
            
            for channel_id, missing_users in missing_users_per_channel.items():
                self._post_missing_users_to_channel(channel_id, missing_users, timesheet_type)
            
            db.close()
            logger.info(f"Completed posting missing users for {timesheet_type} timesheet to {len(missing_users_per_channel)} channels")
        
        except Exception as e:
            logger.error(f"Error in post_missing_users_to_channels: {str(e)}")
    
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
        logger.info("=== STARTING WEEKLY REMINDER PROCESS ===")
        start_time = datetime.now()
        
        try:
            db = SessionLocal()
            
            # Get all channels where timesheets have been submitted
            result = db.execute(text("SELECT DISTINCT channel_id FROM timesheet_entries WHERE channel_id != 'unknown'"))
            channels = [row[0] for row in result]
            logger.info(f"Found {len(channels)} channels with timesheet history: {channels}")
            
            # Get all users from all channels (this is who should get reminders)
            all_user_ids = set()
            channel_user_counts = {}
            
            for channel_id in channels:
                try:
                    channel_users = self.slack_service.get_all_users_from_channels([channel_id])
                    channel_user_counts[channel_id] = len(channel_users)
                    all_user_ids.update(channel_users)
                    logger.debug(f"Channel {channel_id}: {len(channel_users)} users")
                except Exception as e:
                    logger.warning(f"Error getting users from channel {channel_id}: {str(e)}")
                    continue
            
            logger.info(f"Total unique users to notify: {len(all_user_ids)}")
            logger.info(f"Channel user breakdown: {channel_user_counts}")
            
            reminder_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "⏰ *Weekly Timesheet Reminder*\n\nDon't forget to fill your weekly timesheet for this week!\nUse `/postTimesheetWeekly` to submit."
                    }
                }
            ]
            
            # Send DM to ALL users in channels (not just those who submitted before)
            successful_dms = 0
            failed_dms = 0
            
            for user_id in all_user_ids:
                try:
                    success = self.slack_service.send_dm(
                        user_id,
                        reminder_blocks,
                        "Weekly Timesheet Reminder"
                    )
                    if success:
                        successful_dms += 1
                        logger.debug(f"✅ DM sent successfully to user {user_id}")
                    else:
                        failed_dms += 1
                        logger.warning(f"❌ Failed to send DM to user {user_id}")
                except Exception as e:
                    failed_dms += 1
                    logger.warning(f"❌ Exception sending DM to user {user_id}: {str(e)}")
                    continue
            
            logger.info(f"📊 Weekly reminder results: {successful_dms} successful, {failed_dms} failed out of {len(all_user_ids)} total users")
            
            # Schedule follow-up: post missing users to channels after configured delay
            delay_seconds = settings.reminder_post_delay_seconds  # PRODUCTION: 1 hour delay
            run_time = datetime.now() + timedelta(seconds=delay_seconds)
            
            job_id = f"weekly_followup_{run_time.timestamp()}"
            self.scheduler.add_job(
                self.post_missing_users_to_channels,
                DateTrigger(run_date=run_time),
                args=['weekly'],
                id=job_id,
                replace_existing=False
            )
            
            logger.info(f"⏰ Scheduled weekly follow-up job '{job_id}' to run at {run_time.strftime('%Y-%m-%d %H:%M:%S')} ({delay_seconds} seconds from now)")
            
            db.close()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"=== WEEKLY REMINDER PROCESS COMPLETED in {execution_time:.2f} seconds ===")
        
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"💥 CRITICAL ERROR in weekly reminder after {execution_time:.2f} seconds: {str(e)}", exc_info=True)
    
    async def send_monthly_reminder(self):
        logger.info("=== STARTING MONTHLY REMINDER PROCESS ===")
        start_time = datetime.now()
        
        try:
            db = SessionLocal()
            
            # Get all channels where timesheets have been submitted
            result = db.execute(text("SELECT DISTINCT channel_id FROM timesheet_entries WHERE channel_id != 'unknown'"))
            channels = [row[0] for row in result]
            logger.info(f"Found {len(channels)} channels with timesheet history: {channels}")
            
            # Get all users from all channels (this is who should get reminders)
            all_user_ids = set()
            channel_user_counts = {}
            
            for channel_id in channels:
                try:
                    channel_users = self.slack_service.get_all_users_from_channels([channel_id])
                    channel_user_counts[channel_id] = len(channel_users)
                    all_user_ids.update(channel_users)
                    logger.debug(f"Channel {channel_id}: {len(channel_users)} users")
                except Exception as e:
                    logger.warning(f"Error getting users from channel {channel_id}: {str(e)}")
                    continue
            
            logger.info(f"Total unique users to notify: {len(all_user_ids)}")
            logger.info(f"Channel user breakdown: {channel_user_counts}")
            
            reminder_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "⏰ *Monthly Timesheet Reminder*\n\nDon't forget to fill your monthly timesheet!\nUse `/postTimesheetMonthly` to submit."
                    }
                }
            ]
            
            # Send DM to ALL users in channels (not just those who submitted before)
            successful_dms = 0
            failed_dms = 0
            
            for user_id in all_user_ids:
                try:
                    success = self.slack_service.send_dm(
                        user_id,
                        reminder_blocks,
                        "Monthly Timesheet Reminder"
                    )
                    if success:
                        successful_dms += 1
                        logger.debug(f"✅ DM sent successfully to user {user_id}")
                    else:
                        failed_dms += 1
                        logger.warning(f"❌ Failed to send DM to user {user_id}")
                except Exception as e:
                    failed_dms += 1
                    logger.warning(f"❌ Exception sending DM to user {user_id}: {str(e)}")
                    continue
            
            logger.info(f"📊 Monthly reminder results: {successful_dms} successful, {failed_dms} failed out of {len(all_user_ids)} total users")
            
            # Schedule follow-up: post missing users to channels after configured delay
            delay_seconds = settings.reminder_post_delay_seconds  # PRODUCTION: 1 hour delay
            run_time = datetime.now() + timedelta(seconds=delay_seconds)
            
            job_id = f"monthly_followup_{run_time.timestamp()}"
            self.scheduler.add_job(
                self.post_missing_users_to_channels,
                DateTrigger(run_date=run_time),
                args=['monthly'],
                id=job_id,
                replace_existing=False
            )
            
            logger.info(f"⏰ Scheduled monthly follow-up job '{job_id}' to run at {run_time.strftime('%Y-%m-%d %H:%M:%S')} ({delay_seconds} seconds from now)")
            
            db.close()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"=== MONTHLY REMINDER PROCESS COMPLETED in {execution_time:.2f} seconds ===")
        
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"💥 CRITICAL ERROR in monthly reminder after {execution_time:.2f} seconds: {str(e)}", exc_info=True)
    
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
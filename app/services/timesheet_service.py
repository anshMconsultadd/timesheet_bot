from sqlalchemy.orm import Session
from sqlalchemy import func, extract, desc
from app.models.timesheet import TimesheetEntry
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.utils.timezone import get_ist_now, utc_to_ist, format_ist_date, get_ist_date


class TimesheetService:
    @staticmethod
    def has_submitted_today(
        db: Session,
        user_id: str,
        timesheet_type: str
    ) -> bool:
        """Check if user has already submitted a timesheet of this type today."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        existing_entry = db.query(TimesheetEntry).filter(
            TimesheetEntry.user_id == user_id,
            TimesheetEntry.timesheet_type == timesheet_type,
            TimesheetEntry.submission_date >= today_start,
            TimesheetEntry.submission_date < today_end
        ).first()
        
        return existing_entry is not None

    @staticmethod
    def create_entry(
        db: Session,
        user_id: str,
        username: str,
        channel_id: str,
        client_name: str,
        hours: float,
        timesheet_type: str = 'weekly'  # Add this parameter
    ) -> TimesheetEntry:
        entry = TimesheetEntry(
            user_id=user_id,
            username=username,
            channel_id=channel_id,
            client_name=client_name,
            hours=hours,
            timesheet_type=timesheet_type  # Add this field
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    
    @staticmethod
    def get_weekly_entries(db: Session) -> List[Dict[str, Any]]:
        week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        entries = db.query(TimesheetEntry).filter(
            TimesheetEntry.submission_date >= week_start,
            TimesheetEntry.timesheet_type == 'weekly'  # Add this filter
        ).all()
        
        return [
            {
                'username': e.username,
                'client_name': e.client_name,
                'hours': e.hours,
                'submission_date': e.submission_date.strftime('%Y-%m-%d %H:%M')
            }
            for e in entries
        ]
    
    @staticmethod
    def get_monthly_entries(db: Session) -> List[Dict[str, Any]]:
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        entries = db.query(TimesheetEntry).filter(
            TimesheetEntry.submission_date >= month_start,
            TimesheetEntry.timesheet_type == 'monthly'  # Add this filter
        ).all()
        
        return [
            {
                'username': e.username,
                'client_name': e.client_name,
                'hours': e.hours,
                'submission_date': e.submission_date.strftime('%Y-%m-%d %H:%M')
            }
            for e in entries
        ]
    
    @staticmethod
    def get_user_entries(db: Session, user_id: str, days: int = 7, timesheet_type: str = None) -> List[TimesheetEntry]:
        cutoff_date = datetime.now() - timedelta(days=days)
        query = db.query(TimesheetEntry).filter(
            TimesheetEntry.user_id == user_id,
            TimesheetEntry.submission_date >= cutoff_date
        )
        
        # Add timesheet_type filter if specified
        if timesheet_type:
            query = query.filter(TimesheetEntry.timesheet_type == timesheet_type)
            
        return query.all()

    @staticmethod
    def get_weekly_entries_grouped_by_user(db: Session) -> Dict[str, Dict[str, Any]]:
        """
        Get weekly entries grouped by user_id.
        Returns a dictionary where key is user_id and value contains username and entries list.
        """
        week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        entries = db.query(TimesheetEntry).filter(
            TimesheetEntry.submission_date >= week_start,
            TimesheetEntry.timesheet_type == 'weekly'  # Add this filter
        ).order_by(TimesheetEntry.user_id, TimesheetEntry.submission_date).all()
        
        grouped = {}
        for e in entries:
            if e.user_id not in grouped:
                grouped[e.user_id] = {
                    'username': e.username,
                    'user_id': e.user_id,
                    'entries': []
                }
            
            grouped[e.user_id]['entries'].append({
                'client_name': e.client_name,
                'hours': e.hours,
                'submission_date': e.submission_date.strftime('%Y-%m-%d %H:%M')
            })
        
        return grouped
    
    @staticmethod
    def get_monthly_entries_grouped_by_user(db: Session) -> Dict[str, Dict[str, Any]]:
        """
        Get monthly entries grouped by user_id.
        Returns a dictionary where key is user_id and value contains username and entries list.
        """
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        entries = db.query(TimesheetEntry).filter(
            TimesheetEntry.submission_date >= month_start,
            TimesheetEntry.timesheet_type == 'monthly'  # Add this filter
        ).order_by(TimesheetEntry.user_id, TimesheetEntry.submission_date).all()
        
        grouped = {}
        for e in entries:
            if e.user_id not in grouped:
                grouped[e.user_id] = {
                    'username': e.username,
                    'user_id': e.user_id,
                    'entries': []
                }
            
            grouped[e.user_id]['entries'].append({
                'client_name': e.client_name,
                'hours': e.hours,
                'submission_date': e.submission_date.strftime('%Y-%m-%d %H:%M')
            })
        
        return grouped
    
    @staticmethod
    def get_latest_timesheet_entries(db: Session, user_id: str) -> List[TimesheetEntry]:
        """
        Get all entries from the user's most recent timesheet submission.
        Groups entries by submission date (YYYY-MM-DD) in IST and timesheet type.
        """
        from sqlalchemy import func, cast, Date

        # Get the latest entry
        latest_entry = db.query(TimesheetEntry).filter(
            TimesheetEntry.user_id == user_id
        ).order_by(desc(TimesheetEntry.submission_date)).first()

        if not latest_entry:
            return []

        # Get the IST date of the latest entry
        latest_ist_date = get_ist_date(latest_entry.submission_date)

        # Get all entries submitted on the same IST date with the same type
        entries = db.query(TimesheetEntry).filter(
            TimesheetEntry.user_id == user_id,
            TimesheetEntry.timesheet_type == latest_entry.timesheet_type
        ).order_by(TimesheetEntry.submission_date).all()

        # Filter entries by IST date
        return [
            entry for entry in entries 
            if get_ist_date(entry.submission_date) == latest_ist_date
        ]

    @staticmethod
    def update_timesheet_entry(
        db: Session,
        entry_id: int,
        user_id: str,
        client_name: str,
        hours: float,
        channel_id: str = None
    ) -> Optional[TimesheetEntry]:
        """Update a timesheet entry with optimistic locking for concurrency."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔄 Attempting to update entry {entry_id} for user {user_id}")
        
        entry = db.query(TimesheetEntry).filter(
            TimesheetEntry.id == entry_id,
            TimesheetEntry.user_id == user_id  # Ensure user owns this entry
        ).first()
        
        if not entry:
            logger.error(f"❌ Entry {entry_id} not found for user {user_id}")
            return None
        
        logger.info(f"📍 Found entry: {entry.client_name} - {entry.hours} hours")
        logger.info(f"📍 Updating to: {client_name} - {hours} hours")
        
        try:
            entry.client_name = client_name
            entry.hours = hours
            entry.submission_date = get_ist_now().replace(tzinfo=None)  # Update submission time in IST
            if channel_id:  # Update channel_id if provided
                entry.channel_id = channel_id
            db.commit()
            db.refresh(entry)
            logger.info(f"✅ Successfully updated entry {entry_id}")
            return entry
        except Exception as e:
            logger.error(f"❌ Error updating entry {entry_id}: {str(e)}")
            db.rollback()
            return None

    @staticmethod
    def delete_timesheet_entry(
        db: Session,
        entry_id: int,
        user_id: str
    ) -> bool:
        """Delete a timesheet entry. Only the owner can delete their entry."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🗑️ Attempting to delete entry {entry_id} for user {user_id}")
        
        entry = db.query(TimesheetEntry).filter(
            TimesheetEntry.id == entry_id,
            TimesheetEntry.user_id == user_id  # Ensure user owns this entry
        ).first()
        
        if not entry:
            logger.error(f"❌ Entry {entry_id} not found for user {user_id}")
            return False
        
        logger.info(f"📍 Found entry to delete: {entry.client_name} - {entry.hours} hours")
        
        try:
            db.delete(entry)
            db.commit()
            logger.info(f"✅ Successfully deleted entry {entry_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting entry {entry_id}: {str(e)}")
            db.rollback()
            return False

    @staticmethod
    def format_entry_date(entries: List[TimesheetEntry]) -> str:
        """Format the submission date of entries for display in IST."""
        if not entries:
            return ""
        return format_ist_date(entries[0].submission_date)

    @staticmethod
    def get_all_channels(db: Session) -> List[str]:
        """
        Get all distinct channel IDs from timesheet entries.
        These are channels where the bot has received timesheet submissions.
        """
        from sqlalchemy import text
        result = db.execute(text("SELECT DISTINCT channel_id FROM timesheet_entries"))
        return [row[0] for row in result]
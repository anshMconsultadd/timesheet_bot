from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models.timesheet import TimesheetEntry
from datetime import datetime, timedelta
from typing import List, Dict, Any


class TimesheetService:
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
    def get_user_entries(db: Session, user_id: str, days: int = 7) -> List[TimesheetEntry]:
        cutoff_date = datetime.now() - timedelta(days=days)
        return db.query(TimesheetEntry).filter(
            TimesheetEntry.user_id == user_id,
            TimesheetEntry.submission_date >= cutoff_date
        ).all()

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
    def get_all_channels(db: Session) -> List[str]:
        """
        Get all distinct channel IDs from timesheet entries.
        These are channels where the bot has received timesheet submissions.
        """
        from sqlalchemy import text
        result = db.execute(text("SELECT DISTINCT channel_id FROM timesheet_entries"))
        return [row[0] for row in result]
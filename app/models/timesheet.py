from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from app.database import Base


class TimesheetEntry(Base):
    __tablename__ = "timesheet_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    username = Column(String(100), nullable=False)
    channel_id = Column(String(50), nullable=False)
    client_name = Column(String(200), nullable=False)
    hours = Column(Float, nullable=False)
    timesheet_type = Column(String(20), nullable=False, default='weekly', index=True)  # 'weekly' or 'monthly'
    submission_date = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TimesheetEntry(user={self.username}, client={self.client_name}, hours={self.hours}, type={self.timesheet_type})>"

from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.slack_service import SlackService
from app.services.timesheet_service import TimesheetService
from app.utils.block_builder import BlockBuilder
from app.config import get_settings
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta
from app.models.timesheet import TimesheetEntry

logger = logging.getLogger(__name__)
settings = get_settings()


class CommandHandler:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.slack_service = SlackService()
        self.block_builder = BlockBuilder()
    
    # async def handle_timesheet_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    #     # Show initial form
    #     blocks = self.block_builder.build_initial_form()
        
    #     return {
    #         "response_type": "ephemeral",
    #         "blocks": blocks,
    #         "text": "Fill your timesheet"
    #     }

    async def handle_timesheet_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        trigger_id = payload.get("trigger_id")
        blocks = self.block_builder.build_initial_form()

        # Open modal with the full form
        self.slack_service.open_modal(trigger_id, blocks)

        # Return None to avoid showing any message
        return None
    
    async def handle_timesheet_weekly_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        trigger_id = payload.get("trigger_id")
        blocks = self.block_builder.build_weekly_form()

        # Open modal with the weekly form - use specific callback_id
        self.slack_service.open_modal(trigger_id, blocks, "Weekly Timesheet", "submit_weekly_timesheet")

        # Return success message instead of None
        return {
            "response_type": "ephemeral",
            "text": "Timesheet Submitted Successfully"
        }
    
    async def handle_timesheet_monthly_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        trigger_id = payload.get("trigger_id")
        blocks = self.block_builder.build_monthly_form()

        # Open modal with the monthly form - use specific callback_id
        self.slack_service.open_modal(trigger_id, blocks, "Monthly Timesheet", "submit_monthly_timesheet")

        # Return success message instead of None
        return {
            "response_type": "ephemeral",
            "text": "Timesheet Submitted Successfully"
        }

    async def handle_weekly_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        user_id = payload.get('user_id')
        
        # Get weekly entries grouped by user
        grouped_entries = TimesheetService.get_weekly_entries_grouped_by_user(self.db)
        
        # Get all channels where bot is present
        channel_ids = TimesheetService.get_all_channels(self.db)
        
        # Get all users from those channels
        all_user_ids = set(self.slack_service.get_all_users_from_channels(channel_ids))
        submitted_user_ids = set(grouped_entries.keys())
        missing_user_ids = list(all_user_ids - submitted_user_ids)
        
        blocks = self.block_builder.build_user_grouped_report_blocks(
            grouped_entries,
            "📊 Weekly Timesheet Report",
            missing_user_ids
        )
        
        return {
            "response_type": "ephemeral",
            "blocks": blocks,
            "text": "Weekly Report"
        }
    
    async def handle_monthly_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        user_id = payload.get('user_id')
        
        # Get monthly entries grouped by user
        grouped_entries = TimesheetService.get_monthly_entries_grouped_by_user(self.db)
        
        # Get all channels where bot is present
        channel_ids = TimesheetService.get_all_channels(self.db)
        
        # Get all users from those channels
        all_user_ids = set(self.slack_service.get_all_users_from_channels(channel_ids))
        submitted_user_ids = set(grouped_entries.keys())
        missing_user_ids = list(all_user_ids - submitted_user_ids)
        
        blocks = self.block_builder.build_user_grouped_report_blocks(
            grouped_entries,
            "📊 Monthly Timesheet Report",
            missing_user_ids
        )
        
        return {
            "response_type": "ephemeral",
            "blocks": blocks,
            "text": "Monthly Report"
        }


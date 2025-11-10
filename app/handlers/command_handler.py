from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.slack_service import SlackService
from app.services.timesheet_service import TimesheetService
from app.utils.block_builder import BlockBuilder
from app.config import get_settings
from typing import Dict, Any, List
import logging
import json
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
        channel_id = payload.get("channel_id")
        blocks = self.block_builder.build_initial_form()

        # Open modal with the full form and channel_id in metadata
        self.slack_service.open_modal(
            trigger_id=trigger_id,
            blocks=blocks,
            private_metadata=json.dumps({"channel_id": channel_id})
        )

        # Return None to avoid showing any message
        return None
    
    async def handle_timesheet_weekly_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        trigger_id = payload.get("trigger_id")
        channel_id = payload.get("channel_id")
        blocks = self.block_builder.build_weekly_form()

        # Store channel_id in metadata
        metadata = json.dumps({"channel_id": channel_id})

        # Open modal with the weekly form - use specific callback_id and include metadata
        self.slack_service.open_modal(
            trigger_id=trigger_id,
            blocks=blocks,
            title="Weekly Timesheet",
            callback_id="submit_weekly_timesheet",
            private_metadata=metadata
        )

        # Return success message instead of None
        return {
            "response_type": "ephemeral",
            "text": "Timesheet Submitted Successfully"
        }
    
    async def handle_timesheet_monthly_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        trigger_id = payload.get("trigger_id")
        channel_id = payload.get("channel_id")
        blocks = self.block_builder.build_monthly_form()

        # Store channel_id in metadata
        metadata = json.dumps({"channel_id": channel_id})

        # Open modal with the monthly form - use specific callback_id and include metadata
        self.slack_service.open_modal(
            trigger_id=trigger_id,
            blocks=blocks,
            title="Monthly Timesheet",
            callback_id="submit_monthly_timesheet",
            private_metadata=metadata
        )

        # Return success message instead of None
        return {
            "response_type": "ephemeral",
            "text": "Timesheet Submitted Successfully"
        }

    async def handle_weekly_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        user_id = payload.get('user_id')

        # Manager(s) list from env (comma-separated supported)
        manager_ids = [m.strip() for m in (settings.slack_manager_user_id or "").split(',') if m.strip()]

        # If caller is manager, show full grouped report
        if user_id in manager_ids:
            grouped_entries = TimesheetService.get_weekly_entries_grouped_by_user(self.db)
            channel_ids = TimesheetService.get_all_channels(self.db)
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

        # Non-manager: show only the caller's entries for last 7 days
        entries = TimesheetService.get_user_entries(self.db, user_id, days=7)
        entry_dicts = [
            {
                'username': e.username,
                'client_name': e.client_name,
                'hours': e.hours,
                'submission_date': e.submission_date.strftime('%Y-%m-%d %H:%M')
            }
            for e in entries
        ]

        blocks = self.block_builder.build_report_blocks(entry_dicts, "📊 Your Weekly Timesheet Report")
        return {
            "response_type": "ephemeral",
            "blocks": blocks,
            "text": "Your Weekly Report"
        }
    
    async def handle_monthly_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        user_id = payload.get('user_id')

        # Manager(s) list from env (comma-separated supported)
        manager_ids = [m.strip() for m in (settings.slack_manager_user_id or "").split(',') if m.strip()]

        # If caller is manager, show full grouped report
        if user_id in manager_ids:
            grouped_entries = TimesheetService.get_monthly_entries_grouped_by_user(self.db)
            channel_ids = TimesheetService.get_all_channels(self.db)
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

        # Non-manager: show only the caller's entries for last ~31 days
        entries = TimesheetService.get_user_entries(self.db, user_id, days=31)
        entry_dicts = [
            {
                'username': e.username,
                'client_name': e.client_name,
                'hours': e.hours,
                'submission_date': e.submission_date.strftime('%Y-%m-%d %H:%M')
            }
            for e in entries
        ]

        blocks = self.block_builder.build_report_blocks(entry_dicts, "📊 Your Monthly Timesheet Report")
        return {
            "response_type": "ephemeral",
            "blocks": blocks,
            "text": "Your Monthly Report"
        }

    async def handle_edit_timesheet_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the /edit_timesheet command."""
        user_id = payload.get('user_id')
        channel_id = payload.get('channel_id')
        trigger_id = payload.get('trigger_id', '')  # Get trigger_id with empty string default

        if not trigger_id:
            logger.error("No trigger_id provided in edit_timesheet command")
            return {
                "response_type": "ephemeral",
                "text": "Error: Unable to open edit form. Please try again."
            }

        # Get user's latest timesheet entries
        latest_entries = TimesheetService.get_latest_timesheet_entries(self.db, user_id)
        
        if not latest_entries:
            return {
                "response_type": "ephemeral",
                "text": "No previous timesheet found to edit. Please submit a new timesheet first."
            }

        # Build blocks with pre-filled values for all entries
        initial_values = [{
            'client_name': entry.client_name,
            'hours': entry.hours
        } for entry in latest_entries]

        blocks = self.block_builder.build_entry_forms(
            num_entries=len(latest_entries),
            timesheet_type=latest_entries[0].timesheet_type,
            initial_values=initial_values
        )

        # Store all entry IDs and channel ID in private_metadata
        view_metadata = {
            'entry_ids': [entry.id for entry in latest_entries],
            'timesheet_type': latest_entries[0].timesheet_type,
            'channel_id': channel_id  # Store channel_id in metadata
        }

        # Get formatted date for display
        submission_date = TimesheetService.format_entry_date(latest_entries)
        timesheet_type = latest_entries[0].timesheet_type.capitalize()
        
        try:
            # Open modal with pre-filled form - use shorter title and move date to first block
            # Add date as first block instead of in title
            date_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Date:* {submission_date}"
                }
            }
            blocks.insert(0, {"type": "divider"})
            blocks.insert(0, date_block)
            
            success = self.slack_service.open_modal(
                trigger_id=trigger_id,
                blocks=blocks,
                title=f"Edit {timesheet_type}",  # Shorter title
                callback_id="edit_timesheet_modal",
                private_metadata=json.dumps(view_metadata)
            )
            
            if not success:
                raise Exception("Failed to open modal")

            return {
                "response_type": "ephemeral",
                "text": "Opening edit form..."
            }
        except Exception as e:
            logger.error(f"Failed to open edit modal: {str(e)}")
            return {
                "response_type": "ephemeral",
                "text": "Error: Unable to open edit form. Please try again."
            }


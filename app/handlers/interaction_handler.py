from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.slack_service import SlackService
from app.services.timesheet_service import TimesheetService
from app.utils.block_builder import BlockBuilder
from typing import Dict, Any
import logging
import json

logger = logging.getLogger(__name__)


class InteractionHandler:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.slack_service = SlackService()
        self.block_builder = BlockBuilder()
    
    async def handle_interaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        interaction_type = payload.get('type')
        
        if interaction_type == 'view_submission':
            return await self._handle_modal_submission(payload)
        elif interaction_type == 'block_actions':
            action_id = payload.get('actions', [{}])[0].get('action_id', '')
            logger.info(f"�� Handling action: {action_id}")
            
            if action_id == 'submit_timesheet':
                return await self._handle_submit(payload)
            elif action_id == 'entry_count_select':
                logger.info("�� Dropdown selection received (no action required)")
                return {}
            
            logger.warning(f"⚠️ Unknown action: {action_id}")
            return {"text": "Unknown action"}
        
        logger.warning(f"⚠️ Unknown interaction type: {interaction_type}")
        return {"text": "Unknown interaction"}
    
    async def _handle_submit(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            user_id = payload['user']['id']
            user_name = payload['user'].get('username', payload['user'].get('name', 'Unknown'))
            channel_id = payload.get('channel', {}).get('id', 'unknown')
            state_values = payload.get('state', {}).get('values', {})
            message_ts = payload.get('message', {}).get('ts')
            
            # Default to weekly for block_actions (button submissions)
            timesheet_type = 'weekly'

            entries = []
            skipped_entries = []
            i = 0
            while f'client_block_{i}' in state_values:
                client_block = state_values.get(f'client_block_{i}', {})
                hours_block = state_values.get(f'hours_block_{i}', {})
                
                client_name = client_block.get(f'client_input_{i}', {}).get('value', '').strip() if client_block.get(f'client_input_{i}', {}).get('value') else ''
                hours_value = hours_block.get(f'hours_input_{i}', {}).get('value', '').strip() if hours_block.get(f'hours_input_{i}', {}).get('value') else ''
                
                # Skip entry if client_name or hours is empty (mark as Not Applicable, don't store)
                if not client_name or not hours_value:
                    skipped_entries.append(i + 1)
                    i += 1
                    continue
                
                try:
                    hours = float(hours_value)
                except (ValueError, TypeError):
                    skipped_entries.append(i + 1)
                    i += 1
                    continue

                TimesheetService.create_entry(
                    db=self.db,
                    user_id=user_id,
                    username=user_name,
                    channel_id=channel_id,
                    client_name=client_name,
                    hours=hours,
                    timesheet_type=timesheet_type  # Add this parameter
                )

                entries.append({'client': client_name, 'hours': hours})
                i += 1

            confirmation_text = f"✅ {timesheet_type.capitalize()} Timesheet submitted successfully!\n\n"
            for idx, entry in enumerate(entries, 1):
                confirmation_text += f"{idx}. {entry['client']} - {entry['hours']} hours\n"
            
            if skipped_entries:
                confirmation_text += f"\n⚠️ Entries #{', '.join(map(str, skipped_entries))} were skipped (Not Applicable - missing required fields)."

            self.slack_service.send_dm(
                user_id,
                [{
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": confirmation_text}
                }],
                "Timesheet submitted"
            )

            confirmation_blocks = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "✅ *Timesheet Submitted Successfully!*"}
                }
            ]

            if channel_id and message_ts:
                self.slack_service.update_message(
                    channel_id,
                    message_ts,
                    confirmation_blocks,
                    "Timesheet submitted"
                )

            return {"response_action": "update", "blocks": confirmation_blocks}

        except Exception as e:
            logger.error(f"Error submitting timesheet: {str(e)}")
            return {
                "response_action": "errors",
                "errors": {"hours_block_0": f"Submission failed: {str(e)}"}
            }

    async def _handle_modal_submission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            user_id = payload['user']['id']
            user_name = payload['user'].get('username', payload['user'].get('name', 'Unknown'))
            channel_id = payload.get('channel', {}).get('id', 'unknown')
            state_values = payload.get('view', {}).get('state', {}).get('values', {})
            
            # Determine timesheet type from callback_id
            callback_id = payload.get('view', {}).get('callback_id', 'submit_timesheet')
            if callback_id == 'submit_monthly_timesheet':
                timesheet_type = 'monthly'
            else:
                timesheet_type = 'weekly'  # Default to weekly for 'submit_weekly_timesheet' or 'submit_timesheet'

            entries = []
            skipped_entries = []
            i = 0
            while f'client_block_{i}' in state_values:
                client_block = state_values.get(f'client_block_{i}', {})
                hours_block = state_values.get(f'hours_block_{i}', {})
                
                client_name = client_block.get(f'client_input_{i}', {}).get('value', '').strip() if client_block.get(f'client_input_{i}', {}).get('value') else ''
                hours_value = hours_block.get(f'hours_input_{i}', {}).get('value', '').strip() if hours_block.get(f'hours_input_{i}', {}).get('value') else ''
                
                # Skip entry if client_name or hours is empty (mark as Not Applicable, don't store)
                if not client_name or not hours_value:
                    skipped_entries.append(i + 1)
                    i += 1
                    continue
                
                try:
                    hours = float(hours_value)
                except (ValueError, TypeError):
                    skipped_entries.append(i + 1)
                    i += 1
                    continue

                TimesheetService.create_entry(
                    db=self.db,
                    user_id=user_id,
                    username=user_name,
                    channel_id=channel_id,
                    client_name=client_name,
                    hours=hours,
                    timesheet_type=timesheet_type  # Add this parameter
                )

                entries.append({'client': client_name, 'hours': hours})
                i += 1

            confirmation_text = f"✅ {timesheet_type.capitalize()} Timesheet submitted successfully!\n\n"
            for idx, entry in enumerate(entries, 1):
                confirmation_text += f"{idx}. {entry['client']} - {entry['hours']} hours\n"
            
            if skipped_entries:
                confirmation_text += f"\n⚠️ Entries #{', '.join(map(str, skipped_entries))} were skipped (Not Applicable - missing required fields)."

            # Send confirmation DM
            self.slack_service.send_dm(
                user_id,
                [{
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": confirmation_text}
                }],
                "Timesheet submitted"
            )

            # Return success response for modal
            return {"response_action": "clear"}

        except Exception as e:
            logger.error(f"Error submitting timesheet: {str(e)}")
            return {
                "response_action": "errors",
                "errors": {"hours_block_0": f"Submission failed: {str(e)}"}
            }

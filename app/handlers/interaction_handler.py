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
        logger.info("📥 Received payload:")
        logger.info(json.dumps(payload, indent=2))
        
        interaction_type = payload.get('type')
        logger.info(f"📋 Interaction type: {interaction_type}")

        if interaction_type == 'view_submission':
            # Check callback_id to determine which submission handler to use
            callback_id = payload.get('view', {}).get('callback_id')
            if callback_id == 'edit_timesheet_modal':
                return await self._handle_edit_timesheet_submission(payload)
            return await self._handle_modal_submission(payload)
        elif interaction_type == 'block_actions':
            action = payload.get('actions', [{}])[0]
            action_id = action.get('action_id', '')
            logger.info(f"⚙️ Handling action: {action_id}")
            logger.info(f"🔍 Action details: {json.dumps(action, indent=2)}")
            logger.info(f"🖼️ View context: {json.dumps(payload.get('view', {}), indent=2)}")

            if action_id == 'submit_timesheet':
                return await self._handle_submit(payload)
            elif action_id == 'entry_count_select':
                return await self._handle_entry_count_update(payload, action)
        
        # Default response if no matching interaction
        return {"response_action": "update", "blocks": []}

    async def _handle_entry_count_update(self, payload: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info("🎯 Starting entry count update...")
            
            # Extract and validate selection
            selected_value = action.get('selected_option', {}).get('value')
            logger.info(f"📊 Selected value: {selected_value}")
            if not selected_value:
                raise ValueError("No value selected")
            
            # Parse number of entries
            num_entries = int(selected_value)
            logger.info(f"🔢 Number of entries requested: {num_entries}")
            
            # Get view information
            view = payload.get('view', {})
            view_id = view.get('id')
            callback_id = view.get('callback_id', 'timesheet_modal')
            private_metadata = view.get('private_metadata', '{}')
            logger.info(f"🪟 View ID: {view_id}")
            logger.info(f"🎫 Callback ID: {callback_id}")
            logger.info(f"📍 Private metadata to preserve: {private_metadata}")
            
            if not view_id:
                raise ValueError("No view ID found in payload")

            # Build blocks
            logger.info("🏗️ Building new blocks...")
            new_blocks = self.block_builder.build_entry_forms(num_entries)
            logger.info(f"📦 Generated {len(new_blocks)} blocks")
            
            # Try updating view with preserved metadata
            logger.info("🔄 Attempting to update view...")
            success = self.slack_service.update_modal_view(
                view_id=view_id,
                blocks=new_blocks,
                title="Weekly Timesheet",
                callback_id=callback_id,
                private_metadata=private_metadata
            )
            
            if not success:
                raise Exception("Failed to update modal view")
            
            logger.info("✅ View update successful!")
            # For debugging, return both ways - direct update and response
            return {
                "response_action": "update",
                "view": {
                    "type": "modal",
                    "callback_id": callback_id,
                    "title": {"type": "plain_text", "text": "Weekly Timesheet"},
                    "submit": {"type": "plain_text", "text": "Submit"},
                    "close": {"type": "plain_text", "text": "Cancel"},
                    "blocks": new_blocks
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error updating entry count: {str(e)}")
            logger.exception("Detailed error:")  # This will log the full stack trace
            return {
                "response_action": "errors", 
                "errors": {"entry_count_block": f"Failed to update form: {str(e)}"}
            }


    async def _handle_submit(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            user_id = payload['user']['id']
            # Get actual username for storage
            user_name = self.slack_service.get_user_display_name(user_id)
            logger.info(f"Processing submission for user: {user_id} ({user_name})")
            
            # Try to get channel_id from multiple sources with detailed logging
            channel_id = payload.get('channel', {}).get('id')
            logger.info(f"📍 Channel ID from payload['channel']: {channel_id}")
            
            if not channel_id:
                logger.warning("⚠️ Channel ID not in payload['channel'], checking view metadata...")
                view = payload.get('view', {})
                try:
                    private_metadata = view.get('private_metadata', '{}')
                    logger.info(f"📍 Raw private_metadata in _handle_submit: {private_metadata}")
                    
                    if private_metadata and private_metadata != '{}':
                        metadata = json.loads(private_metadata)
                        channel_id = metadata.get('channel_id')
                        logger.info(f"📍 Channel ID from metadata in _handle_submit: {channel_id}")
                        if channel_id:
                            logger.info(f"✅ Got channel_id from view metadata: {channel_id}")
                    else:
                        logger.warning("⚠️ No private_metadata in view")
                except Exception as e:
                    logger.error(f"❌ Error parsing metadata in _handle_submit: {str(e)}")
            
            if not channel_id:
                logger.error("❌ CRITICAL: Could not find channel_id anywhere in _handle_submit!")
                logger.error(f"❌ Payload keys: {list(payload.keys())}")
                if 'view' in payload:
                    logger.error(f"❌ View keys: {list(payload['view'].keys())}")
                channel_id = 'unknown'
            else:
                logger.info(f"✅ Final channel_id for submission: {channel_id}")
            
            view = payload.get('view', {})
            state_values = view.get('state', {}).get('values', {})
            message_ts = payload.get('message', {}).get('ts')

            # Default to weekly unless otherwise specified
            timesheet_type = 'weekly'

            entries = []
            skipped_entries = []

            # Dynamically iterate over all blocks, not assuming only 3
            entry_map = {}
            for block_id, block_data in state_values.items():
                for action_id, action_data in block_data.items():
                    value = (action_data.get('value') or '').strip()
                    if "client_input_" in action_id:
                        index = action_id.split("_")[-1]
                        entry_map.setdefault(index, {})["client_name"] = value
                    elif "hours_input_" in action_id:
                        index = action_id.split("_")[-1]
                        entry_map.setdefault(index, {})["hours_value"] = value

            # Process each collected entry
            for idx, data in entry_map.items():
                client_name = data.get("client_name", "")
                hours_value = data.get("hours_value", "")

                # Skip empty entries
                if not client_name or not hours_value:
                    skipped_entries.append(int(idx) + 1)
                    continue

                try:
                    hours = float(hours_value)
                except (ValueError, TypeError):
                    skipped_entries.append(int(idx) + 1)
                    continue

                # Save entry to DB
                TimesheetService.create_entry(
                    db=self.db,
                    user_id=user_id,
                    username=user_name,
                    channel_id=channel_id,
                    client_name=client_name,
                    hours=hours,
                    timesheet_type=timesheet_type
                )

                entries.append({'client': client_name, 'hours': hours})

            # Build confirmation message using mention format for display
            user_mention = self.slack_service.format_user_mention(user_id)
            confirmation_text = f"✅ *{timesheet_type.capitalize()} Timesheet submitted successfully by {user_mention}!*\n\n"
            for idx, entry in enumerate(entries, 1):
                confirmation_text += f"{idx}. {entry['client']} — {entry['hours']} hours\n"

            if skipped_entries:
                confirmation_text += (
                    f"\n⚠️ Entries #{', '.join(map(str, skipped_entries))} "
                    f"were skipped (missing client or hours)."
                )

            # Send DM confirmation to user
            self.slack_service.send_dm(
                user_id,
                [{
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": confirmation_text}
                }],
                "Timesheet submitted"
            )

            # Update original message (replace form with confirmation)
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
            logger.error(f"❌ Error submitting timesheet: {str(e)}", exc_info=True)
            return {
                "response_action": "errors",
                "errors": {"hours_block_0": f"Submission failed: {str(e)}"}
            }

    async def _handle_edit_timesheet_submission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle submission of the edit timesheet modal."""
        try:
            user_id = payload['user']['id']
            # Get user's display name in Slack mention format
            user_name = self.slack_service.get_user_display_name(user_id)
            view = payload['view']
            
            logger.info(f"🔧 Edit timesheet submission for user: {user_id}")
            
            # Get metadata containing entry_ids and timesheet_type
            try:
                metadata = json.loads(view.get('private_metadata', '{}'))
                entry_ids = metadata.get('entry_ids')
                channel_id = metadata.get('channel_id', 'unknown')
                logger.info(f"📍 Metadata: {metadata}")
                logger.info(f"📍 Entry IDs to update: {entry_ids}")
                logger.info(f"📍 Channel ID: {channel_id}")
                if not entry_ids:
                    raise ValueError("No entry IDs found in metadata")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"❌ Metadata error: {str(e)}")
                return {
                    "response_action": "errors",
                    "errors": {"entry_count_block": f"Invalid metadata: {str(e)}"}
                }
            
            # Get values from form for all entries
            values = view['state']['values']
            updates = []
            new_entries = []
            errors = {}
            
            # Count how many form entries we have
            form_entry_count = 0
            for i in range(20):  # Check up to 20 entries
                if f'client_block_{i}' in values:
                    form_entry_count = i + 1
                else:
                    break
            
            logger.info(f"📊 Form has {form_entry_count} entries, existing entries: {len(entry_ids)}")
            
            # Determine which entries to delete (if form has fewer entries than existing)
            entries_to_delete = []
            if form_entry_count < len(entry_ids):
                entries_to_delete = entry_ids[form_entry_count:]  # Entries beyond form count
                logger.info(f"🗑️ Will delete {len(entries_to_delete)} entries: {entries_to_delete}")
            
            # Process all form entries
            for i in range(form_entry_count):
                client_block = values.get(f'client_block_{i}', {})
                hours_block = values.get(f'hours_block_{i}', {})
                
                client_name = client_block.get(f'client_input_{i}', {}).get('value', '').strip()
                hours_value = hours_block.get(f'hours_input_{i}', {}).get('value', '').strip()
                
                # Skip empty entries
                if not client_name and not hours_value:
                    continue
                
                if not client_name:
                    errors[f'client_block_{i}'] = "Client name is required"
                    continue
                    
                if not hours_value:
                    errors[f'hours_block_{i}'] = "Hours are required"
                    continue
                
                try:
                    hours = float(hours_value)
                except ValueError:
                    errors[f'hours_block_{i}'] = "Hours must be a valid number"
                    continue
                
                # If this is an existing entry, add to updates
                if i < len(entry_ids):
                    updates.append({
                        'entry_id': entry_ids[i],
                        'client_name': client_name,
                        'hours': hours
                    })
                else:
                    # This is a new entry, add to new_entries
                    new_entries.append({
                        'client_name': client_name,
                        'hours': hours
                    })
            
            if errors:
                return {
                    "response_action": "errors",
                    "errors": errors
                }
            
            # Update existing timesheet entries
            successful_updates = []
            logger.info(f"🔄 Attempting to update {len(updates)} existing entries")
            for update in updates:
                logger.info(f"🔄 Updating entry {update['entry_id']}: {update['client_name']} - {update['hours']} hours")
                updated_entry = TimesheetService.update_timesheet_entry(
                    db=self.db,
                    entry_id=update['entry_id'],
                    user_id=user_id,
                    client_name=update['client_name'],
                    hours=update['hours'],
                    channel_id=channel_id  # Include channel_id in update
                )
                if updated_entry:
                    logger.info(f"✅ Successfully updated entry {update['entry_id']}")
                    successful_updates.append(update)
                else:
                    logger.error(f"❌ Failed to update entry {update['entry_id']}")
            
            # Create new timesheet entries
            successful_new_entries = []
            logger.info(f"🆕 Attempting to create {len(new_entries)} new entries")
            for new_entry in new_entries:
                logger.info(f"🆕 Creating new entry: {new_entry['client_name']} - {new_entry['hours']} hours")
                created_entry = TimesheetService.create_entry(
                    db=self.db,
                    user_id=user_id,
                    username=user_name,
                    channel_id=channel_id,
                    client_name=new_entry['client_name'],
                    hours=new_entry['hours'],
                    timesheet_type=metadata.get('timesheet_type', 'weekly')
                )
                if created_entry:
                    logger.info(f"✅ Successfully created new entry {created_entry.id}")
                    successful_new_entries.append(new_entry)
                else:
                    logger.error(f"❌ Failed to create new entry")
            
            # Delete entries that are no longer needed (when reducing entry count)
            successful_deletions = []
            logger.info(f"🗑️ Attempting to delete {len(entries_to_delete)} entries")
            for entry_id in entries_to_delete:
                logger.info(f"🗑️ Deleting entry {entry_id}")
                deleted = TimesheetService.delete_timesheet_entry(
                    db=self.db,
                    entry_id=entry_id,
                    user_id=user_id
                )
                if deleted:
                    logger.info(f"✅ Successfully deleted entry {entry_id}")
                    successful_deletions.append(entry_id)
                else:
                    logger.error(f"❌ Failed to delete entry {entry_id}")
            
            logger.info(f"📊 Successfully updated {len(successful_updates)} entries, created {len(successful_new_entries)} new entries, and deleted {len(successful_deletions)} entries")
            
            if not successful_updates and not successful_new_entries and not successful_deletions:
                return {
                    "response_action": "errors",
                    "errors": {"client_block_0": "Failed to update timesheet. The entries may have been modified by someone else."}
                }
            
            # Send DM confirmation with all updated, new, and deleted entries
            update_text = "✅ Your timesheet has been updated:\n"
            for update in successful_updates:
                update_text += f"• {update['client_name']}: {update['hours']} hours (updated)\n"
            for new_entry in successful_new_entries:
                update_text += f"• {new_entry['client_name']}: {new_entry['hours']} hours (new)\n"
            if successful_deletions:
                update_text += f"\n🗑️ Removed {len(successful_deletions)} entries\n"
            
            self.slack_service.send_dm(
                user_id,
                [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": update_text
                    }
                }],
                "Timesheet Updated"
            )
            
            return {"response_action": "clear"}
            
        except Exception as e:
            logger.error(f"Error updating timesheet: {str(e)}")
            return {
                "response_action": "errors",
                "errors": {"client_block_0": f"Error updating timesheet: {str(e)}"}
            }

    async def _handle_modal_submission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            user_id = payload['user']['id']
            # Get user's display name in Slack mention format
            user_name = self.slack_service.get_user_display_name(user_id)
            view = payload.get('view', {})
            state_values = view.get('state', {}).get('values', {})
            
            # Log the full view structure for debugging
            logger.info(f"📍 Full view object keys: {list(view.keys())}")
            logger.info(f"📍 View callback_id: {view.get('callback_id')}")
            logger.info(f"📍 View id: {view.get('id')}")
            
            # Get channel_id from metadata with detailed logging
            channel_id = 'unknown'  # Default fallback
            
            try:
                private_metadata = view.get('private_metadata', '{}')
                logger.info(f"📍 Raw private_metadata: '{private_metadata}'")
                logger.info(f"📍 Private metadata type: {type(private_metadata)}")
                logger.info(f"📍 Private metadata length: {len(private_metadata) if private_metadata else 0}")
                
                if private_metadata and private_metadata.strip() and private_metadata != '{}':
                    metadata = json.loads(private_metadata)
                    logger.info(f"📍 Parsed metadata: {metadata}")
                    
                    # Try to get channel_id from metadata first
                    channel_id = metadata.get('channel_id')
                    logger.info(f"📍 Channel ID from metadata: {channel_id}")
                    
                    if channel_id:
                        logger.info(f"✅ Successfully retrieved channel_id from metadata: {channel_id}")
                    else:
                        logger.warning("⚠️ Channel ID not found in metadata")
                else:
                    logger.warning("⚠️ No private_metadata found in view")
                
                # If still no channel_id, try to get from payload
                if not channel_id or channel_id == 'unknown':
                    logger.warning("⚠️ Channel ID not in metadata, checking payload...")
                    payload_channel_id = (
                        payload.get('channel', {}).get('id') or  # Try channel object
                        payload.get('channel_id')  # Try direct channel_id
                    )
                    if payload_channel_id:
                        channel_id = payload_channel_id
                        logger.info(f"📍 Retrieved channel_id from payload: {channel_id}")
                    else:
                        logger.error("❌ No channel_id found in payload either!")
                
                if channel_id == 'unknown':
                    logger.error("❌ CRITICAL: Channel ID is UNKNOWN! This will break reminders!")
                    logger.error(f"❌ Full payload keys: {list(payload.keys())}")
                    logger.error(f"❌ View keys: {list(view.keys())}")
                else:
                    logger.info(f"✅ Final channel_id for submission: {channel_id}")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"❌ Error parsing metadata: {str(e)}")
                logger.error(f"❌ Raw metadata was: {view.get('private_metadata', 'None')}")
                # Try to get channel_id from payload as final fallback
                payload_channel_id = (
                    payload.get('channel', {}).get('id') or
                    payload.get('channel_id')
                )
                if payload_channel_id:
                    channel_id = payload_channel_id
                    logger.warning(f"⚠️ Using fallback channel_id from payload: {channel_id}")
                else:
                    logger.error("❌ CRITICAL: No channel_id available anywhere!")
            
            # Determine timesheet type from callback_id
            callback_id = payload.get('view', {}).get('callback_id', 'submit_timesheet')
            if callback_id == 'submit_monthly_timesheet':
                timesheet_type = 'monthly'
            else:
                timesheet_type = 'weekly'  # Default to weekly for 'submit_weekly_timesheet' or 'submit_timesheet'

            # Check if user has already submitted this timesheet type today
            if TimesheetService.has_submitted_today(self.db, user_id, timesheet_type):
                logger.warning(f"User {user_id} attempted duplicate {timesheet_type} submission")
                return {
                    "response_action": "errors",
                    "errors": {
                        "client_block_0": f"You have already submitted a {timesheet_type} timesheet today. Use /edit_timesheet to modify your existing entries."
                    }
                }

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
        

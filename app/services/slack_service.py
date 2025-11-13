from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import List, Dict, Any, Optional
from app.config import get_settings
import logging
import json
from typing import List, Dict, Any

logger = logging.getLogger(__name__)
settings = get_settings()


class SlackService:
    def __init__(self):
        self.client = WebClient(token=settings.slack_bot_token)
    
    def post_message(self, channel: str, blocks: List[Dict[str, Any]], text: str = "") -> Optional[str]:
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=text
            )
            return response['ts']
        except SlackApiError as e:
            logger.error(f"Error posting message: {e.response['error']}")
            return None
    
    def update_message(self, channel: str, ts: str, blocks: List[Dict[str, Any]], text: str = "") -> bool:
        try:
            self.client.chat_update(
                channel=channel,
                ts=ts,
                blocks=blocks,
                text=text
            )
            return True
        except SlackApiError as e:
            logger.error(f"Error updating message: {e.response['error']}")
            return False
    
    def get_channel_members(self, channel: str) -> List[str]:
        try:
            response = self.client.conversations_members(channel=channel)
            return response['members']
        except SlackApiError as e:
            logger.error(f"Error getting channel members: {e.response['error']}")
            return []
    
    def get_bot_channels(self) -> List[str]:
        """Get all channels where the bot is a member."""
        try:
            response = self.client.conversations_list(
                types="public_channel,private_channel",
                exclude_archived=True
            )
            
            bot_channels = []
            for channel in response.get('channels', []):
                channel_id = channel['id']
                # Check if bot is a member of this channel
                if channel.get('is_member', False):
                    bot_channels.append(channel_id)
                    logger.debug(f"Bot is member of channel: {channel_id} ({channel.get('name', 'unknown')})")
            
            logger.info(f"Found {len(bot_channels)} channels where bot is a member")
            return bot_channels
            
        except SlackApiError as e:
            logger.error(f"Error getting bot channels: {e.response['error']}")
            return []
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.client.users_info(user=user_id)
            return response['user']
        except SlackApiError as e:
            logger.error(f"Error getting user info: {e.response['error']}")
            return None
            
    def get_user_display_name(self, user_id: str) -> str:
        """Get user's actual display name from Slack for storage in DB."""
        if not user_id:
            logger.error("No user_id provided to get_user_display_name")
            return "Unknown User"
            
        try:
            user_info = self.get_user_info(user_id)
            if not user_info:
                return "Unknown User"

            # Try to get the best available name in order of preference
            name = (user_info.get('profile', {}).get('real_name') or  # Real name first
                   user_info.get('profile', {}).get('display_name') or  # Then display name
                   user_info.get('name') or  # Then username
                   f"User_{user_id}")  # Fallback
            
            logger.info(f"Retrieved display name for {user_id}: {name}")
            return name

        except Exception as e:
            logger.error(f"Error getting user display name: {str(e)}")
            return f"User_{user_id}"
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.client.files_info(file=file_id)
            return response['file']
        except SlackApiError as e:
            logger.error(f"Error getting file info: {e.response['error']}")
            return None
    
    def send_dm(self, user_id: str, blocks: List[Dict[str, Any]], text: str = "") -> bool:
        try:
            # Open DM channel
            response = self.client.conversations_open(users=user_id)
            channel_id = response['channel']['id']
            
            # Send message
            self.client.chat_postMessage(
                channel=channel_id,
                blocks=blocks,
                text=text
            )
            return True
        except SlackApiError as e:
            logger.error(f"Error sending DM: {e.response['error']}")
            return False
    
    def open_modal(self, trigger_id: str, blocks: List[Dict[str, Any]], title: str = "Weekly Timesheet", 
                  callback_id: str = "submit_timesheet", private_metadata: str = None):
        try:
            logger.info(f"Opening modal with trigger_id: {trigger_id}")
            logger.info(f"Title: {title}")
            logger.info(f"Callback ID: {callback_id}")
            logger.info(f"Number of blocks: {len(blocks)}")
            
            if not trigger_id:
                raise ValueError("No trigger_id provided")
            
            view = {
                "type": "modal",
                "callback_id": callback_id,
                "title": {"type": "plain_text", "text": title, "emoji": True},
                "submit": {"type": "plain_text", "text": "Submit", "emoji": True},
                "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
                "blocks": blocks
            }
            
            # Add private_metadata if provided
            if private_metadata:
                view["private_metadata"] = private_metadata
                logger.info(f"✅ Added private_metadata to view: {private_metadata}")
            else:
                logger.warning("⚠️ No private_metadata provided to open_modal")

            logger.info(f"📤 Sending view to Slack: {json.dumps(view, indent=2)}")
            
            response = self.client.views_open(
                trigger_id=trigger_id,
                view=view
            )
            
            if not response["ok"]:
                logger.error(f"❌ Error in views.open response: {response}")
                return False
                
            logger.info("✅ Modal opened successfully")
            logger.info(f"📨 Slack response: {response.get('view', {}).get('id', 'No view ID')}")
            return True
            
        except ValueError as ve:
            logger.error(f"Validation error opening modal: {str(ve)}")
            return False
        except SlackApiError as e:
            logger.error(f"Error opening modal: {e.response['error']}")
            logger.error(f"Response data: {e.response}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error opening modal: {str(e)}")
            return False

    def get_all_users_from_channels(self, channel_ids: List[str]) -> List[str]:
        """
        Get all user IDs from the given channels where bot is present.
        Excludes bots and returns unique user IDs.
        """
        all_user_ids = set()
        
        for channel_id in channel_ids:
            try:
                members = self.get_channel_members(channel_id)
                logger.info(f"📊 Channel {channel_id} has {len(members)} total members")
                # Filter out bots
                channel_users = []
                for member_id in members:
                    user_info = self.get_user_info(member_id)
                    if user_info and not user_info.get('is_bot', False) and not user_info.get('deleted', False):
                        all_user_ids.add(member_id)
                        channel_users.append(member_id)
                        logger.debug(f"📊 Added user {member_id} ({user_info.get('name', 'unknown')}) from channel {channel_id}")
                logger.info(f"📊 Channel {channel_id} has {len(channel_users)} non-bot users: {channel_users}")
            except Exception as e:
                logger.warning(f"Error getting members from channel {channel_id}: {str(e)}")
                continue
        
        logger.info(f"📊 Total unique users from all channels: {len(all_user_ids)} - {list(all_user_ids)}")
        return list(all_user_ids)

    def format_user_mention(self, user_id: str) -> str:
        """Format a user ID as a Slack mention for display purposes only."""
        return f"<@{user_id}>"

    def format_user_for_display(self, user_id: str, stored_username: str) -> str:
        """
        Format a user mention for display in Slack messages.
        Uses user_id for mention and falls back to stored username if needed.
        """
        if not user_id:
            return stored_username
        return self.format_user_mention(user_id)

    def update_modal_view(self, view_id: str, blocks: List[Dict[str, Any]], title: str = "Weekly Timesheet", callback_id: str = "timesheet_modal", private_metadata: str = None) -> bool:
        """Update an existing modal view"""
        try:
            logger.info(f"🔄 Updating modal view {view_id}")
            logger.info(f"📦 Number of blocks: {len(blocks)}")
            logger.info(f"🎫 Callback ID: {callback_id}")
            
            view_payload = {
                "type": "modal",
                "callback_id": callback_id,
                "title": {"type": "plain_text", "text": title},
                "submit": {"type": "plain_text", "text": "Submit"},
                "close": {"type": "plain_text", "text": "Cancel"},
                "blocks": blocks
            }
            
            # Add private_metadata if provided to preserve it during update
            if private_metadata:
                view_payload["private_metadata"] = private_metadata
                logger.info(f"✅ Preserving private_metadata in view update: {private_metadata}")
            else:
                logger.warning("⚠️ No private_metadata provided to update_modal_view")
            
            logger.info("📤 Sending update to Slack...")
            response = self.client.views_update(
                view_id=view_id,
                view=view_payload
            )
            
            logger.info("✅ View update API call successful")
            # Log only the serializable parts of the response
            response_data = {
                "ok": response.get("ok", False),
                "view": response.get("view", {}).get("id", "N/A")
            }
            logger.info(f"📨 Slack response: {json.dumps(response_data, indent=2)}")
            return True
            
        except SlackApiError as e:
            logger.error("❌ Slack API Error:")
            logger.error(f"Error Code: {e.response.get('error', 'Unknown')}")
            logger.error(f"Error Data: {json.dumps(e.response.get('data', {}), indent=2)}")
            logger.error(f"Response Headers: {json.dumps(dict(e.response.headers), indent=2)}")
            return False
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import List, Dict, Any, Optional
from app.config import get_settings
import logging
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
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.client.users_info(user=user_id)
            return response['user']
        except SlackApiError as e:
            logger.error(f"Error getting user info: {e.response['error']}")
            return None
    
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
    
    def open_modal(self, trigger_id: str, blocks: List[Dict[str, Any]], title: str = "Weekly Timesheet", callback_id: str = "submit_timesheet"):
        try:
            self.client.views_open(
                trigger_id=trigger_id,
                view={
                    "type": "modal",
                    "callback_id": callback_id,  # Use passed callback_id
                    "title": {"type": "plain_text", "text": title},
                    "submit": {"type": "plain_text", "text": "Submit"},
                    "close": {"type": "plain_text", "text": "Cancel"},
                    "blocks": blocks
                },
            )
            return True
        except SlackApiError as e:
            logger.error(f"Error opening modal: {e.response['error']}")
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
                # Filter out bots
                for member_id in members:
                    user_info = self.get_user_info(member_id)
                    if user_info and not user_info.get('is_bot', False) and not user_info.get('deleted', False):
                        all_user_ids.add(member_id)
            except Exception as e:
                logger.warning(f"Error getting members from channel {channel_id}: {str(e)}")
                continue
        
        return list(all_user_ids)
"""
Service for managing user exemptions (users who don't need to fill timesheets)
"""
import json
import os
import logging
from typing import List

logger = logging.getLogger(__name__)

EXEMPTION_FILE = "/app/data/exempted_users.json"


def get_exempted_users_from_json() -> List[str]:
    """Get list of exempted user IDs from JSON file."""
    try:
        if os.path.exists(EXEMPTION_FILE):
            with open(EXEMPTION_FILE, 'r') as f:
                data = json.load(f)
                users = data.get('exempted_users', [])
                logger.info(f"Loaded {len(users)} exempted users from JSON file")
                return users
        return []
    except Exception as e:
        logger.error(f"Error reading exemption file: {str(e)}")
        return []


def add_exempted_user(user_id: str, username: str = None) -> bool:
    """Add a user to the exemption list."""
    try:
        logger.info(f"Writing exemption file to: {os.path.abspath(EXEMPTION_FILE)}")
        users = get_exempted_users_from_json()
        
        if user_id in users:
            logger.info(f"User {user_id} is already exempted")
            return False
        
        users.append(user_id)
        
        with open(EXEMPTION_FILE, 'w') as f:
            json.dump({'exempted_users': users}, f, indent=2)
        
        logger.info(f"Added user {user_id} ({username}) to exemption list")
        return True
        
    except Exception as e:
        logger.error(f"Error adding exempted user: {str(e)}")
        return False


def remove_exempted_user(user_id: str) -> bool:
    """Remove a user from the exemption list."""
    try:
        users = get_exempted_users_from_json()
        
        if user_id not in users:
            logger.info(f"User {user_id} is not in exemption list")
            return False
        
        users.remove(user_id)
        
        with open(EXEMPTION_FILE, 'w') as f:
            json.dump({'exempted_users': users}, f, indent=2)
        
        logger.info(f"Removed user {user_id} from exemption list")
        return True
        
    except Exception as e:
        logger.error(f"Error removing exempted user: {str(e)}")
        return False


def get_all_exempted_users(env_excluded: List[str] = None) -> List[str]:
    """
    Get all exempted users from both .env and JSON file.
    
    Args:
        env_excluded: List of user IDs from .env EXCLUDED_USER_IDS
    
    Returns:
        Combined list of all exempted user IDs (no duplicates)
    """
    # Get from JSON file
    json_excluded = get_exempted_users_from_json()
    
    # Get from .env (if provided)
    if env_excluded is None:
        env_excluded = []
    
    # Combine both sources (remove duplicates)
    all_excluded = list(set(env_excluded + json_excluded))
    
    logger.info(f"Total exempted users: {len(all_excluded)} (env: {len(env_excluded)}, json: {len(json_excluded)})")
    
    return all_excluded

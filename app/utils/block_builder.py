from typing import List, Dict, Any


class BlockBuilder:
    @staticmethod
    def build_initial_form() -> List[Dict[str, Any]]:
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📝 Timesheet Submission*\nPlease fill in your timesheet details."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "input",
                "block_id": "entry_count_block",
                "element": {
                    "type": "static_select",
                    "action_id": "entry_count_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select number of entries"
                    },
                "options": [
                    {"text": {"type": "plain_text", "text": f"{i}"}, "value": str(i)}
                    for i in range(1, 11)  # 🔄 was 1–3, now 1–10
                ]
                },
                "label": {
                    "type": "plain_text",
                    "text": "Number of entries"
                }
            }
        ]
        
        # Add only 3 entry forms to stay within Slack limits
        for i in range(1):
            blocks.extend([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Entry #{i + 1}*"
                    }
                },
                {
                    "type": "input",
                    "block_id": f"client_block_{i}",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": f"client_input_{i}",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Enter client name"
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Client Name"
                    }
                },
                {
                    "type": "input",
                    "block_id": f"hours_block_{i}",
                    "element": {
                        "type": "number_input",
                        "action_id": f"hours_input_{i}",
                        "is_decimal_allowed": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Enter hours"
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Hours"
                    }
                },
                {
                    "type": "input",
                    "block_id": f"description_block_{i}",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": f"description_input_{i}",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Enter work description"
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Description"
                    },
                    "optional": True
                },
                {
                    "type": "divider"
                }
            ])
        
        return blocks
    
    @staticmethod
    def build_weekly_form() -> List[Dict[str, Any]]:
        # Use build_entry_forms but customize the header text
        blocks = BlockBuilder.build_entry_forms(1)  # Start with 1 entry
        if blocks and blocks[0]["type"] == "section":
            blocks[0]["text"]["text"] = "*📝 Weekly Timesheet Submission*\nPlease fill in your weekly timesheet details."
        return blocks
    
    @staticmethod
    def build_monthly_form() -> List[Dict[str, Any]]:
        # Use build_entry_forms but customize the header text for monthly
        blocks = BlockBuilder.build_entry_forms(1)  # Start with 1 entry
        if blocks and blocks[0]["type"] == "section":
            blocks[0]["text"]["text"] = "*📝 Monthly Timesheet Submission*\nPlease fill in your monthly timesheet details."
        
        # Make all fields optional for monthly timesheet
        for block in blocks:
            if block["type"] == "input" and block["block_id"] != "entry_count_block":
                block["optional"] = True
                
        return blocks

    # Update build_entry_forms to remove description and make fields optional
    @staticmethod
    def build_entry_forms(num_entries: int, timesheet_type: str = 'weekly', initial_values: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Build entry forms with optional pre-filled values.
        Args:
            num_entries: Number of entry blocks to create
            timesheet_type: 'weekly' or 'monthly'
            initial_values: Optional list of dicts with client_name and hours to pre-fill
        """
        # Set title based on timesheet type
        title_text = "*📝 Weekly Timesheet*" if timesheet_type == 'weekly' else "*📝 Monthly Timesheet*"
        if initial_values:
            title_text += "\nEdit your previous timesheet entries:"
        else:
            title_text += "\nPlease fill in your timesheet details:"

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": title_text
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "input",
                "block_id": "entry_count_block",
                "dispatch_action": True,
                "element": {
                    "type": "static_select",
                    "action_id": "entry_count_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select number of entries"
                    },
                    "initial_option": {
                        "text": {"type": "plain_text", "text": str(num_entries)},
                        "value": str(num_entries)
                    },
                    "options": [
                        {"text": {"type": "plain_text", "text": f"{i}"}, "value": str(i)}
                        for i in range(1, 21)  # Allow 1-20 entries
                    ]
                },
                "label": {
                    "type": "plain_text",
                    "text": "Number of entries"
                }
            },
            {
                "type": "divider"
            }
        ]
        
        for i in range(num_entries):
            # Get initial values if available
            initial_value = None
            if initial_values and i < len(initial_values):
                initial_value = initial_values[i]

            blocks.extend([
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Entry #{i + 1}*"},
                },
                {
                    "type": "input",
                    "block_id": f"client_block_{i}",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": f"client_input_{i}",
                        "placeholder": {"type": "plain_text", "text": "Enter client name"},
                        **({"initial_value": initial_value["client_name"]} if initial_value else {})
                    },
                    "label": {"type": "plain_text", "text": "Client Name"},
                },
                {
                    "type": "input",
                    "block_id": f"hours_block_{i}",
                    "element": {
                        "type": "number_input",
                        "action_id": f"hours_input_{i}",
                        "is_decimal_allowed": True,
                        "placeholder": {"type": "plain_text", "text": "Enter hours"},
                        **({"initial_value": str(initial_value["hours"])} if initial_value else {})
                    },
                    "label": {"type": "plain_text", "text": "Hours"},
                },
                {"type": "divider"},
            ])
        return blocks   
    @staticmethod
    def build_report_blocks(entries: List[Dict[str, Any]], title: str) -> List[Dict[str, Any]]:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title
                }
            },
            {
                "type": "divider"
            }
        ]
        
        if not entries:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "_No timesheet entries found for this period._"
                }
            })
            return blocks
        
        for entry in entries:
            blocks.extend([
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*User:*\n{entry.get('user_id', entry['username'])}"  # Use user_id for mention if available
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Client:*\n{entry['client_name']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Hours:*\n{entry['hours']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Date:*\n{entry['submission_date']}"
                        }
                    ]
                },
                {
                    "type": "divider"
                }
            ])
        
        total_hours = sum(entry['hours'] for entry in entries)
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Total Hours:* {total_hours}"
            }
        })
        
        return blocks

    @staticmethod
    def build_user_grouped_report_blocks(
        grouped_entries: Dict[str, Dict[str, Any]], 
        title: str,
        missing_user_ids: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Build report blocks grouped by user showing:
        - Username
        - Number of clients (total entries)
        - List of all clients with hours
        - Then next user
        - At the end, tag users who haven't submitted
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title
                }
            },
            {
                "type": "divider"
            }
        ]
        
        if not grouped_entries:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "_No timesheet entries found for this period._"
                }
            })
        else:
            # Sort users by username for consistent ordering
            sorted_users = sorted(grouped_entries.items(), key=lambda x: x[1]['username'])
            
            for user_id, user_data in sorted_users:
                username = user_data['username']
                entries = user_data['entries']
                num_clients = len(entries)
                
                # Calculate total hours for this user
                total_hours = sum(entry['hours'] for entry in entries)
                
                # Build client list text
                client_list = []
                for entry in entries:
                    client_list.append(f"• {entry['client_name']}: {entry['hours']} hours")
                
                client_list_text = "\n".join(client_list) if client_list else "_No clients listed_"
                
                # User section (username should already be in mention format)
                # Format user mention for display using user_id
                user_mention = f"<@{user_data['user_id']}>"
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*👤* {user_mention}\n*Number of Clients:* {num_clients}\n*Total Hours:* {total_hours}\n\n*Clients & Hours:*\n{client_list_text}"
                    }
                })
                
                blocks.append({
                    "type": "divider"
                })
        
        # Add missing users section (removed summary section above)
        if missing_user_ids:
            blocks.append({
                "type": "divider"
            })
            
            # Format user mentions
            user_mentions = "\n".join([f"<@{user_id}>" for user_id in missing_user_ids])
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*⚠️ Users who haven't submitted timesheet:*\n{user_mentions}"
                }
            })
        
        return blocks
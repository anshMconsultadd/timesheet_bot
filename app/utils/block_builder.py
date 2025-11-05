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
                        for i in range(1, 4)  # Reduced from 5 to 3
                    ]
                },
                "label": {
                    "type": "plain_text",
                    "text": "Number of entries"
                }
            }
        ]
        
        # Add only 3 entry forms to stay within Slack limits
        for i in range(3):
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
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📝 Weekly Timesheet Submission*\nPlease fill in your weekly timesheet details."
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
                        for i in range(1, 4)
                    ]
                },
                "label": {
                    "type": "plain_text",
                    "text": "Number of entries"
                }
            }
        ]
        
        # Add entry forms (all fields optional, no description)
        for i in range(3):
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
                    },
                    "optional": True
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
                    },
                    "optional": True
                },
                {
                    "type": "divider"
                }
            ])
        
        return blocks
    
    @staticmethod
    def build_monthly_form() -> List[Dict[str, Any]]:
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📝 Monthly Timesheet Submission*\nPlease fill in your monthly timesheet details."
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
                        for i in range(1, 4)
                    ]
                },
                "label": {
                    "type": "plain_text",
                    "text": "Number of entries"
                }
            }
        ]
        
        # Add entry forms (all fields optional, same as weekly, no description)
        for i in range(3):
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
                    },
                    "optional": True
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
                    },
                    "optional": True
                },
                {
                    "type": "divider"
                }
            ])
        
        return blocks

    # Update build_entry_forms to remove description and make fields optional
    @staticmethod
    def build_entry_forms(num_entries: int) -> List[Dict[str, Any]]:
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📋 Fill in your timesheet entries*"
                }
            },
            {
                "type": "divider"
            }
        ]
        
        for i in range(num_entries):
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
                    },
                    "optional": True
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
                    },
                    "optional": True
                },
                {
                    "type": "divider"
                }
            ])
        
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Submit Timesheet"
                    },
                    "action_id": "submit_timesheet",
                    "style": "primary"
                }
            ]
        })
        
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
                            "text": f"*User:*\n{entry['username']}"
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
                
                # User section
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*👤 {username}*\n*Number of Clients:* {num_clients}\n*Total Hours:* {total_hours}\n\n*Clients & Hours:*\n{client_list_text}"
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
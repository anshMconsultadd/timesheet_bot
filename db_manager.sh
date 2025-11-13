#!/bin/bash

# Timesheet Database Manager Script
# Provides various database operations for timesheet management

show_help() {
    echo "🗄️  Timesheet Database Manager"
    echo "================================"
    echo "Usage: ./db_manager.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  show       - Show all timesheet entries"
    echo "  count      - Count entries by type"
    echo "  today      - Show today's entries"
    echo "  weekly     - Show this week's entries"
    echo "  monthly    - Show this month's entries"
    echo "  users      - Show unique users"
    echo "  channels   - Show unique channels"
    echo "  truncate   - Clear all entries (DANGEROUS!)"
    echo "  help       - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./db_manager.sh show"
    echo "  ./db_manager.sh count"
    echo "  ./db_manager.sh truncate"
}

execute_query() {
    local query="$1"
    local description="$2"
    
    echo "🔍 $description"
    echo "================================================"
    docker exec -it timesheet_db psql -U postgres -d timesheet_db -c "$query"
    echo ""
}

case "$1" in
    "show"|"")
        execute_query "
        SELECT 
            id,
            user_id,
            username,
            channel_id,
            client_name,
            hours,
            timesheet_type,
            submission_date,
            created_at
        FROM timesheet_entries 
        ORDER BY created_at DESC;
        " "Showing all timesheet entries (newest first)"
        ;;
    
    "count")
        execute_query "
        SELECT 
            timesheet_type,
            COUNT(*) as entry_count,
            SUM(hours) as total_hours,
            COUNT(DISTINCT user_id) as unique_users
        FROM timesheet_entries 
        GROUP BY timesheet_type
        ORDER BY timesheet_type;
        " "Entry count by timesheet type"
        ;;
    
    "today")
        execute_query "
        SELECT 
            user_id,
            username,
            client_name,
            hours,
            timesheet_type,
            submission_date
        FROM timesheet_entries 
        WHERE DATE(submission_date) = CURRENT_DATE
        ORDER BY submission_date DESC;
        " "Today's timesheet entries"
        ;;
    
    "weekly")
        execute_query "
        SELECT 
            user_id,
            username,
            client_name,
            hours,
            submission_date
        FROM timesheet_entries 
        WHERE timesheet_type = 'weekly' 
        AND submission_date >= DATE_TRUNC('week', CURRENT_DATE)
        ORDER BY submission_date DESC;
        " "This week's timesheet entries"
        ;;
    
    "monthly")
        execute_query "
        SELECT 
            user_id,
            username,
            client_name,
            hours,
            submission_date
        FROM timesheet_entries 
        WHERE timesheet_type = 'monthly' 
        AND submission_date >= DATE_TRUNC('month', CURRENT_DATE)
        ORDER BY submission_date DESC;
        " "This month's timesheet entries"
        ;;
    
    "users")
        execute_query "
        SELECT 
            user_id,
            username,
            COUNT(*) as total_entries,
            SUM(hours) as total_hours,
            MAX(submission_date) as last_submission
        FROM timesheet_entries 
        GROUP BY user_id, username
        ORDER BY last_submission DESC;
        " "Unique users and their activity"
        ;;
    
    "channels")
        execute_query "
        SELECT 
            channel_id,
            COUNT(*) as entry_count,
            COUNT(DISTINCT user_id) as unique_users,
            SUM(hours) as total_hours
        FROM timesheet_entries 
        WHERE channel_id != 'unknown'
        GROUP BY channel_id
        ORDER BY entry_count DESC;
        " "Channel activity summary"
        ;;
    
    "truncate")
        echo "⚠️  WARNING: This will DELETE ALL timesheet entries!"
        echo "This action cannot be undone."
        echo ""
        read -p "Are you sure you want to continue? (type 'YES' to confirm): " confirm
        
        if [ "$confirm" = "YES" ]; then
            execute_query "TRUNCATE TABLE timesheet_entries RESTART IDENTITY;" "Clearing all timesheet entries"
            echo "✅ All timesheet entries have been deleted!"
        else
            echo "❌ Operation cancelled."
        fi
        ;;
    
    "help"|"-h"|"--help")
        show_help
        ;;
    
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

echo "✅ Operation completed!"
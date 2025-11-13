#!/bin/bash

# Timesheet Database Query Script
# This script connects to the PostgreSQL database and shows timesheet entries

echo "🔍 Connecting to timesheet database..."
echo "================================================"

# Execute the database query
docker exec -it timesheet_db psql -U postgres -d timesheet_db -c "
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
"

echo ""
echo "================================================"
echo "✅ Database query completed!"
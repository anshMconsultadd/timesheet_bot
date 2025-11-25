#!/bin/bash

# Script to check timesheet database status

echo "=== Checking Timesheet Database ==="
echo ""

echo "1️⃣ Channels in database:"
docker exec -it timesheet_db psql -U postgres -d timesheet_db -c \
  "SELECT DISTINCT channel_id, COUNT(*) as count FROM timesheet_entries GROUP BY channel_id;"

echo ""
echo "2️⃣ Users in database:"
docker exec -it timesheet_db psql -U postgres -d timesheet_db -c \
  "SELECT DISTINCT user_id, username, COUNT(*) as count FROM timesheet_entries GROUP BY user_id, username;"

echo ""
echo "3️⃣ Recent entries:"
docker exec -it timesheet_db psql -U postgres -d timesheet_db -c \
  "SELECT id, user_id, username, channel_id, client_name, hours, timesheet_type, submission_date FROM timesheet_entries ORDER BY id DESC LIMIT 10;"

echo ""
echo "4️⃣ Total entries by type:"
docker exec -it timesheet_db psql -U postgres -d timesheet_db -c \
  "SELECT timesheet_type, COUNT(*) FROM timesheet_entries GROUP BY timesheet_type;"

echo ""
echo "✅ Database check complete"

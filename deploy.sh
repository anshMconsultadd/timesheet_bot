#!/bin/bash

# Deployment script for EC2
# This ensures data persistence across container restarts

set -e

echo "🚀 Starting deployment..."

# Ensure required directories exist
echo "📁 Creating required directories..."
mkdir -p data logs

# Set proper permissions
echo "🔒 Setting permissions..."
chmod 755 data logs

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Rebuild and start services
echo "🔨 Building and starting services..."
docker-compose up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Verify containers are running
echo "✅ Checking container status..."
docker-compose ps

# Verify volume mounts
echo "📦 Verifying volume mounts..."
docker exec slack_timesheet_bot ls -la /app/data || echo "⚠️  Data directory check failed"

echo ""
echo "✨ Deployment complete!"
echo ""
echo "To verify data persistence:"
echo "  - Host: cat data/exempted_users.json"
echo "  - Container: docker exec slack_timesheet_bot cat /app/data/exempted_users.json"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f app"

#!/bin/bash

# Surveillance System - Docker Startup Script
# This script ensures .env is loaded correctly

set -e

echo "======================================================================"
echo "  🐳 Starting Surveillance System with Docker"
echo "======================================================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found in project root"
    echo ""
    echo "Please create .env file:"
    echo "  cp config/.env.example .env"
    echo "  # Then edit .env with your configuration"
    exit 1
fi

echo "✅ Found .env file"
echo ""

# Check if running from project root
if [ ! -d "docker" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# Load .env to verify configuration
source .env

echo "📋 Configuration:"
echo "  Database User: ${DB_USER}"
echo "  Database: surveillance_db"
echo "  Video Source: ${VIDEO_SOURCE_TYPE}"
echo "  Base URL: ${BASE_URL}"
echo ""

# Start Docker services
echo "🚀 Starting Docker services..."
echo ""

# Use --env-file to explicitly specify .env location
docker-compose -f docker/docker-compose.yml --env-file .env up -d

echo ""
echo "======================================================================"
echo "  ✅ Docker services started!"
echo "======================================================================"
echo ""
echo "📊 Service Status:"
docker-compose -f docker/docker-compose.yml ps
echo ""
echo "🔗 Access Points:"
echo "  - Application: ${BASE_URL}"
echo "  - Database: localhost:5432"
echo ""
echo "📝 Useful Commands:"
echo "  - View logs: docker-compose -f docker/docker-compose.yml logs -f"
echo "  - Stop services: docker-compose -f docker/docker-compose.yml down"
echo "  - Restart: docker-compose -f docker/docker-compose.yml restart"
echo ""

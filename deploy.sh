#!/bin/bash

# Deployment script for LocalMCP
# This script sets up and starts all MCP services

set -e

echo "=== LocalMCP Deployment Script ==="
echo "This script will deploy all MCP services using Docker Compose"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "# LocalMCP Environment Variables" > .env
    echo "VENICE_API_KEY=your_venice_api_key_here" >> .env
    echo "Please update the .env file with your API keys."
fi

# Build and start services
echo "Building and starting services..."
docker-compose build
docker-compose up -d

echo "=== Deployment Complete ==="
echo "Services are now running. You can access the web interface at http://localhost:8000"
echo "To view logs: docker-compose logs -f"
echo "To stop services: docker-compose down"

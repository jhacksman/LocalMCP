#!/bin/bash

# Setup script for LocalMCP
# This script installs dependencies and prepares the environment

set -e

echo "=== LocalMCP Setup Script ==="
echo "This script will install dependencies and prepare the environment"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Installing npm..."
    sudo apt-get install -y npm
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed. Installing Python..."
    sudo apt-get install -y python3 python3-pip
fi

# Install dependencies for each service
echo "Installing dependencies for MCP Manager..."
cd mcp-services/mcp-manager
npm install
cd ../..

echo "Installing dependencies for Vector DB MCP..."
cd mcp-services/vector-db-mcp
npm install
cd ../..

echo "Installing dependencies for Document MCP..."
cd mcp-services/document-mcp
npm install
cd ../..

echo "Installing dependencies for Stable Diffusion MCP..."
cd mcp-services/stable-diffusion-mcp
npm install
cd ../..

echo "Installing dependencies for SQL MCP..."
cd mcp-services/sql
pip install -r requirements.txt
cd ../..

echo "Installing dependencies for Venice MCP..."
cd mcp-services/venice-mcp
npm install
cd ../..

echo "Installing dependencies for Web Interface..."
cd web-interface
pip install -r requirements.txt
cd ..

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "# LocalMCP Environment Variables" > .env
    echo "VENICE_API_KEY=your_venice_api_key_here" >> .env
    echo "Please update the .env file with your API keys."
fi

echo "=== Setup Complete ==="
echo "You can now run the deployment script: ./deploy.sh"

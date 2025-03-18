# ManusMCP Launch Guide

This document provides comprehensive commands for deploying and running the ManusMCP multi-agent system on a Linux server.

## Quick Start (Docker)

The fastest way to get ManusMCP running:

```bash
# Clone the repository
git clone https://github.com/jhacksman/LocalMCP.git
cd LocalMCP/mcp-services/manusmcp

# Set up environment variables
cp .env.example .env
nano .env  # Add your API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY)

# Start with Docker Compose
docker-compose up -d

# Access Flowise UI
# Open http://your-server-ip:8001 in your browser
```

## Manual Installation

### Prerequisites Installation

```bash
# Update package lists
sudo apt update

# Install Node.js and npm
sudo apt install -y nodejs npm

# Install Bun runtime
curl -fsSL https://bun.sh/install | bash
source ~/.bashrc  # or restart your terminal

# Verify Bun installation
bun --version
```

### Conda Environment Setup

```bash
# Install Miniconda (if not already installed)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
source ~/.bashrc  # or restart your terminal

# Create and activate conda environment
conda create -n manusmcp python=3.10 nodejs -y
conda activate manusmcp

# Install additional Python packages
conda install -c conda-forge requests python-dotenv -y
```

### ManusMCP Installation

```bash
# Clone the repository
git clone https://github.com/jhacksman/LocalMCP.git
cd LocalMCP/mcp-services/manusmcp

# Set up environment variables
cp .env.example .env
nano .env  # Add your API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY)

# Install runtime dependencies
cd .runtime
bun install
cd ..
```

## Running ManusMCP

### Start the MCP Server

```bash
# Navigate to the runtime directory
cd .runtime

# Start the MCP server
bun run index.ts

# The server will be available at http://your-server-ip:8003
```

### Start Flowise UI

```bash
# Option 1: Using Docker (recommended)
cd ..  # Return to manusmcp directory
docker-compose up -d

# Option 2: Manual installation (if Docker is not available)
npm install -g flowise
flowise start --PORT=8001
```

The Flowise UI will be available at http://your-server-ip:8001

### Import Agent Flow Configuration

```bash
# Using Flowise UI:
# 1. Open http://your-server-ip:8001 in your browser
# 2. Go to "Agentflows" section
# 3. Click Settings (Top Right)
# 4. Click Import and select the flow.json file
```

## Inspecting the MCP Server

```bash
cd .runtime
bunx @modelcontextprotocol/inspector bun index.ts
```

## Running as a Service (Systemd)

For production deployments, you can set up ManusMCP as a systemd service:

```bash
# Create a systemd service file for MCP Server
sudo nano /etc/systemd/system/manusmcp.service
```

Add the following content:

```
[Unit]
Description=ManusMCP Server
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/LocalMCP/mcp-services/manusmcp/.runtime
ExecStart=/home/your_username/.bun/bin/bun run index.ts
Restart=on-failure
Environment=PATH=/home/your_username/.bun/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=ANTHROPIC_API_KEY=your_api_key
Environment=OPENAI_API_KEY=your_api_key

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable manusmcp.service
sudo systemctl start manusmcp.service
sudo systemctl status manusmcp.service
```

## Troubleshooting Commands

### Check if MCP Server is Running

```bash
# Check if the process is running
ps aux | grep "bun run index.ts"

# Check the port
sudo lsof -i :8003
```

### Check Docker Containers

```bash
# List running containers
docker ps

# Check container logs
docker logs manusmcp-flowise-1
```

### Restart Services

```bash
# Restart MCP Server (if running as systemd service)
sudo systemctl restart manusmcp.service

# Restart Docker containers
docker-compose down
docker-compose up -d
```

### View Logs

```bash
# View MCP Server logs (if running as systemd service)
sudo journalctl -u manusmcp.service -f

# View Docker container logs
docker-compose logs -f
```

## Updating ManusMCP

```bash
# Pull latest changes
git pull

# Update dependencies
cd .runtime
bun install
cd ..

# Restart services
# If using Docker:
docker-compose down
docker-compose up -d

# If running manually:
# Stop the current process and start it again
```

## Security Hardening (Production)

```bash
# Set proper file permissions
chmod 600 .env

# Configure firewall
sudo ufw allow 8001/tcp  # Flowise UI
sudo ufw allow 8003/tcp  # MCP Server
sudo ufw enable

# Set up HTTPS with Nginx (example)
sudo apt install -y nginx certbot python3-certbot-nginx
sudo nano /etc/nginx/sites-available/manusmcp

# Add reverse proxy configuration
# Then enable the site
sudo ln -s /etc/nginx/sites-available/manusmcp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com
```

## Backup Commands

```bash
# Backup flow configuration
cp flow.json flow.json.backup

# Backup environment variables
cp .env .env.backup

# Create a full backup
tar -czvf manusmcp_backup.tar.gz .env flow.json .runtime/
```

## Performance Monitoring

```bash
# Monitor system resources
htop

# Monitor specific process
ps aux | grep "bun run index.ts"

# Check disk usage
df -h
du -sh .runtime/
```

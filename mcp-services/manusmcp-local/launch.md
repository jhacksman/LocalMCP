# ManusMCP-Local Launch Guide

This document provides comprehensive commands for deploying and running the ManusMCP-Local configurable multi-agent system.

## Quick Start

The fastest way to get ManusMCP-Local running:

```bash
# Clone the repository
git clone https://github.com/jhacksman/LocalMCP.git
cd LocalMCP/mcp-services/manusmcp-local

# Set up environment variables
cp .env.example .env
nano .env  # Configure your API keys and model settings

# Install dependencies
cd .runtime
bun install
cd ..

# Start the MCP server
cd .runtime
bun run index.ts
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
conda create -n manusmcp-local python=3.10 nodejs -y
conda activate manusmcp-local

# Install additional Python packages
conda install -c conda-forge requests python-dotenv -y
```

### ManusMCP-Local Installation

```bash
# Clone the repository
git clone https://github.com/jhacksman/LocalMCP.git
cd LocalMCP/mcp-services/manusmcp-local

# Set up environment variables
cp .env.example .env
nano .env  # Configure your API keys and model settings

# Install runtime dependencies
cd .runtime
bun install
cd ..
```

## Using with Local Models

### Setting up Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3

# Start Ollama server
ollama serve

# Configure ManusMCP-Local
# In your .env file:
# OPENAI_BASE_URL=http://localhost:11434/v1
# OPENAI_API_KEY=ollama
# SECONDARY_MODEL=openai/llama3
```

### Setting up LM Studio

```bash
# Download and install LM Studio from https://lmstudio.ai/
# Start the local server with your chosen model
# Configure ManusMCP-Local
# In your .env file:
# OPENAI_BASE_URL=http://localhost:1234/v1
# OPENAI_API_KEY=lmstudio
# SECONDARY_MODEL=openai/your-model-name
```

### Setting up vLLM

```bash
# Install vLLM
pip install vllm

# Start vLLM server with your model
python -m vllm.entrypoints.openai.api_server --model /path/to/your/model --port 8000

# Configure ManusMCP-Local
# In your .env file:
# OPENAI_BASE_URL=http://localhost:8000/v1
# OPENAI_API_KEY=vllm
# SECONDARY_MODEL=openai/your-model-name
```

## Running as a Service (Systemd)

For production deployments, you can set up ManusMCP-Local as a systemd service:

```bash
# Create a systemd service file
sudo nano /etc/systemd/system/manusmcp-local.service
```

Add the following content:

```
[Unit]
Description=ManusMCP-Local Server
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/LocalMCP/mcp-services/manusmcp-local/.runtime
ExecStart=/home/your_username/.bun/bin/bun run index.ts
Restart=on-failure
Environment=PATH=/home/your_username/.bun/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=ANTHROPIC_API_KEY=your_api_key
Environment=OPENAI_API_KEY=your_api_key
Environment=OPENAI_BASE_URL=https://api.openai.com/v1
Environment=PRIMARY_MODEL=anthropic/claude-3-7-latest
Environment=SECONDARY_MODEL=openai/gpt-4o-mini
Environment=PORT=8003
Environment=LOG_LEVEL=info
Environment=ENABLE_BROWSER_SERVICE=true
Environment=ENABLE_FILE_SERVICE=true
Environment=ENABLE_SHELL_SERVICE=true

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable manusmcp-local.service
sudo systemctl start manusmcp-local.service
sudo systemctl status manusmcp-local.service
```

## Troubleshooting

### Model Configuration Issues

If you're having issues with model configuration:

```bash
# Check if your local model server is running
curl http://localhost:11434/v1/models  # For Ollama
curl http://localhost:1234/v1/models   # For LM Studio
curl http://localhost:8000/v1/models   # For vLLM

# Verify environment variables are loaded
cd .runtime
bun run -e "console.log(process.env.OPENAI_BASE_URL, process.env.SECONDARY_MODEL)"

# Check LiteLLM logs
docker logs litellm
```

### Service Connection Issues

```bash
# Check if the service is running
ps aux | grep "bun run index.ts"

# Check the port
sudo lsof -i :8003

# Restart the service
sudo systemctl restart manusmcp-local.service
```

### VRAM Considerations

When running multiple models locally, be aware of VRAM limitations:

```bash
# Check GPU memory usage
nvidia-smi

# Monitor GPU usage in real-time
watch -n 1 nvidia-smi
```

Remember that the total VRAM limit of 64GB applies to all models running simultaneously. Choose model sizes accordingly to avoid out-of-memory errors.

## Updating ManusMCP-Local

```bash
# Pull latest changes
git pull

# Update dependencies
cd .runtime
bun install
cd ..

# Restart the service
sudo systemctl restart manusmcp-local.service
```

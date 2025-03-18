# LocalMCP Deployment Guide

This guide provides instructions for deploying the LocalMCP multi-agent system with MCP-compatible services.

## System Requirements

- **Hardware Requirements**:
  - CPU: 8+ cores recommended
  - RAM: 16GB+ recommended
  - GPU: NVIDIA GPU with 64GB VRAM (can be distributed across multiple GPUs)
  - Storage: 20GB+ free space

- **Software Requirements**:
  - Docker and Docker Compose
  - Node.js 18+
  - Python 3.9+
  - Git

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/jhacksman/LocalMCP.git
   cd LocalMCP
   ```

2. Make the setup and deployment scripts executable:
   ```bash
   chmod +x setup.sh deploy.sh
   ```

3. Run the setup script to install dependencies:
   ```bash
   ./setup.sh
   ```

4. Configure your environment:
   - Edit the `.env` file with your API keys and configuration
   - Adjust VRAM allocation in the `.env` file based on your hardware

5. Deploy the services:
   ```bash
   ./deploy.sh
   ```

6. Access the web interface at http://localhost:8000

## Manual Deployment

If you prefer to deploy services manually or need more control over the deployment process, follow these steps:

### 1. Install Dependencies

For each service, navigate to its directory and install dependencies:

```bash
# MCP Manager
cd mcp-services/mcp-manager
npm install
npm run build

# Vector DB MCP
cd ../vector-db-mcp
npm install
npm run build

# Document MCP
cd ../document-mcp
npm install
npm run build

# Stable Diffusion MCP
cd ../stable-diffusion-mcp
npm install
npm run build

# SQL MCP
cd ../sql
pip install -r requirements.txt

# Venice MCP
cd ../venice-mcp
npm install
npm run build

# Web Interface
cd ../../web-interface
pip install -r requirements.txt
```

### 2. Configure Services

Each service has its own configuration file. Copy the `.env.example` file to `.env` in each service directory and adjust the settings as needed:

```bash
cp mcp-services/mcp-manager/.env.example mcp-services/mcp-manager/.env
cp mcp-services/vector-db-mcp/.env.example mcp-services/vector-db-mcp/.env
cp mcp-services/document-mcp/.env.example mcp-services/document-mcp/.env
cp mcp-services/stable-diffusion-mcp/.env.example mcp-services/stable-diffusion-mcp/.env
cp mcp-services/sql/.env.example mcp-services/sql/.env
cp mcp-services/venice-mcp/.env.example mcp-services/venice-mcp/.env
```

### 3. Start Services

Start each service in a separate terminal:

```bash
# MCP Manager
cd mcp-services/mcp-manager
npm start

# Vector DB MCP
cd mcp-services/vector-db-mcp
npm start

# Document MCP
cd mcp-services/document-mcp
npm start

# Stable Diffusion MCP
cd mcp-services/stable-diffusion-mcp
npm start

# SQL MCP
cd mcp-services/sql
python sql_server.py

# Venice MCP
cd mcp-services/venice-mcp
npm start

# Web Interface
cd web-interface
python app.py
```

## VRAM Management

The LocalMCP system is designed to work within a 64GB VRAM constraint. The MCP Manager service handles VRAM allocation and monitors usage across all services.

### Default VRAM Allocation

- MCP Manager: 0GB (control service only)
- Vector DB MCP: 2GB
- Document MCP: 1GB
- Stable Diffusion MCP: 16GB
- SQL MCP: 1GB
- Venice MCP: 0GB (uses external API)
- ManusMCP: Variable (depends on models loaded)

### Adjusting VRAM Allocation

You can adjust the VRAM allocation for each service by modifying the `VRAM_USAGE_GB` environment variable in the service's `.env` file or in the `docker-compose.yml` file.

## Troubleshooting

### Common Issues

1. **Service fails to start**:
   - Check if the required port is already in use
   - Verify that all dependencies are installed
   - Check the service logs for specific error messages

2. **Out of VRAM errors**:
   - Reduce the VRAM allocation for services
   - Enable model quantization where available
   - Enable CPU offloading for less critical operations

3. **Docker container issues**:
   - Run `docker-compose down` and then `docker-compose up -d` to restart all containers
   - Check container logs with `docker-compose logs -f [service_name]`

### Logs

- Docker logs: `docker-compose logs -f [service_name]`
- Service logs: Check the console output or log files in each service directory

## Testing

To run tests for all services:

```bash
cd mcp-services
./run-tests.sh
```

To test a specific service:

```bash
cd mcp-services/[service_name]
npm test
```

## Updating

To update the LocalMCP system:

1. Pull the latest changes:
   ```bash
   git pull
   ```

2. Rebuild and restart the services:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

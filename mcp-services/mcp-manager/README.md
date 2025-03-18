# MCP Manager

MCP Manager is a central service for coordinating VRAM usage across multiple MCP services in the LocalMCP ecosystem. It provides tools for monitoring GPU memory usage, managing model loading/unloading, and optimizing resource allocation to stay within the 64GB VRAM constraint.

## Features

- Real-time VRAM usage monitoring across all services
- Model loading/unloading coordination
- Automatic VRAM optimization
- Scheduling system for model operations
- HTTP API for service registration and status reporting

## Configuration

All configuration is done through environment variables in the `.env` file:

```
# Server Configuration
PORT=8010
LOG_LEVEL=info

# VRAM Management
MAX_VRAM_USAGE_GB=60
VRAM_RESERVE_GB=4
ENABLE_AUTO_UNLOAD=true
UNLOAD_TIMEOUT_MINUTES=30

# Service Registration
SERVICES_CONFIG_PATH=./services.json
```

### Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| PORT | Port for the HTTP server | 8010 |
| LOG_LEVEL | Logging level (debug, info, warn, error) | info |
| MAX_VRAM_USAGE_GB | Maximum allowed VRAM usage in GB | 60 |
| VRAM_RESERVE_GB | VRAM to reserve for system operations | 4 |
| ENABLE_AUTO_UNLOAD | Automatically unload inactive models | true |
| UNLOAD_TIMEOUT_MINUTES | Time before inactive models are unloaded | 30 |
| SERVICES_CONFIG_PATH | Path to services configuration file | ./services.json |

## Installation

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file to customize settings:
   ```bash
   nano .env
   ```

3. Install dependencies:
   ```bash
   npm install
   ```

## Usage

Start the MCP Manager server:

```bash
npm start
```

The server will be available at:
- MCP Protocol: Standard input/output
- HTTP Server: http://localhost:8010 (or your configured PORT)

## MCP Tools

The MCP Manager provides the following tools:

### get_vram_status

Returns the current VRAM usage status across all registered services.

**Input**: None

**Output**:
```json
{
  "total_vram_gb": 64,
  "used_vram_gb": 32,
  "available_vram_gb": 32,
  "services": [
    {
      "name": "stable-diffusion-mcp",
      "used_vram_gb": 16,
      "models": ["stable-diffusion-xl"]
    },
    {
      "name": "vector-db-mcp",
      "used_vram_gb": 2,
      "models": ["all-MiniLM-L6-v2"]
    }
  ]
}
```

### unload_model

Unloads a specific model to free VRAM.

**Input**:
```json
{
  "model_name": "stable-diffusion-xl",
  "service_name": "stable-diffusion-mcp"
}
```

**Output**:
```json
{
  "success": true,
  "freed_vram_gb": 16,
  "message": "Model stable-diffusion-xl unloaded successfully"
}
```

### register_service

Registers a new service with the MCP Manager.

**Input**:
```json
{
  "service_name": "document-mcp",
  "service_url": "http://localhost:8012",
  "models": [
    {
      "name": "tesseract-ocr",
      "vram_usage_gb": 1
    }
  ]
}
```

**Output**:
```json
{
  "success": true,
  "message": "Service document-mcp registered successfully"
}
```

## HTTP API

The MCP Manager also provides an HTTP API for service registration and status reporting:

- `GET /health` - Health check endpoint
- `GET /vram/status` - Get current VRAM usage status
- `POST /vram/unload` - Unload a specific model
- `POST /services/register` - Register a new service
- `GET /services/list` - List all registered services

## Integration with LocalMCP

MCP Manager is designed to work with the LocalMCP framework. To integrate:

1. Configure each MCP service to register with the MCP Manager on startup
2. Update the web interface to display VRAM usage information
3. Implement model loading/unloading coordination in each service

## VRAM Optimization Strategies

The MCP Manager implements several strategies to optimize VRAM usage:

1. **Sequential Model Loading**: Only load one model at a time
2. **Automatic Unloading**: Unload inactive models after a configurable timeout
3. **Priority-based Scheduling**: Prioritize critical services for VRAM allocation
4. **VRAM Reservation**: Reserve a portion of VRAM for system operations

## Troubleshooting

- If the server fails to start, check that the NVIDIA drivers are installed and working
- For service registration issues, verify that the service URL is accessible
- If VRAM usage reporting is inaccurate, try restarting the NVIDIA driver with `sudo systemctl restart nvidia-persistenced`

## Development

For development:

```bash
npm run dev
```

This will start the server in development mode with hot reloading.

## Testing

Run the tests:

```bash
npm test
```

## License

MIT

# ManusMCP-Local

ManusMCP-Local is a configurable version of the ManusMCP multi-agent system with support for custom API endpoints and service toggles.

## Features

- Configurable OpenAI and Anthropic API base URLs
- Ability to enable/disable specific services (Browser, File, Shell)
- Customizable port and logging level
- HTTP server with health endpoint

## Configuration

All configuration is done through environment variables in the `.env` file:

```
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
ANTHROPIC_BASE_URL=https://api.anthropic.com
PORT=8003
LOG_LEVEL=info
ENABLE_BROWSER_SERVICE=true
ENABLE_FILE_SERVICE=true
ENABLE_SHELL_SERVICE=true
```

### Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| ANTHROPIC_API_KEY | Your Anthropic API key | (required) |
| OPENAI_API_KEY | Your OpenAI API key | (required) |
| OPENAI_BASE_URL | Base URL for OpenAI API | https://api.openai.com/v1 |
| ANTHROPIC_BASE_URL | Base URL for Anthropic API | https://api.anthropic.com |
| PORT | Port for the HTTP server | 8003 |
| LOG_LEVEL | Logging level (debug, info, warn, error) | info |
| ENABLE_BROWSER_SERVICE | Enable browser automation service | true |
| ENABLE_FILE_SERVICE | Enable file system operations | true |
| ENABLE_SHELL_SERVICE | Enable shell command execution | true |

## Installation

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file to add your API keys and customize settings:
   ```bash
   nano .env
   ```

3. Install dependencies:
   ```bash
   cd .runtime
   bun install
   ```

## Usage

Start the MCP server:

```bash
cd .runtime
bun run index.ts
```

The server will be available at:
- MCP Protocol: Standard input/output
- HTTP Server: http://localhost:8003 (or your configured PORT)

## Health Check

You can verify the server is running by accessing the health endpoint:

```bash
curl http://localhost:8003/health
```

## Using with Custom API Endpoints

ManusMCP-Local allows you to use alternative API endpoints for OpenAI and Anthropic, which is useful for:

- Using local LLM servers (like LM Studio, Ollama, etc.)
- Connecting to proxy services
- Using regional API endpoints
- Testing with mock services

Example configuration for using a local LLM server:

```
OPENAI_BASE_URL=http://localhost:1234/v1
```

## Docker Deployment

A Dockerfile is provided for containerized deployment:

```bash
docker build -t manusmcp-local .
docker run -p 8003:8003 --env-file .env manusmcp-local
```

## Integration with LocalMCP

ManusMCP-Local is designed to work with the LocalMCP framework. To integrate:

1. Configure the service in the web interface at `web-interface/app.py`
2. Set the URL to `http://localhost:8003` (or your configured port)
3. Enable the service in the web interface

## Troubleshooting

- If you encounter connection issues with custom API endpoints, verify the endpoint is accessible and properly formatted
- For service-specific issues, check the logs and consider enabling only that service for debugging
- If the server fails to start, ensure all required environment variables are set

## Source

Based on the ManusMCP multi-agent system: https://github.com/mantrakp04/manusmcp

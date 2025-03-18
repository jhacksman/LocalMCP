# ManusMCP-Local

ManusMCP-Local is a configurable version of the ManusMCP multi-agent system with support for custom API endpoints, model selection, and service toggles.

## Features

- Configurable OpenAI and Anthropic API base URLs
- Customizable model selection for primary and secondary models
- Ability to enable/disable specific services (Browser, File, Shell)
- Customizable port and logging level
- HTTP server with health endpoint
- Support for local LLM hosting with OpenAI-compatible APIs

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
| PRIMARY_MODEL | Primary model identifier | anthropic/claude-3-7-latest |
| SECONDARY_MODEL | Secondary model identifier | openai/gpt-4o-mini |
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

## Using with Local Models

ManusMCP-Local allows you to use locally hosted models with OpenAI-compatible APIs. Here are some examples:

### Using with Ollama

```
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
PRIMARY_MODEL=anthropic/claude-3-7-latest
SECONDARY_MODEL=openai/llama3
```

### Using with LM Studio

```
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lmstudio
PRIMARY_MODEL=anthropic/claude-3-7-latest
SECONDARY_MODEL=openai/mixtral-8x7b
```

### Using with vLLM

```
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=vllm
PRIMARY_MODEL=anthropic/claude-3-7-latest
SECONDARY_MODEL=openai/mistral-7b
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

## Model Configuration Details

The system uses LiteLLM to manage model configurations. The model names follow the format:

- For OpenAI models: `openai/model-name` (e.g., `openai/gpt-4o-mini`)
- For Anthropic models: `anthropic/model-name` (e.g., `anthropic/claude-3-7-latest`)
- For local models: Use the OpenAI format with your local model name (e.g., `openai/llama3`)

When using local models with OpenAI-compatible APIs, make sure your local server supports the OpenAI API format.

## Source

Based on the ManusMCP multi-agent system: https://github.com/mantrakp04/manusmcp

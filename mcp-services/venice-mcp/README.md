# Venice.ai MCP Server

A Model Context Protocol (MCP) compatible server for Venice.ai's OpenAI-compatible API with <think> tags filtering.

## Features

- Removes <think> tags from Venice.ai API responses
- Exposes a clean API endpoint for chat completions
- Configurable model selection
- Health check endpoint

## Installation

```bash
# Clone the repository
git clone https://github.com/jhacksman/LocalMCP.git
cd LocalMCP/mcp-services/venice-mcp

# Install dependencies
npm install
```

## Configuration

The server can be configured using environment variables:

- `VENICE_API_BASE_URL`: Base URL for Venice.ai API (default: "https://api.venice.ai/api/v1")
- `VENICE_API_KEY`: Your Venice.ai API key
- `VENICE_MODEL`: Default model to use (default: "deepseek-r1-671b")
- `PORT`: Port to run the server on (default: 3000)

## Usage

```bash
# Start the server
node venice-mcp-server.js
```

## API Endpoints

### Health Check

```
GET /health
```

Returns the status of the server.

### Chat Completion

```
POST /api/chat
```

Request body:
```json
{
  "prompt": "Tell me a joke about programming",
  "system_prompt": "You are a helpful assistant",
  "model": "deepseek-r1-671b",
  "max_tokens": 1000
}
```

Response:
```json
{
  "original": "<think>Original response with think tags</think>",
  "cleaned": "Cleaned response without think tags",
  "model": "deepseek-r1-671b",
  "usage": {
    "prompt_tokens": 10,
    "total_tokens": 100,
    "completion_tokens": 90
  }
}
```

## <think> Tags Filter

The server automatically removes <think> tags from Venice.ai API responses. These tags contain the model's internal reasoning process and are not meant to be shown to end users.

The filter handles:
- Properly closed <think> tags
- Unclosed <think> tags
- Multiple <think> tags
- Content entirely within <think> tags

## Testing

To test the <think> tags filter:

```bash
node test-think-tags-filter.js
```

## Integration with MCP

This server can be integrated with the Model Context Protocol (MCP) to provide a standardized interface for AI tools.

Example MCP integration:

```javascript
const { FastMCP } = require("@modelcontextprotocol/sdk");
const mcp = new FastMCP("Venice.ai MCP Server");

mcp.tool(
  "chat_completion",
  {
    prompt: z.string(),
    system_prompt: z.string().optional(),
    model: z.string().optional(),
    max_tokens: z.number().optional()
  },
  async ({ prompt, system_prompt, model, max_tokens }) => {
    // Call the Venice.ai API and filter <think> tags
    // ...
    return {
      content: [{ type: "text", text: cleanedContent }]
    };
  }
);
```

## License

MIT

# Venice.ai MCP Server

This project implements a Model Context Protocol (MCP) server for Venice.ai's OpenAI-compatible API. It includes a special filter to remove `<think>` tags from the model's responses, providing clean and usable content.

## Features

- MCP-compatible server for Venice.ai API
- Automatic removal of `<think>` tags from responses
- TypeScript implementation with Zod schema validation
- Express HTTP server for testing and debugging

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
4. Add your Venice.ai API key to the `.env` file

## Usage

### Start the MCP Server

```bash
npm start
```

This will start the MCP server using stdio transport, which is compatible with MCP clients.

### Test the Think Tags Filter

```bash
npm test
```

This will run the test suite for the think tags filter to ensure it correctly removes all types of think tags from responses.

### Test with HTTP Server

```bash
node venice-mcp-server.js
```

This will start an HTTP server on port 3000 (or the port specified in your `.env` file). You can then test the API using:

```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Tell me a joke about programming.","system_prompt":"You are a helpful assistant.","max_tokens":100}'
```

## Think Tags Filter

The Venice.ai API sometimes includes `<think>` tags in responses, which contain the model's internal reasoning. This implementation automatically removes these tags to provide clean, usable content.

The filter handles:
- Nested `<think>` tags
- Unclosed `<think>` tags
- Content entirely within `<think>` tags

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| VENICE_API_BASE_URL | Base URL for Venice.ai API | https://api.venice.ai/api/v1 |
| VENICE_API_KEY | Your Venice.ai API key | (required) |
| VENICE_MODEL | Default model to use | deepseek-r1-671b |
| PORT | Port for HTTP server | 3000 |

## MCP Tool Schema

The MCP server exposes a single tool:

```typescript
mcp.tool(
  "chat_completion",
  {
    prompt: z.string(),
    system_prompt: z.string().optional(),
    model: z.string().optional(),
    max_tokens: z.number().optional()
  },
  async ({ prompt, system_prompt, model, max_tokens }) => {
    // Implementation
  }
);
```

## License

MIT

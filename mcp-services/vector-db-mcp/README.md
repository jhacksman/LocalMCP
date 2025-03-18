# Vector Database MCP Service

MCP-compatible service for vector database operations including embedding generation and semantic search. This service provides tools for working with vector embeddings while maintaining low VRAM usage.

## Features

- Generate embeddings from text using lightweight models
- Store embeddings in vector database
- Perform semantic search with customizable parameters
- Low VRAM usage (approximately 2GB)
- Integration with MCP Manager for VRAM coordination

## Architecture

The Vector Database MCP Service uses the following components:

- **Embedding Model**: [Xenova/all-MiniLM-L6-v2](https://huggingface.co/Xenova/all-MiniLM-L6-v2) - A lightweight sentence transformer model that creates 384-dimensional embeddings
- **Vector Database**: ChromaDB - An efficient, open-source vector database
- **MCP Server**: Model Context Protocol server for standardized AI tool integration
- **HTTP API**: REST API for direct integration with other services

## Configuration

Configuration is done through environment variables:

```
# Server Configuration
PORT=8005
LOG_LEVEL=info

# Vector Database Configuration
VECTOR_DB_PATH=./data
EMBEDDING_MODEL=all-MiniLM-L6-v2
VRAM_USAGE_GB=2

# MCP Manager Integration
MCP_MANAGER_URL=http://localhost:8010
SERVICE_NAME=vector-db-mcp
SERVICE_URL=http://localhost:8005
```

## MCP Tools

The service provides the following MCP tools:

### generate_embedding

Generates vector embeddings from text input.

**Input**:
```json
{
  "text": "The text to generate embeddings for",
  "model": "all-MiniLM-L6-v2" // Optional, defaults to configured model
}
```

**Output**:
```json
{
  "content": [
    { "type": "text", "text": "Embedding generated successfully" }
  ],
  "metadata": {
    "model": "all-MiniLM-L6-v2",
    "vector_size": 384,
    "embedding_id": "12345"
  }
}
```

### store_embedding

Stores a document with its embedding in the vector database.

**Input**:
```json
{
  "text": "The document text to store",
  "collection": "my_collection",
  "metadata": { "source": "example", "author": "user" } // Optional
}
```

**Output**:
```json
{
  "content": [
    { "type": "text", "text": "Document stored successfully" }
  ],
  "metadata": {
    "document_id": "67890",
    "collection": "my_collection"
  }
}
```

### vector_search

Performs semantic search using the vector database.

**Input**:
```json
{
  "query": "The search query text",
  "collection": "my_collection",
  "limit": 5, // Optional, defaults to 5
  "threshold": 0.7 // Optional, defaults to 0.7
}
```

**Output**:
```json
{
  "content": [
    { 
      "type": "text", 
      "text": "[{\"text\":\"Document 1 content\",\"score\":0.92,\"metadata\":{\"source\":\"example\"}}, ...]" 
    }
  ],
  "metadata": {
    "total_results": 5,
    "search_time_ms": 12
  }
}
```

## Installation

1. Clone the repository
2. Install dependencies: `npm install`
3. Copy the example environment file: `cp .env.example .env`
4. Edit the `.env` file to customize settings
5. Start the service: `npm start`

## Development

For development:

```bash
npm run dev
```

This will start the server in development mode with hot reloading.

## Integration with MCP Manager

On startup, the service automatically registers with the MCP Manager to coordinate VRAM usage. The service reports its VRAM requirements and can respond to unload requests when VRAM needs to be freed for other services.

## License

MIT

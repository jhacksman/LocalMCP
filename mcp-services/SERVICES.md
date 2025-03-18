# LocalMCP Services Documentation

This document provides an overview of all MCP-compatible services in the LocalMCP project, their configuration options, and usage examples.

## Table of Contents

1. [MCP Manager](#mcp-manager)
2. [Vector Database MCP](#vector-database-mcp)
3. [Document Processing MCP](#document-processing-mcp)
4. [Stable Diffusion MCP](#stable-diffusion-mcp)
5. [Venice MCP](#venice-mcp)
6. [SQL MCP](#sql-mcp)
7. [ManusMCP](#manusmcp)

## MCP Manager

The MCP Manager service coordinates VRAM usage across all MCP services to ensure the system stays within the 64GB VRAM constraint.

### Features

- Global VRAM usage tracking
- Automatic model unloading when VRAM is needed
- Service registration and discovery
- Priority-based VRAM allocation
- REST API for VRAM management

### Configuration

| Option | Description | Default | Required |
|--------|-------------|---------|----------|
| PORT | HTTP server port | 8010 | No |
| LOG_LEVEL | Logging level (debug, info, warn, error) | info | No |
| MAX_VRAM_USAGE_GB | Maximum VRAM usage in GB | 60 | No |
| VRAM_RESERVE_GB | VRAM to reserve for system use | 4 | No |
| ENABLE_AUTO_UNLOAD | Whether to automatically unload models | true | No |
| UNLOAD_TIMEOUT_MINUTES | Time before unused models are unloaded | 30 | No |
| SERVICES_CONFIG_PATH | Path to services configuration file | ./services.json | No |

### API Endpoints

#### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

#### GET /vram_usage

Get current VRAM usage information.

**Response:**
```json
{
  "vram_usage_gb": 32.5,
  "max_vram_gb": 64,
  "available_vram_gb": 31.5,
  "services": [
    {
      "name": "stable-diffusion-mcp",
      "vram_usage_gb": 8
    },
    {
      "name": "vector-db-mcp",
      "vram_usage_gb": 2
    }
  ]
}
```

#### POST /services/register

Register a service with the MCP Manager.

**Request:**
```json
{
  "service_name": "stable-diffusion-mcp",
  "service_url": "http://localhost:8015",
  "models": [
    {
      "name": "stabilityai/stable-diffusion-xl-base-1.0",
      "vram_usage_gb": 8
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Service registered successfully"
}
```

#### POST /services/request_vram

Request VRAM allocation for a service.

**Request:**
```json
{
  "service_name": "stable-diffusion-mcp",
  "vram_needed_gb": 8,
  "priority": "high"
}
```

**Response:**
```json
{
  "success": true,
  "vram_allocated_gb": 8,
  "unloaded_services": ["vector-db-mcp"]
}
```

### Installation

```bash
# Clone the repository
git clone https://github.com/jhacksman/LocalMCP.git
cd LocalMCP/mcp-services/mcp-manager

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env file as needed

# Start the service
npm start
```

### VRAM Optimization

- The MCP Manager reserves a small amount of VRAM (default 4GB) for system use
- Services are unloaded based on last-used time and priority
- High-priority services are unloaded last
- Services can specify their VRAM requirements during registration

## Vector Database MCP

The Vector Database MCP service provides vector embedding and similarity search capabilities with minimal VRAM usage.

### Features

- Text embedding generation
- Vector similarity search
- Document indexing
- Low VRAM usage (~2GB)
- MCP Manager integration

### Configuration

| Option | Description | Default | Required |
|--------|-------------|---------|----------|
| PORT | HTTP server port | 8011 | No |
| LOG_LEVEL | Logging level (debug, info, warn, error) | info | No |
| EMBEDDING_MODEL | Model to use for embeddings | all-MiniLM-L6-v2 | No |
| VECTOR_DB_PATH | Path to vector database | ./vector_db | No |
| VRAM_USAGE_GB | VRAM usage in GB | 2 | No |
| MCP_MANAGER_URL | URL of MCP Manager | http://localhost:8010 | No |
| SERVICE_NAME | Name of this service | vector-db-mcp | No |
| SERVICE_URL | URL of this service | http://localhost:8011 | No |

### MCP Tools

#### generate_embedding

Generates vector embeddings for text.

**Input:**
```json
{
  "text": "This is a sample text to embed",
  "model": "all-MiniLM-L6-v2"
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "embedding",
      "embedding": [0.123, 0.456, ...]
    }
  ],
  "metadata": {
    "model": "all-MiniLM-L6-v2",
    "dimensions": 384
  }
}
```

#### similarity_search

Performs similarity search against stored vectors.

**Input:**
```json
{
  "query": "Sample query text",
  "collection_name": "my_documents",
  "top_k": 5
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Results:\n1. Document A (score: 0.92)\n2. Document B (score: 0.85)\n3. Document C (score: 0.76)\n4. Document D (score: 0.71)\n5. Document E (score: 0.65)"
    }
  ],
  "metadata": {
    "matches": [
      {
        "id": "doc_a",
        "score": 0.92,
        "metadata": {
          "title": "Document A",
          "source": "collection_1"
        }
      },
      ...
    ]
  }
}
```

#### index_document

Indexes a document in the vector database.

**Input:**
```json
{
  "document": "This is the content of the document to index",
  "metadata": {
    "title": "Sample Document",
    "author": "John Doe"
  },
  "collection_name": "my_documents",
  "document_id": "doc_123"
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Document indexed successfully with ID: doc_123"
    }
  ],
  "metadata": {
    "document_id": "doc_123",
    "collection": "my_documents"
  }
}
```

### Installation

```bash
# Clone the repository
git clone https://github.com/jhacksman/LocalMCP.git
cd LocalMCP/mcp-services/vector-db-mcp

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env file as needed

# Start the service
npm start
```

### VRAM Optimization

- Uses lightweight embedding models (all-MiniLM-L6-v2) with ~2GB VRAM usage
- Implements model unloading when requested by MCP Manager
- Batches embedding operations to minimize VRAM fragmentation
- Uses CPU for vector search operations to minimize VRAM usage

## Document Processing MCP

The Document Processing MCP service provides document text extraction and OCR capabilities with minimal VRAM usage.

### Features

- Extract text from PDF documents
- Perform OCR on images
- Process documents sequentially to minimize VRAM usage
- Integration with MCP Manager for VRAM coordination
- Lightweight implementation (~1GB VRAM)

### Configuration

| Option | Description | Default | Required |
|--------|-------------|---------|----------|
| PORT | HTTP server port | 8012 | No |
| LOG_LEVEL | Logging level (debug, info, warn, error) | info | No |
| TEMP_DIR | Directory for temporary files | ./temp | No |
| OCR_WORKER_THREADS | Number of OCR worker threads | 2 | No |
| PDF_WORKER_THREADS | Number of PDF worker threads | 2 | No |
| VRAM_USAGE_GB | VRAM usage in GB | 1 | No |
| MCP_MANAGER_URL | URL of MCP Manager | http://localhost:8010 | No |
| SERVICE_NAME | Name of this service | document-mcp | No |
| SERVICE_URL | URL of this service | http://localhost:8012 | No |

### MCP Tools

#### extract_pdf_text

Extracts text from PDF documents.

**Input:**
```json
{
  "file_path": "/path/to/document.pdf",
  "page_numbers": [1, 2, 3]
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Extracted text from the PDF document..."
    }
  ],
  "metadata": {
    "page_count": 10,
    "extracted_pages": [1, 2, 3]
  }
}
```

#### ocr_image

Performs OCR on an image to extract text.

**Input:**
```json
{
  "image_path": "/path/to/image.jpg",
  "language": "eng",
  "preprocess": true
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Extracted text from the image..."
    }
  ],
  "metadata": {
    "confidence": 0.95,
    "processing_time_ms": 1200
  }
}
```

#### convert_document_to_text

Converts various document formats to text.

**Input:**
```json
{
  "file_path": "/path/to/document.docx",
  "output_format": "text"
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Extracted text from the document..."
    }
  ],
  "metadata": {
    "original_format": "docx",
    "processing_time_ms": 1500
  }
}
```

### Installation

```bash
# Clone the repository
git clone https://github.com/jhacksman/LocalMCP.git
cd LocalMCP/mcp-services/document-mcp

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env file as needed

# Start the service
npm start
```

### VRAM Optimization

- Sequential document processing to minimize VRAM usage
- Worker threads for PDF and OCR processing
- Lightweight OCR implementation with minimal VRAM requirements
- Image preprocessing to improve OCR accuracy and reduce processing time

## Stable Diffusion MCP

The Stable Diffusion MCP service provides image generation capabilities using Stable Diffusion models while managing VRAM usage.

### Features

- Generate images from text prompts
- Support for multiple model variants (SD 1.5, SD 2.1, SDXL)
- 4-bit quantization for reduced VRAM usage
- Model offloading capabilities
- Integration with MCP Manager for VRAM coordination

### Configuration

| Option | Description | Default | Required |
|--------|-------------|---------|----------|
| PORT | HTTP server port | 8015 | No |
| LOG_LEVEL | Logging level (debug, info, warn, error) | info | No |
| MODEL_ID | Hugging Face model ID | stabilityai/stable-diffusion-xl-base-1.0 | No |
| MODEL_CACHE_DIR | Directory for model cache | ./model_cache | No |
| VRAM_USAGE_GB | VRAM usage in GB | 16 | No |
| ENABLE_4BIT_QUANTIZATION | Whether to use 4-bit quantization | true | No |
| ENABLE_CPU_OFFLOAD | Whether to offload model to CPU | true | No |
| MAX_IMAGE_WIDTH | Maximum image width | 1024 | No |
| MAX_IMAGE_HEIGHT | Maximum image height | 1024 | No |
| MCP_MANAGER_URL | URL of MCP Manager | http://localhost:8010 | No |
| SERVICE_NAME | Name of this service | stable-diffusion-mcp | No |
| SERVICE_URL | URL of this service | http://localhost:8015 | No |

### Model Options

| Model | MODEL_ID | VRAM Usage (FP16) | VRAM Usage (4-bit) |
|-------|----------|-------------------|-------------------|
| SD 1.5 | runwayml/stable-diffusion-v1-5 | ~8GB | ~4GB |
| SD 2.1 | stabilityai/stable-diffusion-2-1 | ~8GB | ~4GB |
| SDXL | stabilityai/stable-diffusion-xl-base-1.0 | ~16GB | ~8GB |

### MCP Tools

#### generate_image

Generates an image from a text prompt.

**Input:**
```json
{
  "prompt": "A beautiful sunset over mountains",
  "negative_prompt": "blurry, low quality",
  "width": 512,
  "height": 512,
  "num_inference_steps": 50,
  "guidance_scale": 7.5
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "image",
      "data": "base64_encoded_image_data"
    }
  ],
  "metadata": {
    "model": "stabilityai/stable-diffusion-xl-base-1.0",
    "generation_time_ms": 5000
  }
}
```

#### get_model_info

Returns information about the currently loaded model.

**Input:** None

**Output:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Model: stabilityai/stable-diffusion-xl-base-1.0\nVRAM Usage: 8GB (4-bit quantized)\nMax Dimensions: 1024x1024"
    }
  ]
}
```

### Installation

```bash
# Clone the repository
git clone https://github.com/jhacksman/LocalMCP.git
cd LocalMCP/mcp-services/stable-diffusion-mcp

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env file as needed

# Start the service
npm start
```

### VRAM Optimization

- 4-bit quantization reduces model precision to 4 bits, cutting VRAM usage by up to 75%
- CPU offloading moves parts of the model to CPU when not in use
- Sequential processing ensures only one image is generated at a time
- Model unloading frees VRAM when requested by MCP Manager

## Venice MCP

The Venice MCP service provides an OpenAI-compatible API for accessing Venice.ai's large language models.

### Features

- OpenAI-compatible API
- Support for Venice.ai models
- Filtering of `<think>` tags from model output
- Low VRAM usage (API-based)
- MCP Manager integration

### Configuration

| Option | Description | Default | Required |
|--------|-------------|---------|----------|
| PORT | HTTP server port | 8005 | No |
| LOG_LEVEL | Logging level (debug, info, warn, error) | info | No |
| VENICE_API_KEY | Venice.ai API key (set in .env file) | - | Yes |
| VENICE_API_BASE | Venice.ai API base URL | https://api.venice.ai/api/v1 | No |
| VENICE_MODEL | Venice.ai model to use | deepseek-r1-671b | No |
| FILTER_THINK_TAGS | Whether to filter `<think>` tags | true | No |
| MCP_MANAGER_URL | URL of MCP Manager | http://localhost:8010 | No |
| SERVICE_NAME | Name of this service | venice-mcp | No |
| SERVICE_URL | URL of this service | http://localhost:8005 | No |

### MCP Tools

#### chat_completion

Generates a chat completion response.

**Input:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Tell me about the Model Context Protocol."
    }
  ],
  "model": "deepseek-r1-671b",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "The Model Context Protocol (MCP) is a standardized way for applications to interact with AI models and tools..."
    }
  ],
  "metadata": {
    "model": "deepseek-r1-671b",
    "usage": {
      "prompt_tokens": 42,
      "completion_tokens": 156,
      "total_tokens": 198
    }
  }
}
```

#### text_completion

Generates a text completion response.

**Input:**
```json
{
  "prompt": "The Model Context Protocol is",
  "model": "deepseek-r1-671b",
  "temperature": 0.7,
  "max_tokens": 100
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "a standardized way for applications to interact with AI models and tools..."
    }
  ],
  "metadata": {
    "model": "deepseek-r1-671b",
    "usage": {
      "prompt_tokens": 5,
      "completion_tokens": 20,
      "total_tokens": 25
    }
  }
}
```

### Installation

```bash
# Clone the repository
git clone https://github.com/jhacksman/LocalMCP.git
cd LocalMCP/mcp-services/venice-mcp

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env file as needed
# Add your Venice.ai API key to .env

# Start the service
npm start
```

### VRAM Optimization

- Uses API-based access to Venice.ai models, requiring no local VRAM
- Implements efficient streaming of responses
- Filters `<think>` tags to reduce token usage

## SQL MCP

The SQL MCP service provides SQL database querying capabilities through natural language.

### Features

- Natural language to SQL conversion
- SQLite database integration
- Query execution and result formatting
- Data visualization capabilities
- MCP Manager integration

### Configuration

| Option | Description | Default | Required |
|--------|-------------|---------|----------|
| PORT | HTTP server port | 8002 | No |
| LOG_LEVEL | Logging level (debug, info, warn, error) | info | No |
| DATABASE_PATH | Path to SQLite database | ./database.db | No |
| MODEL_URL | URL of the language model to use | http://localhost:7000 | No |
| MCP_MANAGER_URL | URL of MCP Manager | http://localhost:8010 | No |
| SERVICE_NAME | Name of this service | sql-mcp | No |
| SERVICE_URL | URL of this service | http://localhost:8002 | No |

### MCP Tools

#### query_data

Executes SQL queries safely.

**Input:**
```json
{
  "sql": "SELECT * FROM users LIMIT 10"
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "id|name|email\n1|John Doe|john@example.com\n2|Jane Smith|jane@example.com\n..."
    }
  ],
  "metadata": {
    "row_count": 10,
    "columns": ["id", "name", "email"]
  }
}
```

#### natural_language_query

Converts natural language to SQL and executes the query.

**Input:**
```json
{
  "query": "Show me the top 10 users by registration date"
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "id|name|email|registration_date\n1|John Doe|john@example.com|2023-01-15\n2|Jane Smith|jane@example.com|2023-01-20\n..."
    }
  ],
  "metadata": {
    "sql": "SELECT id, name, email, registration_date FROM users ORDER BY registration_date DESC LIMIT 10",
    "row_count": 10
  }
}
```

### Installation

```bash
# Clone the repository
git clone https://github.com/jhacksman/LocalMCP.git
cd LocalMCP/mcp-services/sql

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python data/init_db.py

# Start the service
python sql_server.py
```

### VRAM Optimization

- Uses external language models via API to minimize VRAM usage
- Implements efficient query execution with result pagination
- Optimizes database connections to reduce memory usage

## ManusMCP

The ManusMCP service provides a multi-agent system with browser automation, shell command execution, and file manipulation capabilities.

### Features

- Browser automation
- Shell command execution
- File manipulation
- Multi-agent coordination
- MCP Manager integration

### Configuration

| Option | Description | Default | Required |
|--------|-------------|---------|----------|
| PORT | HTTP server port | 8003 | No |
| LOG_LEVEL | Logging level (debug, info, warn, error) | info | No |
| MODEL_URL | URL of the language model to use | http://localhost:7000 | No |
| BROWSER_HEADLESS | Whether to run browser in headless mode | true | No |
| BROWSER_TIMEOUT | Browser operation timeout in seconds | 30 | No |
| SHELL_TIMEOUT | Shell command timeout in seconds | 60 | No |
| MCP_MANAGER_URL | URL of MCP Manager | http://localhost:8010 | No |
| SERVICE_NAME | Name of this service | manusmcp | No |
| SERVICE_URL | URL of this service | http://localhost:8003 | No |

### MCP Tools

#### browse_web

Automates browser interactions.

**Input:**
```json
{
  "url": "https://www.example.com",
  "actions": [
    {
      "type": "click",
      "selector": "#login-button"
    },
    {
      "type": "type",
      "selector": "#username",
      "text": "user123"
    }
  ]
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Browser actions completed successfully"
    },
    {
      "type": "image",
      "data": "base64_encoded_screenshot"
    }
  ],
  "metadata": {
    "url": "https://www.example.com/dashboard",
    "title": "User Dashboard"
  }
}
```

#### execute_shell

Executes shell commands.

**Input:**
```json
{
  "command": "ls -la",
  "working_dir": "/home/user/project"
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "total 24\ndrwxr-xr-x  5 user user 4096 Mar 15 10:30 .\ndrwxr-xr-x 20 user user 4096 Mar 15 10:25 ..\n-rw-r--r--  1 user user  512 Mar 15 10:30 file1.txt\n..."
    }
  ],
  "metadata": {
    "exit_code": 0,
    "execution_time_ms": 25
  }
}
```

#### manipulate_file

Reads, writes, or modifies files.

**Input:**
```json
{
  "action": "read",
  "path": "/home/user/project/file1.txt"
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Content of file1.txt..."
    }
  ],
  "metadata": {
    "file_size": 512,
    "last_modified": "2023-03-15T10:30:00Z"
  }
}
```

### Installation

```bash
# Clone the repository
git clone https://github.com/jhacksman/LocalMCP.git
cd LocalMCP/mcp-services/manusmcp

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env file as needed

# Start the service
npm start
```

### VRAM Optimization

- Uses external language models via API to minimize VRAM usage
- Implements efficient browser automation with resource cleanup
- Optimizes shell command execution to reduce memory usage

## Deployment

For detailed deployment instructions, see the [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) file.

### Quick Start

```bash
# Clone the repository
git clone https://github.com/jhacksman/LocalMCP.git
cd LocalMCP

# Start all services using Docker Compose
docker-compose up -d

# Or start individual services
cd mcp-services/mcp-manager
npm install
npm start
```

### VRAM Management

The LocalMCP system is designed to work within a 64GB VRAM constraint. The MCP Manager service coordinates VRAM usage across all services to ensure this constraint is met.

#### VRAM Usage by Service

| Service | VRAM Usage (GB) | Notes |
|---------|----------------|-------|
| MCP Manager | 0 | No model loading |
| Vector Database MCP | 2 | Embedding model |
| Document Processing MCP | 1 | OCR model |
| Stable Diffusion MCP | 8-16 | Depends on model and quantization |
| Venice MCP | 0 | API-based, no local VRAM |
| SQL MCP | 0 | Uses external models |
| ManusMCP | 0 | Uses external models |
| Gemma3-27B | 27 | Language model |
| QWQ-32B | 32 | Language model |

#### VRAM Optimization Tips

1. Use 4-bit quantization for Stable Diffusion models
2. Enable CPU offloading for models when possible
3. Use the MCP Manager to coordinate VRAM usage
4. Disable services that are not needed
5. Use API-based services when possible
6. Run only one large language model at a time

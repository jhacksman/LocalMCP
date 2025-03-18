# Document Processing MCP Service

MCP-compatible service for document processing, including PDF text extraction and OCR (Optical Character Recognition) capabilities. This service provides tools for extracting text from various document formats while maintaining low VRAM usage.

## Features

- Extract text from PDF documents
- Perform OCR on images to extract text
- Process documents sequentially to minimize VRAM usage
- Integration with MCP Manager for VRAM coordination
- Lightweight implementation (~1GB VRAM)

## Architecture

The Document Processing MCP Service uses the following components:

- **PDF Processing**: pdf-parse library for efficient text extraction from PDF files
- **OCR Engine**: Tesseract.js for optical character recognition
- **Image Processing**: Sharp for image preprocessing to improve OCR accuracy
- **MCP Server**: Model Context Protocol server for standardized AI tool integration
- **HTTP API**: REST API for direct integration with other services

## Configuration

Configuration is done through environment variables:

```
# Server Configuration
PORT=8012
LOG_LEVEL=info

# Document Processing Configuration
TEMP_DIR=./temp
OCR_WORKER_THREADS=2
PDF_WORKER_THREADS=2
VRAM_USAGE_GB=1

# MCP Manager Integration
MCP_MANAGER_URL=http://localhost:8010
SERVICE_NAME=document-mcp
SERVICE_URL=http://localhost:8012
```

## MCP Tools

The service provides the following MCP tools:

### extract_pdf_text

Extracts text from PDF documents.

**Input**:
```json
{
  "file_path": "/path/to/document.pdf",
  "page_numbers": [1, 2, 3] // Optional, extracts all pages if not provided
}
```

**Output**:
```json
{
  "content": [
    { "type": "text", "text": "Extracted text from the PDF document..." }
  ],
  "metadata": {
    "page_count": 10,
    "extracted_pages": [1, 2, 3]
  }
}
```

### ocr_image

Performs OCR on an image to extract text.

**Input**:
```json
{
  "image_path": "/path/to/image.jpg",
  "language": "eng", // Optional, defaults to English
  "preprocess": true // Optional, whether to preprocess the image
}
```

**Output**:
```json
{
  "content": [
    { "type": "text", "text": "Extracted text from the image..." }
  ],
  "metadata": {
    "confidence": 0.95,
    "processing_time_ms": 1200
  }
}
```

### convert_document_to_text

Converts various document formats to text (combines PDF extraction and OCR as needed).

**Input**:
```json
{
  "file_path": "/path/to/document.docx",
  "output_format": "text" // Optional, defaults to text
}
```

**Output**:
```json
{
  "content": [
    { "type": "text", "text": "Extracted text from the document..." }
  ],
  "metadata": {
    "original_format": "docx",
    "processing_time_ms": 1500
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

## VRAM Optimization

The Document Processing MCP Service is designed to use minimal VRAM:

1. **Sequential Processing**: Only one document is processed at a time
2. **Worker Threads**: Separate threads for PDF and OCR processing
3. **Lightweight OCR**: Uses Tesseract.js which has minimal VRAM requirements
4. **Image Preprocessing**: Optimizes images before OCR to improve accuracy and reduce processing time

## Integration with MCP Manager

On startup, the service automatically registers with the MCP Manager to coordinate VRAM usage. The service reports its VRAM requirements and can respond to unload requests when VRAM needs to be freed for other services.

## License

MIT

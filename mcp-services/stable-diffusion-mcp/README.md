# Stable Diffusion MCP Service

MCP-compatible service for image generation using Stable Diffusion models. This service provides tools for generating images from text prompts while managing VRAM usage to stay within the 64GB constraint.

## Features

- Generate images from text prompts using Stable Diffusion models
- Support for multiple model variants (SD 1.5, SD 2.1, SDXL)
- 4-bit quantization for reduced VRAM usage
- Model offloading capabilities for efficient VRAM management
- Integration with MCP Manager for VRAM coordination
- Configurable image dimensions and generation parameters

## Architecture

The Stable Diffusion MCP Service uses the following components:

- **Diffusers Library**: Hugging Face's Diffusers for Stable Diffusion implementation
- **4-bit Quantization**: BitsAndBytes for model quantization to reduce VRAM usage
- **Model Offloading**: Accelerate for CPU offloading when needed
- **MCP Server**: Model Context Protocol server for standardized AI tool integration
- **HTTP API**: REST API for direct integration with other services

## Configuration

Configuration is done through environment variables:

```
# Server Configuration
PORT=8015
LOG_LEVEL=info

# Stable Diffusion Configuration
MODEL_ID=stabilityai/stable-diffusion-xl-base-1.0
MODEL_CACHE_DIR=./model_cache
VRAM_USAGE_GB=16
ENABLE_4BIT_QUANTIZATION=true
ENABLE_CPU_OFFLOAD=true
MAX_IMAGE_WIDTH=1024
MAX_IMAGE_HEIGHT=1024

# MCP Manager Integration
MCP_MANAGER_URL=http://localhost:8010
SERVICE_NAME=stable-diffusion-mcp
SERVICE_URL=http://localhost:8015
```

### Model Options

The service supports various Stable Diffusion models with different VRAM requirements:

| Model | MODEL_ID | VRAM Usage (FP16) | VRAM Usage (4-bit) |
|-------|----------|-------------------|-------------------|
| SD 1.5 | runwayml/stable-diffusion-v1-5 | ~8GB | ~4GB |
| SD 2.1 | stabilityai/stable-diffusion-2-1 | ~8GB | ~4GB |
| SDXL | stabilityai/stable-diffusion-xl-base-1.0 | ~16GB | ~8GB |

## MCP Tools

The service provides the following MCP tools:

### generate_image

Generates an image from a text prompt using Stable Diffusion.

**Input**:
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

**Output**:
```json
{
  "content": [
    { "type": "image", "data": "base64_encoded_image_data" }
  ],
  "metadata": {
    "model": "stabilityai/stable-diffusion-xl-base-1.0",
    "generation_time_ms": 5000
  }
}
```

### get_model_info

Returns information about the currently loaded model.

**Input**: None

**Output**:
```json
{
  "content": [
    { "type": "text", "text": "Model: stabilityai/stable-diffusion-xl-base-1.0\nVRAM Usage: 8GB (4-bit quantized)\nMax Dimensions: 1024x1024" }
  ]
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

The Stable Diffusion MCP Service implements several strategies to optimize VRAM usage:

1. **4-bit Quantization**: Reduces model precision to 4 bits, cutting VRAM usage by up to 75%
2. **CPU Offloading**: Moves parts of the model to CPU when not in use
3. **Sequential Processing**: Only one image is generated at a time
4. **Model Unloading**: Unloads the model when requested by the MCP Manager

## Integration with MCP Manager

On startup, the service automatically registers with the MCP Manager to coordinate VRAM usage. The service reports its VRAM requirements and can respond to unload requests when VRAM needs to be freed for other services.

## License

MIT

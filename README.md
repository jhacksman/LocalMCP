# LocalMCP: Self-Hosted Web-Based MCP Implementation

A comprehensive implementation of Model Context Protocol (MCP) servers for local hosting on Linux, with support for advanced models like gemma3:27b and qwq:32b.

## Overview

LocalMCP provides a fully self-hosted implementation of the Model Context Protocol (MCP) for integrating AI models with various services and tools. This repository focuses on:

- **Self-hosting**: Complete control over your data and infrastructure
- **Web-based interface**: Monitor and interact with MCP services through a browser
- **Advanced model integration**: Support for gemma3:27b and qwq:32b models
- **Modular architecture**: Easily extensible with new services and tools

## Repository Structure

```
LocalMCP/
├── mcp-services/           # Service-specific MCP implementations
│   ├── gmail/              # Gmail integration
│   ├── google-drive/       # Google Drive integration
│   ├── discord/            # Discord integration
│   ├── slack/              # Slack integration
│   ├── twitter/            # Twitter (X.com) integration
│   ├── bluesky/            # Bluesky integration
│   ├── telegram/           # Telegram integration
│   ├── signal/             # Signal integration
│   ├── reddit/             # Reddit integration
│   └── notion/             # Notion integration
├── models/                 # Model integration implementations
│   ├── gemma3-27b/         # Gemma3 27B model integration
│   └── qwq-32b/            # QWQ 32B model integration
└── web-interface/          # Web-based monitoring and control interface
```

## Key Features

### MCP Service Implementations

Each service folder contains a complete FastAPI-based MCP server implementation with:

- Dynamic tool registration
- Authentication handling
- Comprehensive logging
- Error management
- Health monitoring

### Model Integration

The repository includes optimized implementations for:

- **gemma3:27b**: Google's 27 billion parameter model
- **qwq:32b**: Advanced 32 billion parameter model

Both implementations feature:

- 4-bit quantization for VRAM efficiency
- Flash Attention 2 support
- Asynchronous processing
- Memory management optimizations

### Web Interface

A comprehensive web-based interface for:

- Monitoring service health
- Testing MCP tools
- Managing model loading/unloading
- Viewing system logs
- Controlling service configuration

## Hardware Requirements

This implementation is optimized for:

- Linux server environment
- 3x NVIDIA 3090 GPUs (64GB VRAM total)
- 256GB RAM
- Local LAN deployment

## Getting Started

### Prerequisites

- Linux server (Ubuntu recommended)
- NVIDIA GPUs with appropriate drivers
- Conda for environment management
- Python 3.8+

### Basic Setup

1. Clone this repository
2. Set up conda environments for services and models
3. Configure service authentication
4. Start the web interface
5. Access the dashboard through your browser

## Service Configuration

Each MCP service requires specific configuration:

- **Gmail/Google Drive**: OAuth2 credentials
- **Discord/Slack**: Bot tokens and permissions
- **Twitter/Bluesky**: API keys
- **Telegram/Signal**: Bot tokens and phone numbers
- **Reddit/Notion**: API credentials

## Model Optimization

The implementation includes several optimizations for running large models on consumer hardware:

- Quantization (4-bit precision)
- Efficient attention mechanisms
- Memory management
- Multi-GPU distribution

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

#### Prerequisites for gemma3:27b

- NVIDIA GPUs with sufficient VRAM (24GB+ for a single GPU)
- CUDA toolkit installed
- Transformers library

#### Implementation Steps

1. **Create a model service file** named `src/models/gemma_service.py`:

```python
import os
import torch
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer

from ..config import GEMMA_MODEL_PATH, DEVICE_MAP, PRECISION

logger = logging.getLogger(__name__)

class Gemma3Service:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.is_ready = False
        
    def initialize(self):
        """Load the model and tokenizer"""
        logger.info(f"Initializing Gemma3 model from {GEMMA_MODEL_PATH}")
        
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(GEMMA_MODEL_PATH)
            
            # Determine precision
            dtype = torch.float16 if PRECISION == "float16" else torch.float32
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                GEMMA_MODEL_PATH,
                torch_dtype=dtype,
                device_map=DEVICE_MAP
            )
            
            self.is_ready = True
            logger.info("Gemma3 model initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Gemma3 model: {str(e)}")
            return False
    
    def generate(self, prompt, max_tokens=256, temperature=0.7):
        """Generate text using the model"""
        if not self.is_ready:
            raise RuntimeError("Gemma3 model not initialized")
        
        try:
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            # Generate text
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=temperature > 0
                )
            
            # Decode output
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Return only the newly generated text (not the prompt)
            new_text = generated_text[len(prompt):]
            
            # Calculate token usage
            usage = {
                "prompt_tokens": len(inputs.input_ids[0]),
                "completion_tokens": len(outputs[0]) - len(inputs.input_ids[0]),
                "total_tokens": len(outputs[0])
            }
            
            return {
                "text": new_text,
                "usage": usage
            }
        except Exception as e:
            logger.error(f"Error generating text with Gemma3: {str(e)}")
            raise
    
    def shutdown(self):
        """Unload the model to free up GPU memory"""
        if self.model:
            del self.model
            torch.cuda.empty_cache()
            self.model = None
            self.is_ready = False
            logger.info("Gemma3 model unloaded")
```

2. **Create a similar service for qwq:32b** named `src/models/qwq_service.py`:

```python
import os
import torch
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer

from ..config import QWQ_MODEL_PATH, DEVICE_MAP, PRECISION

logger = logging.getLogger(__name__)

class QwqService:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.is_ready = False
        
    def initialize(self):
        """Load the model and tokenizer"""
        logger.info(f"Initializing QWQ model from {QWQ_MODEL_PATH}")
        
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(QWQ_MODEL_PATH)
            
            # Determine precision
            dtype = torch.float16 if PRECISION == "float16" else torch.float32
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                QWQ_MODEL_PATH,
                torch_dtype=dtype,
                device_map=DEVICE_MAP
            )
            
            self.is_ready = True
            logger.info("QWQ model initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize QWQ model: {str(e)}")
            return False
    
    def generate(self, prompt, max_tokens=256, temperature=0.7):
        """Generate text using the model"""
        if not self.is_ready:
            raise RuntimeError("QWQ model not initialized")
        
        try:
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            # Generate text
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=temperature > 0
                )
            
            # Decode output
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Return only the newly generated text (not the prompt)
            new_text = generated_text[len(prompt):]
            
            # Calculate token usage
            usage = {
                "prompt_tokens": len(inputs.input_ids[0]),
                "completion_tokens": len(outputs[0]) - len(inputs.input_ids[0]),
                "total_tokens": len(outputs[0])
            }
            
            return {
                "text": new_text,
                "usage": usage
            }
        except Exception as e:
            logger.error(f"Error generating text with QWQ: {str(e)}")
            raise
    
    def shutdown(self):
        """Unload the model to free up GPU memory"""
        if self.model:
            del self.model
            torch.cuda.empty_cache()
            self.model = None
            self.is_ready = False
            logger.info("QWQ model unloaded")
```

3. **Create a model manager** to handle multiple models efficiently:

```python
import logging
from .gemma_service import Gemma3Service
from .qwq_service import QwqService

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self.models = {
            "gemma3": Gemma3Service(),
            "qwq": QwqService()
        }
        self.active_model = None
    
    async def initialize_models(self, model_names=None):
        """Initialize specified models or all models if none specified"""
        if model_names is None:
            model_names = list(self.models.keys())
        
        for name in model_names:
            if name in self.models:
                logger.info(f"Initializing model: {name}")
                success = self.models[name].initialize()
                if success:
                    self.active_model = name
            else:
                logger.warning(f"Unknown model: {name}")
    
    async def generate(self, model_name, prompt, options=None):
        """Generate text using the specified model"""
        if options is None:
            options = {}
        
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")
        
        model = self.models[model_name]
        
        # Initialize model if not already initialized
        if not model.is_ready:
            success = model.initialize()
            if not success:
                raise RuntimeError(f"Failed to initialize model: {model_name}")
        
        # Generate text
        return model.generate(
            prompt,
            max_tokens=options.get("max_tokens", 256),
            temperature=options.get("temperature", 0.7)
        )
    
    def shutdown(self):
        """Shutdown all models"""
        for name, model in self.models.items():
            if model.is_ready:
                logger.info(f"Shutting down model: {name}")
                model.shutdown()
```

4. **Update your server.py** to integrate the models:

```python
# Add these imports at the top
from models.model_manager import ModelManager
import asyncio

# Initialize model manager
model_manager = ModelManager()

# Register model tools
@app.on_event("startup")
async def startup_event():
    # Initialize models in background
    asyncio.create_task(model_manager.initialize_models(["gemma3"]))  # Start with just one model to save VRAM
    
    # Register Gemma3 tool
    register_tool(
        name="gemma3_generate",
        description="Generate text using the Gemma3 27B model",
        parameters={
            "prompt": {
                "type": "string",
                "description": "Input prompt for the model",
                "required": True
            },
            "max_tokens": {
                "type": "integer",
                "description": "Maximum number of tokens to generate",
                "default": 256
            },
            "temperature": {
                "type": "number",
                "description": "Sampling temperature (0-1)",
                "default": 0.7
            }
        },
        handler_func=lambda params: asyncio.run(model_manager.generate(
            "gemma3",
            params.get("prompt", ""),
            {
                "max_tokens": params.get("max_tokens", 256),
                "temperature": params.get("temperature", 0.7)
            }
        ))
    )
    
    # Register QWQ tool
    register_tool(
        name="qwq_generate",
        description="Generate text using the QWQ 32B model with improved capabilities",
        parameters={
            "prompt": {
                "type": "string",
                "description": "Input prompt for the model",
                "required": True
            },
            "max_tokens": {
                "type": "integer",
                "description": "Maximum number of tokens to generate",
                "default": 256
            },
            "temperature": {
                "type": "number",
                "description": "Sampling temperature (0-1)",
                "default": 0.7
            }
        },
        handler_func=lambda params: asyncio.run(model_manager.generate(
            "qwq",
            params.get("prompt", ""),
            {
                "max_tokens": params.get("max_tokens", 256),
                "temperature": params.get("temperature", 0.7)
            }
        ))
    )

@app.on_event("shutdown")
async def shutdown_event():
    model_manager.shutdown()
```

### VRAM Optimization for Multiple Models

When running multiple large models like gemma3:27b and qwq:32b on the same machine, VRAM management becomes critical. Here are some strategies implemented in the code:

1. **Sequential Model Loading**: Only load one model at a time based on which one is needed
2. **Model Quantization**: Reduce precision from FP32 to FP16 (or INT8 with additional code)
3. **Device Map Configuration**: Automatically distribute model layers across available GPUs
4. **Model Unloading**: Unload models from VRAM when not in use

To implement INT8 quantization for even more VRAM savings, update the model loading code:

```python
from transformers import BitsAndBytesConfig

# For INT8 quantization
quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_threshold=6.0
)

# Load model with quantization
self.model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    device_map=DEVICE_MAP,
    quantization_config=quantization_config
)
```

## Best Practices and Troubleshooting

### Security Best Practices

1. **Enable Authentication**: Implement token-based authentication for production
2. **Use HTTPS**: Secure your MCP server with SSL/TLS using Nginx as a reverse proxy
3. **Implement Rate Limiting**: Prevent abuse with request rate limiting
4. **Validate Inputs**: Thoroughly validate all inputs to prevent injection attacks
5. **Restrict Network Access**: Limit access to your MCP server to trusted networks

Example Nginx configuration for HTTPS and reverse proxy:

```nginx
server {
    listen 443 ssl;
    server_name your-server-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3000;  # Web interface
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;  # MCP server
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Performance Optimization

1. **Model Caching**: Cache model outputs for common queries
2. **Batch Processing**: Implement batching for multiple requests
3. **Asynchronous Processing**: Use async/await for non-blocking operations
4. **Load Balancing**: Distribute requests across multiple instances for high traffic
5. **Memory Management**: Implement proper cleanup of unused resources

Example implementation of a simple caching mechanism:

```python
import functools
from datetime import datetime, timedelta

# Simple time-based cache decorator
def cache_with_timeout(timeout_seconds=300):
    def decorator(func):
        cache = {}
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create a cache key from the arguments
            key = str(args) + str(kwargs)
            
            # Check if we have a cached result that's still valid
            if key in cache:
                result, timestamp = cache[key]
                if datetime.now() - timestamp < timedelta(seconds=timeout_seconds):
                    return result
            
            # Call the original function
            result = await func(*args, **kwargs)
            
            # Cache the result
            cache[key] = (result, datetime.now())
            
            return result
        
        return wrapper
    
    return decorator

# Usage example
@cache_with_timeout(timeout_seconds=60)
async def generate_text(model_name, prompt, options=None):
    # This function will only be called once per minute for the same arguments
    return await model_manager.generate(model_name, prompt, options)
```

### Troubleshooting Common Issues

#### CUDA Out of Memory Errors

If you encounter CUDA out of memory errors:

1. **Reduce Model Precision**: Switch to FP16 or INT8 quantization
2. **Optimize Batch Size**: Reduce batch size for inference
3. **Implement Model Offloading**: Offload unused layers to CPU
4. **Monitor GPU Memory**: Use `nvidia-smi` to monitor VRAM usage

Example script to monitor GPU usage:

```python
import subprocess
import time
import json

def monitor_gpus():
    """Monitor GPU usage and log when it exceeds thresholds"""
    while True:
        try:
            # Get GPU stats
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=index,memory.used,memory.total,utilization.gpu', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse output
            for line in result.stdout.strip().split('\n'):
                gpu_id, mem_used, mem_total, util = map(float, line.split(','))
                mem_percent = (mem_used / mem_total) * 100
                
                # Log high memory usage
                if mem_percent > 90:
                    print(f"WARNING: GPU {int(gpu_id)} memory usage is high: {mem_percent:.1f}%")
                
                # Log stats
                print(f"GPU {int(gpu_id)}: {mem_used:.0f}MB/{mem_total:.0f}MB ({mem_percent:.1f}%), Utilization: {util:.0f}%")
            
            time.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            print(f"Error monitoring GPUs: {str(e)}")
            time.sleep(30)  # Longer wait on error
```

#### Model Loading Failures

If models fail to load:

1. **Check Model Path**: Ensure the model path is correct
2. **Verify CUDA Availability**: Confirm PyTorch can access CUDA
3. **Check Disk Space**: Ensure sufficient disk space for model weights
4. **Update Libraries**: Keep transformers and PyTorch updated

#### API Connection Issues

If clients can't connect to your MCP server:

1. **Check Firewall Rules**: Ensure ports are open
2. **Verify Network Configuration**: Check IP binding and port settings
3. **Test Locally**: Confirm the server works on localhost
4. **Check Logs**: Review server logs for connection errors

### Monitoring and Logging

Implement comprehensive logging and monitoring:

```python
import logging
import time
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('mcp_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Performance monitoring decorator
def log_execution_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f} seconds: {str(e)}")
            raise
    
    return wrapper

# Usage example
@log_execution_time
async def generate_text(model_name, prompt, options=None):
    return await model_manager.generate(model_name, prompt, options)
```

## References

1. [Composio MCP Documentation](https://mcp.composio.dev/)
2. [Composio GitHub Repository](https://github.com/ComposioHQ/composio)
3. [Top 5 MCP Servers for Claude Desktop](https://hub.athina.ai/top-5-mcp-servers-for-claude-desktop-2/)
4. [Transformers Documentation](https://huggingface.co/docs/transformers/index)
5. [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)
6. [FastAPI Documentation](https://fastapi.tiangolo.com/)
7. [Next.js Documentation](https://nextjs.org/docs)

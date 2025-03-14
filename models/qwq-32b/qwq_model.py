"""
QWQ-32B Model Integration
-----------------------
This module provides integration for the QWQ-32B model with MCP servers.
"""

import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging
from typing import Dict, List, Optional, Any
import gc
import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("qwq_model.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("qwq_model")

# Define API models
class GenerationRequest(BaseModel):
    prompt: str = Field(..., description="Input prompt for generation")
    max_new_tokens: int = Field(512, description="Maximum number of tokens to generate")
    temperature: float = Field(0.7, description="Sampling temperature")
    top_p: float = Field(0.9, description="Top-p sampling parameter")
    top_k: int = Field(50, description="Top-k sampling parameter")
    repetition_penalty: float = Field(1.1, description="Repetition penalty")
    do_sample: bool = Field(True, description="Whether to use sampling")
    num_return_sequences: int = Field(1, description="Number of sequences to return")

class GenerationResponse(BaseModel):
    generated_text: str
    tokens_generated: int
    generation_time: float

# Create FastAPI app
app = FastAPI(title="QWQ-32B Model Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model and tokenizer
model = None
tokenizer = None
executor = ThreadPoolExecutor(max_workers=1)

# Model configuration
MODEL_ID = "qwq/qwq-32b"  # Replace with actual model ID when available
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.bfloat16 if torch.cuda.is_available() else torch.float32

# VRAM optimization settings
USE_4BIT = True  # Use 4-bit quantization
USE_FLASH_ATTN = True  # Use Flash Attention
USE_BETTERTRANSFORMER = False  # Use BetterTransformer (not needed with Flash Attention)
OFFLOAD_FOLDER = "./offload"  # Folder for disk offloading if needed

def load_model():
    """Load the QWQ-32B model and tokenizer."""
    global model, tokenizer
    
    try:
        logger.info(f"Loading QWQ-32B model on {DEVICE} with {DTYPE}")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        
        # Prepare quantization config if using 4-bit quantization
        if USE_4BIT and DEVICE == "cuda":
            from transformers import BitsAndBytesConfig
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=DTYPE,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
        else:
            quantization_config = None
        
        # Prepare model loading arguments
        model_args = {
            "pretrained_model_name_or_path": MODEL_ID,
            "device_map": "auto",
            "torch_dtype": DTYPE,
        }
        
        # Add quantization config if available
        if quantization_config:
            model_args["quantization_config"] = quantization_config
        
        # Add Flash Attention if available
        if USE_FLASH_ATTN and DEVICE == "cuda":
            try:
                from transformers import AutoConfig
                config = AutoConfig.from_pretrained(MODEL_ID)
                if hasattr(config, "attn_implementation"):
                    model_args["attn_implementation"] = "flash_attention_2"
            except ImportError:
                logger.warning("Flash Attention not available, falling back to standard attention")
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(**model_args)
        
        # Apply BetterTransformer if requested and not using Flash Attention
        if USE_BETTERTRANSFORMER and not USE_FLASH_ATTN and DEVICE == "cuda":
            try:
                from optimum.bettertransformer import BetterTransformer
                model = BetterTransformer.transform(model)
                logger.info("Applied BetterTransformer optimization")
            except ImportError:
                logger.warning("BetterTransformer not available, skipping optimization")
        
        logger.info("QWQ-32B model loaded successfully")
        
        # Log VRAM usage
        if DEVICE == "cuda":
            gpu_memory = torch.cuda.memory_allocated() / 1024**3
            logger.info(f"GPU memory allocated: {gpu_memory:.2f} GB")
    
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise

def unload_model():
    """Unload the model to free up VRAM."""
    global model, tokenizer
    
    if model is not None:
        del model
        model = None
        
        # Force CUDA to release memory
        if DEVICE == "cuda":
            torch.cuda.empty_cache()
            gc.collect()
        
        logger.info("Model unloaded from memory")

def generate_text(prompt, params):
    """Generate text using the model."""
    if model is None or tokenizer is None:
        load_model()
    
    try:
        # Tokenize input
        input_ids = tokenizer.encode(prompt, return_tensors="pt").to(DEVICE)
        
        # Set up generation parameters
        gen_params = {
            "input_ids": input_ids,
            "max_new_tokens": params.max_new_tokens,
            "temperature": params.temperature,
            "top_p": params.top_p,
            "top_k": params.top_k,
            "repetition_penalty": params.repetition_penalty,
            "do_sample": params.do_sample,
            "num_return_sequences": params.num_return_sequences,
            "pad_token_id": tokenizer.eos_token_id
        }
        
        # Record start time
        start_time = torch.cuda.Event(enable_timing=True)
        end_time = torch.cuda.Event(enable_timing=True)
        
        start_time.record()
        
        # Generate text
        with torch.no_grad():
            output = model.generate(**gen_params)
        
        end_time.record()
        
        # Wait for CUDA kernels to finish
        torch.cuda.synchronize()
        
        # Calculate generation time
        generation_time = start_time.elapsed_time(end_time) / 1000  # Convert to seconds
        
        # Decode output
        generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Remove the prompt from the generated text
        prompt_length = len(prompt)
        if generated_text.startswith(prompt):
            generated_text = generated_text[prompt_length:]
        
        # Calculate tokens generated
        tokens_generated = output.shape[1] - input_ids.shape[1]
        
        return {
            "generated_text": generated_text,
            "tokens_generated": tokens_generated,
            "generation_time": generation_time
        }
    
    except Exception as e:
        logger.error(f"Error generating text: {str(e)}")
        raise

@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    # We'll load the model on the first request to avoid blocking startup
    logger.info("Model server starting up")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    unload_model()
    executor.shutdown(wait=True)
    logger.info("Model server shutting down")

@app.post("/generate", response_model=GenerationResponse)
async def generate(request: GenerationRequest):
    """Generate text from a prompt."""
    try:
        # Run generation in a separate thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor, 
            generate_text, 
            request.prompt, 
            request
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error in generate endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")

@app.get("/model_info")
async def model_info():
    """Get information about the model."""
    try:
        # Get GPU information if available
        gpu_info = {}
        if torch.cuda.is_available():
            gpu_info = {
                "gpu_name": torch.cuda.get_device_name(0),
                "gpu_memory_total": torch.cuda.get_device_properties(0).total_memory / 1024**3,
                "gpu_memory_allocated": torch.cuda.memory_allocated() / 1024**3,
                "gpu_memory_reserved": torch.cuda.memory_reserved() / 1024**3
            }
        
        return {
            "model_id": MODEL_ID,
            "device": DEVICE,
            "dtype": str(DTYPE),
            "quantization": "4-bit" if USE_4BIT else "None",
            "flash_attention": USE_FLASH_ATTN,
            "better_transformer": USE_BETTERTRANSFORMER,
            "model_loaded": model is not None,
            "gpu_info": gpu_info
        }
    
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting model info: {str(e)}")

@app.post("/unload_model")
async def api_unload_model():
    """Unload the model from memory."""
    try:
        unload_model()
        return {"status": "success", "message": "Model unloaded from memory"}
    
    except Exception as e:
        logger.error(f"Error unloading model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error unloading model: {str(e)}")

@app.post("/load_model")
async def api_load_model():
    """Load the model into memory."""
    try:
        if model is None:
            # Run loading in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(executor, load_model)
        
        return {"status": "success", "message": "Model loaded into memory"}
    
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading model: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=7001)

import { FastMCP } from "@modelcontextprotocol/sdk";
import { z } from "zod";
import { StableDiffusionService } from "./services/stableDiffusionService";
import express from "express";
import * as dotenv from "dotenv";

// Load environment variables
dotenv.config();

// Define types for tool parameters
interface GenerateImageParams {
  prompt: string;
  negative_prompt?: string;
  width?: number;
  height?: number;
  num_inference_steps?: number;
  guidance_scale?: number;
}

// Create MCP server
const mcp = new FastMCP("Stable Diffusion MCP Server");
const sdService = new StableDiffusionService();

// Create HTTP server for service registration
const app = express();
app.use(express.json());
const port = process.env.PORT || 8015;

// Register image generation tool
mcp.tool(
  "generate_image",
  {
    prompt: z.string(),
    negative_prompt: z.string().optional(),
    width: z.number().optional(),
    height: z.number().optional(),
    num_inference_steps: z.number().optional(),
    guidance_scale: z.number().optional()
  },
  async ({ 
    prompt, 
    negative_prompt = "", 
    width = 512, 
    height = 512, 
    num_inference_steps = 50, 
    guidance_scale = 7.5 
  }: GenerateImageParams) => {
    try {
      const result = await sdService.generateImage(
        prompt, 
        negative_prompt, 
        width, 
        height, 
        num_inference_steps, 
        guidance_scale
      );
      
      return {
        content: [
          { type: "image", data: result.image_base64 }
        ],
        metadata: {
          model: result.model,
          generation_time_ms: result.generation_time
        }
      };
    } catch (error: any) {
      console.error('Error:', error.message);
      throw new Error(`Stable Diffusion error: ${error.message}`);
    }
  }
);

// Register model info tool
mcp.tool(
  "get_model_info",
  {},
  async () => {
    try {
      const modelInfo = sdService.getModelInfo();
      const infoText = `Model: ${modelInfo.name}
VRAM Usage: ${modelInfo.vram_usage_gb}GB${modelInfo.quantized ? ' (4-bit quantized)' : ''}
Max Dimensions: ${modelInfo.max_dimensions.width}x${modelInfo.max_dimensions.height}
Status: ${modelInfo.loaded ? 'Loaded' : 'Not Loaded'}`;
      
      return {
        content: [
          { type: "text", text: infoText }
        ],
        metadata: {
          model_name: modelInfo.name,
          vram_usage_gb: modelInfo.vram_usage_gb,
          quantized: modelInfo.quantized,
          loaded: modelInfo.loaded
        }
      };
    } catch (error: any) {
      console.error('Error:', error.message);
      throw new Error(`Model info error: ${error.message}`);
    }
  }
);

// HTTP API routes
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

app.post('/models/unload', (req, res) => {
  // This endpoint is called by the MCP Manager to unload models
  sdService.unloadModel().then(unloaded => {
    res.status(200).json({ 
      success: true, 
      message: unloaded ? "Model unloaded successfully" : "Model was not loaded" 
    });
  }).catch(error => {
    res.status(500).json({
      success: false,
      message: `Error unloading model: ${error.message}`
    });
  });
});

// Register with MCP Manager on startup
async function registerWithMCPManager() {
  const managerUrl = process.env.MCP_MANAGER_URL;
  const serviceName = process.env.SERVICE_NAME || 'stable-diffusion-mcp';
  const serviceUrl = process.env.SERVICE_URL || `http://localhost:${port}`;
  const modelInfo = sdService.getModelInfo();
  
  if (!managerUrl) {
    console.log('MCP Manager URL not configured, skipping registration');
    return;
  }
  
  try {
    const response = await fetch(`${managerUrl}/services/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        service_name: serviceName,
        service_url: serviceUrl,
        models: [
          {
            name: modelInfo.name,
            vram_usage_gb: modelInfo.vram_usage_gb
          }
        ]
      })
    });
    
    if (response.ok) {
      console.log(`Registered with MCP Manager at ${managerUrl}`);
    } else {
      console.warn(`Failed to register with MCP Manager: ${response.statusText}`);
    }
  } catch (error) {
    console.error('Error registering with MCP Manager:', error);
  }
}

// Start HTTP server
app.listen(port, () => {
  console.log(`Stable Diffusion MCP HTTP server running on port ${port}`);
  registerWithMCPManager();
});

// Start MCP server
console.log('Starting Stable Diffusion MCP server...');
mcp.run({ transport: "stdio" });

// Handle process termination
process.on('SIGINT', async () => {
  console.log('Shutting down...');
  await sdService.unloadModel();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('Shutting down...');
  await sdService.unloadModel();
  process.exit(0);
});

import { FastMCP } from "@modelcontextprotocol/sdk";
import { z } from "zod";
import { VRAMManager } from "./services/vramManager";
import express from "express";

// Create MCP server
const mcp = new FastMCP("MCP Manager Server");
const vramManager = new VRAMManager();

// Create HTTP server for service registration
const app = express();
app.use(express.json());
const port = process.env.PORT || 8010;

// Register VRAM status tool
mcp.tool(
  "get_vram_status",
  {},
  async () => {
    try {
      const status = await vramManager.getVRAMStatus();
      return {
        content: [
          { type: "text", text: JSON.stringify(status, null, 2) }
        ]
      };
    } catch (error: any) {
      console.error('Error:', error.message);
      throw new Error(`VRAM status error: ${error.message}`);
    }
  }
);

// Register model unload tool
mcp.tool(
  "unload_model",
  {
    model_name: z.string(),
    service_name: z.string()
  },
  async ({ model_name, service_name }) => {
    try {
      const result = await vramManager.unloadModel(model_name, service_name);
      return {
        content: [
          { type: "text", text: `Model ${model_name} unloaded successfully` }
        ],
        metadata: {
          freed_vram_gb: result.freedVramGb
        }
      };
    } catch (error: any) {
      console.error('Error:', error.message);
      throw new Error(`Model unload error: ${error.message}`);
    }
  }
);

// Register service registration tool
mcp.tool(
  "register_service",
  {
    service_name: z.string(),
    service_url: z.string(),
    models: z.array(
      z.object({
        name: z.string(),
        vram_usage_gb: z.number()
      })
    )
  },
  async ({ service_name, service_url, models }) => {
    try {
      const result = await vramManager.registerService(
        service_name,
        service_url,
        models.map(model => ({
          name: model.name,
          vramUsageGb: model.vram_usage_gb
        }))
      );
      return {
        content: [
          { type: "text", text: result.message }
        ],
        metadata: {
          success: result.success
        }
      };
    } catch (error: any) {
      console.error('Error:', error.message);
      throw new Error(`Service registration error: ${error.message}`);
    }
  }
);

// Register service list tool
mcp.tool(
  "list_services",
  {},
  async () => {
    try {
      const services = await vramManager.getServiceList();
      return {
        content: [
          { type: "text", text: JSON.stringify(services, null, 2) }
        ]
      };
    } catch (error: any) {
      console.error('Error:', error.message);
      throw new Error(`Service list error: ${error.message}`);
    }
  }
);

// HTTP API routes
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

app.get('/vram/status', async (req, res) => {
  try {
    const status = await vramManager.getVRAMStatus();
    res.status(200).json(status);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/vram/unload', async (req, res) => {
  try {
    const { model_name, service_name } = req.body;
    if (!model_name || !service_name) {
      return res.status(400).json({ error: 'Missing model_name or service_name' });
    }
    const result = await vramManager.unloadModel(model_name, service_name);
    res.status(200).json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/services/register', async (req, res) => {
  try {
    const { service_name, service_url, models } = req.body;
    if (!service_name || !service_url || !models) {
      return res.status(400).json({ error: 'Missing service_name, service_url, or models' });
    }
    const result = await vramManager.registerService(service_name, service_url, models);
    res.status(result.success ? 200 : 400).json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/services/list', async (req, res) => {
  try {
    const services = await vramManager.getServiceList();
    res.status(200).json(services);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Start HTTP server
app.listen(port, () => {
  console.log(`MCP Manager HTTP server running on port ${port}`);
});

// Start MCP server
console.log('Starting MCP Manager server...');
mcp.run({ transport: "stdio" });

import { FastMCP } from "@modelcontextprotocol/sdk";
import { z } from "zod";
import { VectorDBService } from "./services/vectorDBService";
import express from "express";
import * as dotenv from "dotenv";

// Define types for tool parameters
interface GenerateEmbeddingParams {
  text: string;
  model?: string;
}

interface StoreDocumentParams {
  text: string;
  collection: string;
  metadata?: Record<string, any>;
}

interface VectorSearchParams {
  query: string;
  collection: string;
  limit?: number;
  threshold?: number;
}

// Load environment variables
dotenv.config();

// Create MCP server
const mcp = new FastMCP("Vector Database MCP Server");
const vectorService = new VectorDBService();

// Create HTTP server for service registration
const app = express();
app.use(express.json());
const port = process.env.PORT || 8005;

// Register embedding generation tool
mcp.tool(
  "generate_embedding",
  {
    text: z.string(),
    model: z.string().optional()
  },
  async ({ text, model }: GenerateEmbeddingParams) => {
    try {
      const result = await vectorService.generateEmbedding(text, model);
      return {
        content: [
          { type: "text", text: "Embedding generated successfully" }
        ],
        metadata: {
          model: result.model,
          vector_size: result.vector_size,
          embedding_id: result.embedding_id
        }
      };
    } catch (error: any) {
      console.error('Error:', error.message);
      throw new Error(`Embedding generation error: ${error.message}`);
    }
  }
);

// Register document storage tool
mcp.tool(
  "store_document",
  {
    text: z.string(),
    collection: z.string(),
    metadata: z.record(z.any()).optional()
  },
  async ({ text, collection, metadata = {} }: StoreDocumentParams) => {
    try {
      const result = await vectorService.storeDocument(text, collection, metadata);
      return {
        content: [
          { type: "text", text: "Document stored successfully" }
        ],
        metadata: {
          document_id: result.document_id,
          collection: result.collection
        }
      };
    } catch (error: any) {
      console.error('Error:', error.message);
      throw new Error(`Document storage error: ${error.message}`);
    }
  }
);

// Register vector search tool
mcp.tool(
  "vector_search",
  {
    query: z.string(),
    collection: z.string(),
    limit: z.number().optional(),
    threshold: z.number().optional()
  },
  async ({ query, collection, limit = 5, threshold = 0.7 }: VectorSearchParams) => {
    try {
      const results = await vectorService.searchVectors(query, collection, limit, threshold);
      return {
        content: [
          { type: "text", text: JSON.stringify(results.documents) }
        ],
        metadata: {
          total_results: results.total,
          search_time_ms: results.search_time
        }
      };
    } catch (error: any) {
      console.error('Error:', error.message);
      throw new Error(`Vector search error: ${error.message}`);
    }
  }
);

// Register collection listing tool
mcp.tool(
  "list_collections",
  {},
  async () => {
    try {
      const collections = await vectorService.listCollections();
      return {
        content: [
          { type: "text", text: JSON.stringify(collections) }
        ],
        metadata: {
          count: collections.length
        }
      };
    } catch (error: any) {
      console.error('Error:', error.message);
      throw new Error(`Collection listing error: ${error.message}`);
    }
  }
);

// Register model info tool
mcp.tool(
  "get_model_info",
  {},
  async () => {
    try {
      const modelInfo = await vectorService.getModelInfo();
      return {
        content: [
          { type: "text", text: JSON.stringify(modelInfo) }
        ]
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
  // Since our embedding model is lightweight, we don't need to actually unload it
  // But we acknowledge the request to maintain compatibility
  res.status(200).json({ 
    success: true, 
    message: "Model unload acknowledged (no action needed for lightweight model)" 
  });
});

// Register with MCP Manager on startup
async function registerWithMCPManager() {
  const managerUrl = process.env.MCP_MANAGER_URL;
  const serviceName = process.env.SERVICE_NAME || 'vector-db-mcp';
  const serviceUrl = process.env.SERVICE_URL || `http://localhost:${port}`;
  const vramUsageGb = parseFloat(process.env.VRAM_USAGE_GB || '2');
  
  if (!managerUrl) {
    console.log('MCP Manager URL not configured, skipping registration');
    return;
  }
  
  try {
    const modelInfo = await vectorService.getModelInfo();
    
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
            vram_usage_gb: vramUsageGb
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
  console.log(`Vector Database MCP HTTP server running on port ${port}`);
  registerWithMCPManager();
});

// Start MCP server
console.log('Starting Vector Database MCP server...');
mcp.run({ transport: "stdio" });

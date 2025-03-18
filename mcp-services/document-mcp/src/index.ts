import { FastMCP } from "@modelcontextprotocol/sdk";
import { z } from "zod";
import { DocumentService } from "./services/documentService";
import express from "express";
import * as dotenv from "dotenv";

// Load environment variables
dotenv.config();

// Define types for tool parameters
interface PdfExtractionParams {
  file_path: string;
  page_numbers?: number[];
}

interface OcrParams {
  image_path: string;
  language?: string;
  preprocess?: boolean;
}

interface DocumentConversionParams {
  file_path: string;
  output_format?: string;
}

// Create MCP server
const mcp = new FastMCP("Document Processing MCP Server");
const documentService = new DocumentService();

// Create HTTP server for service registration
const app = express();
app.use(express.json());
const port = process.env.PORT || 8012;

// Register PDF text extraction tool
mcp.tool(
  "extract_pdf_text",
  {
    file_path: z.string(),
    page_numbers: z.array(z.number()).optional()
  },
  async ({ file_path, page_numbers }: PdfExtractionParams) => {
    try {
      const result = await documentService.extractPdfText(file_path, page_numbers);
      return {
        content: [
          { type: "text", text: result.text }
        ],
        metadata: {
          page_count: result.page_count,
          extracted_pages: result.extracted_pages
        }
      };
    } catch (error: any) {
      console.error('Error:', error.message);
      throw new Error(`PDF extraction error: ${error.message}`);
    }
  }
);

// Register OCR tool
mcp.tool(
  "ocr_image",
  {
    image_path: z.string(),
    language: z.string().optional(),
    preprocess: z.boolean().optional()
  },
  async ({ image_path, language = 'eng', preprocess = true }: OcrParams) => {
    try {
      const result = await documentService.performOcr(image_path, language, preprocess);
      return {
        content: [
          { type: "text", text: result.text }
        ],
        metadata: {
          confidence: result.confidence,
          processing_time_ms: result.processing_time
        }
      };
    } catch (error: any) {
      console.error('Error:', error.message);
      throw new Error(`OCR error: ${error.message}`);
    }
  }
);

// Register document conversion tool
mcp.tool(
  "convert_document_to_text",
  {
    file_path: z.string(),
    output_format: z.string().optional()
  },
  async ({ file_path, output_format = 'text' }: DocumentConversionParams) => {
    try {
      const result = await documentService.convertDocumentToText(file_path, output_format);
      return {
        content: [
          { type: "text", text: result.text }
        ],
        metadata: {
          original_format: result.original_format,
          processing_time_ms: result.processing_time
        }
      };
    } catch (error: any) {
      console.error('Error:', error.message);
      throw new Error(`Document conversion error: ${error.message}`);
    }
  }
);

// HTTP API routes
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

app.post('/models/unload', (req, res) => {
  // This endpoint is called by the MCP Manager to unload models
  // For OCR, we can actually unload the workers to free up memory
  documentService.cleanup().then(() => {
    res.status(200).json({ 
      success: true, 
      message: "OCR workers unloaded successfully" 
    });
  }).catch(error => {
    res.status(500).json({
      success: false,
      message: `Error unloading OCR workers: ${error.message}`
    });
  });
});

// Register with MCP Manager on startup
async function registerWithMCPManager() {
  const managerUrl = process.env.MCP_MANAGER_URL;
  const serviceName = process.env.SERVICE_NAME || 'document-mcp';
  const serviceUrl = process.env.SERVICE_URL || `http://localhost:${port}`;
  const vramUsageGb = parseFloat(process.env.VRAM_USAGE_GB || '1');
  
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
            name: 'tesseract-ocr',
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
  console.log(`Document Processing MCP HTTP server running on port ${port}`);
  registerWithMCPManager();
});

// Start MCP server
console.log('Starting Document Processing MCP server...');
mcp.run({ transport: "stdio" });

// Handle process termination
process.on('SIGINT', async () => {
  console.log('Shutting down...');
  await documentService.cleanup();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('Shutting down...');
  await documentService.cleanup();
  process.exit(0);
});

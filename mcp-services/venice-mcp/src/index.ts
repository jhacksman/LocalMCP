import { FastMCP } from "@modelcontextprotocol/sdk";
import axios from "axios";
import { z } from "zod";

// Venice.ai API configuration
const VENICE_API_BASE_URL = process.env.VENICE_API_BASE_URL || "https://api.venice.ai/api/v1";
const VENICE_API_KEY = process.env.VENICE_API_KEY || "";
const VENICE_MODEL = process.env.VENICE_MODEL || "deepseek-r1-671b";

// Function to remove <think> tags from content
function removeThinkTags(content: string): string {
  if (!content) return "";
  
  // Handle nested <think> tags by repeatedly applying the regex until no more matches
  let previousContent = "";
  let cleanedContent = content;
  
  while (previousContent !== cleanedContent) {
    previousContent = cleanedContent;
    cleanedContent = cleanedContent.replace(/<think>[\s\S]*?<\/think>/g, '');
  }
  
  // Handle unclosed <think> tags
  if (cleanedContent.includes('<think>')) {
    const thinkIndex = cleanedContent.indexOf('<think>');
    cleanedContent = cleanedContent.substring(0, thinkIndex);
  }
  
  // Special case: entire content is within an unclosed <think> tag
  if (content.trim().startsWith('<think>') && !content.includes('</think>')) {
    // Try to extract meaningful content after the <think> tag
    const extractedContent = content.replace('<think>', '').trim();
    if (extractedContent.length > 0) {
      return extractedContent;
    }
  }
  
  // Clean up any extra spaces that might have been created
  cleanedContent = cleanedContent.replace(/\s+/g, ' ').trim();
  
  return cleanedContent.length > 0 ? cleanedContent : "I'm sorry, I couldn't generate a proper response.";
}

// Create MCP server
const mcp = new FastMCP("Venice.ai MCP Server");

// Register chat completion tool
mcp.tool(
  "chat_completion",
  {
    prompt: z.string(),
    system_prompt: z.string().optional(),
    model: z.string().optional(),
    max_tokens: z.number().optional()
  },
  async ({ prompt, system_prompt = "You are a helpful assistant.", model = VENICE_MODEL, max_tokens = 1000 }) => {
    if (!VENICE_API_KEY) {
      throw new Error("API key not provided. Set VENICE_API_KEY environment variable.");
    }
    
    console.log(`Sending request to Venice.ai API (${model})...`);
    console.log(`Prompt: ${prompt}`);
    
    try {
      const response = await axios.post(
        `${VENICE_API_BASE_URL}/chat/completions`,
        {
          model,
          messages: [
            { role: 'system', content: system_prompt },
            { role: 'user', content: prompt }
          ],
          max_tokens
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${VENICE_API_KEY}`
          }
        }
      );
      
      const originalContent = response.data.choices[0].message.content;
      const cleanedContent = removeThinkTags(originalContent);
      
      console.log('Original response:', originalContent);
      console.log('Cleaned response:', cleanedContent);
      
      return {
        content: [{ type: "text", text: cleanedContent }],
        metadata: {
          model,
          usage: response.data.usage,
          original_content: originalContent
        }
      };
    } catch (error: any) {
      console.error('Error:', error.response ? error.response.data : error.message);
      throw new Error(`Venice.ai API error: ${error.message}`);
    }
  }
);

// Start the server
mcp.run({ transport: "stdio" });

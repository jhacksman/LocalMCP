const axios = require('axios');
const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

// Venice.ai API configuration
const VENICE_API_BASE_URL = process.env.VENICE_API_BASE_URL || "https://api.venice.ai/api/v1";
const VENICE_API_KEY = process.env.VENICE_API_KEY || "";
const VENICE_MODEL = process.env.VENICE_MODEL || "deepseek-r1-671b";

// Function to remove <think> tags from content
function removeThinkTags(content) {
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

// Configure Express
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Venice.ai MCP Server is running' });
});

// Chat completion endpoint
app.post('/api/chat', async (req, res) => {
  try {
    const { prompt, system_prompt = "You are a helpful assistant.", model = VENICE_MODEL, max_tokens = 1000 } = req.body;
    
    if (!VENICE_API_KEY) {
      return res.status(400).json({ error: "API key not provided. Set VENICE_API_KEY environment variable." });
    }
    
    console.log(`Sending request to Venice.ai API (${model})...`);
    console.log(`Prompt: ${prompt}`);
    
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
    
    res.json({
      original: originalContent,
      cleaned: cleanedContent,
      model: model,
      usage: response.data.usage
    });
  } catch (error) {
    console.error('Error:', error.response ? error.response.data : error.message);
    res.status(500).json({ 
      error: error.response ? error.response.data : error.message 
    });
  }
});

// Start the server
app.listen(port, () => {
  console.log(`Venice.ai MCP Server listening on port ${port}`);
  console.log(`API Base URL: ${VENICE_API_BASE_URL}`);
  console.log(`Default Model: ${VENICE_MODEL}`);
});

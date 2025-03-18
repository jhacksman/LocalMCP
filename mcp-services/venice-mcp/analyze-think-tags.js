// Script to analyze <think> tags in Venice.ai API responses
const axios = require('axios');

// Venice.ai API configuration
const VENICE_API_BASE_URL = process.env.VENICE_API_BASE_URL || "https://api.venice.ai/api/v1";
const VENICE_API_KEY = process.env.VENICE_API_KEY || "";
const VENICE_MODEL = process.env.VENICE_MODEL || "deepseek-r1-671b";

// Function to analyze <think> tags in content
function analyzeThinkTags(content) {
  // Check if content contains <think> tags
  const hasThinkTags = content.includes('<think>');
  
  // Count number of <think> tags
  const thinkTagCount = (content.match(/<think>/g) || []).length;
  
  // Count number of </think> tags
  const closeThinkTagCount = (content.match(/<\/think>/g) || []).length;
  
  // Extract content within <think> tags
  const thinkContent = [];
  const regex = /<think>([\s\S]*?)<\/think>/g;
  let match;
  
  while ((match = regex.exec(content)) !== null) {
    thinkContent.push(match[1]);
  }
  
  return {
    hasThinkTags,
    thinkTagCount,
    closeThinkTagCount,
    thinkContent,
    unclosedTags: thinkTagCount > closeThinkTagCount
  };
}

// Function to test the Venice.ai API and analyze <think> tags
async function testVeniceAPI() {
  try {
    if (!VENICE_API_KEY) {
      console.error('Error: VENICE_API_KEY environment variable not set');
      return;
    }
    
    console.log('Testing Venice.ai API...');
    
    const prompts = [
      'Tell me a joke about programming.',
      'What is the capital of France?',
      'Write a short poem about AI.',
      'Explain quantum computing in simple terms.'
    ];
    
    for (const prompt of prompts) {
      console.log(`\nPrompt: "${prompt}"`);
      
      const response = await axios.post(
        `${VENICE_API_BASE_URL}/chat/completions`,
        {
          model: VENICE_MODEL,
          messages: [
            { role: 'system', content: 'You are a helpful assistant.' },
            { role: 'user', content: prompt }
          ],
          max_tokens: 100
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${VENICE_API_KEY}`
          }
        }
      );
      
      const content = response.data.choices[0].message.content;
      console.log('Response:', content);
      
      const analysis = analyzeThinkTags(content);
      console.log('Analysis:');
      console.log(`- Has <think> tags: ${analysis.hasThinkTags}`);
      console.log(`- Number of <think> tags: ${analysis.thinkTagCount}`);
      console.log(`- Number of </think> tags: ${analysis.closeThinkTagCount}`);
      console.log(`- Unclosed tags: ${analysis.unclosedTags}`);
      
      if (analysis.thinkContent.length > 0) {
        console.log('- Content within <think> tags:');
        analysis.thinkContent.forEach((content, index) => {
          console.log(`  [${index + 1}] ${content.substring(0, 100)}...`);
        });
      }
    }
  } catch (error) {
    console.error('Error:', error.response ? error.response.data : error.message);
  }
}

// Run the test if this file is executed directly
if (require.main === module) {
  testVeniceAPI();
}

module.exports = { analyzeThinkTags };

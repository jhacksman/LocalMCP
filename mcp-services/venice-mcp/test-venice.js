// Test script for Venice.ai API
const axios = require('axios');

// Venice.ai API configuration
const VENICE_API_BASE_URL = process.env.VENICE_API_BASE_URL || "https://api.venice.ai/api/v1";
const VENICE_API_KEY = process.env.VENICE_API_KEY || "";
const VENICE_MODEL = process.env.VENICE_MODEL || "deepseek-r1-671b";

// Function to test the Venice.ai API
async function testVeniceAPI() {
  try {
    if (!VENICE_API_KEY) {
      console.error('Error: VENICE_API_KEY environment variable not set');
      return;
    }
    
    console.log('Testing Venice.ai API...');
    console.log(`API Base URL: ${VENICE_API_BASE_URL}`);
    console.log(`Model: ${VENICE_MODEL}`);
    
    const prompt = 'Tell me a joke about programming.';
    console.log(`Prompt: "${prompt}"`);
    
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
    
    console.log('\nResponse:');
    console.log(JSON.stringify(response.data, null, 2));
    
    console.log('\nContent:');
    console.log(response.data.choices[0].message.content);
    
    console.log('\nTest completed successfully!');
  } catch (error) {
    console.error('Error:', error.response ? error.response.data : error.message);
  }
}

// Run the test
testVeniceAPI();

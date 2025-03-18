const axios = require('axios');

// Test the Venice.ai MCP Server
async function testServer() {
  try {
    console.log('Testing Venice.ai MCP Server...');
    
    // Test health endpoint
    console.log('\nTesting health endpoint...');
    const healthResponse = await axios.get('http://localhost:3000/health');
    console.log('Health response:', healthResponse.data);
    
    // Test chat completion endpoint
    console.log('\nTesting chat completion endpoint...');
    const chatResponse = await axios.post('http://localhost:3000/api/chat', {
      prompt: 'Tell me a short joke about programming.',
      system_prompt: 'You are a helpful assistant who responds with short, concise answers.',
      max_tokens: 100
    });
    
    console.log('\nChat response:');
    console.log('Original:', chatResponse.data.original);
    console.log('Cleaned:', chatResponse.data.cleaned);
    console.log('Model:', chatResponse.data.model);
    console.log('Usage:', chatResponse.data.usage);
    
    // Check if the response contains <think> tags
    if (chatResponse.data.cleaned.includes('<think>')) {
      console.log('\nWARNING: Cleaned response still contains <think> tags!');
    } else {
      console.log('\nSuccess: Cleaned response does not contain <think> tags.');
    }
    
    console.log('\nTest completed successfully!');
  } catch (error) {
    console.error('Error testing server:', error.response ? error.response.data : error.message);
  }
}

// Run the test
testServer();

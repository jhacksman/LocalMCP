const axios = require('axios');

// Test the Venice.ai MCP Server Wrapper
async function testMCPWrapper() {
  try {
    console.log('Testing Venice.ai MCP Server Wrapper...');
    
    // Test health endpoint
    console.log('\nTesting health endpoint...');
    const healthResponse = await axios.get('http://localhost:3000/health');
    console.log('Health response:', healthResponse.data);
    
    // Test MCP chat completion endpoint
    console.log('\nTesting MCP chat completion endpoint...');
    const chatResponse = await axios.post('http://localhost:3000/mcp/chat', {
      prompt: 'Tell me a short joke about programming.',
      system_prompt: 'You are a helpful assistant who responds with short, concise answers.',
      max_tokens: 100
    });
    
    console.log('\nMCP chat response:');
    console.log('Content type:', chatResponse.data.content[0].type);
    console.log('Content text:', chatResponse.data.content[0].text);
    console.log('Model:', chatResponse.data.metadata.model);
    console.log('Usage:', chatResponse.data.metadata.usage);
    console.log('Original content:', chatResponse.data.metadata.original_content);
    
    // Check if the response contains <think> tags
    if (chatResponse.data.content[0].text.includes('<think>')) {
      console.log('\nWARNING: Cleaned response still contains <think> tags!');
    } else {
      console.log('\nSuccess: Cleaned response does not contain <think> tags.');
    }
    
    // Validate MCP response format
    const isValidMCPResponse = 
      chatResponse.data.content && 
      Array.isArray(chatResponse.data.content) && 
      chatResponse.data.content.length > 0 &&
      chatResponse.data.content[0].type === 'text' &&
      typeof chatResponse.data.content[0].text === 'string';
    
    console.log(`\nValid MCP response format: ${isValidMCPResponse ? 'YES' : 'NO'}`);
    
    console.log('\nTest completed successfully!');
  } catch (error) {
    console.error('Error testing MCP wrapper:', error.response ? error.response.data : error.message);
  }
}

// Run the test
testMCPWrapper();

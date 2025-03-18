/**
 * Test script for Venice.ai MCP Server
 * 
 * This script tests the MCP server implementation for Venice.ai API.
 * It sends a test prompt to the server and displays the response.
 */

const { spawn } = require('child_process');
const axios = require('axios');

// Start the MCP server
console.log('Starting Venice.ai MCP Server...');
const server = spawn('node', ['venice-mcp-server.js']);

// Wait for server to start
setTimeout(async () => {
  try {
    console.log('Testing server...');
    
    // Send test request
    const response = await axios.post('http://localhost:3000/api/chat', {
      prompt: 'Tell me a joke about programming.',
      system_prompt: 'You are a helpful assistant.',
      max_tokens: 100
    });
    
    console.log('\nServer Response:');
    console.log(JSON.stringify(response.data, null, 2));
    
    console.log('\nOriginal Response:');
    console.log(response.data.original);
    
    console.log('\nCleaned Response:');
    console.log(response.data.cleaned);
    
    console.log('\nTest completed successfully!');
  } catch (error) {
    console.error('Error:', error.response ? error.response.data : error.message);
  } finally {
    // Kill the server
    server.kill();
    process.exit(0);
  }
}, 2000);

// Handle server output
server.stdout.on('data', (data) => {
  console.log(`Server: ${data}`);
});

server.stderr.on('data', (data) => {
  console.error(`Server Error: ${data}`);
});

#!/bin/bash

# Run tests for all MCP services
echo "Running tests for all MCP services..."

# MCP Manager tests
echo "=== Running MCP Manager tests ==="
cd mcp-manager
npm test || echo "MCP Manager tests failed"
cd ..

# Vector DB MCP tests
echo "=== Running Vector DB MCP tests ==="
cd vector-db-mcp
npm test || echo "Vector DB MCP tests failed"
cd ..

# Document MCP tests
echo "=== Running Document MCP tests ==="
cd document-mcp
npm test || echo "Document MCP tests failed"
cd ..

# Stable Diffusion MCP tests
echo "=== Running Stable Diffusion MCP tests ==="
cd stable-diffusion-mcp
npm test || echo "Stable Diffusion MCP tests failed"
cd ..

echo "All tests completed."

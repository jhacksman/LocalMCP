#!/bin/bash

# Service Verification Script for LocalMCP
# This script tests all MCP services for functionality and VRAM management

set -e

echo "=== LocalMCP Service Verification Script ==="
echo "This script will verify all MCP services"

# Function to check if a service is running
check_service() {
  local service_name=$1
  local port=$2
  echo "Checking $service_name on port $port..."
  
  # Try to connect to the service
  if curl -s "http://localhost:$port/health" > /dev/null; then
    echo "✅ $service_name is running"
    return 0
  else
    echo "❌ $service_name is not running"
    return 1
  fi
}

# Function to test VRAM usage
check_vram_usage() {
  echo "Checking VRAM usage..."
  
  # Get VRAM usage from MCP Manager
  local vram_usage=$(curl -s "http://localhost:8010/tools/get_vram_status" | grep -o '"total_vram_usage_gb":[0-9.]*' | cut -d':' -f2)
  
  echo "Current VRAM usage: ${vram_usage}GB"
  
  # Check if VRAM usage is within limit
  if (( $(echo "$vram_usage < 64" | bc -l) )); then
    echo "✅ VRAM usage is within limit"
    return 0
  else
    echo "❌ VRAM usage exceeds limit"
    return 1
  fi
}

# Function to test model loading/unloading
test_model_loading() {
  local service_name=$1
  local port=$2
  
  echo "Testing model loading/unloading for $service_name..."
  
  # Unload model
  echo "Unloading model..."
  curl -s -X POST "http://localhost:$port/tools/unload_model" -H "Content-Type: application/json" -d '{}'
  
  # Check VRAM usage after unloading
  sleep 2
  local vram_after_unload=$(curl -s "http://localhost:8010/tools/get_vram_status" | grep -o '"total_vram_usage_gb":[0-9.]*' | cut -d':' -f2)
  echo "VRAM usage after unloading: ${vram_after_unload}GB"
  
  # Load model again by making a request that requires the model
  echo "Loading model again..."
  curl -s "http://localhost:$port/tools/get_model_info"
  
  # Check VRAM usage after loading
  sleep 2
  local vram_after_load=$(curl -s "http://localhost:8010/tools/get_vram_status" | grep -o '"total_vram_usage_gb":[0-9.]*' | cut -d':' -f2)
  echo "VRAM usage after loading: ${vram_after_load}GB"
  
  # Check if VRAM usage increased after loading
  if (( $(echo "$vram_after_load > $vram_after_unload" | bc -l) )); then
    echo "✅ Model loading/unloading works correctly"
    return 0
  else
    echo "❌ Model loading/unloading test failed"
    return 1
  fi
}

# Function to test concurrent operation
test_concurrent_operation() {
  echo "Testing concurrent operation of multiple services..."
  
  # Make concurrent requests to multiple services
  curl -s "http://localhost:8005/tools/get_model_info" &
  curl -s "http://localhost:8012/tools/get_model_info" &
  curl -s "http://localhost:8015/tools/get_model_info" &
  
  # Wait for all requests to complete
  wait
  
  # Check VRAM usage after concurrent requests
  sleep 2
  check_vram_usage
}

# Function to test for memory leaks
test_memory_leaks() {
  local service_name=$1
  local port=$2
  local iterations=10
  
  echo "Testing for memory leaks in $service_name..."
  
  # Get initial VRAM usage
  local initial_vram=$(curl -s "http://localhost:8010/tools/get_vram_status" | grep -o '"total_vram_usage_gb":[0-9.]*' | cut -d':' -f2)
  echo "Initial VRAM usage: ${initial_vram}GB"
  
  # Make multiple requests to the service
  for i in $(seq 1 $iterations); do
    echo "Request $i/$iterations"
    curl -s "http://localhost:$port/tools/get_model_info" > /dev/null
    sleep 1
  done
  
  # Get final VRAM usage
  local final_vram=$(curl -s "http://localhost:8010/tools/get_vram_status" | grep -o '"total_vram_usage_gb":[0-9.]*' | cut -d':' -f2)
  echo "Final VRAM usage: ${final_vram}GB"
  
  # Check if VRAM usage increased significantly
  local vram_diff=$(echo "$final_vram - $initial_vram" | bc -l)
  if (( $(echo "$vram_diff < 0.5" | bc -l) )); then
    echo "✅ No significant memory leaks detected"
    return 0
  else
    echo "❌ Possible memory leak detected (VRAM increase: ${vram_diff}GB)"
    return 1
  fi
}

# Main verification process
echo "Starting verification process..."

# Check if services are running
check_service "MCP Manager" 8010
check_service "Vector DB MCP" 8005
check_service "Document MCP" 8012
check_service "Stable Diffusion MCP" 8015

# Check VRAM usage
check_vram_usage

# Test model loading/unloading for each service
test_model_loading "Vector DB MCP" 8005
test_model_loading "Document MCP" 8012
test_model_loading "Stable Diffusion MCP" 8015

# Test concurrent operation
test_concurrent_operation

# Test for memory leaks
test_memory_leaks "Vector DB MCP" 8005
test_memory_leaks "Document MCP" 8012
test_memory_leaks "Stable Diffusion MCP" 8015

echo "=== Verification Complete ==="
echo "All services have been verified for functionality and VRAM management"

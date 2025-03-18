# ManusMCP Integration for LocalMCP

This is an integration of the ManusMCP multi-agent system with LocalMCP. ManusMCP is a framework for orchestrating specialized AI agents that work together to accomplish complex tasks using the Model Context Protocol (MCP).

## Agent Members

ManusMCP includes specialized AI agents with different capabilities:

### Supervisor
Analyzes requests and delegates to the appropriate specialist agent based on the task requirements.

### Planner
Strategic planning expert who breaks complex tasks into manageable steps with clear dependencies. Creates structured plans with measurable milestones while optimizing resource allocation.

### FileWizard
File system expert for manipulating and organizing digital content. Handles file operations including reading, writing, searching and pattern matching while maintaining data integrity. Includes full Next.js runtime support.

### CommandRunner
Command-line expert for executing and managing shell commands and processes. Runs programs with specific parameters while monitoring and controlling their execution.

### WebNavigator
Web automation specialist controlling browser actions with precision. Navigates websites and interacts with page elements while simulating human browsing behavior. Uses omni-parser for data extraction.

## Implementation Details

The framework uses state management to maintain context between different agents and includes specialized routing conditions to ensure each request is handled by the most appropriate agent.

Built entirely with the sequential agent framework in Flowise, creating an efficient agent collaboration system where each agent has its own specialized role and capabilities.

## Usage

To use ManusMCP:

1. Set up the required environment variables in `.env`
2. Start the MCP server using Bun
3. Access the Flowise UI to configure and interact with the agents

## Source Repository

Original repository: https://github.com/mantrakp04/manusmcp

# Model Context Protocol (MCP) Compatibility Guide

## What is Model Context Protocol (MCP)?

Model Context Protocol (MCP) is a standardized way for applications to interact with AI models and tools. It provides a consistent interface for discovering and using tools, regardless of the underlying implementation.

MCP was developed to address the challenge of integrating AI capabilities into applications in a modular, maintainable way. It creates a clear separation between:

1. **AI Models**: The language models that generate responses
2. **Tools**: Functions that perform specific actions (like browser automation, file operations, etc.)
3. **Applications**: The software that uses AI models and tools to solve problems

## Key Concepts

### MCP Server

The MCP Server exposes tools and their capabilities to AI models. It:
- Registers tools with their input/output schemas
- Handles tool execution
- Returns results in a standardized format

### MCP Client

The MCP Client discovers and uses tools provided by the server. It:
- Queries the server for available tools
- Calls tools with appropriate parameters
- Processes tool results

### Tools

Tools are functions with defined input/output schemas. They:
- Have clear parameter specifications
- Return results in a consistent format
- Can be discovered and used dynamically

## MCP vs. manus-open Architecture

### MCP Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │
│  AI Model   │◄────┤  MCP Client │◄────┤  MCP Server │
│             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │             │
                                        │    Tools    │
                                        │             │
                                        └─────────────┘
```

### manus-open Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │
│  AI Model   │◄────┤  API Client │◄────┤  FastAPI    │
│             │     │             │     │  Server     │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │             │
                                        │  Managers   │
                                        │  (Browser,  │
                                        │  Terminal,  │
                                        │  Text Editor)│
                                        │             │
                                        └─────────────┘
```

## Integration Strategy for manus-open

To make manus-open MCP-compatible, we need to create an adapter layer that translates between the MCP protocol and manus-open's API. This can be done in several ways:

### Option 1: MCP Server Wrapper

Create an MCP server that wraps manus-open's API endpoints:

```typescript
import { FastMCP } from "@modelcontextprotocol/sdk";
import { z } from "zod";

const mcp = new FastMCP("manus-open MCP Server");

// Register browser tools
mcp.tool(
  "browser_navigate",
  {
    url: z.string()
  },
  async ({ url }) => {
    // Call manus-open browser navigation API
    const response = await fetch("http://localhost:8000/browser/action", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        action: "action_browser_navigate",
        params: { url }
      })
    });
    const result = await response.json();
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

// Start the server
mcp.run({ transport: "stdio" });
```

### Option 2: Direct Integration

Modify manus-open to directly implement the MCP protocol:

```python
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from app.tools.browser.browser_manager import BrowserManager

app = FastAPI()
mcp = FastMCP("manus-open MCP Server")

browser_manager = BrowserManager()

@mcp.tool()
async def browser_navigate(url: str) -> str:
    """Navigate to a URL in the browser."""
    result = await browser_manager.navigate(url)
    return result

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Option 3: Hybrid Approach

Keep the existing FastAPI server for backward compatibility, but add an MCP server that uses the same underlying tools:

```python
# Existing FastAPI server
app = FastAPI()

@app.post("/browser/action")
async def browser_action(request: BrowserActionRequest):
    # Existing implementation
    pass

# New MCP server
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("manus-open MCP Server")

@mcp.tool()
async def browser_navigate(url: str) -> str:
    # Use the same underlying implementation
    result = await browser_manager.navigate(url)
    return result

# Run both servers
import asyncio

async def main():
    # Run FastAPI server
    fastapi_task = asyncio.create_task(uvicorn.run(app, host="0.0.0.0", port=8000))
    
    # Run MCP server
    mcp_task = asyncio.create_task(mcp.run(transport="stdio"))
    
    await asyncio.gather(fastapi_task, mcp_task)

if __name__ == "__main__":
    asyncio.run(main())
```

## Tool Mapping

Here's how the 27 tools in manus-open map to MCP tools:

### Browser Tools

| manus-open Tool | MCP Tool | Description |
|-----------------|----------|-------------|
| action_browser_navigate | browser_navigate | Navigate to a URL |
| action_browser_click | browser_click | Click on an element |
| action_browser_input | browser_input | Type text into an element |
| action_browser_view | browser_view | Get the current page content |
| action_browser_screenshot | browser_screenshot | Take a screenshot |
| action_browser_scroll_down | browser_scroll_down | Scroll down the page |
| action_browser_scroll_up | browser_scroll_up | Scroll up the page |
| action_browser_press_key | browser_press_key | Press a keyboard key |
| action_browser_move_mouse | browser_move_mouse | Move the mouse to coordinates |
| action_browser_select_option | browser_select_option | Select an option from a dropdown |
| action_browser_console_view | browser_console_view | View browser console output |
| action_browser_console_exec | browser_console_exec | Execute JavaScript in console |
| action_browser_restart | browser_restart | Restart the browser |

### Terminal Tools

| manus-open Tool | MCP Tool | Description |
|-----------------|----------|-------------|
| terminal_execute_command | terminal_execute | Execute a shell command |
| terminal_send_control | terminal_send_control | Send control characters |
| terminal_send_key | terminal_send_key | Send a keyboard key |
| terminal_send_line | terminal_send_line | Send a line of text |
| terminal_kill_process | terminal_kill | Kill a running process |
| terminal_reset | terminal_reset | Reset the terminal |

### Text Editor Tools

| manus-open Tool | MCP Tool | Description |
|-----------------|----------|-------------|
| text_editor_view_dir | editor_view_dir | View directory contents |
| text_editor_view | editor_view | View file contents |
| text_editor_str_replace | editor_replace | Replace text in a file |
| text_editor_find_content | editor_find_content | Find content in files |
| text_editor_find_file | editor_find_file | Find files by pattern |
| text_editor_read_file | editor_read | Read a file |
| text_editor_write_file | editor_write | Write to a file |
| text_editor_create_file | editor_create | Create a new file |

## Implementation Plan

1. **Create MCP Server Wrapper**
   - Implement a TypeScript MCP server that wraps manus-open's API
   - Map each manus-open API endpoint to an MCP tool
   - Handle parameter conversion and result formatting

2. **Implement Tool Adapters**
   - Create adapter functions for each tool category (browser, terminal, text editor)
   - Handle error cases and status reporting
   - Ensure consistent response formats

3. **Add WebSocket Support**
   - Implement WebSocket communication for real-time tools (terminal, browser)
   - Create event-driven updates for long-running operations

4. **Enhance Response Formatting**
   - Ensure all tool responses follow MCP's content format
   - Add support for different content types (text, image, etc.)

5. **Test Integration**
   - Verify all tools work correctly through the MCP interface
   - Test with different AI models and clients
   - Benchmark performance and optimize as needed

## Example Implementation

Here's a more complete example of how to implement an MCP server that wraps manus-open's API:

```typescript
import { FastMCP } from "@modelcontextprotocol/sdk";
import { z } from "zod";
import axios from "axios";

const MANUS_OPEN_API = "http://localhost:8000";

const mcp = new FastMCP("manus-open MCP Server");

// Browser tools
mcp.tool(
  "browser_navigate",
  {
    url: z.string().url()
  },
  async ({ url }) => {
    try {
      const response = await axios.post(`${MANUS_OPEN_API}/browser/action`, {
        action: "action_browser_navigate",
        params: { url }
      });
      
      return {
        content: [
          {
            type: "text",
            text: `Successfully navigated to ${url}`
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error navigating to ${url}: ${error.message}`
          }
        ]
      };
    }
  }
);

mcp.tool(
  "browser_click",
  {
    selector: z.string()
  },
  async ({ selector }) => {
    try {
      const response = await axios.post(`${MANUS_OPEN_API}/browser/action`, {
        action: "action_browser_click",
        params: { selector }
      });
      
      return {
        content: [
          {
            type: "text",
            text: `Successfully clicked on ${selector}`
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error clicking on ${selector}: ${error.message}`
          }
        ]
      };
    }
  }
);

// Terminal tools
mcp.tool(
  "terminal_execute",
  {
    command: z.string(),
    terminal_id: z.string().optional()
  },
  async ({ command, terminal_id = "default" }) => {
    try {
      const response = await axios.post(`${MANUS_OPEN_API}/terminal/${terminal_id}/write`, {
        input: command,
        enter: true
      });
      
      // Wait for command to complete
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Get terminal output
      const outputResponse = await axios.get(`${MANUS_OPEN_API}/terminal/${terminal_id}/view`);
      
      return {
        content: [
          {
            type: "text",
            text: outputResponse.data.output
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error executing command: ${error.message}`
          }
        ]
      };
    }
  }
);

// Text editor tools
mcp.tool(
  "editor_read",
  {
    path: z.string(),
    sudo: z.boolean().optional()
  },
  async ({ path, sudo = false }) => {
    try {
      const response = await axios.post(`${MANUS_OPEN_API}/text_editor`, {
        action: "read_file",
        params: {
          path,
          sudo
        }
      });
      
      return {
        content: [
          {
            type: "text",
            text: response.data.content
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error reading file: ${error.message}`
          }
        ]
      };
    }
  }
);

// Start the server
mcp.run({ transport: "stdio" });
```

## Conclusion

Making manus-open MCP-compatible is feasible and would provide several benefits:

1. **Standardized Interface**: A consistent way to interact with AI models and tools
2. **Modularity**: Easier to swap out components or add new ones
3. **Future-Proofing**: Alignment with emerging standards in the AI ecosystem

The integration can be done incrementally, starting with the most commonly used tools and gradually adding more as needed. The existing API can be maintained for backward compatibility while adding the new MCP interface.

By following this guide, you can transform manus-open into an MCP-compatible tool that can be easily integrated with various AI models and applications.

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import * as MCPTypes from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { FileService } from "./src/services/fileService";
import { ShellService } from "./src/services/shellService";
import { BrowserService } from "./src/services/browserService";
import * as dotenv from "dotenv";

// Load environment variables
dotenv.config();

// Get configuration from environment variables
const PORT = process.env.PORT ? parseInt(process.env.PORT) : 8003;
const LOG_LEVEL = process.env.LOG_LEVEL || "info";
const ENABLE_BROWSER_SERVICE = process.env.ENABLE_BROWSER_SERVICE !== "false";
const ENABLE_FILE_SERVICE = process.env.ENABLE_FILE_SERVICE !== "false";
const ENABLE_SHELL_SERVICE = process.env.ENABLE_SHELL_SERVICE !== "false";
const OPENAI_BASE_URL = process.env.OPENAI_BASE_URL || "https://api.openai.com/v1";
const ANTHROPIC_BASE_URL = process.env.ANTHROPIC_BASE_URL || "https://api.anthropic.com";

// Initialize services based on configuration
const shellService = ENABLE_SHELL_SERVICE ? new ShellService() : undefined;
const fileService = ENABLE_FILE_SERVICE && shellService ? new FileService(shellService) : undefined;
const browserService = ENABLE_BROWSER_SERVICE ? new BrowserService() : undefined;

// Create an MCP server
const server = new McpServer({
  name: "ManusMCP-Local",
  version: "1.0.0",
  logLevel: LOG_LEVEL
});

// File operations
if (fileService) {
  server.tool(
    "file_read",
    {
      file: z.string(),
      startLine: z.number().optional(),
      endLine: z.number().optional(),
      sudo: z.boolean().optional()
    },
    async ({ file, startLine, endLine, sudo }) => {
      const result = await fileService.readFile(file, startLine, endLine, sudo);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }
  );
}

if (fileService) {
  server.tool(
    "file_read_image",
    {
      file: z.string(),
      sudo: z.boolean().optional()
    },
    async ({ file, sudo }) => {
      const result = await fileService.readImageFile(file, sudo);
      if (result.error) {
        return { content: [{ type: "text", text: JSON.stringify(result) }] };
      }
      return MCPTypes.CallToolResultSchema.parse({
        content: [
          { type: "image", data: `data:${result.mimeType};base64,${result.imageContent}`},
          { type: "text", text: JSON.stringify({ success: result.success }) }
        ]
      });
    }
  );
}

if (fileService) {
  server.tool(
    "file_write",
    {
      file: z.string(),
      content: z.string(),
      append: z.boolean().optional(),
      leadingNewline: z.boolean().optional(),
      trailingNewline: z.boolean().optional(),
      sudo: z.boolean().optional()
    },
    async ({ file, content, append, leadingNewline, trailingNewline, sudo }) => {
      const result = await fileService.writeFile(file, content, append, leadingNewline, trailingNewline, sudo);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }
  );
}

if (fileService) {
  server.tool(
    "file_str_replace",
    {
      file: z.string(),
      oldStr: z.string(),
      newStr: z.string(),
      sudo: z.boolean().optional()
    },
    async ({ file, oldStr, newStr, sudo }) => {
      const result = await fileService.replaceInFile(file, oldStr, newStr, sudo);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }
  );
}

if (fileService) {
  server.tool(
    "file_find_in_content",
    {
      file: z.string(),
      regex: z.string(),
      sudo: z.boolean().optional()
    },
    async ({ file, regex, sudo }) => {
      const result = await fileService.findInContent(file, regex, sudo);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }
  );
}

server.tool(
  "file_find_by_name",
  {
    path: z.string(),
    globPattern: z.string()
  },
  async ({ path, globPattern }) => {
    const result = await fileService.findByName(path, globPattern);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

// Shell operations
server.tool(
  "shell_exec",
  {
    id: z.string(),
    execDir: z.string().default("."),
    command: z.string()
  },
  async ({ id, execDir, command }) => {
    const result = await shellService.execCommand(id, execDir, command);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

server.tool(
  "shell_view",
  {
    id: z.string()
  },
  ({ id }) => {
    const result = shellService.viewSession(id);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

server.tool(
  "shell_wait",
  {
    id: z.string(),
    seconds: z.number().optional()
  },
  async ({ id, seconds }) => {
    const result = await shellService.waitForSession(id, seconds);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

server.tool(
  "shell_write_to_process",
  {
    id: z.string(),
    input: z.string(),
    pressEnter: z.boolean().optional()
  },
  async ({ id, input, pressEnter }) => {
    const result = await shellService.writeToProcess(id, input, pressEnter);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

server.tool(
  "shell_kill_process",
  {
    id: z.string()
  },
  async ({ id }) => {
    const result = await shellService.killProcess(id);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

server.tool(
  "shell_attach_nextjs_runtime",
  {
    useLinter: z.boolean().optional()
  },
  async ({ useLinter }) => {
    const result = await shellService.attachNextJSRuntime(useLinter ?? false);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

// Browser operations

server.tool(
  "browser_view",
  {},
  async () => {
    const result = await browserService.view();
    const screenshot = result.screenshot?.toString('base64') || "";
    const parsedScreenshot = result.parsedScreenshot?.toString('base64') || "";
    const parsedText = result.parsedText || "";
    return MCPTypes.CallToolResultSchema.parse({
      content: [
        { type: "image", data: `data:image/png;base64,${screenshot}`},
        { type: "image", data: `data:image/png;base64,${parsedScreenshot}`},
        { type: "text", text: parsedText}
      ]
    })
  }
);

server.tool(
  "browser_navigate",
  {
    url: z.string()
  },
  async ({ url }) => {
    const result = await browserService.navigate(url);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

server.tool(
  "browser_click",
  {
    index: z.number().optional(),
    coordinateX: z.number().optional(),
    coordinateY: z.number().optional()
  },
  async ({ index, coordinateX, coordinateY }) => {
    const result = await browserService.click(index, coordinateX, coordinateY);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

server.tool(
  "browser_input",
  {
    text: z.string(),
    pressEnter: z.boolean(),
    index: z.number().optional(),
    coordinateX: z.number().optional(),
    coordinateY: z.number().optional()
  },
  async ({ text, pressEnter, index, coordinateX, coordinateY }) => {
    const result = await browserService.input(text, pressEnter, index, coordinateX, coordinateY);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

server.tool(
  "browser_move_mouse",
  {
    coordinateX: z.number(),
    coordinateY: z.number()
  },
  async ({ coordinateX, coordinateY }) => {
    const result = await browserService.moveMouse(coordinateX, coordinateY);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

server.tool(
  "browser_press_key",
  {
    key: z.string()
  },
  async ({ key }) => {
    const result = await browserService.pressKey(key);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

server.tool(
  "browser_select_option",
  {
    index: z.number(),
    option: z.number()
  },
  async ({ index, option }) => {
    const result = await browserService.selectOption(index, option);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

server.tool(
  "browser_scroll_up",
  {
    toTop: z.boolean().optional()
  },
  async ({ toTop }) => {
    const result = await browserService.scroll('up', toTop ?? false);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

server.tool(
  "browser_scroll_down",
  {
    toBottom: z.boolean().optional()
  },
  async ({ toBottom }) => {
    const result = await browserService.scroll('down', toBottom ?? false);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

server.tool(
  "browser_console_exec",
  {
    javascript: z.string()
  },
  async ({ javascript }) => {
    const result = await browserService.executeJavaScript(javascript);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

server.tool(
  "browser_console_view",
  {
    maxLines: z.number().optional()
  },
  ({ maxLines }) => {
    const result = browserService.viewConsoleLogs(maxLines);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
);

// Configure API base URLs
if (process.env.OPENAI_API_KEY) {
  process.env.OPENAI_API_BASE = OPENAI_BASE_URL;
  console.log(`OpenAI API base URL set to: ${OPENAI_BASE_URL}`);
}

if (process.env.ANTHROPIC_API_KEY) {
  process.env.ANTHROPIC_API_URL = ANTHROPIC_BASE_URL;
  console.log(`Anthropic API base URL set to: ${ANTHROPIC_BASE_URL}`);
}

// Start HTTP server if PORT is specified
if (PORT) {
  const express = await import('express');
  const app = express.default();
  
  app.get('/health', (req, res) => {
    res.json({ status: 'ok', name: 'ManusMCP-Local', version: '1.0.0' });
  });
  
  app.listen(PORT, () => {
    console.log(`ManusMCP-Local server listening on port ${PORT}`);
  });
}

// Start receiving messages on stdin and sending messages on stdout
const transport = new StdioServerTransport();
await server.connect(transport);
console.log('ManusMCP-Local server started with transport');

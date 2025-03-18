"""
SQL MCP Client Implementation
----------------------------
This client interacts with the SQL MCP server using Anthropic's Claude model.
"""

import os
import asyncio
from dataclasses import dataclass, field
from typing import Union, cast, Dict, Any, List, Optional

import anthropic
from anthropic.types import MessageParam, TextBlock, ToolUnionParam, ToolUseBlock
from dotenv import load_dotenv
import httpx

load_dotenv()

# Anthropic API key
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

# SQL MCP server URL
SQL_MCP_SERVER_URL = os.environ.get("SQL_MCP_SERVER_URL", "http://localhost:8002")


@dataclass
class SQLChat:
    messages: List[MessageParam] = field(default_factory=list)
    
    system_prompt: str = """You are a master SQLite assistant. 
    Your job is to use the tools at your disposal to execute SQL queries and provide the results to the user.
    
    The database contains information about employees and departments with the following schema:
    
    Table: employees
    Columns:
      - id (INTEGER) - Primary key
      - name (TEXT) - Employee name
      - department (TEXT) - Department name
      - salary (REAL) - Employee salary
      - hire_date (TEXT) - Date when employee was hired
    
    Table: departments
    Columns:
      - id (INTEGER) - Primary key
      - name (TEXT) - Department name
      - budget (REAL) - Department budget
      - location (TEXT) - Department location
    
    When the user asks a question, translate it into an appropriate SQL query, execute it, and explain the results.
    Always show the SQL query you're using to answer the question.
    """
    
    async def get_available_tools(self) -> List[ToolUnionParam]:
        """Get the available tools from the MCP server."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SQL_MCP_SERVER_URL}/mcp/tools")
            response.raise_for_status()
            tools_data = response.json()
            
            return [
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["input_schema"]
                }
                for tool in tools_data["tools"]
            ]
    
    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SQL_MCP_SERVER_URL}/mcp/tools/{tool_name}",
                json=tool_args
            )
            response.raise_for_status()
            return response.json()
    
    async def process_query(self, query: str) -> None:
        """Process a user query using Claude and the MCP tools."""
        # Get available tools
        available_tools = await self.get_available_tools()
        
        # Create Anthropic client
        anthropic_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        
        # Add user message to conversation
        self.messages.append(MessageParam(role="user", content=query))
        
        # Initial Claude API call
        res = await anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            system=self.system_prompt,
            max_tokens=4000,
            messages=self.messages,
            tools=available_tools,
        )
        
        assistant_message_content: List[Union[ToolUseBlock, TextBlock]] = []
        for content in res.content:
            if content.type == "text":
                assistant_message_content.append(content)
                print(content.text)
            elif content.type == "tool_use":
                tool_name = content.name
                tool_args = content.input
                
                # Execute tool call
                result = await self.call_tool(tool_name, cast(Dict[str, Any], tool_args))
                
                assistant_message_content.append(content)
                self.messages.append({"role": "assistant", "content": assistant_message_content})
                self.messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": result.get("result", "No result returned")
                        }
                    ]
                })
                
                # Get next response from Claude
                res = await anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4000,
                    messages=self.messages,
                    tools=available_tools,
                )
                
                self.messages.append({
                    "role": "assistant",
                    "content": res.content[0].text if res.content[0].type == "text" else ""
                })
                
                if res.content[0].type == "text":
                    print(res.content[0].text)
    
    async def chat_loop(self):
        """Run an interactive chat loop."""
        print("SQL AI Assistant (type 'exit' to quit)")
        print("-------------------------------------")
        
        while True:
            query = input("\nQuery: ").strip()
            if query.lower() in ["exit", "quit"]:
                break
            
            await self.process_query(query)


async def main():
    chat = SQLChat()
    await chat.chat_loop()


if __name__ == "__main__":
    asyncio.run(main())

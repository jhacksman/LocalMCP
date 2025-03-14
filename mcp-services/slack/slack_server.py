"""
Slack MCP Server Implementation
------------------------------
This server provides MCP-compatible tools for Slack integration.
"""

import os
import json
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("slack_mcp_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("slack_mcp")

# Define API models
class MessageData(BaseModel):
    channel: str = Field(..., description="Slack channel ID or name")
    text: str = Field(..., description="Message text")
    thread_ts: Optional[str] = Field(None, description="Thread timestamp to reply to")
    blocks: Optional[List[Dict[str, Any]]] = Field(None, description="Slack blocks for rich messages")

class ChannelData(BaseModel):
    name: str = Field(..., description="Channel name")
    is_private: bool = Field(False, description="Whether the channel is private")
    user_ids: Optional[List[str]] = Field(None, description="User IDs to invite to the channel")

class SearchQuery(BaseModel):
    query: str = Field(..., description="Search query")
    count: int = Field(20, description="Number of results to return")
    sort: str = Field("score", description="Sort method (score or timestamp)")
    sort_dir: str = Field("desc", description="Sort direction (asc or desc)")

# Create FastAPI app
app = FastAPI(title="Slack MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Slack client setup
TOKEN_FILE = 'slack_token.json'

def get_slack_client():
    """Get the Slack client."""
    if not os.path.exists(TOKEN_FILE):
        logger.error("Slack token file not found")
        raise HTTPException(
            status_code=500,
            detail="Slack token file not found. Please create a slack_token.json file with your bot token."
        )
    
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)
        token = token_data.get('token')
    
    if not token:
        logger.error("No token found in token file")
        raise HTTPException(
            status_code=500,
            detail="No token found in slack_token.json. Please add your bot token."
        )
    
    return WebClient(token=token)

# MCP Tool Registration
@app.get("/mcp/tools")
async def get_tools():
    """Return the list of tools provided by this MCP server."""
    return {
        "tools": [
            {
                "name": "slack_send_message",
                "description": "Send a message to a Slack channel",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "channel": {"type": "string", "description": "Slack channel ID or name"},
                        "text": {"type": "string", "description": "Message text"},
                        "thread_ts": {"type": "string", "description": "Thread timestamp to reply to"},
                        "blocks": {"type": "array", "description": "Slack blocks for rich messages"}
                    },
                    "required": ["channel", "text"]
                }
            },
            {
                "name": "slack_create_channel",
                "description": "Create a new Slack channel",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Channel name"},
                        "is_private": {"type": "boolean", "description": "Whether the channel is private"},
                        "user_ids": {"type": "array", "items": {"type": "string"}, "description": "User IDs to invite to the channel"}
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "slack_list_channels",
                "description": "List all channels in the Slack workspace",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "slack_search",
                "description": "Search for messages in Slack",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "count": {"type": "integer", "description": "Number of results to return"},
                        "sort": {"type": "string", "description": "Sort method (score or timestamp)"},
                        "sort_dir": {"type": "string", "description": "Sort direction (asc or desc)"}
                    },
                    "required": ["query"]
                }
            }
        ]
    }

# Tool implementations
@app.post("/mcp/tools/slack_send_message")
async def send_message(message_data: MessageData):
    """Send a message to a Slack channel."""
    try:
        client = get_slack_client()
        
        # Prepare message payload
        payload = {
            "channel": message_data.channel,
            "text": message_data.text
        }
        
        # Add thread_ts if provided
        if message_data.thread_ts:
            payload["thread_ts"] = message_data.thread_ts
        
        # Add blocks if provided
        if message_data.blocks:
            payload["blocks"] = message_data.blocks
        
        # Send the message
        response = client.chat_postMessage(**payload)
        
        logger.info(f"Message sent to channel {message_data.channel}")
        return {
            "status": "success",
            "ts": response["ts"],
            "channel": response["channel"]
        }
    
    except SlackApiError as e:
        logger.error(f"Error sending message: {e.response['error']}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {e.response['error']}")
    
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")

@app.post("/mcp/tools/slack_create_channel")
async def create_channel(channel_data: ChannelData):
    """Create a new Slack channel."""
    try:
        client = get_slack_client()
        
        # Create the channel
        if channel_data.is_private:
            response = client.conversations_create(
                name=channel_data.name,
                is_private=True
            )
        else:
            response = client.conversations_create(
                name=channel_data.name,
                is_private=False
            )
        
        channel_id = response["channel"]["id"]
        
        # Invite users if provided
        if channel_data.user_ids:
            for user_id in channel_data.user_ids:
                try:
                    client.conversations_invite(
                        channel=channel_id,
                        users=[user_id]
                    )
                except SlackApiError as e:
                    logger.warning(f"Could not invite user {user_id}: {e.response['error']}")
        
        logger.info(f"Channel {channel_data.name} created with ID {channel_id}")
        return {
            "status": "success",
            "channel_id": channel_id,
            "name": channel_data.name,
            "is_private": channel_data.is_private
        }
    
    except SlackApiError as e:
        logger.error(f"Error creating channel: {e.response['error']}")
        raise HTTPException(status_code=500, detail=f"Error creating channel: {e.response['error']}")
    
    except Exception as e:
        logger.error(f"Error creating channel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating channel: {str(e)}")

@app.post("/mcp/tools/slack_list_channels")
async def list_channels():
    """List all channels in the Slack workspace."""
    try:
        client = get_slack_client()
        
        # Get public channels
        public_channels = []
        cursor = None
        
        while True:
            if cursor:
                response = client.conversations_list(cursor=cursor)
            else:
                response = client.conversations_list()
            
            public_channels.extend(response["channels"])
            
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        
        # Format the response
        channels = []
        for channel in public_channels:
            channels.append({
                "id": channel["id"],
                "name": channel["name"],
                "is_private": channel["is_private"],
                "is_archived": channel["is_archived"],
                "num_members": channel.get("num_members", 0),
                "topic": channel.get("topic", {}).get("value", ""),
                "purpose": channel.get("purpose", {}).get("value", "")
            })
        
        logger.info(f"Listed {len(channels)} channels")
        return {"channels": channels}
    
    except SlackApiError as e:
        logger.error(f"Error listing channels: {e.response['error']}")
        raise HTTPException(status_code=500, detail=f"Error listing channels: {e.response['error']}")
    
    except Exception as e:
        logger.error(f"Error listing channels: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing channels: {str(e)}")

@app.post("/mcp/tools/slack_search")
async def search(search_data: SearchQuery):
    """Search for messages in Slack."""
    try:
        client = get_slack_client()
        
        # Execute search
        response = client.search_messages(
            query=search_data.query,
            count=search_data.count,
            sort=search_data.sort,
            sort_dir=search_data.sort_dir
        )
        
        # Format the response
        messages = []
        for match in response["messages"]["matches"]:
            messages.append({
                "ts": match["ts"],
                "channel": {
                    "id": match["channel"]["id"],
                    "name": match["channel"]["name"]
                },
                "user": match.get("user", ""),
                "username": match.get("username", ""),
                "text": match["text"],
                "permalink": match.get("permalink", ""),
                "team": match.get("team", "")
            })
        
        logger.info(f"Found {len(messages)} messages matching query: {search_data.query}")
        return {
            "messages": messages,
            "total": response["messages"]["total"]
        }
    
    except SlackApiError as e:
        logger.error(f"Error searching messages: {e.response['error']}")
        raise HTTPException(status_code=500, detail=f"Error searching messages: {e.response['error']}")
    
    except Exception as e:
        logger.error(f"Error searching messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching messages: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

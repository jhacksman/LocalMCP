"""
Discord MCP Server Implementation
--------------------------------
This server provides MCP-compatible tools for Discord integration.
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import discord
from discord.ext import commands
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("discord_mcp_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("discord_mcp")

# Define API models
class MessageData(BaseModel):
    channel_id: str = Field(..., description="Discord channel ID")
    content: str = Field(..., description="Message content")

class ChannelData(BaseModel):
    guild_id: str = Field(..., description="Discord guild/server ID")
    name: str = Field(..., description="Channel name")
    topic: Optional[str] = Field(None, description="Channel topic/description")
    is_private: bool = Field(False, description="Whether the channel is private")

class SearchQuery(BaseModel):
    guild_id: str = Field(..., description="Discord guild/server ID")
    channel_id: Optional[str] = Field(None, description="Discord channel ID")
    query: str = Field(..., description="Search query")
    limit: int = Field(10, description="Maximum number of results")

# Create FastAPI app
app = FastAPI(title="Discord MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Discord bot setup
TOKEN_FILE = 'discord_token.json'

# Discord client with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Bot state
bot_ready = asyncio.Event()
bot_task = None

@bot.event
async def on_ready():
    """Called when the bot is ready."""
    logger.info(f"Logged in as {bot.user.name} ({bot.user.id})")
    bot_ready.set()

async def start_bot():
    """Start the Discord bot."""
    global bot_task
    
    if not os.path.exists(TOKEN_FILE):
        logger.error("Discord token file not found")
        raise HTTPException(
            status_code=500,
            detail="Discord token file not found. Please create a discord_token.json file with your bot token."
        )
    
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)
        token = token_data.get('token')
    
    if not token:
        logger.error("No token found in token file")
        raise HTTPException(
            status_code=500,
            detail="No token found in discord_token.json. Please add your bot token."
        )
    
    bot_task = asyncio.create_task(bot.start(token))
    await bot_ready.wait()

async def get_bot():
    """Get the Discord bot, starting it if necessary."""
    if not bot_ready.is_set():
        await start_bot()
    return bot

# MCP Tool Registration
@app.get("/mcp/tools")
async def get_tools():
    """Return the list of tools provided by this MCP server."""
    return {
        "tools": [
            {
                "name": "discord_send_message",
                "description": "Send a message to a Discord channel",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "channel_id": {"type": "string", "description": "Discord channel ID"},
                        "content": {"type": "string", "description": "Message content"}
                    },
                    "required": ["channel_id", "content"]
                }
            },
            {
                "name": "discord_create_channel",
                "description": "Create a new Discord channel in a server",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "guild_id": {"type": "string", "description": "Discord guild/server ID"},
                        "name": {"type": "string", "description": "Channel name"},
                        "topic": {"type": "string", "description": "Channel topic/description"},
                        "is_private": {"type": "boolean", "description": "Whether the channel is private"}
                    },
                    "required": ["guild_id", "name"]
                }
            },
            {
                "name": "discord_list_channels",
                "description": "List all channels in a Discord server",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "guild_id": {"type": "string", "description": "Discord guild/server ID"}
                    },
                    "required": ["guild_id"]
                }
            },
            {
                "name": "discord_search_messages",
                "description": "Search for messages in a Discord server or channel",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "guild_id": {"type": "string", "description": "Discord guild/server ID"},
                        "channel_id": {"type": "string", "description": "Discord channel ID (optional)"},
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Maximum number of results"}
                    },
                    "required": ["guild_id", "query"]
                }
            }
        ]
    }

# Tool implementations
@app.post("/mcp/tools/discord_send_message")
async def send_message(message_data: MessageData):
    """Send a message to a Discord channel."""
    try:
        discord_bot = await get_bot()
        
        # Get the channel
        channel = discord_bot.get_channel(int(message_data.channel_id))
        if not channel:
            raise HTTPException(status_code=404, detail=f"Channel with ID {message_data.channel_id} not found")
        
        # Send the message
        sent_message = await channel.send(message_data.content)
        
        logger.info(f"Message sent to channel {message_data.channel_id}")
        return {
            "status": "success",
            "message_id": str(sent_message.id),
            "timestamp": sent_message.created_at.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")

@app.post("/mcp/tools/discord_create_channel")
async def create_channel(channel_data: ChannelData):
    """Create a new Discord channel in a server."""
    try:
        discord_bot = await get_bot()
        
        # Get the guild
        guild = discord_bot.get_guild(int(channel_data.guild_id))
        if not guild:
            raise HTTPException(status_code=404, detail=f"Guild with ID {channel_data.guild_id} not found")
        
        # Create the channel
        if channel_data.is_private:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True)
            }
            channel = await guild.create_text_channel(
                name=channel_data.name,
                topic=channel_data.topic,
                overwrites=overwrites
            )
        else:
            channel = await guild.create_text_channel(
                name=channel_data.name,
                topic=channel_data.topic
            )
        
        logger.info(f"Channel {channel.name} created in guild {guild.name}")
        return {
            "status": "success",
            "channel_id": str(channel.id),
            "name": channel.name,
            "is_private": channel_data.is_private
        }
    
    except Exception as e:
        logger.error(f"Error creating channel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating channel: {str(e)}")

@app.post("/mcp/tools/discord_list_channels")
async def list_channels(guild_data: Dict[str, str]):
    """List all channels in a Discord server."""
    try:
        guild_id = guild_data.get("guild_id")
        if not guild_id:
            raise HTTPException(status_code=400, detail="guild_id is required")
        
        discord_bot = await get_bot()
        
        # Get the guild
        guild = discord_bot.get_guild(int(guild_id))
        if not guild:
            raise HTTPException(status_code=404, detail=f"Guild with ID {guild_id} not found")
        
        # Get all channels
        channels = []
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                channels.append({
                    "id": str(channel.id),
                    "name": channel.name,
                    "topic": channel.topic,
                    "type": "text",
                    "position": channel.position,
                    "is_nsfw": channel.is_nsfw()
                })
            elif isinstance(channel, discord.VoiceChannel):
                channels.append({
                    "id": str(channel.id),
                    "name": channel.name,
                    "type": "voice",
                    "position": channel.position,
                    "user_limit": channel.user_limit
                })
            elif isinstance(channel, discord.CategoryChannel):
                channels.append({
                    "id": str(channel.id),
                    "name": channel.name,
                    "type": "category",
                    "position": channel.position
                })
        
        # Sort channels by position
        channels.sort(key=lambda c: c["position"])
        
        logger.info(f"Listed {len(channels)} channels in guild {guild.name}")
        return {"channels": channels}
    
    except Exception as e:
        logger.error(f"Error listing channels: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing channels: {str(e)}")

@app.post("/mcp/tools/discord_search_messages")
async def search_messages(search: SearchQuery):
    """Search for messages in a Discord server or channel."""
    try:
        discord_bot = await get_bot()
        
        # Get the guild
        guild = discord_bot.get_guild(int(search.guild_id))
        if not guild:
            raise HTTPException(status_code=404, detail=f"Guild with ID {search.guild_id} not found")
        
        # Determine which channels to search
        channels_to_search = []
        if search.channel_id:
            channel = guild.get_channel(int(search.channel_id))
            if not channel:
                raise HTTPException(status_code=404, detail=f"Channel with ID {search.channel_id} not found")
            if isinstance(channel, discord.TextChannel):
                channels_to_search.append(channel)
        else:
            channels_to_search = [c for c in guild.channels if isinstance(c, discord.TextChannel)]
        
        # Search for messages
        results = []
        for channel in channels_to_search:
            async for message in channel.history(limit=100):
                if search.query.lower() in message.content.lower():
                    results.append({
                        "id": str(message.id),
                        "channel_id": str(channel.id),
                        "channel_name": channel.name,
                        "author": message.author.name,
                        "content": message.content,
                        "timestamp": message.created_at.isoformat(),
                        "attachments": [
                            {"filename": a.filename, "url": a.url}
                            for a in message.attachments
                        ]
                    })
                    
                    if len(results) >= search.limit:
                        break
            
            if len(results) >= search.limit:
                break
        
        logger.info(f"Found {len(results)} messages matching query: {search.query}")
        return {"messages": results}
    
    except Exception as e:
        logger.error(f"Error searching messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching messages: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    import uvicorn
    
    # Start the bot in the background
    asyncio.run(start_bot())
    
    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8001)

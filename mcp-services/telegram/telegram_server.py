"""
Telegram MCP Server Implementation
--------------------------------
This server provides MCP-compatible tools for Telegram integration.
"""

import os
import json
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.error import TelegramError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("telegram_mcp_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("telegram_mcp")

# Define API models
class MessageData(BaseModel):
    chat_id: str = Field(..., description="Telegram chat ID")
    text: str = Field(..., description="Message text")
    reply_to_message_id: Optional[int] = Field(None, description="Message ID to reply to")
    parse_mode: Optional[str] = Field(None, description="Parse mode (Markdown, MarkdownV2, HTML)")

class ChatData(BaseModel):
    chat_id: str = Field(..., description="Telegram chat ID")

class FileData(BaseModel):
    chat_id: str = Field(..., description="Telegram chat ID")
    file_path: str = Field(..., description="Path to file to send")
    caption: Optional[str] = Field(None, description="File caption")

# Create FastAPI app
app = FastAPI(title="Telegram MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Telegram bot setup
TOKEN_FILE = 'telegram_token.json'
bot_instance = None

async def get_bot():
    """Get the Telegram bot instance."""
    global bot_instance
    
    if bot_instance is not None:
        return bot_instance
    
    if not os.path.exists(TOKEN_FILE):
        logger.error("Telegram token file not found")
        raise HTTPException(
            status_code=500,
            detail="Telegram token file not found. Please create a telegram_token.json file with your bot token."
        )
    
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)
        token = token_data.get('token')
    
    if not token:
        logger.error("No token found in token file")
        raise HTTPException(
            status_code=500,
            detail="No token found in telegram_token.json. Please add your bot token."
        )
    
    bot_instance = Bot(token=token)
    return bot_instance

# MCP Tool Registration
@app.get("/mcp/tools")
async def get_tools():
    """Return the list of tools provided by this MCP server."""
    return {
        "tools": [
            {
                "name": "telegram_send_message",
                "description": "Send a message to a Telegram chat",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "chat_id": {"type": "string", "description": "Telegram chat ID"},
                        "text": {"type": "string", "description": "Message text"},
                        "reply_to_message_id": {"type": "integer", "description": "Message ID to reply to"},
                        "parse_mode": {"type": "string", "description": "Parse mode (Markdown, MarkdownV2, HTML)"}
                    },
                    "required": ["chat_id", "text"]
                }
            },
            {
                "name": "telegram_get_chat",
                "description": "Get information about a Telegram chat",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "chat_id": {"type": "string", "description": "Telegram chat ID"}
                    },
                    "required": ["chat_id"]
                }
            },
            {
                "name": "telegram_send_file",
                "description": "Send a file to a Telegram chat",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "chat_id": {"type": "string", "description": "Telegram chat ID"},
                        "file_path": {"type": "string", "description": "Path to file to send"},
                        "caption": {"type": "string", "description": "File caption"}
                    },
                    "required": ["chat_id", "file_path"]
                }
            },
            {
                "name": "telegram_get_chat_history",
                "description": "Get recent messages from a Telegram chat",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "chat_id": {"type": "string", "description": "Telegram chat ID"},
                        "limit": {"type": "integer", "description": "Maximum number of messages to retrieve"}
                    },
                    "required": ["chat_id"]
                }
            }
        ]
    }

# Tool implementations
@app.post("/mcp/tools/telegram_send_message")
async def send_message(message_data: MessageData):
    """Send a message to a Telegram chat."""
    try:
        bot = await get_bot()
        
        # Prepare message parameters
        params = {
            "chat_id": message_data.chat_id,
            "text": message_data.text
        }
        
        # Add optional parameters if provided
        if message_data.reply_to_message_id:
            params["reply_to_message_id"] = message_data.reply_to_message_id
        
        if message_data.parse_mode:
            params["parse_mode"] = message_data.parse_mode
        
        # Send the message
        message = await bot.send_message(**params)
        
        logger.info(f"Message sent to chat {message_data.chat_id}")
        return {
            "status": "success",
            "message_id": message.message_id,
            "date": message.date.isoformat()
        }
    
    except TelegramError as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")

@app.post("/mcp/tools/telegram_get_chat")
async def get_chat(chat_data: ChatData):
    """Get information about a Telegram chat."""
    try:
        bot = await get_bot()
        
        # Get chat info
        chat = await bot.get_chat(chat_data.chat_id)
        
        # Format the response
        chat_info = {
            "id": chat.id,
            "type": chat.type,
            "title": chat.title if chat.title else None,
            "username": chat.username if chat.username else None,
            "first_name": chat.first_name if hasattr(chat, "first_name") else None,
            "last_name": chat.last_name if hasattr(chat, "last_name") else None,
            "description": chat.description if hasattr(chat, "description") else None,
            "invite_link": chat.invite_link if hasattr(chat, "invite_link") else None,
            "member_count": chat.get_member_count() if hasattr(chat, "get_member_count") else None
        }
        
        logger.info(f"Retrieved chat info for chat {chat_data.chat_id}")
        return chat_info
    
    except TelegramError as e:
        logger.error(f"Error getting chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting chat: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error getting chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting chat: {str(e)}")

@app.post("/mcp/tools/telegram_send_file")
async def send_file(file_data: FileData):
    """Send a file to a Telegram chat."""
    try:
        bot = await get_bot()
        
        # Check if file exists
        if not os.path.exists(file_data.file_path):
            raise HTTPException(status_code=400, detail=f"File not found: {file_data.file_path}")
        
        # Determine file type based on extension
        file_ext = os.path.splitext(file_data.file_path)[1].lower()
        
        # Prepare file parameters
        params = {
            "chat_id": file_data.chat_id,
            "caption": file_data.caption
        }
        
        # Send the file based on its type
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
            with open(file_data.file_path, 'rb') as photo:
                message = await bot.send_photo(photo=photo, **params)
        elif file_ext in ['.mp4', '.avi', '.mov']:
            with open(file_data.file_path, 'rb') as video:
                message = await bot.send_video(video=video, **params)
        elif file_ext in ['.mp3', '.ogg', '.wav']:
            with open(file_data.file_path, 'rb') as audio:
                message = await bot.send_audio(audio=audio, **params)
        elif file_ext in ['.pdf', '.doc', '.docx', '.txt']:
            with open(file_data.file_path, 'rb') as document:
                message = await bot.send_document(document=document, **params)
        else:
            # Default to document for unknown file types
            with open(file_data.file_path, 'rb') as document:
                message = await bot.send_document(document=document, **params)
        
        logger.info(f"File sent to chat {file_data.chat_id}")
        return {
            "status": "success",
            "message_id": message.message_id,
            "date": message.date.isoformat()
        }
    
    except TelegramError as e:
        logger.error(f"Error sending file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending file: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error sending file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending file: {str(e)}")

@app.post("/mcp/tools/telegram_get_chat_history")
async def get_chat_history(history_data: Dict[str, Any]):
    """Get recent messages from a Telegram chat."""
    try:
        bot = await get_bot()
        
        chat_id = history_data.get("chat_id")
        limit = history_data.get("limit", 10)
        
        if not chat_id:
            raise HTTPException(status_code=400, detail="chat_id is required")
        
        # Get chat history
        # Note: This is a simplified implementation as the Telegram Bot API
        # doesn't provide a direct way to get chat history. In a real implementation,
        # you would need to use the Telegram API or maintain a message database.
        
        # For now, we'll return a placeholder response
        logger.warning("Chat history retrieval is limited in the Telegram Bot API")
        return {
            "status": "partial",
            "message": "Chat history retrieval is limited in the Telegram Bot API. Consider using the Telegram API directly or implementing a message database.",
            "messages": []
        }
    
    except TelegramError as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting chat history: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting chat history: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)

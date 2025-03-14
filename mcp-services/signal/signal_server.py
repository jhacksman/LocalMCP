"""
Signal MCP Server Implementation
------------------------------
This server provides MCP-compatible tools for Signal integration.
"""

import os
import json
import subprocess
import tempfile
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("signal_mcp_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("signal_mcp")

# Define API models
class MessageData(BaseModel):
    recipient: str = Field(..., description="Signal recipient (phone number)")
    message: str = Field(..., description="Message text")
    attachments: Optional[List[str]] = Field(None, description="Paths to attachment files")

class GroupMessageData(BaseModel):
    group_id: str = Field(..., description="Signal group ID")
    message: str = Field(..., description="Message text")
    attachments: Optional[List[str]] = Field(None, description="Paths to attachment files")

class GroupData(BaseModel):
    name: str = Field(..., description="Group name")
    members: List[str] = Field(..., description="List of phone numbers to add to the group")

# Create FastAPI app
app = FastAPI(title="Signal MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Signal CLI configuration
SIGNAL_CLI_PATH = "/usr/local/bin/signal-cli"
CONFIG_FILE = "signal_config.json"

def get_signal_config():
    """Get Signal configuration."""
    if not os.path.exists(CONFIG_FILE):
        logger.error("Signal configuration file not found")
        raise HTTPException(
            status_code=500,
            detail="Signal configuration file not found. Please create a signal_config.json file with your configuration."
        )
    
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    required_keys = ['phone_number']
    missing_keys = [key for key in required_keys if key not in config]
    
    if missing_keys:
        logger.error(f"Missing Signal configuration: {', '.join(missing_keys)}")
        raise HTTPException(
            status_code=500,
            detail=f"Missing Signal configuration: {', '.join(missing_keys)}"
        )
    
    return config

def run_signal_cli(args):
    """Run signal-cli command."""
    config = get_signal_config()
    phone_number = config['phone_number']
    
    # Check if signal-cli is installed
    if not os.path.exists(SIGNAL_CLI_PATH):
        logger.error(f"signal-cli not found at {SIGNAL_CLI_PATH}")
        raise HTTPException(
            status_code=500,
            detail=f"signal-cli not found at {SIGNAL_CLI_PATH}. Please install signal-cli."
        )
    
    # Build the command
    cmd = [SIGNAL_CLI_PATH, "-u", phone_number] + args
    
    try:
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return result.stdout
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running signal-cli: {e.stderr}")
        raise HTTPException(
            status_code=500,
            detail=f"Error running signal-cli: {e.stderr}"
        )
    
    except Exception as e:
        logger.error(f"Error running signal-cli: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error running signal-cli: {str(e)}"
        )

# MCP Tool Registration
@app.get("/mcp/tools")
async def get_tools():
    """Return the list of tools provided by this MCP server."""
    return {
        "tools": [
            {
                "name": "signal_send_message",
                "description": "Send a message to a Signal recipient",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "recipient": {"type": "string", "description": "Signal recipient (phone number)"},
                        "message": {"type": "string", "description": "Message text"},
                        "attachments": {"type": "array", "items": {"type": "string"}, "description": "Paths to attachment files"}
                    },
                    "required": ["recipient", "message"]
                }
            },
            {
                "name": "signal_send_group_message",
                "description": "Send a message to a Signal group",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "group_id": {"type": "string", "description": "Signal group ID"},
                        "message": {"type": "string", "description": "Message text"},
                        "attachments": {"type": "array", "items": {"type": "string"}, "description": "Paths to attachment files"}
                    },
                    "required": ["group_id", "message"]
                }
            },
            {
                "name": "signal_create_group",
                "description": "Create a new Signal group",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Group name"},
                        "members": {"type": "array", "items": {"type": "string"}, "description": "List of phone numbers to add to the group"}
                    },
                    "required": ["name", "members"]
                }
            },
            {
                "name": "signal_list_groups",
                "description": "List all Signal groups",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    }

# Tool implementations
@app.post("/mcp/tools/signal_send_message")
async def send_message(message_data: MessageData):
    """Send a message to a Signal recipient."""
    try:
        # Prepare command arguments
        args = ["send", "-m", message_data.message, message_data.recipient]
        
        # Add attachments if provided
        if message_data.attachments:
            for attachment in message_data.attachments:
                if not os.path.exists(attachment):
                    raise HTTPException(status_code=400, detail=f"Attachment file not found: {attachment}")
                args.extend(["-a", attachment])
        
        # Run the command
        output = run_signal_cli(args)
        
        logger.info(f"Message sent to {message_data.recipient}")
        return {
            "status": "success",
            "recipient": message_data.recipient,
            "output": output
        }
    
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")

@app.post("/mcp/tools/signal_send_group_message")
async def send_group_message(message_data: GroupMessageData):
    """Send a message to a Signal group."""
    try:
        # Prepare command arguments
        args = ["send", "-m", message_data.message, "-g", message_data.group_id]
        
        # Add attachments if provided
        if message_data.attachments:
            for attachment in message_data.attachments:
                if not os.path.exists(attachment):
                    raise HTTPException(status_code=400, detail=f"Attachment file not found: {attachment}")
                args.extend(["-a", attachment])
        
        # Run the command
        output = run_signal_cli(args)
        
        logger.info(f"Message sent to group {message_data.group_id}")
        return {
            "status": "success",
            "group_id": message_data.group_id,
            "output": output
        }
    
    except Exception as e:
        logger.error(f"Error sending group message: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error sending group message: {str(e)}")

@app.post("/mcp/tools/signal_create_group")
async def create_group(group_data: GroupData):
    """Create a new Signal group."""
    try:
        # Create a temporary file for the group avatar
        with tempfile.NamedTemporaryFile(suffix=".tmp") as tmp:
            # Prepare command arguments
            args = ["updateGroup", "-n", group_data.name, "-m"] + group_data.members
            
            # Run the command
            output = run_signal_cli(args)
            
            # Extract group ID from output
            # Note: This is a simplified implementation. In practice, you would need to
            # parse the output to extract the group ID, which depends on the signal-cli version.
            group_id = "unknown"  # Placeholder
            
            logger.info(f"Group {group_data.name} created")
            return {
                "status": "success",
                "name": group_data.name,
                "members": group_data.members,
                "group_id": group_id,
                "output": output
            }
    
    except Exception as e:
        logger.error(f"Error creating group: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error creating group: {str(e)}")

@app.post("/mcp/tools/signal_list_groups")
async def list_groups():
    """List all Signal groups."""
    try:
        # Prepare command arguments
        args = ["listGroups", "-d"]
        
        # Run the command
        output = run_signal_cli(args)
        
        # Parse the output to extract group information
        # Note: This is a simplified implementation. In practice, you would need to
        # parse the output to extract the group information, which depends on the signal-cli version.
        groups = []
        
        logger.info("Listed Signal groups")
        return {
            "status": "success",
            "groups": groups,
            "output": output
        }
    
    except Exception as e:
        logger.error(f"Error listing groups: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error listing groups: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)

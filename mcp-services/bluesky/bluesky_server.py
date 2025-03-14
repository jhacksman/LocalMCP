"""
Bluesky MCP Server Implementation
-------------------------------
This server provides MCP-compatible tools for Bluesky integration.
"""

import os
import json
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import atproto
from atproto.xrpc_client import XrpcClient
from atproto.exceptions import AtProtocolError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bluesky_mcp_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("bluesky_mcp")

# Define API models
class PostData(BaseModel):
    text: str = Field(..., description="Post text content")
    images: Optional[List[str]] = Field(None, description="List of image file paths to upload")
    reply_to: Optional[str] = Field(None, description="URI of post to reply to")
    quote: Optional[str] = Field(None, description="URI of post to quote")

class SearchQuery(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(10, description="Number of results to return")

class ProfileLookup(BaseModel):
    handle: str = Field(..., description="Bluesky handle (e.g., user.bsky.social)")

# Create FastAPI app
app = FastAPI(title="Bluesky MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bluesky client setup
CREDENTIALS_FILE = 'bluesky_credentials.json'

def get_bluesky_client():
    """Get the Bluesky API client."""
    if not os.path.exists(CREDENTIALS_FILE):
        logger.error("Bluesky credentials file not found")
        raise HTTPException(
            status_code=500,
            detail="Bluesky credentials file not found. Please create a bluesky_credentials.json file with your credentials."
        )
    
    with open(CREDENTIALS_FILE, 'r') as f:
        creds = json.load(f)
    
    required_keys = ['handle', 'password']
    missing_keys = [key for key in required_keys if key not in creds]
    
    if missing_keys:
        logger.error(f"Missing Bluesky credentials: {', '.join(missing_keys)}")
        raise HTTPException(
            status_code=500,
            detail=f"Missing Bluesky credentials: {', '.join(missing_keys)}"
        )
    
    client = atproto.Client()
    try:
        client.login(creds['handle'], creds['password'])
        return client
    except Exception as e:
        logger.error(f"Error logging in to Bluesky: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error logging in to Bluesky: {str(e)}"
        )

# MCP Tool Registration
@app.get("/mcp/tools")
async def get_tools():
    """Return the list of tools provided by this MCP server."""
    return {
        "tools": [
            {
                "name": "bluesky_post",
                "description": "Create a new post on Bluesky",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Post text content"},
                        "images": {"type": "array", "items": {"type": "string"}, "description": "List of image file paths to upload"},
                        "reply_to": {"type": "string", "description": "URI of post to reply to"},
                        "quote": {"type": "string", "description": "URI of post to quote"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "bluesky_search",
                "description": "Search for posts on Bluesky",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Number of results to return"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "bluesky_get_profile",
                "description": "Get information about a Bluesky user",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "handle": {"type": "string", "description": "Bluesky handle (e.g., user.bsky.social)"}
                    },
                    "required": ["handle"]
                }
            },
            {
                "name": "bluesky_get_timeline",
                "description": "Get the user's timeline",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Number of posts to return"}
                    }
                }
            }
        ]
    }

# Tool implementations
@app.post("/mcp/tools/bluesky_post")
async def create_post(post_data: PostData):
    """Create a new post on Bluesky."""
    try:
        client = get_bluesky_client()
        
        # Handle images if provided
        images = []
        if post_data.images:
            for image_path in post_data.images:
                if not os.path.exists(image_path):
                    raise HTTPException(status_code=400, detail=f"Image file not found: {image_path}")
                
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                
                # Upload the image
                upload_response = client.upload_blob(image_data)
                
                # Add image to the list
                images.append({
                    "image": upload_response.blob,
                    "alt": os.path.basename(image_path)  # Use filename as alt text
                })
        
        # Prepare post parameters
        params = {
            "text": post_data.text,
            "facets": []  # For mentions, links, etc.
        }
        
        # Add images if any
        if images:
            params["embed"] = {
                "$type": "app.bsky.embed.images",
                "images": images
            }
        
        # Handle reply
        if post_data.reply_to:
            # Parse the URI to get the repo and record ID
            parts = post_data.reply_to.split('/')
            if len(parts) >= 2:
                repo = parts[-2]
                record_id = parts[-1]
                
                params["reply"] = {
                    "root": {
                        "uri": post_data.reply_to,
                        "cid": ""  # We don't have the CID, but the API can handle it
                    },
                    "parent": {
                        "uri": post_data.reply_to,
                        "cid": ""
                    }
                }
        
        # Handle quote
        if post_data.quote:
            params["embed"] = {
                "$type": "app.bsky.embed.record",
                "record": {
                    "uri": post_data.quote,
                    "cid": ""  # We don't have the CID, but the API can handle it
                }
            }
        
        # Create the post
        response = client.send_post(**params)
        
        logger.info(f"Post created with URI: {response.uri}")
        return {
            "status": "success",
            "uri": response.uri,
            "cid": response.cid
        }
    
    except AtProtocolError as e:
        logger.error(f"Error creating post: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating post: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating post: {str(e)}")

@app.post("/mcp/tools/bluesky_search")
async def search_posts(search_data: SearchQuery):
    """Search for posts on Bluesky."""
    try:
        client = get_bluesky_client()
        
        # Execute search
        response = client.app.bsky.feed.search_posts({
            "q": search_data.query,
            "limit": search_data.limit
        })
        
        # Format the response
        posts = []
        for post in response.posts:
            post_data = {
                "uri": post.uri,
                "cid": post.cid,
                "text": post.record.text,
                "created_at": post.record.created_at,
                "author": {
                    "did": post.author.did,
                    "handle": post.author.handle,
                    "display_name": post.author.display_name
                },
                "like_count": post.like_count,
                "reply_count": post.reply_count,
                "repost_count": post.repost_count
            }
            
            # Add embed data if available
            if hasattr(post.record, "embed"):
                if post.record.embed.get("$type") == "app.bsky.embed.images":
                    post_data["images"] = [
                        {"url": img.get("fullsize", "")}
                        for img in post.record.embed.get("images", [])
                    ]
                elif post.record.embed.get("$type") == "app.bsky.embed.record":
                    post_data["quote"] = {
                        "uri": post.record.embed.get("record", {}).get("uri", "")
                    }
            
            posts.append(post_data)
        
        logger.info(f"Found {len(posts)} posts matching query: {search_data.query}")
        return {"posts": posts}
    
    except AtProtocolError as e:
        logger.error(f"Error searching posts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching posts: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error searching posts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching posts: {str(e)}")

@app.post("/mcp/tools/bluesky_get_profile")
async def get_profile(profile_data: ProfileLookup):
    """Get information about a Bluesky user."""
    try:
        client = get_bluesky_client()
        
        # Get profile info
        response = client.app.bsky.actor.get_profile({
            "actor": profile_data.handle
        })
        
        # Format the response
        profile = {
            "did": response.did,
            "handle": response.handle,
            "display_name": response.display_name,
            "description": response.description,
            "followers_count": response.followers_count,
            "follows_count": response.follows_count,
            "posts_count": response.posts_count,
            "indexed_at": response.indexed_at
        }
        
        # Add avatar if available
        if hasattr(response, "avatar"):
            profile["avatar"] = response.avatar
        
        logger.info(f"Retrieved profile for: {profile_data.handle}")
        return profile
    
    except AtProtocolError as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting profile: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting profile: {str(e)}")

@app.post("/mcp/tools/bluesky_get_timeline")
async def get_timeline(timeline_data: Dict[str, Any] = {}):
    """Get the user's timeline."""
    try:
        client = get_bluesky_client()
        
        # Get timeline
        limit = timeline_data.get("limit", 10)
        response = client.app.bsky.feed.get_timeline({
            "limit": limit
        })
        
        # Format the response
        posts = []
        for feed_view in response.feed:
            post = feed_view.post
            
            post_data = {
                "uri": post.uri,
                "cid": post.cid,
                "text": post.record.text,
                "created_at": post.record.created_at,
                "author": {
                    "did": post.author.did,
                    "handle": post.author.handle,
                    "display_name": post.author.display_name
                },
                "like_count": post.like_count,
                "reply_count": post.reply_count,
                "repost_count": post.repost_count
            }
            
            # Add embed data if available
            if hasattr(post.record, "embed"):
                if post.record.embed.get("$type") == "app.bsky.embed.images":
                    post_data["images"] = [
                        {"url": img.get("fullsize", "")}
                        for img in post.record.embed.get("images", [])
                    ]
                elif post.record.embed.get("$type") == "app.bsky.embed.record":
                    post_data["quote"] = {
                        "uri": post.record.embed.get("record", {}).get("uri", "")
                    }
            
            posts.append(post_data)
        
        logger.info(f"Retrieved {len(posts)} posts from timeline")
        return {"posts": posts}
    
    except AtProtocolError as e:
        logger.error(f"Error getting timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting timeline: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error getting timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting timeline: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

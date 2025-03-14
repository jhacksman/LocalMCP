"""
Notion MCP Server Implementation
------------------------------
This server provides MCP-compatible tools for Notion integration.
"""

import os
import json
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from notion_client import Client
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("notion_mcp_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("notion_mcp")

# Define API models
class PageData(BaseModel):
    parent_id: str = Field(..., description="Parent page or database ID")
    title: str = Field(..., description="Page title")
    content: Optional[str] = Field(None, description="Page content in Markdown format")
    properties: Optional[Dict[str, Any]] = Field(None, description="Additional page properties for database pages")
    is_database: bool = Field(False, description="Whether the parent is a database")

class DatabaseData(BaseModel):
    parent_id: str = Field(..., description="Parent page ID")
    title: str = Field(..., description="Database title")
    properties: Dict[str, Dict[str, Any]] = Field(..., description="Database properties schema")

class QueryData(BaseModel):
    database_id: str = Field(..., description="Database ID to query")
    filter: Optional[Dict[str, Any]] = Field(None, description="Filter to apply to the query")
    sorts: Optional[List[Dict[str, Any]]] = Field(None, description="Sort order for the query results")
    page_size: int = Field(10, description="Number of results per page")

class BlockData(BaseModel):
    block_id: str = Field(..., description="Block ID to update")
    content: str = Field(..., description="Block content")
    type: str = Field("paragraph", description="Block type")

class SearchData(BaseModel):
    query: str = Field(..., description="Search query")
    filter: Optional[Dict[str, Any]] = Field(None, description="Filter to apply to the search")
    sort: Optional[Dict[str, Any]] = Field(None, description="Sort order for the search results")
    page_size: int = Field(10, description="Number of results per page")

# Create FastAPI app
app = FastAPI(title="Notion MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Notion client setup
TOKEN_FILE = 'notion_token.json'

def get_notion_client():
    """Get the Notion API client."""
    if not os.path.exists(TOKEN_FILE):
        logger.error("Notion token file not found")
        raise HTTPException(
            status_code=500,
            detail="Notion token file not found. Please create a notion_token.json file with your integration token."
        )
    
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)
        token = token_data.get('token')
    
    if not token:
        logger.error("No token found in token file")
        raise HTTPException(
            status_code=500,
            detail="No token found in notion_token.json. Please add your integration token."
        )
    
    return Client(auth=token)

# MCP Tool Registration
@app.get("/mcp/tools")
async def get_tools():
    """Return the list of tools provided by this MCP server."""
    return {
        "tools": [
            {
                "name": "notion_create_page",
                "description": "Create a new page in Notion",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "parent_id": {"type": "string", "description": "Parent page or database ID"},
                        "title": {"type": "string", "description": "Page title"},
                        "content": {"type": "string", "description": "Page content in Markdown format"},
                        "properties": {"type": "object", "description": "Additional page properties for database pages"},
                        "is_database": {"type": "boolean", "description": "Whether the parent is a database"}
                    },
                    "required": ["parent_id", "title"]
                }
            },
            {
                "name": "notion_get_page",
                "description": "Get a Notion page by ID",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "page_id": {"type": "string", "description": "Notion page ID"}
                    },
                    "required": ["page_id"]
                }
            },
            {
                "name": "notion_update_page",
                "description": "Update a Notion page",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "page_id": {"type": "string", "description": "Notion page ID"},
                        "properties": {"type": "object", "description": "Page properties to update"}
                    },
                    "required": ["page_id", "properties"]
                }
            },
            {
                "name": "notion_create_database",
                "description": "Create a new database in Notion",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "parent_id": {"type": "string", "description": "Parent page ID"},
                        "title": {"type": "string", "description": "Database title"},
                        "properties": {"type": "object", "description": "Database properties schema"}
                    },
                    "required": ["parent_id", "title", "properties"]
                }
            },
            {
                "name": "notion_query_database",
                "description": "Query a Notion database",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "database_id": {"type": "string", "description": "Database ID to query"},
                        "filter": {"type": "object", "description": "Filter to apply to the query"},
                        "sorts": {"type": "array", "description": "Sort order for the query results"},
                        "page_size": {"type": "integer", "description": "Number of results per page"}
                    },
                    "required": ["database_id"]
                }
            },
            {
                "name": "notion_get_block_children",
                "description": "Get children blocks of a block",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "block_id": {"type": "string", "description": "Block ID"},
                        "page_size": {"type": "integer", "description": "Number of results per page"}
                    },
                    "required": ["block_id"]
                }
            },
            {
                "name": "notion_append_block_children",
                "description": "Append children blocks to a block",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "block_id": {"type": "string", "description": "Block ID"},
                        "children": {"type": "array", "description": "Children blocks to append"}
                    },
                    "required": ["block_id", "children"]
                }
            },
            {
                "name": "notion_search",
                "description": "Search Notion",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "filter": {"type": "object", "description": "Filter to apply to the search"},
                        "sort": {"type": "object", "description": "Sort order for the search results"},
                        "page_size": {"type": "integer", "description": "Number of results per page"}
                    },
                    "required": ["query"]
                }
            }
        ]
    }

# Tool implementations
@app.post("/mcp/tools/notion_create_page")
async def create_page(page_data: PageData):
    """Create a new page in Notion."""
    try:
        notion = get_notion_client()
        
        # Prepare parent object
        if page_data.is_database:
            parent = {"database_id": page_data.parent_id}
        else:
            parent = {"page_id": page_data.parent_id}
        
        # Prepare properties
        if page_data.is_database:
            # For database pages, use provided properties or create minimal ones
            properties = page_data.properties or {}
            
            # Ensure there's a title property
            if "Name" not in properties and "Title" not in properties:
                properties["Name"] = {"title": [{"text": {"content": page_data.title}}]}
        else:
            # For regular pages, create a title property
            properties = {
                "title": [{"text": {"content": page_data.title}}]
            }
        
        # Create the page
        new_page = notion.pages.create(
            parent=parent,
            properties=properties
        )
        
        # If content is provided, add it to the page
        if page_data.content:
            # Convert Markdown to Notion blocks (simplified)
            blocks = []
            for line in page_data.content.split('\n'):
                if line.strip():
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": line}}]
                        }
                    })
            
            # Append blocks to the page
            if blocks:
                notion.blocks.children.append(
                    block_id=new_page["id"],
                    children=blocks
                )
        
        logger.info(f"Created page with ID: {new_page['id']}")
        return {
            "status": "success",
            "page_id": new_page["id"],
            "url": new_page.get("url")
        }
    
    except Exception as e:
        logger.error(f"Error creating page: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating page: {str(e)}")

@app.post("/mcp/tools/notion_get_page")
async def get_page(page_data: Dict[str, str]):
    """Get a Notion page by ID."""
    try:
        page_id = page_data.get("page_id")
        
        if not page_id:
            raise HTTPException(status_code=400, detail="page_id is required")
        
        notion = get_notion_client()
        
        # Get the page
        page = notion.pages.retrieve(page_id=page_id)
        
        # Get page content (blocks)
        blocks = notion.blocks.children.list(block_id=page_id)
        
        logger.info(f"Retrieved page with ID: {page_id}")
        return {
            "page": page,
            "blocks": blocks
        }
    
    except Exception as e:
        logger.error(f"Error getting page: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting page: {str(e)}")

@app.post("/mcp/tools/notion_update_page")
async def update_page(page_data: Dict[str, Any]):
    """Update a Notion page."""
    try:
        page_id = page_data.get("page_id")
        properties = page_data.get("properties")
        
        if not page_id:
            raise HTTPException(status_code=400, detail="page_id is required")
        
        if not properties:
            raise HTTPException(status_code=400, detail="properties is required")
        
        notion = get_notion_client()
        
        # Update the page
        updated_page = notion.pages.update(
            page_id=page_id,
            properties=properties
        )
        
        logger.info(f"Updated page with ID: {page_id}")
        return {
            "status": "success",
            "page_id": updated_page["id"],
            "url": updated_page.get("url")
        }
    
    except Exception as e:
        logger.error(f"Error updating page: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating page: {str(e)}")

@app.post("/mcp/tools/notion_create_database")
async def create_database(database_data: DatabaseData):
    """Create a new database in Notion."""
    try:
        notion = get_notion_client()
        
        # Prepare parent object
        parent = {"page_id": database_data.parent_id}
        
        # Prepare title
        title = [{"type": "text", "text": {"content": database_data.title}}]
        
        # Create the database
        new_database = notion.databases.create(
            parent=parent,
            title=title,
            properties=database_data.properties
        )
        
        logger.info(f"Created database with ID: {new_database['id']}")
        return {
            "status": "success",
            "database_id": new_database["id"],
            "url": new_database.get("url")
        }
    
    except Exception as e:
        logger.error(f"Error creating database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating database: {str(e)}")

@app.post("/mcp/tools/notion_query_database")
async def query_database(query_data: QueryData):
    """Query a Notion database."""
    try:
        notion = get_notion_client()
        
        # Prepare query parameters
        params = {
            "database_id": query_data.database_id,
            "page_size": query_data.page_size
        }
        
        # Add filter if provided
        if query_data.filter:
            params["filter"] = query_data.filter
        
        # Add sorts if provided
        if query_data.sorts:
            params["sorts"] = query_data.sorts
        
        # Query the database
        results = notion.databases.query(**params)
        
        logger.info(f"Queried database with ID: {query_data.database_id}")
        return results
    
    except Exception as e:
        logger.error(f"Error querying database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error querying database: {str(e)}")

@app.post("/mcp/tools/notion_get_block_children")
async def get_block_children(block_data: Dict[str, Any]):
    """Get children blocks of a block."""
    try:
        block_id = block_data.get("block_id")
        page_size = block_data.get("page_size", 100)
        
        if not block_id:
            raise HTTPException(status_code=400, detail="block_id is required")
        
        notion = get_notion_client()
        
        # Get block children
        children = notion.blocks.children.list(
            block_id=block_id,
            page_size=page_size
        )
        
        logger.info(f"Retrieved children of block with ID: {block_id}")
        return children
    
    except Exception as e:
        logger.error(f"Error getting block children: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting block children: {str(e)}")

@app.post("/mcp/tools/notion_append_block_children")
async def append_block_children(block_data: Dict[str, Any]):
    """Append children blocks to a block."""
    try:
        block_id = block_data.get("block_id")
        children = block_data.get("children")
        
        if not block_id:
            raise HTTPException(status_code=400, detail="block_id is required")
        
        if not children:
            raise HTTPException(status_code=400, detail="children is required")
        
        notion = get_notion_client()
        
        # Append block children
        result = notion.blocks.children.append(
            block_id=block_id,
            children=children
        )
        
        logger.info(f"Appended children to block with ID: {block_id}")
        return result
    
    except Exception as e:
        logger.error(f"Error appending block children: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error appending block children: {str(e)}")

@app.post("/mcp/tools/notion_search")
async def search_notion(search_data: SearchData):
    """Search Notion."""
    try:
        notion = get_notion_client()
        
        # Prepare search parameters
        params = {
            "query": search_data.query,
            "page_size": search_data.page_size
        }
        
        # Add filter if provided
        if search_data.filter:
            params["filter"] = search_data.filter
        
        # Add sort if provided
        if search_data.sort:
            params["sort"] = search_data.sort
        
        # Search Notion
        results = notion.search(**params)
        
        logger.info(f"Searched Notion for: {search_data.query}")
        return results
    
    except Exception as e:
        logger.error(f"Error searching Notion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching Notion: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)

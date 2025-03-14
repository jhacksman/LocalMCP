"""
Google Drive MCP Server Implementation
-----------------------------------
This server provides MCP-compatible tools for Google Drive integration.
"""

import os
import json
import io
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("google_drive_mcp_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("google_drive_mcp")

# Define API models
class FileData(BaseModel):
    name: str = Field(..., description="File name")
    parent_folder_id: Optional[str] = Field("root", description="Parent folder ID")
    mime_type: Optional[str] = Field(None, description="MIME type of the file")

class FolderData(BaseModel):
    name: str = Field(..., description="Folder name")
    parent_folder_id: Optional[str] = Field("root", description="Parent folder ID")

class SearchQuery(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: int = Field(10, description="Maximum number of results to return")

class ShareData(BaseModel):
    file_id: str = Field(..., description="File or folder ID")
    email: str = Field(..., description="Email address to share with")
    role: str = Field("reader", description="Role to grant (reader, writer, commenter, owner)")

# Create FastAPI app
app = FastAPI(title="Google Drive MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

# Path to token file
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'

def get_drive_service():
    """Authenticate and build the Google Drive service."""
    creds = None
    
    # Load token from file if it exists
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as token:
            creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)
    
    # If credentials don't exist or are invalid, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise HTTPException(
                    status_code=500, 
                    detail="credentials.json file not found. Please download OAuth credentials from Google Cloud Console."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return build('drive', 'v3', credentials=creds)

# MCP Tool Registration
@app.get("/mcp/tools")
async def get_tools():
    """Return the list of tools provided by this MCP server."""
    return {
        "tools": [
            {
                "name": "gdrive_list_files",
                "description": "List files in Google Drive",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "folder_id": {"type": "string", "description": "Folder ID to list files from"},
                        "max_results": {"type": "integer", "description": "Maximum number of results to return"}
                    }
                }
            },
            {
                "name": "gdrive_upload_file",
                "description": "Upload a file to Google Drive",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the file to upload"},
                        "name": {"type": "string", "description": "File name"},
                        "parent_folder_id": {"type": "string", "description": "Parent folder ID"},
                        "mime_type": {"type": "string", "description": "MIME type of the file"}
                    },
                    "required": ["file_path", "name"]
                }
            },
            {
                "name": "gdrive_download_file",
                "description": "Download a file from Google Drive",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string", "description": "File ID to download"}
                    },
                    "required": ["file_id"]
                }
            },
            {
                "name": "gdrive_create_folder",
                "description": "Create a new folder in Google Drive",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Folder name"},
                        "parent_folder_id": {"type": "string", "description": "Parent folder ID"}
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "gdrive_search",
                "description": "Search for files in Google Drive",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "description": "Maximum number of results to return"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "gdrive_share_file",
                "description": "Share a file or folder with another user",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string", "description": "File or folder ID"},
                        "email": {"type": "string", "description": "Email address to share with"},
                        "role": {"type": "string", "description": "Role to grant (reader, writer, commenter, owner)"}
                    },
                    "required": ["file_id", "email"]
                }
            },
            {
                "name": "gdrive_delete_file",
                "description": "Delete a file or folder from Google Drive",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string", "description": "File or folder ID"}
                    },
                    "required": ["file_id"]
                }
            }
        ]
    }

# Tool implementations
@app.post("/mcp/tools/gdrive_list_files")
async def list_files(file_data: Dict[str, Any] = {}):
    """List files in Google Drive."""
    try:
        service = get_drive_service()
        
        folder_id = file_data.get("folder_id", "root")
        max_results = file_data.get("max_results", 10)
        
        # Prepare query
        query = f"'{folder_id}' in parents and trashed = false"
        
        # List files
        results = service.files().list(
            q=query,
            pageSize=max_results,
            fields="files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)"
        ).execute()
        
        files = results.get('files', [])
        
        logger.info(f"Listed {len(files)} files from folder {folder_id}")
        return {"files": files}
    
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@app.post("/mcp/tools/gdrive_upload_file")
async def upload_file(file_data: Dict[str, str]):
    """Upload a file to Google Drive."""
    try:
        service = get_drive_service()
        
        file_path = file_data.get("file_path")
        name = file_data.get("name")
        parent_folder_id = file_data.get("parent_folder_id", "root")
        mime_type = file_data.get("mime_type")
        
        if not file_path:
            raise HTTPException(status_code=400, detail="file_path is required")
        
        if not name:
            raise HTTPException(status_code=400, detail="name is required")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=400, detail=f"File not found: {file_path}")
        
        # Prepare file metadata
        file_metadata = {
            'name': name,
            'parents': [parent_folder_id]
        }
        
        # Upload the file
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, mimeType, size, webViewLink'
        ).execute()
        
        logger.info(f"Uploaded file {name} with ID: {file.get('id')}")
        return {
            "status": "success",
            "file_id": file.get('id'),
            "name": file.get('name'),
            "mime_type": file.get('mimeType'),
            "size": file.get('size'),
            "web_view_link": file.get('webViewLink')
        }
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.post("/mcp/tools/gdrive_download_file")
async def download_file(file_data: Dict[str, str]):
    """Download a file from Google Drive."""
    try:
        service = get_drive_service()
        
        file_id = file_data.get("file_id")
        
        if not file_id:
            raise HTTPException(status_code=400, detail="file_id is required")
        
        # Get file metadata
        file_metadata = service.files().get(fileId=file_id, fields="name, mimeType").execute()
        
        # Create a BytesIO object to store the downloaded file
        file_content = io.BytesIO()
        
        # Download the file
        request = service.files().get_media(fileId=file_id)
        downloader = MediaIoBaseDownload(file_content, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        # Reset the file pointer to the beginning
        file_content.seek(0)
        
        logger.info(f"Downloaded file {file_metadata.get('name')} with ID: {file_id}")
        
        # Return the file as a streaming response
        return StreamingResponse(
            file_content,
            media_type=file_metadata.get('mimeType', 'application/octet-stream'),
            headers={"Content-Disposition": f"attachment; filename={file_metadata.get('name')}"}
        )
    
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@app.post("/mcp/tools/gdrive_create_folder")
async def create_folder(folder_data: FolderData):
    """Create a new folder in Google Drive."""
    try:
        service = get_drive_service()
        
        # Prepare folder metadata
        folder_metadata = {
            'name': folder_data.name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [folder_data.parent_folder_id]
        }
        
        # Create the folder
        folder = service.files().create(
            body=folder_metadata,
            fields='id, name, mimeType, webViewLink'
        ).execute()
        
        logger.info(f"Created folder {folder_data.name} with ID: {folder.get('id')}")
        return {
            "status": "success",
            "folder_id": folder.get('id'),
            "name": folder.get('name'),
            "mime_type": folder.get('mimeType'),
            "web_view_link": folder.get('webViewLink')
        }
    
    except Exception as e:
        logger.error(f"Error creating folder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating folder: {str(e)}")

@app.post("/mcp/tools/gdrive_search")
async def search_files(search_data: SearchQuery):
    """Search for files in Google Drive."""
    try:
        service = get_drive_service()
        
        # Execute search
        results = service.files().list(
            q=search_data.query,
            pageSize=search_data.max_results,
            fields="files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)"
        ).execute()
        
        files = results.get('files', [])
        
        logger.info(f"Found {len(files)} files matching query: {search_data.query}")
        return {"files": files}
    
    except Exception as e:
        logger.error(f"Error searching files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching files: {str(e)}")

@app.post("/mcp/tools/gdrive_share_file")
async def share_file(share_data: ShareData):
    """Share a file or folder with another user."""
    try:
        service = get_drive_service()
        
        # Create permission
        permission = {
            'type': 'user',
            'role': share_data.role,
            'emailAddress': share_data.email
        }
        
        # Share the file
        result = service.permissions().create(
            fileId=share_data.file_id,
            body=permission,
            fields='id'
        ).execute()
        
        logger.info(f"Shared file/folder {share_data.file_id} with {share_data.email}")
        return {
            "status": "success",
            "permission_id": result.get('id'),
            "file_id": share_data.file_id,
            "shared_with": share_data.email,
            "role": share_data.role
        }
    
    except Exception as e:
        logger.error(f"Error sharing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sharing file: {str(e)}")

@app.post("/mcp/tools/gdrive_delete_file")
async def delete_file(file_data: Dict[str, str]):
    """Delete a file or folder from Google Drive."""
    try:
        service = get_drive_service()
        
        file_id = file_data.get("file_id")
        
        if not file_id:
            raise HTTPException(status_code=400, detail="file_id is required")
        
        # Delete the file
        service.files().delete(fileId=file_id).execute()
        
        logger.info(f"Deleted file/folder with ID: {file_id}")
        return {
            "status": "success",
            "file_id": file_id
        }
    
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)

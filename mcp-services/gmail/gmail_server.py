"""
Gmail MCP Server Implementation
-------------------------------
This server provides MCP-compatible tools for Gmail integration.
"""

import os
import json
import base64
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gmail_mcp_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gmail_mcp")

# Define API models
class EmailMessage(BaseModel):
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    cc: Optional[List[str]] = Field(None, description="CC recipients")
    bcc: Optional[List[str]] = Field(None, description="BCC recipients")

class SearchQuery(BaseModel):
    query: str = Field(..., description="Gmail search query")
    max_results: int = Field(10, description="Maximum number of results to return")

class EmailResponse(BaseModel):
    id: str
    thread_id: str
    subject: str
    sender: str
    date: str
    snippet: str
    has_attachments: bool

# Create FastAPI app
app = FastAPI(title="Gmail MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Path to token file
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'

def get_gmail_service():
    """Authenticate and build the Gmail service."""
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
    
    return build('gmail', 'v1', credentials=creds)

# MCP Tool Registration
@app.get("/mcp/tools")
async def get_tools():
    """Return the list of tools provided by this MCP server."""
    return {
        "tools": [
            {
                "name": "gmail_send_email",
                "description": "Send an email using Gmail",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email address"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email body content"},
                        "cc": {"type": "array", "items": {"type": "string"}, "description": "CC recipients"},
                        "bcc": {"type": "array", "items": {"type": "string"}, "description": "BCC recipients"}
                    },
                    "required": ["to", "subject", "body"]
                }
            },
            {
                "name": "gmail_search",
                "description": "Search for emails in Gmail using Gmail's search syntax",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Gmail search query"},
                        "max_results": {"type": "integer", "description": "Maximum number of results to return"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "gmail_read_email",
                "description": "Read the content of a specific email by ID",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "email_id": {"type": "string", "description": "Gmail message ID"}
                    },
                    "required": ["email_id"]
                }
            }
        ]
    }

# Tool implementations
@app.post("/mcp/tools/gmail_send_email")
async def send_email(email: EmailMessage):
    """Send an email using Gmail."""
    try:
        service = get_gmail_service()
        
        # Create message
        message = {
            'raw': base64.urlsafe_b64encode(
                f"To: {email.to}\n"
                f"Subject: {email.subject}\n"
                f"{'CC: ' + ','.join(email.cc) + '\n' if email.cc else ''}"
                f"{'BCC: ' + ','.join(email.bcc) + '\n' if email.bcc else ''}"
                f"\n{email.body}"
                .encode("utf-8")
            ).decode("utf-8")
        }
        
        # Send message
        sent_message = service.users().messages().send(userId="me", body=message).execute()
        
        logger.info(f"Email sent successfully. Message ID: {sent_message['id']}")
        return {"status": "success", "message_id": sent_message['id']}
    
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")

@app.post("/mcp/tools/gmail_search")
async def search_emails(search: SearchQuery):
    """Search for emails in Gmail using Gmail's search syntax."""
    try:
        service = get_gmail_service()
        
        # Execute search
        results = service.users().messages().list(
            userId="me", 
            q=search.query, 
            maxResults=search.max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return {"emails": []}
        
        # Get details for each message
        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(userId="me", id=msg['id']).execute()
            
            # Extract headers
            headers = msg_data['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown')
            
            # Check for attachments
            has_attachments = False
            if 'parts' in msg_data['payload']:
                for part in msg_data['payload']['parts']:
                    if part.get('filename') and part.get('filename') != '':
                        has_attachments = True
                        break
            
            emails.append(EmailResponse(
                id=msg['id'],
                thread_id=msg['threadId'],
                subject=subject,
                sender=sender,
                date=date,
                snippet=msg_data['snippet'],
                has_attachments=has_attachments
            ))
        
        logger.info(f"Found {len(emails)} emails matching query: {search.query}")
        return {"emails": [email.dict() for email in emails]}
    
    except Exception as e:
        logger.error(f"Error searching emails: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching emails: {str(e)}")

@app.post("/mcp/tools/gmail_read_email")
async def read_email(email_data: Dict[str, str]):
    """Read the content of a specific email by ID."""
    try:
        email_id = email_data.get("email_id")
        if not email_id:
            raise HTTPException(status_code=400, detail="email_id is required")
            
        service = get_gmail_service()
        
        # Get the email
        message = service.users().messages().get(userId="me", id=email_id, format="full").execute()
        
        # Extract headers
        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
        to = next((h['value'] for h in headers if h['name'].lower() == 'to'), 'Unknown')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown')
        
        # Extract body
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        
        # Extract attachments info
        attachments = []
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part.get('filename') and part.get('filename') != '':
                    attachments.append({
                        'filename': part['filename'],
                        'mimeType': part['mimeType'],
                        'size': part['body'].get('size', 0),
                        'attachment_id': part['body'].get('attachmentId', '')
                    })
        
        logger.info(f"Email {email_id} read successfully")
        return {
            "id": email_id,
            "thread_id": message['threadId'],
            "subject": subject,
            "sender": sender,
            "to": to,
            "date": date,
            "body": body,
            "attachments": attachments
        }
    
    except Exception as e:
        logger.error(f"Error reading email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading email: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

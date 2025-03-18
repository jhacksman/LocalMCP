"""
LocalMCP Web Interface
--------------------
This module provides a web-based interface for monitoring and interacting with MCP servers.
"""

import os
import json
import requests
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("web_interface.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("web_interface")

# Create FastAPI app
app = FastAPI(title="LocalMCP Web Interface")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "services": [
        {
            "name": "Gmail",
            "url": "http://localhost:8000",
            "enabled": True
        },
        {
            "name": "Discord",
            "url": "http://localhost:8001",
            "enabled": True
        },
        {
            "name": "SQL",
            "url": "http://localhost:8002",
            "enabled": True
        },
        {
            "name": "ManusMCP",
            "url": "http://localhost:8003",
            "enabled": True
        },
        {
            "name": "Slack",
            "url": "http://localhost:8004",
            "enabled": True
        },
        {
            "name": "Twitter",
            "url": "http://localhost:8003",
            "enabled": True
        },
        {
            "name": "Bluesky",
            "url": "http://localhost:8004",
            "enabled": True
        },
        {
            "name": "Telegram",
            "url": "http://localhost:8005",
            "enabled": True
        },
        {
            "name": "Signal",
            "url": "http://localhost:8006",
            "enabled": True
        },
        {
            "name": "Reddit",
            "url": "http://localhost:8007",
            "enabled": True
        },
        {
            "name": "Notion",
            "url": "http://localhost:8008",
            "enabled": True
        },
        {
            "name": "Google Drive",
            "url": "http://localhost:8009",
            "enabled": True
        }
    ],
    "models": [
        {
            "name": "Gemma3-27B",
            "url": "http://localhost:7000",
            "enabled": True
        },
        {
            "name": "QWQ-32B",
            "url": "http://localhost:7001",
            "enabled": True
        }
    ]
}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

def load_config():
    """Load configuration from file or create default if not exists."""
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    """Save configuration to file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

async def check_service_health(service):
    """Check if a service is healthy."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{service['url']}/health", timeout=2) as response:
                if response.status == 200:
                    return True
                return False
    except:
        return False

async def get_service_tools(service):
    """Get the tools provided by a service."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{service['url']}/mcp/tools", timeout=2) as response:
                if response.status == 200:
                    return await response.json()
                return None
    except:
        return None

async def check_model_health(model):
    """Check if a model is healthy."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{model['url']}/health", timeout=2) as response:
                if response.status == 200:
                    return True
                return False
    except:
        return False

async def get_model_info(model):
    """Get information about a model."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{model['url']}/model_info", timeout=2) as response:
                if response.status == 200:
                    return await response.json()
                return None
    except:
        return None

@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    # Create templates directory if it doesn't exist
    os.makedirs("templates", exist_ok=True)
    
    # Create static directory if it doesn't exist
    os.makedirs("static", exist_ok=True)
    
    # Create index.html template if it doesn't exist
    if not os.path.exists("templates/index.html"):
        with open("templates/index.html", "w") as f:
            f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LocalMCP Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', path='/styles.css') }}">
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-2 d-none d-md-block bg-light sidebar">
                <div class="sidebar-sticky">
                    <h6 class="sidebar-heading d-flex justify-content-between align-items-center px-3 mt-4 mb-1 text-muted">
                        <span>MCP Services</span>
                    </h6>
                    <ul class="nav flex-column">
                        {% for service in services %}
                        <li class="nav-item">
                            <a class="nav-link {% if service.healthy %}text-success{% else %}text-danger{% endif %}" href="#service-{{ loop.index }}">
                                {{ service.name }} {% if service.healthy %}<span class="badge bg-success">Online</span>{% else %}<span class="badge bg-danger">Offline</span>{% endif %}
                            </a>
                        </li>
                        {% endfor %}
                    </ul>
                    
                    <h6 class="sidebar-heading d-flex justify-content-between align-items-center px-3 mt-4 mb-1 text-muted">
                        <span>Models</span>
                    </h6>
                    <ul class="nav flex-column">
                        {% for model in models %}
                        <li class="nav-item">
                            <a class="nav-link {% if model.healthy %}text-success{% else %}text-danger{% endif %}" href="#model-{{ loop.index }}">
                                {{ model.name }} {% if model.healthy %}<span class="badge bg-success">Online</span>{% else %}<span class="badge bg-danger">Offline</span>{% endif %}
                            </a>
                        </li>
                        {% endfor %}
                    </ul>
                </div>
            </nav>

            <main role="main" class="col-md-10 ml-sm-auto px-4">
                <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                    <h1 class="h2">LocalMCP Dashboard</h1>
                    <div class="btn-toolbar mb-2 mb-md-0">
                        <button id="refreshBtn" class="btn btn-sm btn-outline-secondary">
                            <span data-feather="refresh-cw"></span>
                            Refresh
                        </button>
                    </div>
                </div>

                <h2>System Overview</h2>
                <div class="row">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Services</h5>
                                <p class="card-text">{{ services|selectattr('healthy', 'eq', true)|list|length }} / {{ services|length }} online</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Models</h5>
                                <p class="card-text">{{ models|selectattr('healthy', 'eq', true)|list|length }} / {{ models|length }} online</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Tools</h5>
                                <p class="card-text">{{ total_tools }} available</p>
                            </div>
                        </div>
                    </div>
                </div>

                <h2 class="mt-4">MCP Services</h2>
                {% for service in services %}
                <div id="service-{{ loop.index }}" class="card mb-3">
                    <div class="card-header {% if service.healthy %}bg-success text-white{% else %}bg-danger text-white{% endif %}">
                        {{ service.name }}
                    </div>
                    <div class="card-body">
                        <h5 class="card-title">Status: {% if service.healthy %}Online{% else %}Offline{% endif %}</h5>
                        <p class="card-text">URL: {{ service.url }}</p>
                        
                        {% if service.tools %}
                        <h6>Available Tools:</h6>
                        <ul class="list-group">
                            {% for tool in service.tools %}
                            <li class="list-group-item">
                                <strong>{{ tool.name }}</strong>: {{ tool.description }}
                            </li>
                            {% endfor %}
                        </ul>
                        {% else %}
                        <p>No tools available or service is offline.</p>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}

                <h2 class="mt-4">Models</h2>
                {% for model in models %}
                <div id="model-{{ loop.index }}" class="card mb-3">
                    <div class="card-header {% if model.healthy %}bg-success text-white{% else %}bg-danger text-white{% endif %}">
                        {{ model.name }}
                    </div>
                    <div class="card-body">
                        <h5 class="card-title">Status: {% if model.healthy %}Online{% else %}Offline{% endif %}</h5>
                        <p class="card-text">URL: {{ model.url }}</p>
                        
                        {% if model.info %}
                        <h6>Model Information:</h6>
                        <ul class="list-group">
                            <li class="list-group-item">Model ID: {{ model.info.model_id }}</li>
                            <li class="list-group-item">Device: {{ model.info.device }}</li>
                            <li class="list-group-item">Data Type: {{ model.info.dtype }}</li>
                            <li class="list-group-item">Quantization: {{ model.info.quantization }}</li>
                            <li class="list-group-item">Flash Attention: {{ model.info.flash_attention }}</li>
                            <li class="list-group-item">Model Loaded: {{ model.info.model_loaded }}</li>
                        </ul>
                        
                        {% if model.info.gpu_info %}
                        <h6 class="mt-3">GPU Information:</h6>
                        <ul class="list-group">
                            <li class="list-group-item">GPU: {{ model.info.gpu_info.gpu_name }}</li>
                            <li class="list-group-item">Total Memory: {{ "%.2f"|format(model.info.gpu_info.gpu_memory_total) }} GB</li>
                            <li class="list-group-item">Allocated Memory: {{ "%.2f"|format(model.info.gpu_info.gpu_memory_allocated) }} GB</li>
                            <li class="list-group-item">Reserved Memory: {{ "%.2f"|format(model.info.gpu_info.gpu_memory_reserved) }} GB</li>
                        </ul>
                        {% endif %}
                        
                        {% else %}
                        <p>No model information available or model is offline.</p>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}

                <h2 class="mt-4">System Logs</h2>
                <div class="card">
                    <div class="card-body">
                        <div id="logs" class="logs">
                            <p>Connecting to log stream...</p>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // WebSocket for real-time logs
        const logsElement = document.getElementById('logs');
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onmessage = function(event) {
            const log = document.createElement('p');
            log.textContent = event.data;
            logsElement.appendChild(log);
            logsElement.scrollTop = logsElement.scrollHeight;
            
            // Limit the number of log entries to prevent browser slowdown
            while (logsElement.children.length > 100) {
                logsElement.removeChild(logsElement.firstChild);
            }
        };
        
        ws.onopen = function() {
            logsElement.innerHTML = '<p>Connected to log stream.</p>';
        };
        
        ws.onclose = function() {
            logsElement.innerHTML += '<p>Disconnected from log stream.</p>';
        };
        
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', function() {
            window.location.reload();
        });
    </script>
</body>
</html>
            """)
    
    # Create styles.css if it doesn't exist
    if not os.path.exists("static/styles.css"):
        with open("static/styles.css", "w") as f:
            f.write("""
body {
    font-size: .875rem;
}

.sidebar {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    z-index: 100;
    padding: 48px 0 0;
    box-shadow: inset -1px 0 0 rgba(0, 0, 0, .1);
}

.sidebar-sticky {
    position: relative;
    top: 0;
    height: calc(100vh - 48px);
    padding-top: .5rem;
    overflow-x: hidden;
    overflow-y: auto;
}

.sidebar .nav-link {
    font-weight: 500;
    color: #333;
}

.sidebar .nav-link.active {
    color: #007bff;
}

.logs {
    height: 300px;
    overflow-y: auto;
    background-color: #f8f9fa;
    padding: 10px;
    border-radius: 5px;
    font-family: monospace;
}

.logs p {
    margin: 0;
    padding: 2px 0;
}
            """)
    
    logger.info("Web interface started")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the dashboard."""
    config = load_config()
    
    # Check service health and get tools
    services = []
    total_tools = 0
    
    for service in config["services"]:
        if not service["enabled"]:
            continue
        
        healthy = await check_service_health(service)
        tools_data = await get_service_tools(service) if healthy else None
        tools = tools_data.get("tools", []) if tools_data else []
        
        total_tools += len(tools)
        
        services.append({
            "name": service["name"],
            "url": service["url"],
            "healthy": healthy,
            "tools": tools
        })
    
    # Check model health and get info
    models = []
    
    for model in config["models"]:
        if not model["enabled"]:
            continue
        
        healthy = await check_model_health(model)
        info = await get_model_info(model) if healthy else None
        
        models.append({
            "name": model["name"],
            "url": model["url"],
            "healthy": healthy,
            "info": info
        })
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "services": services,
        "models": models,
        "total_tools": total_tools
    })

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time logs."""
    await manager.connect(websocket)
    try:
        # Send initial message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await websocket.send_text(f"[{timestamp}] Connected to log stream")
        
        # Keep the connection alive and periodically send system status
        while True:
            # Check service health
            config = load_config()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Log service status
            for service in config["services"]:
                if not service["enabled"]:
                    continue
                
                healthy = await check_service_health(service)
                status = "online" if healthy else "offline"
                await websocket.send_text(f"[{timestamp}] Service {service['name']} is {status}")
            
            # Log model status
            for model in config["models"]:
                if not model["enabled"]:
                    continue
                
                healthy = await check_model_health(model)
                status = "online" if healthy else "offline"
                await websocket.send_text(f"[{timestamp}] Model {model['name']} is {status}")
            
            # Wait before next update
            await asyncio.sleep(30)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/services")
async def get_services():
    """Get all services."""
    config = load_config()
    return {"services": config["services"]}

@app.get("/api/models")
async def get_models():
    """Get all models."""
    config = load_config()
    return {"models": config["models"]}

@app.get("/api/status")
async def get_status():
    """Get system status."""
    config = load_config()
    
    # Check service health
    services = []
    for service in config["services"]:
        if not service["enabled"]:
            continue
        
        healthy = await check_service_health(service)
        services.append({
            "name": service["name"],
            "url": service["url"],
            "healthy": healthy
        })
    
    # Check model health
    models = []
    for model in config["models"]:
        if not model["enabled"]:
            continue
        
        healthy = await check_model_health(model)
        models.append({
            "name": model["name"],
            "url": model["url"],
            "healthy": healthy
        })
    
    return {
        "services": services,
        "models": models,
        "timestamp": time.time()
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=9000)

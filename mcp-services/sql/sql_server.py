"""
SQL MCP Server Implementation
----------------------------
This server provides MCP-compatible tools for SQL database interaction.
"""

import os
import sqlite3
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sql_mcp_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("sql_mcp")

# Define API models
class SQLQuery(BaseModel):
    query: str = Field(..., description="SQL query to execute")

# Create FastAPI app
app = FastAPI(title="SQL MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = os.environ.get("DB_PATH", "./database.db")

# MCP Tool Registration
@app.get("/mcp/tools")
async def get_tools():
    """Return the list of tools provided by this MCP server."""
    return {
        "tools": [
            {
                "name": "sql_query",
                "description": "Execute SQL queries against a SQLite database",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL query to execute"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "sql_get_schema",
                "description": "Get the database schema",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    }

# Tool implementations
@app.post("/mcp/tools/sql_query")
async def execute_query(query_data: SQLQuery):
    """Execute an SQL query against the database."""
    try:
        logger.info(f"Executing SQL query: {query_data.query}")
        conn = sqlite3.connect(DB_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute(query_data.query)
            
            # Check if this is a SELECT query
            if query_data.query.strip().upper().startswith("SELECT"):
                # Fetch column names
                column_names = [description[0] for description in cursor.description]
                
                # Fetch results
                results = cursor.fetchall()
                
                # Format results as a table
                formatted_results = []
                formatted_results.append(" | ".join(column_names))
                formatted_results.append("-" * (sum(len(name) for name in column_names) + 3 * (len(column_names) - 1)))
                
                for row in results:
                    formatted_results.append(" | ".join(str(value) for value in row))
                
                conn.commit()
                return {"result": "\n".join(formatted_results)}
            else:
                # For non-SELECT queries, return the number of affected rows
                affected_rows = cursor.rowcount
                conn.commit()
                return {"result": f"Query executed successfully. Rows affected: {affected_rows}"}
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return {"result": f"Error: {str(e)}"}
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@app.post("/mcp/tools/sql_get_schema")
async def get_schema():
    """Get the database schema."""
    try:
        logger.info("Getting database schema")
        conn = sqlite3.connect(DB_PATH)
        try:
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            schema = []
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                
                schema.append(f"Table: {table_name}")
                schema.append("Columns:")
                for column in columns:
                    schema.append(f"  - {column[1]} ({column[2]})")
                schema.append("")
            
            return {"result": "\n".join(schema)}
        except Exception as e:
            logger.error(f"Error getting schema: {str(e)}")
            return {"result": f"Error: {str(e)}"}
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    # Initialize the database if it doesn't exist
    if not os.path.exists(DB_PATH):
        logger.info("Database not found. Initializing with sample data.")
        try:
            # Run the initialization script
            import sys
            sys.path.append("./data")
            import init_db
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
    
    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8002)

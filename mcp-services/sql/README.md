# SQL MCP Service

This service provides MCP-compatible tools for interacting with a SQLite database using natural language through AI models.

## Features

- Execute SQL queries against a SQLite database
- Get database schema information
- Interactive chat interface with Claude AI for natural language to SQL conversion

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Initialize the database with sample data:

```bash
python data/init_db.py
```

3. Set up environment variables:

Create a `.env` file with the following content:

```
ANTHROPIC_API_KEY=your_anthropic_api_key
SQL_MCP_SERVER_URL=http://localhost:8002
DB_PATH=./database.db
```

## Usage

### Starting the Server

```bash
python sql_server.py
```

This will start the SQL MCP server on port 8002.

### Using the Client

```bash
python sql_client.py
```

This will start an interactive chat session where you can ask questions about the database in natural language.

Example queries:

- "How many employees are in the Engineering department?"
- "What is the average salary by department?"
- "Who are the top 3 highest paid employees?"
- "When was the most recent hire in the Marketing department?"

## API Endpoints

### MCP Tools

- `GET /mcp/tools` - List available tools
- `POST /mcp/tools/sql_query` - Execute an SQL query
- `POST /mcp/tools/sql_get_schema` - Get the database schema

### Health Check

- `GET /health` - Check if the server is running

## Database Schema

The sample database contains two tables:

### Employees

| Column    | Type    | Description                    |
|-----------|---------|--------------------------------|
| id        | INTEGER | Primary key                    |
| name      | TEXT    | Employee name                  |
| department| TEXT    | Department name                |
| salary    | REAL    | Employee salary                |
| hire_date | TEXT    | Date when employee was hired   |

### Departments

| Column    | Type    | Description                    |
|-----------|---------|--------------------------------|
| id        | INTEGER | Primary key                    |
| name      | TEXT    | Department name                |
| budget    | REAL    | Department budget              |
| location  | TEXT    | Department location            |

## Integration with MCP Clients

This service follows the Model Context Protocol (MCP) specification, making it compatible with any MCP client. The tools provided by this service can be discovered and used by MCP clients to execute SQL queries and retrieve database schema information.

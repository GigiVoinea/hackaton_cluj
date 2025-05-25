# Finn - Financial Assistant

A comprehensive financial assistant application built with LangGraph, FastAPI, and React.

## Features

- **Agentic Workflow**: Powered by LangGraph for intelligent financial advice
- **MCP Integration**: Model Context Protocol for extensible tool integration
- **Modern UI**: React frontend with beautiful, responsive design
- **RESTful API**: FastAPI backend with automatic documentation
- **Unified Startup**: Single script to run the entire application stack

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+ and npm
- OpenAI API key

### Setup

1. **Clone and setup the environment:**
   ```bash
   git clone <repository-url>
   cd hackathon
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Start the complete application stack:**
   ```bash
   python run_all.py
   ```

This single command will:
- Install frontend dependencies (if needed)
- Start the main MCP server
- Start the email MCP server
- Start the FastAPI backend
- Start the React frontend (Vite dev server)
- Handle graceful shutdown with Ctrl+C

### Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Architecture

### Backend Components

- **`main.py`**: FastAPI application with CORS support
- **`orchestrator.py`**: LangGraph workflow orchestrator
- **`mcp_server.py`**: Model Context Protocol server
- **`email_mcp_server.py`**: Email inbox simulation MCP server
- **`mcp_client.py`**: MCP client wrapper for multiple servers
- **`email_models.py`**: Email data models and storage
- **`state.py`**: Pydantic state models

### Frontend Components

- **`App.jsx`**: Main application component with routing
- **`WorkflowForm.jsx`**: Input form for user queries
- **`WorkflowResult.jsx`**: Display component for AI responses
- **`api.js`**: API client service

### Startup Scripts

- **`run_all.py`**: Unified startup script (recommended)
- **`run_both.py`**: Legacy script for backend only

## Development

### Individual Services

If you need to run services individually:

```bash
# MCP Server
python mcp_server.py

# Backend API
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm run dev
```

### API Usage

The backend exposes a simple workflow endpoint:

```bash
curl -X POST "http://localhost:8000/run-workflow" \
     -H "Content-Type: application/json" \
     -d '{"user_message": "Help me analyze my finances"}'
```

## Features

### Financial Assistant Capabilities

- **Financial Impact Scan**: Analyze your financial situation
- **Subscription Optimization**: Review and optimize recurring expenses
- **General Financial Advice**: Ask any financial question

### Email Management Capabilities

- **Email Inbox Simulation**: Complete email management system
- **Folder Organization**: Manage emails across inbox, sent, drafts, trash, spam, and archive folders
- **Email Operations**: List, read, search, send, move, and delete emails
- **Smart Email Assistance**: AI-powered email organization and response suggestions
- **Sample Data Generation**: Realistic email simulation for testing and demonstration

### Technical Features

- **Real-time Communication**: WebSocket-like experience through polling
- **Error Handling**: Comprehensive error handling and user feedback
- **Responsive Design**: Works on desktop and mobile devices
- **Process Management**: Graceful startup and shutdown of all services

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `python run_all.py`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

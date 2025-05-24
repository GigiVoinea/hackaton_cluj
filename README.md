# hackaton_cluj
Hackaton Cluj. Gigi, Adi si Mihai

## Overview

This project integrates with the Open Bank Project (OBP) API to provide real banking operations through an MCP (Model Context Protocol) server. The system provides tools for account management, balance checking, transaction history, and card operations.

## Features

- **Real Banking API Integration**: Connected to OBP sandbox environment
- **MCP Server**: Exposes banking operations as tools for AI agents
- **Comprehensive Error Handling**: Robust error handling with fallback responses
- **Authentication Management**: Automatic DirectLogin authentication with OBP
- **Multiple Banking Operations**: Support for accounts, balances, transactions, and cards

## Available Banking Tools

The MCP server exposes the following banking tools:

1. **get_banks()** - Get list of available banks
2. **accounts_at_bank(bank_id)** - Get accounts at a specific bank
3. **get_accounts_held_by_user(user_id, account_type_filter, account_type_filter_operation)** - Get accounts held by a specific user (useful for onboarding)
4. **check_available_funds(bank_id, account_id)** - Check account balance and funds availability
5. **get_account_transactions(bank_id, account_id, limit)** - Get recent transactions
6. **get_account_cards(bank_id, account_id)** - Get cards associated with an account
7. **create_card(bank_id, account_id, card_type, name_on_card)** - Create a new card

## Configuration

### Environment Variables

For production use, set these environment variables:

```bash
export OBP_USERNAME="your_username@example.com"
export OBP_PASSWORD="your_password"
export OBP_CONSUMER_KEY="your_consumer_key"
```

### Default Credentials

The system uses sandbox credentials by default:
- Username: `katja.fi.29@example.com`
- Password: `ca0317`
- Consumer Key: `h1lquhpcl3jx43xbfaqqygi2hjp1bdb3qivlanku`

## MCP Server and Client Usage

### 1. Start the MCP Server

You can start the MCP server directly:

```bash
python mcp_server.py
```

Or, to run both the MCP server and FastAPI app together (with colored logs):

```bash
python run_both.py
```

### 2. Run the MCP Client

In a separate terminal, run:

```bash
python mcp_client.py
```

### Expected Output

The client will connect to the server and print the available tools, e.g.:

```
Available tools: ['check_available_funds', 'accounts_at_bank', 'create_card', 'get_banks', 'get_account_transactions', 'get_account_cards', 'get_accounts_held_by_user']
```

If you see the list of tools, the client-server connection is working!

## API Response Format

All MCP tools return structured responses with the following format:

```json
{
  "success": true,
  "data": {...},
  "count": 10,
  "error": null,
  "status_code": null
}
```

In case of errors:

```json
{
  "success": false,
  "data": [],
  "error": "Error description",
  "status_code": 404
}
```

## Dependencies

- `httpx>=0.27.0` - For HTTP requests to OBP API
- `langgraph>=0.0.30` - For graph-based workflows
- `langchain>=0.1.16` - For LLM integration
- `fastapi>=0.110.0` - For web API
- `pydantic>=2.0.0` - For data validation
- `uvicorn[standard]>=0.29.0` - For ASGI server
- `langchain-mcp-adapters>=0.0.6` - For MCP integration

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LangGraph     │    │   MCP Server    │    │   OBP API       │
│   Orchestrator  │◄──►│   (FastMCP)     │◄──►│   (Sandbox)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

The system consists of:
1. **LangGraph Orchestrator**: Manages AI agent workflows
2. **MCP Server**: Exposes banking tools using FastMCP framework
3. **OBP API Client**: Handles authentication and API communication
4. **Error Handling**: Comprehensive error management with fallbacks

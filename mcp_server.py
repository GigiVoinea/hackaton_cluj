# mcp_server.py
"""
MCP server implementation using FastMCP, following best practices and official documentation.
Integrated with Open Bank Project (OBP) API for real banking operations.
"""
import httpx
import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseModel):
    log_level: str = Field(default="info")

class OBPError(Exception):
    """Custom exception for OBP API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)

class OBPAPIClient:
    """
    Open Bank Project API client with DirectLogin authentication.
    """
    
    def __init__(self, base_url: str = "https://apisandbox.openbankproject.com"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def authenticate(self, username: str, password: str, consumer_key: str) -> bool:
        """
        Authenticate with OBP using DirectLogin method.
        
        Args:
            username: User's email/username
            password: User's password
            consumer_key: Consumer key for the application
            
        Returns:
            bool: True if authentication successful, False otherwise
            
        Raises:
            OBPError: If authentication fails with detailed error information
        """
        if not username or not password or not consumer_key:
            raise OBPError("Username, password, and consumer_key are required for authentication")
            
        login_url = f"{self.base_url}/my/logins/direct"
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'DirectLogin username="{username}", password="{password}", consumer_key="{consumer_key}"'
        }
        
        try:
            response = await self.client.post(login_url, headers=headers)
            
            if response.status_code == 201:
                data = response.json()
                self.token = data.get('token')
                if self.token:
                    logger.info("Successfully authenticated with OBP")
                    return True
                else:
                    raise OBPError("No token found in response", response.status_code, data)
            else:
                error_data = None
                try:
                    error_data = response.json()
                except:
                    pass
                raise OBPError(f"Authentication failed: {response.status_code}", response.status_code, error_data)
                
        except httpx.RequestError as e:
            raise OBPError(f"Authentication request failed: {e}")
        except OBPError:
            raise
        except Exception as e:
            raise OBPError(f"Unexpected error during authentication: {e}")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        if not self.token:
            raise OBPError("Not authenticated. Call authenticate() first.")
        
        return {
            'Accept': 'application/json',
            'Authorization': f'DirectLogin token="{self.token}"'
        }
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request to the OBP API."""
        try:
            response = await self.client.request(method, url, headers=self._get_auth_headers(), **kwargs)
            
            if response.status_code >= 400:
                error_data = None
                try:
                    error_data = response.json()
                except:
                    pass
                raise OBPError(f"API request failed: {response.status_code}", response.status_code, error_data)
            
            return response.json()
            
        except httpx.RequestError as e:
            raise OBPError(f"Request failed: {e}")
        except OBPError:
            raise
        except Exception as e:
            raise OBPError(f"Unexpected error during API request: {e}")
    
    async def get_banks(self) -> List[Dict[str, Any]]:
        """Get list of available banks."""
        url = f"{self.base_url}/obp/v5.1.0/banks"
        
        try:
            data = await self._make_request("GET", url)
            # Handle both cases: banks as direct list or wrapped in dict
            if isinstance(data, list):
                banks = data
            else:
                banks = data.get('banks', [])
            logger.info(f"Retrieved {len(banks)} banks")
            return banks
        except OBPError as e:
            logger.error(f"Failed to get banks: {e.message}")
            raise
    
    async def get_accounts_at_bank(self, bank_id: str) -> List[Dict[str, Any]]:
        """Get accounts at a specific bank."""
        if not bank_id:
            raise OBPError("bank_id is required")
            
        url = f"{self.base_url}/obp/v5.1.0/banks/{bank_id}/accounts"
        
        try:
            data = await self._make_request("GET", url)
            # Handle both cases: accounts as direct list or wrapped in dict
            if isinstance(data, list):
                accounts = data
            else:
                accounts = data.get('accounts', [])
            logger.info(f"Retrieved {len(accounts)} accounts for bank {bank_id}")
            return accounts
        except OBPError as e:
            logger.error(f"Failed to get accounts for bank {bank_id}: {e.message}")
            raise
    
    async def get_account_balance(self, bank_id: str, account_id: str) -> Optional[Dict[str, Any]]:
        """Get account balance."""
        if not bank_id or not account_id:
            raise OBPError("bank_id and account_id are required")
            
        url = f"{self.base_url}/obp/v5.1.0/banks/{bank_id}/accounts/{account_id}/balances"
        
        try:
            data = await self._make_request("GET", url)
            # Handle both cases: balances as direct list or wrapped in dict
            if isinstance(data, list):
                balances = data
            else:
                balances = data.get('balances', [])
            balance = balances[0] if balances else None
            logger.info(f"Retrieved balance for account {account_id}")
            return balance
        except OBPError as e:
            logger.error(f"Failed to get balance for account {account_id}: {e.message}")
            raise
    
    async def get_transactions(self, bank_id: str, account_id: str, view_id: str = "owner", 
                              limit: int = 50, offset: int = 0, sort_direction: str = "DESC",
                              from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get Transactions for Account (Full).
        
        Returns transactions list of the account specified by ACCOUNT_ID and moderated by the view (VIEW_ID).
        User Authentication is Optional. The User need not be logged in.
        Authentication is required if the view is not public.
        
        Args:
            bank_id: Bank ID
            account_id: Account ID  
            view_id: View ID (default: "owner")
            limit: Number of transactions to return (default: 50)
            offset: Number of transactions to skip (default: 0)
            sort_direction: Sort direction "ASC" or "DESC" (default: "DESC")
            from_date: Start date in format yyyy-MM-dd'T'HH:mm:ss.SSS'Z' (default: one year ago)
            to_date: End date in format yyyy-MM-dd'T'HH:mm:ss.SSS'Z' (default: now)
            
        Returns:
            List of transactions
        """
        if not bank_id or not account_id:
            raise OBPError("bank_id and account_id are required")
        if limit <= 0:
            raise OBPError("limit must be greater than 0")
        if sort_direction not in ["ASC", "DESC"]:
            raise OBPError("sort_direction must be 'ASC' or 'DESC'")
        if offset < 0:
            raise OBPError("offset must be >= 0")
            
        # Use standard transactions endpoint
        url = f"{self.base_url}/obp/v5.1.0/banks/{bank_id}/accounts/{account_id}/{view_id}/transactions"
        
        # Build query parameters
        params = {
            "limit": limit,
            "offset": offset,
            "sort_direction": sort_direction
        }
        
        # Add date filters if provided
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        
        try:
            data = await self._make_request("GET", url, params=params)
            # Handle both cases: transactions as direct list or wrapped in dict
            if isinstance(data, list):
                transactions = data
            else:
                transactions = data.get('transactions', [])
            logger.info(f"Retrieved {len(transactions)} transactions for account {account_id}")
            return transactions
        except OBPError as e:
            logger.error(f"Failed to get transactions for account {account_id}: {e.message}")
            raise
    
    async def get_cards(self, bank_id: str, account_id: str) -> List[Dict[str, Any]]:
        """Get cards for an account."""
        if not bank_id or not account_id:
            raise OBPError("bank_id and account_id are required")
            
        url = f"{self.base_url}/obp/v5.1.0/banks/{bank_id}/accounts/{account_id}/cards"
        
        try:
            data = await self._make_request("GET", url)
            # Handle both cases: cards as direct list or wrapped in dict
            if isinstance(data, list):
                cards = data
            else:
                cards = data.get('cards', [])
            logger.info(f"Retrieved {len(cards)} cards for account {account_id}")
            return cards
        except OBPError as e:
            logger.error(f"Failed to get cards for account {account_id}: {e.message}")
            raise
    
    async def create_card(self, bank_id: str, account_id: str, card_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new card for an account."""
        if not bank_id or not account_id:
            raise OBPError("bank_id and account_id are required")
        if not card_data:
            raise OBPError("card_data is required")
            
        url = f"{self.base_url}/obp/v5.1.0/banks/{bank_id}/accounts/{account_id}/cards"
        
        try:
            data = await self._make_request("POST", url, json=card_data)
            logger.info(f"Created card for account {account_id}")
            return data
        except OBPError as e:
            logger.error(f"Failed to create card for account {account_id}: {e.message}")
            raise
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_accounts_held_by_user(self, user_id: str, account_type_filter: Optional[str] = None, account_type_filter_operation: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get accounts held by a specific user.
        
        Args:
            user_id: The user ID to get accounts for
            account_type_filter: Optional comma-separated account types to filter (e.g., "330,CURRENT+PLUS")
            account_type_filter_operation: Filter operation, must be "INCLUDE" or "EXCLUDE"
            
        Returns:
            List of accounts held by the user
        """
        if not user_id:
            raise OBPError("user_id is required")
        
        if account_type_filter_operation and account_type_filter_operation not in ["INCLUDE", "EXCLUDE"]:
            raise OBPError("account_type_filter_operation must be 'INCLUDE' or 'EXCLUDE'")
            
        url = f"{self.base_url}/obp/v5.1.0/users/{user_id}/accounts-held"
        
        # Build query parameters
        params = {}
        if account_type_filter:
            params["account_type_filter"] = account_type_filter
        if account_type_filter_operation:
            params["account_type_filter_operation"] = account_type_filter_operation
        
        try:
            data = await self._make_request("GET", url, params=params if params else None)
            # Handle both cases: accounts as direct list or wrapped in dict
            if isinstance(data, list):
                accounts = data
            else:
                accounts = data.get('accounts', [])
            logger.info(f"Retrieved {len(accounts)} accounts held by user {user_id}")
            return accounts
        except OBPError as e:
            logger.error(f"Failed to get accounts held by user {user_id}: {e.message}")
            raise

    async def get_current_user(self) -> Dict[str, Any]:
        """Get current user information."""
        url = f"{self.base_url}/obp/v5.1.0/users/current"
        
        try:
            data = await self._make_request("GET", url)
            logger.info("Retrieved current user information")
            return data
        except OBPError as e:
            logger.error(f"Failed to get current user: {e.message}")
            raise

    async def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """Get user information by user ID."""
        if not user_id:
            raise OBPError("user_id is required")
            
        url = f"{self.base_url}/obp/v5.1.0/users/{user_id}"
        
        try:
            data = await self._make_request("GET", url)
            logger.info(f"Retrieved user information for {user_id}")
            return data
        except OBPError as e:
            logger.error(f"Failed to get user {user_id}: {e.message}")
            raise

    async def get_account_by_id(self, bank_id: str, account_id: str, view_id: str = "owner") -> Dict[str, Any]:
        """Get account details by ID."""
        if not bank_id or not account_id:
            raise OBPError("bank_id and account_id are required")
            
        url = f"{self.base_url}/obp/v5.1.0/banks/{bank_id}/accounts/{account_id}/{view_id}/account"
        
        try:
            data = await self._make_request("GET", url)
            logger.info(f"Retrieved account details for {account_id}")
            return data
        except OBPError as e:
            logger.error(f"Failed to get account {account_id}: {e.message}")
            raise

    async def get_transaction_by_id(self, bank_id: str, account_id: str, transaction_id: str, view_id: str = "owner") -> Dict[str, Any]:
        """Get transaction details by ID."""
        if not bank_id or not account_id or not transaction_id:
            raise OBPError("bank_id, account_id, and transaction_id are required")
            
        url = f"{self.base_url}/obp/v5.1.0/banks/{bank_id}/accounts/{account_id}/{view_id}/transactions/{transaction_id}/transaction"
        
        try:
            data = await self._make_request("GET", url)
            logger.info(f"Retrieved transaction details for {transaction_id}")
            return data
        except OBPError as e:
            logger.error(f"Failed to get transaction {transaction_id}: {e.message}")
            raise

    async def add_transaction_narrative(self, bank_id: str, account_id: str, transaction_id: str, narrative: str, view_id: str = "owner") -> Dict[str, Any]:
        """Add a narrative to a transaction."""
        if not bank_id or not account_id or not transaction_id or not narrative:
            raise OBPError("bank_id, account_id, transaction_id, and narrative are required")
            
        url = f"{self.base_url}/obp/v5.1.0/banks/{bank_id}/accounts/{account_id}/{view_id}/transactions/{transaction_id}/metadata/narrative"
        
        try:
            data = await self._make_request("POST", url, json={"narrative": narrative})
            logger.info(f"Added narrative to transaction {transaction_id}")
            return data
        except OBPError as e:
            logger.error(f"Failed to add narrative to transaction {transaction_id}: {e.message}")
            raise

    async def add_transaction_tag(self, bank_id: str, account_id: str, transaction_id: str, tag: str, view_id: str = "owner") -> Dict[str, Any]:
        """Add a tag to a transaction."""
        if not bank_id or not account_id or not transaction_id or not tag:
            raise OBPError("bank_id, account_id, transaction_id, and tag are required")
            
        url = f"{self.base_url}/obp/v5.1.0/banks/{bank_id}/accounts/{account_id}/{view_id}/transactions/{transaction_id}/metadata/tags"
        
        try:
            data = await self._make_request("POST", url, json={"value": tag})
            logger.info(f"Added tag to transaction {transaction_id}")
            return data
        except OBPError as e:
            logger.error(f"Failed to add tag to transaction {transaction_id}: {e.message}")
            raise

    async def get_counterparties(self, bank_id: str, account_id: str, view_id: str = "owner") -> List[Dict[str, Any]]:
        """Get counterparties for an account."""
        if not bank_id or not account_id:
            raise OBPError("bank_id and account_id are required")
            
        url = f"{self.base_url}/obp/v5.1.0/banks/{bank_id}/accounts/{account_id}/{view_id}/counterparties"
        
        try:
            data = await self._make_request("GET", url)
            # Handle both cases: counterparties as direct list or wrapped in dict
            if isinstance(data, list):
                counterparties = data
            else:
                counterparties = data.get('counterparties', [])
            logger.info(f"Retrieved {len(counterparties)} counterparties for account {account_id}")
            return counterparties
        except OBPError as e:
            logger.error(f"Failed to get counterparties for account {account_id}: {e.message}")
            raise

    async def create_transaction_request(self, bank_id: str, account_id: str, view_id: str, request_type: str, transaction_request_body: Dict[str, Any]) -> Dict[str, Any]:
        """Create a transaction request (payment initiation)."""
        if not bank_id or not account_id or not request_type or not transaction_request_body:
            raise OBPError("bank_id, account_id, request_type, and transaction_request_body are required")
            
        url = f"{self.base_url}/obp/v5.1.0/banks/{bank_id}/accounts/{account_id}/{view_id}/transaction-request-types/{request_type}/transaction-requests"
        
        try:
            data = await self._make_request("POST", url, json=transaction_request_body)
            logger.info(f"Created transaction request for account {account_id}")
            return data
        except OBPError as e:
            logger.error(f"Failed to create transaction request for account {account_id}: {e.message}")
            raise

# Initialize settings and OBP client
settings = Settings()
obp_client = OBPAPIClient()

# Initialize MCP server with settings
mcp = FastMCP("Open Bank Project", settings=settings.model_dump())

# OBP Credentials - Use environment variables in production
OBP_USERNAME = os.getenv('OBP_USERNAME', 'katja.fi.29@example.com')
OBP_PASSWORD = os.getenv('OBP_PASSWORD', 'ca0317')
OBP_CONSUMER_KEY = os.getenv('OBP_CONSUMER_KEY', 'h1lquhpcl3jx43xbfaqqygi2hjp1bdb3qivlanku')

async def ensure_authenticated():
    """Ensure the OBP client is authenticated."""
    if not obp_client.token:
        try:
            success = await obp_client.authenticate(OBP_USERNAME, OBP_PASSWORD, OBP_CONSUMER_KEY)
            if not success:
                raise OBPError("Failed to authenticate with OBP API")
        except OBPError as e:
            logger.error(f"Authentication failed: {e.message}")
            raise

@mcp.tool()
async def check_available_funds(bank_id: str, account_id: str) -> Dict[str, Any]:
    """Check if user has funds for the transaction by getting account balance."""
    try:
        await ensure_authenticated()
        
        balance = await obp_client.get_account_balance(bank_id, account_id)
        if balance:
            amount = float(balance.get('amount', 0))
            return {
                "success": True,
                "has_funds": amount > 0,
                "balance": balance,
                "currency": balance.get('currency', 'Unknown')
            }
        else:
            return {
                "success": False,
                "has_funds": False,
                "balance": None,
                "error": "Could not retrieve balance"
            }
    except OBPError as e:
        return {
            "success": False,
            "has_funds": False,
            "error": e.message,
            "status_code": e.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "has_funds": False,
            "error": f"Unexpected error: {str(e)}"
        }

@mcp.tool()
async def accounts_at_bank(bank_id: str) -> Dict[str, Any]:
    """Get the accounts at the bank."""
    try:
        await ensure_authenticated()
        
        accounts = await obp_client.get_accounts_at_bank(bank_id)
        return {
            "success": True,
            "accounts": accounts,
            "count": len(accounts)
        }
    except OBPError as e:
        return {
            "success": False,
            "accounts": [],
            "error": e.message,
            "status_code": e.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "accounts": [],
            "error": f"Unexpected error: {str(e)}"
        }

@mcp.tool()
async def get_banks() -> Dict[str, Any]:
    """Get list of available banks."""
    try:
        await ensure_authenticated()
        
        banks = await obp_client.get_banks()
        return {
            "success": True,
            "banks": banks,
            "count": len(banks)
        }
    except OBPError as e:
        return {
            "success": False,
            "banks": [],
            "error": e.message,
            "status_code": e.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "banks": [],
            "error": f"Unexpected error: {str(e)}"
        }

@mcp.tool()
async def get_account_transactions(bank_id: str, account_id: str, view_id: str = "owner", 
                                 limit: int = 50, offset: int = 0, sort_direction: str = "DESC",
                                 from_date: str = None, to_date: str = None) -> Dict[str, Any]:
    """
    Get Transactions for Account (Full).
    
    Returns transactions list of the account specified by ACCOUNT_ID and moderated by the view (VIEW_ID).
    User Authentication is Optional. The User need not be logged in.
    Authentication is required if the view is not public.
    
    Args:
        bank_id: Bank ID
        account_id: Account ID
        view_id: View ID (default: "owner")
        limit: Number of transactions to return (default: 50)
        offset: Number of transactions to skip for pagination (default: 0)
        sort_direction: Sort direction "ASC" or "DESC" (default: "DESC")
        from_date: Start date in format yyyy-MM-dd'T'HH:mm:ss.SSS'Z' (optional, default: one year ago)
        to_date: End date in format yyyy-MM-dd'T'HH:mm:ss.SSS'Z' (optional, default: now)
    """
    try:
        await ensure_authenticated()
        
        transactions = await obp_client.get_transactions(
            bank_id=bank_id, 
            account_id=account_id, 
            view_id=view_id,
            limit=limit,
            offset=offset,
            sort_direction=sort_direction,
            from_date=from_date,
            to_date=to_date
        )
        return {
            "success": True,
            "transactions": transactions,
            "count": len(transactions),
            "limit": limit,
            "offset": offset,
            "sort_direction": sort_direction,
            "from_date": from_date,
            "to_date": to_date,
            "view_id": view_id
        }
    except OBPError as e:
        return {
            "success": False,
            "transactions": [],
            "error": e.message,
            "status_code": e.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "transactions": [],
            "error": f"Unexpected error: {str(e)}"
        }

@mcp.tool()
async def get_account_cards(bank_id: str, account_id: str) -> Dict[str, Any]:
    """Get cards associated with an account."""
    try:
        await ensure_authenticated()
        
        cards = await obp_client.get_cards(bank_id, account_id)
        return {
            "success": True,
            "cards": cards,
            "count": len(cards)
        }
    except OBPError as e:
        return {
            "success": False,
            "cards": [],
            "error": e.message,
            "status_code": e.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "cards": [],
            "error": f"Unexpected error: {str(e)}"
        }

@mcp.tool()
async def create_card(bank_id: str, account_id: str, card_type: str = "Credit", name_on_card: str = "Default User") -> Dict[str, Any]:
    """Create a card for the account."""
    try:
        await ensure_authenticated()
        
        card_data = {
            "card_type": card_type,
            "name_on_card": name_on_card,
            "issue_number": "1",
            "serial_number": f"{datetime.now().timestamp():.0f}",
            "valid_from_date": datetime.now().isoformat() + "Z",
            "expires_date": "2030-12-31T23:59:59Z",
            "enabled": True,
            "technology": "chip_and_pin",
            "networks": ["visa"],
            "allows": ["credit", "debit"]
        }
        
        result = await obp_client.create_card(bank_id, account_id, card_data)
        return {
            "success": True,
            "card": result
        }
    except OBPError as e:
        # Provide fallback mock data if card creation fails
        return {
            "success": False,
            "error": e.message,
            "status_code": e.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

@mcp.tool()
async def get_accounts_held_by_user(user_id: str, account_type_filter: str = None, account_type_filter_operation: str = None) -> Dict[str, Any]:
    """
    Get accounts held by a specific user.
    
    This endpoint can be used to onboard accounts to the API since all other account 
    and transaction endpoints require views to be assigned.
    
    Args:
        user_id: The user ID to get accounts for (e.g., "9ca9a7e4-6d02-40e3-a129-0b2bf89de9b1")
        account_type_filter: Optional comma-separated account types (e.g., "330,CURRENT+PLUS")
        account_type_filter_operation: Filter operation, must be "INCLUDE" or "EXCLUDE"
    """
    try:
        await ensure_authenticated()
        
        accounts = await obp_client.get_accounts_held_by_user(
            user_id=user_id,
            account_type_filter=account_type_filter,
            account_type_filter_operation=account_type_filter_operation
        )
        return {
            "success": True,
            "accounts": accounts,
            "count": len(accounts),
            "user_id": user_id,
            "filters_applied": {
                "account_type_filter": account_type_filter,
                "account_type_filter_operation": account_type_filter_operation
            } if account_type_filter or account_type_filter_operation else None
        }
    except OBPError as e:
        return {
            "success": False,
            "accounts": [],
            "error": e.message,
            "status_code": e.status_code,
            "user_id": user_id
        }
    except Exception as e:
        return {
            "success": False,
            "accounts": [],
            "error": f"Unexpected error: {str(e)}",
            "user_id": user_id
        }

@mcp.tool()
async def get_current_user() -> Dict[str, Any]:
    """Get current user information including user ID, username, and profile details."""
    try:
        await ensure_authenticated()
        
        user = await obp_client.get_current_user()
        return {
            "success": True,
            "user": user
        }
    except OBPError as e:
        return {
            "success": False,
            "user": None,
            "error": e.message,
            "status_code": e.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "user": None,
            "error": f"Unexpected error: {str(e)}"
        }

@mcp.tool()
async def get_user_by_id(user_id: str) -> Dict[str, Any]:
    """Get user information by user ID."""
    try:
        await ensure_authenticated()
        
        user = await obp_client.get_user_by_id(user_id)
        return {
            "success": True,
            "user": user,
            "user_id": user_id
        }
    except OBPError as e:
        return {
            "success": False,
            "user": None,
            "error": e.message,
            "status_code": e.status_code,
            "user_id": user_id
        }
    except Exception as e:
        return {
            "success": False,
            "user": None,
            "error": f"Unexpected error: {str(e)}",
            "user_id": user_id
        }

@mcp.tool()
async def get_account_details(bank_id: str, account_id: str, view_id: str = "owner") -> Dict[str, Any]:
    """Get detailed account information including balance, account type, and metadata."""
    try:
        await ensure_authenticated()
        
        account = await obp_client.get_account_by_id(bank_id, account_id, view_id)
        return {
            "success": True,
            "account": account,
            "bank_id": bank_id,
            "account_id": account_id,
            "view_id": view_id
        }
    except OBPError as e:
        return {
            "success": False,
            "account": None,
            "error": e.message,
            "status_code": e.status_code,
            "bank_id": bank_id,
            "account_id": account_id
        }
    except Exception as e:
        return {
            "success": False,
            "account": None,
            "error": f"Unexpected error: {str(e)}",
            "bank_id": bank_id,
            "account_id": account_id
        }

@mcp.tool()
async def get_transaction_details(bank_id: str, account_id: str, transaction_id: str, view_id: str = "owner") -> Dict[str, Any]:
    """Get detailed transaction information including metadata, narrative, and tags."""
    try:
        await ensure_authenticated()
        
        transaction = await obp_client.get_transaction_by_id(bank_id, account_id, transaction_id, view_id)
        return {
            "success": True,
            "transaction": transaction,
            "bank_id": bank_id,
            "account_id": account_id,
            "transaction_id": transaction_id,
            "view_id": view_id
        }
    except OBPError as e:
        return {
            "success": False,
            "transaction": None,
            "error": e.message,
            "status_code": e.status_code,
            "bank_id": bank_id,
            "account_id": account_id,
            "transaction_id": transaction_id
        }
    except Exception as e:
        return {
            "success": False,
            "transaction": None,
            "error": f"Unexpected error: {str(e)}",
            "bank_id": bank_id,
            "account_id": account_id,
            "transaction_id": transaction_id
        }

@mcp.tool()
async def add_transaction_narrative(bank_id: str, account_id: str, transaction_id: str, narrative: str, view_id: str = "owner") -> Dict[str, Any]:
    """Add a narrative (description) to a transaction for personal record keeping."""
    try:
        await ensure_authenticated()
        
        result = await obp_client.add_transaction_narrative(bank_id, account_id, transaction_id, narrative, view_id)
        return {
            "success": True,
            "narrative": result,
            "bank_id": bank_id,
            "account_id": account_id,
            "transaction_id": transaction_id,
            "added_narrative": narrative
        }
    except OBPError as e:
        return {
            "success": False,
            "narrative": None,
            "error": e.message,
            "status_code": e.status_code,
            "bank_id": bank_id,
            "account_id": account_id,
            "transaction_id": transaction_id
        }
    except Exception as e:
        return {
            "success": False,
            "narrative": None,
            "error": f"Unexpected error: {str(e)}",
            "bank_id": bank_id,
            "account_id": account_id,
            "transaction_id": transaction_id
        }

@mcp.tool()
async def add_transaction_tag(bank_id: str, account_id: str, transaction_id: str, tag: str, view_id: str = "owner") -> Dict[str, Any]:
    """Add a tag to a transaction for categorization and organization."""
    try:
        await ensure_authenticated()
        
        result = await obp_client.add_transaction_tag(bank_id, account_id, transaction_id, tag, view_id)
        return {
            "success": True,
            "tag": result,
            "bank_id": bank_id,
            "account_id": account_id,
            "transaction_id": transaction_id,
            "added_tag": tag
        }
    except OBPError as e:
        return {
            "success": False,
            "tag": None,
            "error": e.message,
            "status_code": e.status_code,
            "bank_id": bank_id,
            "account_id": account_id,
            "transaction_id": transaction_id
        }
    except Exception as e:
        return {
            "success": False,
            "tag": None,
            "error": f"Unexpected error: {str(e)}",
            "bank_id": bank_id,
            "account_id": account_id,
            "transaction_id": transaction_id
        }

@mcp.tool()
async def get_counterparties(bank_id: str, account_id: str, view_id: str = "owner") -> Dict[str, Any]:
    """Get counterparties (people/organizations you've transacted with) for an account."""
    try:
        await ensure_authenticated()
        
        counterparties = await obp_client.get_counterparties(bank_id, account_id, view_id)
        return {
            "success": True,
            "counterparties": counterparties,
            "count": len(counterparties),
            "bank_id": bank_id,
            "account_id": account_id,
            "view_id": view_id
        }
    except OBPError as e:
        return {
            "success": False,
            "counterparties": [],
            "error": e.message,
            "status_code": e.status_code,
            "bank_id": bank_id,
            "account_id": account_id
        }
    except Exception as e:
        return {
            "success": False,
            "counterparties": [],
            "error": f"Unexpected error: {str(e)}",
            "bank_id": bank_id,
            "account_id": account_id
        }

@mcp.tool()
async def create_payment_request(bank_id: str, account_id: str, to_account_id: str, amount: str, currency: str, description: str = "", view_id: str = "owner") -> Dict[str, Any]:
    """
    Create a payment request (transaction request) to transfer money to another account.
    
    Args:
        bank_id: Source bank ID
        account_id: Source account ID  
        to_account_id: Destination account ID
        amount: Amount to transfer (as string)
        currency: Currency code (e.g., "EUR", "USD")
        description: Optional description for the payment
        view_id: View ID (default: "owner")
    """
    try:
        await ensure_authenticated()
        
        transaction_request_body = {
            "to": {
                "account_id": to_account_id
            },
            "value": {
                "currency": currency,
                "amount": amount
            },
            "description": description,
            "charge_policy": "SHARED"
        }
        
        result = await obp_client.create_transaction_request(
            bank_id=bank_id,
            account_id=account_id,
            view_id=view_id,
            request_type="ACCOUNT",
            transaction_request_body=transaction_request_body
        )
        
        return {
            "success": True,
            "transaction_request": result,
            "bank_id": bank_id,
            "account_id": account_id,
            "to_account_id": to_account_id,
            "amount": amount,
            "currency": currency,
            "description": description
        }
    except OBPError as e:
        return {
            "success": False,
            "transaction_request": None,
            "error": e.message,
            "status_code": e.status_code,
            "bank_id": bank_id,
            "account_id": account_id,
            "to_account_id": to_account_id
        }
    except Exception as e:
        return {
            "success": False,
            "transaction_request": None,
            "error": f"Unexpected error: {str(e)}",
            "bank_id": bank_id,
            "account_id": account_id,
            "to_account_id": to_account_id
        }

if __name__ == "__main__":
    # Run the MCP server using stdio transport (can be changed as needed)
    mcp.run(
        transport="stdio",
    ) 
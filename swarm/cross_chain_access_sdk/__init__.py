"""Cross-Chain Access SDK - Stock market RWA trading through Swarm's Cross-Chain Access integration.

This SDK provides a unified interface for trading Real World Assets (RWAs)
through Swarm's stock market platform powered by Cross-Chain Access, combining:
- Market hours validation (14:30-21:00 UTC, weekdays)
- Account status checks (trading permissions)
- Real-time quotes from Cross-Chain Access API
- On-chain token transfers via Web3
- Off-chain order submission to Cross-Chain Access

Example:
    >>> from cross_chain_access_sdk import CrossChainAccessClient
    >>> from shared.models import Network
    >>> from decimal import Decimal
    >>> 
    >>> async with CrossChainAccessClient(
    ...     network=Network.POLYGON,
    ...     private_key="0x...",
    ...     user_email="user@example.com"
    ... ) as client:
    ...     # Get a quote
    ...     quote = await client.get_quote("AAPL")
    ...     print(f"AAPL price: ${quote.rate}")
    ...     
    ...     # Buy RWA tokens
    ...     result = await client.buy(
    ...         rwa_token_address="0xRWA...",
    ...         rwa_symbol="AAPL",
    ...         rwa_amount=Decimal("10"),
    ...         user_email="user@example.com"
    ...     )
    ...     print(f"Trade successful! TX: {result.tx_hash}")
"""

from .sdk import CrossChainAccessClient
from .cross_chain_access import (
    CrossChainAccessAPIClient,
    CrossChainAccessQuote,
    AccountStatus,
    AccountFunds,
    CalculatedAmounts,
    CrossChainAccessTradeParams,
    CrossChainAccessOrderResponse,
    OrderSide,
    CrossChainAccessException,
    MarketClosedException,
    AccountBlockedException,
    InsufficientFundsException,
    QuoteUnavailableException,
    OrderFailedException,
    InvalidSymbolException,
)
from .market_hours import MarketHours

__version__ = "0.1.0"

__all__ = [
    # Main client
    "CrossChainAccessClient",
    # API client (internal, but exposed for advanced use)
    "CrossChainAccessAPIClient",
    # Models
    "CrossChainAccessQuote",
    "AccountStatus",
    "AccountFunds",
    "CalculatedAmounts",
    "CrossChainAccessTradeParams",
    "CrossChainAccessOrderResponse",
    "OrderSide",
    # Exceptions
    "CrossChainAccessException",
    "MarketClosedException",
    "AccountBlockedException",
    "InsufficientFundsException",
    "QuoteUnavailableException",
    "OrderFailedException",
    "InvalidSymbolException",
    # Utilities
    "MarketHours",
]

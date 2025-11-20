"""Trading SDK - Unified multi-platform RWA trading with smart routing.

This SDK provides the highest-level trading interface that intelligently
combines Market Maker and Cross-Chain Access platforms, with features including:
- Smart routing based on price, liquidity, and availability
- Automatic fallback between platforms
- Quote aggregation and comparison
- Unified trade() method that works across platforms
- Platform-specific optimizations (market hours, gas, etc.)

Routing Strategies:
- BEST_PRICE: Automatically selects platform with best price (default)
- CROSS_CHAIN_ACCESS_FIRST: Try Cross-Chain Access first, fallback to Market Maker
- MARKET_MAKER_FIRST: Try Market Maker first, fallback to Cross-Chain Access
- CROSS_CHAIN_ACCESS_ONLY: Only use Cross-Chain Access (fails if unavailable)
- MARKET_MAKER_ONLY: Only use Market Maker (fails if unavailable)

Example:
    >>> from trading_sdk import TradingClient, RoutingStrategy
    >>> from shared.models import Network
    >>> from decimal import Decimal
    >>> 
    >>> # Smart routing - automatically chooses best platform
    >>> async with TradingClient(
    ...     network=Network.POLYGON,
    ...     private_key="0x...",
    ...     rpq_api_key="key123",
    ...     user_email="user@example.com"
    ... ) as client:
    ...     # Get quotes from all platforms
    ...     quotes = await client.get_quotes(
    ...         from_token="0xUSDC...",
    ...         to_token="0xRWA...",
    ...         from_amount=Decimal("100"),
    ...         to_token_symbol="AAPL"
    ...     )
    ...     print(f"Market Maker: ${quotes['market_maker'].rate if quotes['market_maker'] else 'N/A'}")
    ...     print(f"Cross-Chain Access: ${quotes['cross_chain_access'].rate if quotes['cross_chain_access'] else 'N/A'}")
    ...     
    ...     # Execute trade with smart routing
    ...     result = await client.trade(
    ...         from_token="0xUSDC...",
    ...         to_token="0xRWA...",
    ...         from_amount=Decimal("100"),
    ...         to_token_symbol="AAPL",
    ...         user_email="user@example.com"
    ...     )
    ...     print(f"Trade successful! TX: {result.tx_hash}")
    
    >>> # Force specific platform
    >>> async with TradingClient(
    ...     network=Network.POLYGON,
    ...     private_key="0x...",
    ...     rpq_api_key="key123",
    ...     routing_strategy=RoutingStrategy.MARKET_MAKER_ONLY
    ... ) as client:
    ...     result = await client.trade(...)  # Will only use Market Maker
"""

from .sdk import TradingClient
from .routing import RoutingStrategy, Router
from .exceptions import (
    TradingException,
    NoLiquidityException,
    AllPlatformsFailedException,
    InvalidRoutingStrategyException,
)

__version__ = "0.1.0"

__all__ = [
    # Main client
    "TradingClient",
    # Routing
    "RoutingStrategy",
    "Router",
    # Exceptions
    "TradingException",
    "NoLiquidityException",
    "AllPlatformsFailedException",
    "InvalidRoutingStrategyException",
]

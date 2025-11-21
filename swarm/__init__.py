"""Swarm Collection - Unified SDK collection for trading Real World Assets.

This package provides a comprehensive suite of SDKs for trading RWAs across multiple platforms:

- swarm.shared: Shared utilities, models, and base classes
- swarm.trading_sdk: Unified trading with smart routing
- swarm.market_maker_sdk: Decentralized OTC trading (24/7)
- swarm.cross_chain_access_sdk: Stock market trading (market hours)

Example:
    >>> from swarm.trading_sdk import TradingClient
    >>> from swarm.shared.models import Network
    >>> 
    >>> async with TradingClient(
    ...     network=Network.POLYGON,
    ...     private_key="0x...",
    ...     rpq_api_key="key123",
    ...     user_email="user@example.com"
    ... ) as client:
    ...     result = await client.trade(...)
"""

__version__ = "1.0.0b3"

__all__ = [
    "__version__",
]



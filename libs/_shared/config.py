"""Environment configuration for Swarm Collection.

This module provides environment-aware configuration for the SDK.
By default, all operations run in production mode.

To switch to development mode, set environment variable:
    SWARM_COLLECTION_MODE=dev

All addresses and URLs are centralized here to avoid hardcoding across the codebase.

Dynamic addresses (topup addresses, Market Maker manager contracts) are fetched from remote
JSON files with auto-refresh every 5 minutes.
"""

import os
import asyncio
from typing import Dict, Optional
from .remote_config import get_config_fetcher, RemoteConfigFetcher


def get_is_dev() -> bool:
    """Check if running in development mode.
    
    Returns:
        True if SWARM_COLLECTION_MODE=dev, False otherwise (prod is default)
    
    Example:
        >>> # In production (default)
        >>> get_is_dev()
        False
        
        >>> # In development (SWARM_COLLECTION_MODE=dev in .env)
        >>> get_is_dev()
        True
    """
    mode = os.getenv("SWARM_COLLECTION_MODE", "prod")
    return mode == "dev"


def get_cross_chain_access_api_url() -> str:
    """Get Cross-Chain Access Stock Trading API URL based on environment.
    
    Returns:
        Dev or Prod API URL
    """
    if get_is_dev():
        return "https://stock-trading-api.dev.swarm.com/stock-trading"
    return "https://stock-trading-api.app.swarm.com/stock-trading"


def get_swarm_auth_url() -> str:
    """Get Swarm Auth API URL.
    
    Note: Currently same for dev and prod.
    
    Returns:
        Swarm Auth API URL
    """
    return "https://api.app.swarm.com"


def get_rpq_service_url() -> str:
    """Get RFQ Service API URL.
    
    Note: Currently same for dev and prod.
    
    Returns:
        RFQ Service API URL
    """
    return "https://rfq.swarm.com/v1/client"


async def get_topup_address() -> str:
    """Get Cross-Chain Access topup/escrow address from remote configuration.
    
    Fetches address from remote JSON file (or local fallback) with auto-refresh.
    
    Returns:
        Topup address for current environment
    
    Raises:
        ValueError: If configuration cannot be loaded
    
    Example:
        >>> address = await get_topup_address()
        >>> print(f"Topup address: {address}")
    """
    fetcher = await get_config_fetcher(is_dev=get_is_dev())
    return fetcher.get_topup_address()


def get_topup_address_sync() -> str:
    """Get Cross-Chain Access topup/escrow address synchronously (for backwards compatibility).
    
    WARNING: This is a synchronous wrapper that creates a new event loop if needed.
    Prefer using the async version (get_topup_address) when possible.
    
    Returns:
        Topup address for current environment
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, we can't use run_until_complete
            # This shouldn't happen in normal SDK usage
            raise RuntimeError(
                "Cannot use sync version in async context. Use await get_topup_address() instead."
            )
        return loop.run_until_complete(get_topup_address())
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(get_topup_address())


async def get_dotc_manager_address(chain_id: int) -> str:
    """Get Market Maker Manager contract address from remote configuration.
    
    Fetches address from remote JSON file (or local fallback) with auto-refresh.
    
    Args:
        chain_id: Blockchain network ID (e.g., 1 for Ethereum, 137 for Polygon)
    
    Returns:
        Market Maker Manager contract address
    
    Raises:
        ValueError: If configuration cannot be loaded or address not found
    
    Example:
        >>> address = await get_dotc_manager_address(137)  # Polygon
        >>> print(f"Market Maker Manager: {address}")
    """
    fetcher = await get_config_fetcher(is_dev=get_is_dev())
    return fetcher.get_dotc_manager_address(chain_id)


def get_internal_worker_id() -> str:
    """Get internal worker ID for API headers.
    
    Returns:
        Worker ID string
    """
    return "d36195a5-f707-4a4a-a453-1d1d01aafd3b"


# Environment info (for debugging/logging)
async def get_environment_info() -> Dict[str, str]:
    """Get current environment configuration.
    
    Returns:
        Dictionary with environment settings
    """
    is_dev = get_is_dev()
    topup_address = await get_topup_address()
    
    return {
        "mode": "dev" if is_dev else "prod",
        "cross_chain_access_api_url": get_cross_chain_access_api_url(),
        "swarm_auth_url": get_swarm_auth_url(),
        "rpq_service_url": get_rpq_service_url(),
        "topup_address": topup_address,
    }

"""Remote configuration fetcher with auto-refresh.

This module fetches configuration from remote JSON files and caches them 
with automatic refresh every 5 minutes.

Configuration includes:
- Topup/escrow addresses for Cross-Chain Access
- Market Maker Manager contract addresses
"""

import json
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import aiohttp

logger = logging.getLogger(__name__)


class RemoteConfigFetcher:
    """Fetches and caches remote configuration with auto-refresh.
    
    Loads configuration from remote URL: https://trading-configurations.swarm.com/
    
    Configuration is cached and refreshed every 5 minutes automatically.
    
    Attributes:
        is_dev: Whether running in development mode
        config_url: Remote URL for config file
        cache: Cached configuration data
        last_fetch: Timestamp of last successful fetch
        refresh_interval: Time between refreshes (default 5 minutes)
    
    Example:
        >>> fetcher = RemoteConfigFetcher(is_dev=False)
        >>> await fetcher.initialize()
        >>> topup_address = fetcher.get_topup_address()
        >>> market_maker_address = fetcher.get_market_maker_manager_address(chain_id=137)
    """
    
    # Default refresh interval: 5 minutes
    REFRESH_INTERVAL_SECONDS = 5 * 60
    
    def __init__(self, is_dev: bool = False):
        """Initialize remote config fetcher.
        
        Args:
            is_dev: Whether to use development configuration
        """
        self.is_dev = is_dev
        self.cache: Optional[Dict[str, Any]] = None
        self.last_fetch: Optional[datetime] = None
        self.refresh_interval = timedelta(seconds=self.REFRESH_INTERVAL_SECONDS)
        self._fetch_lock = asyncio.Lock()
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Remote URLs
        dev_url = "https://trading-configurations.swarm.com/config.dev.json"
        prod_url = "https://trading-configurations.swarm.com/config.prod.json"
        self.config_url = dev_url if is_dev else prod_url
        
        logger.info(
            f"Initialized RemoteConfigFetcher "
            f"(mode: {'dev' if is_dev else 'prod'}, "
            f"remote: {self.config_url})"
        )
    
    async def initialize(self):
        """Initialize the config fetcher and load initial configuration.
        
        This should be called once during application startup.
        
        Raises:
            Exception: If configuration cannot be loaded from remote
        """
        logger.info("Initializing configuration...")
        await self._fetch_config()
        
        if not self.cache:
            raise Exception(
                f"Failed to load configuration from remote: {self.config_url}"
            )
        
        logger.info(
            f"Configuration loaded successfully "
            f"(version: {self.cache.get('version', 'unknown')})"
        )
    
    async def close(self):
        """Close HTTP session and cleanup resources."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _fetch_config(self) -> bool:
        """Fetch configuration from remote URL.
        
        Returns:
            True if fetch was successful, False otherwise
        """
        async with self._fetch_lock:
            try:
                config = await self._fetch_from_url(self.config_url)
                if config:
                    self.cache = config
                    self.last_fetch = datetime.utcnow()
                    logger.info(f"Configuration fetched from remote: {self.config_url}")
                    return True
            except Exception as e:
                logger.error(f"Failed to fetch from remote: {e}")
            
            return False
    
    async def _fetch_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch configuration from remote URL.
        
        Args:
            url: Remote URL to fetch from
        
        Returns:
            Configuration dictionary or None if fetch fails
        """
        if not self._session:
            self._session = aiohttp.ClientSession()
        
        async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.warning(f"Remote config returned status {response.status}")
                return None
    
    async def _maybe_refresh(self):
        """Refresh configuration if cache is stale.
        
        This is called automatically before accessing cached data.
        """
        if not self.last_fetch:
            # No initial fetch yet
            await self._fetch_config()
            return
        
        time_since_fetch = datetime.utcnow() - self.last_fetch
        if time_since_fetch >= self.refresh_interval:
            logger.info("Configuration cache is stale, refreshing...")
            success = await self._fetch_config()
            if not success:
                logger.warning(
                    "Failed to refresh configuration, using cached data "
                    f"(age: {time_since_fetch.total_seconds():.0f}s)"
                )
    
    def get_topup_address(self) -> str:
        """Get Cross-Chain Access escrow/topup address.
        
        Returns:
            Topup address for current environment
        
        Raises:
            ValueError: If configuration not loaded or address not found
        """
        if not self.cache:
            raise ValueError("Configuration not loaded. Call initialize() first.")
        
        address = self.cache.get("topup_addresses", {}).get("cross_chain_access_escrow")
        if not address:
            raise ValueError("Topup address not found in configuration")
        
        return address
    
    def get_market_maker_manager_address(self, chain_id: int) -> str:
        """Get Market Maker Manager contract address for a specific chain.
        
        Args:
            chain_id: Blockchain network ID (e.g., 1 for Ethereum, 137 for Polygon)
        
        Returns:
            Market Maker Manager contract address
        
        Raises:
            ValueError: If configuration not loaded or address not found for chain
        """
        if not self.cache:
            raise ValueError("Configuration not loaded. Call initialize() first.")
        
        address = self.cache.get("dotc_manager_addresses", {}).get(str(chain_id))
        if not address:
            raise ValueError(f"Market Maker Manager address not found for chain ID {chain_id}")
        
        return address
    
    def get_config_version(self) -> str:
        """Get configuration version.
        
        Returns:
            Version string or "unknown"
        """
        if not self.cache:
            return "unknown"
        return self.cache.get("version", "unknown")
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get entire configuration dictionary.
        
        Returns:
            Configuration dictionary
        
        Raises:
            ValueError: If configuration not loaded
        """
        if not self.cache:
            raise ValueError("Configuration not loaded. Call initialize() first.")
        return self.cache.copy()


# Global singleton instances
_prod_fetcher: Optional[RemoteConfigFetcher] = None
_dev_fetcher: Optional[RemoteConfigFetcher] = None
_fetcher_lock = asyncio.Lock()


async def get_config_fetcher(is_dev: bool = False) -> RemoteConfigFetcher:
    """Get or create the global config fetcher singleton.
    
    Args:
        is_dev: Whether to use development configuration
    
    Returns:
        RemoteConfigFetcher instance
    
    Example:
        >>> fetcher = await get_config_fetcher(is_dev=False)
        >>> topup_address = fetcher.get_topup_address()
    """
    global _prod_fetcher, _dev_fetcher
    
    async with _fetcher_lock:
        if is_dev:
            if _dev_fetcher is None:
                _dev_fetcher = RemoteConfigFetcher(is_dev=True)
                await _dev_fetcher.initialize()
            else:
                # Auto-refresh if needed
                await _dev_fetcher._maybe_refresh()
            return _dev_fetcher
        else:
            if _prod_fetcher is None:
                _prod_fetcher = RemoteConfigFetcher(is_dev=False)
                await _prod_fetcher.initialize()
            else:
                # Auto-refresh if needed
                await _prod_fetcher._maybe_refresh()
            return _prod_fetcher


async def close_config_fetchers():
    """Close all config fetcher instances.
    
    Should be called during application shutdown.
    """
    global _prod_fetcher, _dev_fetcher
    
    if _prod_fetcher:
        await _prod_fetcher.close()
        _prod_fetcher = None
    
    if _dev_fetcher:
        await _dev_fetcher.close()
        _dev_fetcher = None

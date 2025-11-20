"""Unified Trading SDK combining Market Maker and Cross-Chain Access platforms."""

import asyncio
import logging
from decimal import Decimal
from typing import Optional

from swarm.shared.models import Network, Quote, TradeResult
from swarm.shared.swarm_auth import SwarmAuth
from swarm.shared.config import get_is_dev
from swarm.market_maker_sdk import MarketMakerClient
from swarm.cross_chain_access_sdk import CrossChainAccessClient, MarketClosedException as CrossChainAccessMarketClosedException
from ..routing import Router, RoutingStrategy, PlatformOption
from ..exceptions import (
    TradingException,
    NoLiquidityException,
    AllPlatformsFailedException,
)

logger = logging.getLogger(__name__)


class TradingClient:
    """Unified trading client with smart routing between Market Maker and Cross-Chain Access.
    
    This is the highest-level SDK that provides:
    1. Unified trade() method that works across platforms
    2. Smart routing based on price, liquidity, and availability
    3. Automatic fallback between platforms
    4. Quote comparison and aggregation
    
    The client automatically:
    - Tries both platforms and compares quotes
    - Selects optimal platform based on strategy
    - Falls back to alternative if primary fails
    - Handles platform-specific requirements (market hours for Cross-Chain Access)
    
    Environment (dev/prod) is controlled via SWARM_COLLECTION_MODE env variable.
    
    Attributes:
        network: Network for this client instance
        market_maker_client: Market Maker SDK client
        cross_chain_access_client: Cross-Chain Access SDK client
        routing_strategy: Default routing strategy
    
    Example:
        >>> # Context manager (preferred)
        >>> async with TradingClient(
        ...     network=Network.POLYGON,
        ...     private_key="0x...",
        ...     rpq_api_key="key123",
        ...     user_email="user@example.com"
        ... ) as client:
        ...     # Automatically routes to best platform
        ...     result = await client.trade(
        ...         from_token="0xUSDC...",
        ...         to_token="0xRWA...",
        ...         from_amount=Decimal("100"),
        ...         to_token_symbol="AAPL"
        ...     )
        ...     print(f"Traded via {result.network}! TX: {result.tx_hash}")
    """
    
    def __init__(
        self,
        network: Network,
        private_key: str,
        rpq_api_key: str,
        user_email: Optional[str] = None,
        rpc_url: Optional[str] = None,
        routing_strategy: RoutingStrategy = RoutingStrategy.BEST_PRICE,
    ):
        """Initialize unified trading client.
        
        Args:
            network: Network to trade on
            private_key: Private key for signing transactions
            rpq_api_key: API key for Market Maker RPQ service
            user_email: Optional email for authentication
            rpc_url: Optional custom RPC URL
            routing_strategy: Default routing strategy
        """
        self.network = network
        self.routing_strategy = routing_strategy
        
        # Initialize Market Maker client
        self.market_maker_client = MarketMakerClient(
            network=network,
            private_key=private_key,
            rpq_api_key=rpq_api_key,
            user_email=user_email,
            rpc_url=rpc_url,
        )
        
        # Initialize Cross-Chain Access client
        self.cross_chain_access_client = CrossChainAccessClient(
            network=network,
            private_key=private_key,
            user_email=user_email,
            rpc_url=rpc_url,
        )
        
        logger.info(
            f"Initialized Trading SDK for {network.name} "
            f"({'dev' if get_is_dev() else 'prod'} mode) "
            f"with routing strategy: {routing_strategy.value}"
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.market_maker_client.__aenter__()
        await self.cross_chain_access_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.market_maker_client.__aexit__(exc_type, exc_val, exc_tb)
        await self.cross_chain_access_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def close(self):
        """Close all clients and cleanup resources."""
        await self.market_maker_client.close()
        await self.cross_chain_access_client.close()
        
        # Close remote config fetcher sessions
        from swarm.shared.remote_config import close_config_fetchers
        await close_config_fetchers()
        
        logger.info("Trading SDK closed")
    
    async def get_quotes(
        self,
        from_token: str,
        to_token: str,
        from_amount: Optional[Decimal] = None,
        to_amount: Optional[Decimal] = None,
        to_token_symbol: Optional[str] = None,
    ) -> dict[str, Optional[Quote]]:
        """Get quotes from all available platforms.
        
        Args:
            from_token: Token to sell
            to_token: Token to buy
            from_amount: Amount to sell (optional)
            to_amount: Amount to buy (optional)
            to_token_symbol: Token symbol for Cross-Chain Access (e.g., "AAPL")
        
        Returns:
            Dictionary with platform names as keys and quotes as values
        
        Example:
            >>> quotes = await client.get_quotes(
            ...     from_token="0xUSDC...",
            ...     to_token="0xRWA...",
            ...     from_amount=Decimal("100"),
            ...     to_token_symbol="AAPL"
            ... )
            >>> print(f"Market Maker: {quotes['market_maker'].rate if quotes['market_maker'] else 'N/A'}")
            >>> print(f"Cross-Chain Access: {quotes['cross_chain_access'].rate if quotes['cross_chain_access'] else 'N/A'}")
        """
        # Get quotes in parallel
        market_maker_task = self._get_market_maker_quote(from_token, to_token, from_amount, to_amount)
        cross_chain_access_task = self._get_cross_chain_access_quote(to_token_symbol) if to_token_symbol else None
        
        results = await asyncio.gather(
            market_maker_task,
            cross_chain_access_task if cross_chain_access_task else asyncio.sleep(0),
            return_exceptions=True
        )
        
        market_maker_quote = results[0] if not isinstance(results[0], Exception) else None
        cross_chain_access_quote = results[1] if cross_chain_access_task and not isinstance(results[1], Exception) else None
        
        return {
            "market_maker": market_maker_quote,
            "cross_chain_access": cross_chain_access_quote,
        }
    
    async def trade(
        self,
        from_token: str,
        to_token: str,
        user_email: str,
        from_amount: Optional[Decimal] = None,
        to_amount: Optional[Decimal] = None,
        to_token_symbol: Optional[str] = None,
        routing_strategy: Optional[RoutingStrategy] = None,
    ) -> TradeResult:
        """Execute a trade with smart routing between platforms.
        
        This method:
        1. Gets quotes from all available platforms
        2. Selects optimal platform based on routing strategy
        3. Executes trade on selected platform
        4. Falls back to alternative if primary fails
        
        Args:
            from_token: Token to sell
            to_token: Token to buy
            user_email: User email for notifications
            from_amount: Amount to sell (optional)
            to_amount: Amount to buy (optional)
            to_token_symbol: Token symbol for Cross-Chain Access (required for Cross-Chain Access, e.g., "AAPL")
            routing_strategy: Override default routing strategy
        
        Returns:
            TradeResult with transaction details
        
        Raises:
            ValueError: If both or neither amounts provided
            NoLiquidityException: If no platforms available
            AllPlatformsFailedException: If all platforms fail
        
        Example:
            >>> # Smart routing (default BEST_PRICE)
            >>> result = await client.trade(
            ...     from_token="0xUSDC...",
            ...     to_token="0xRWA...",
            ...     from_amount=Decimal("100"),
            ...     to_token_symbol="AAPL",
            ...     user_email="user@example.com"
            ... )
            
            >>> # Force Market Maker only
            >>> result = await client.trade(
            ...     from_token="0xUSDC...",
            ...     to_token="0xRWA...",
            ...     from_amount=Decimal("100"),
            ...     user_email="user@example.com",
            ...     routing_strategy=RoutingStrategy.MARKET_MAKER_ONLY
            ... )
        """
        # Validate amounts
        if (from_amount is not None and to_amount is not None) or \
           (from_amount is None and to_amount is None):
            raise ValueError(
                "Must provide either from_amount OR to_amount, not both"
            )
        
        strategy = routing_strategy or self.routing_strategy
        is_buy = from_amount is not None  # Buying if we know how much we're spending
        
        logger.info(
            f"Starting trade: {from_token} -> {to_token} "
            f"(strategy: {strategy.value})"
        )
        
        # Step 1: Get quotes from all platforms
        market_maker_option = await self._get_market_maker_option(
            from_token, to_token, from_amount, to_amount
        )
        
        cross_chain_access_option = await self._get_cross_chain_access_option(
            to_token_symbol, from_amount, to_amount
        ) if to_token_symbol else PlatformOption(
            platform="cross_chain_access",
            available=False,
            error="Symbol not provided"
        )
        
        logger.info(
            f"Platform availability - Market Maker: {market_maker_option.available}, "
            f"Cross-Chain Access: {cross_chain_access_option.available}"
        )
        
        # Step 2: Select platform based on strategy
        try:
            selected = Router.select_platform(
                cross_chain_access_option=cross_chain_access_option,
                market_maker_option=market_maker_option,
                strategy=strategy,
                is_buy=is_buy,
            )
            
            logger.info(f"Selected platform: {selected.platform}")
            
        except NoLiquidityException as e:
            logger.error(f"No liquidity available: {e}")
            raise
        
        # Step 3: Execute trade on selected platform
        try:
            if selected.platform == "cross_chain_access":
                result = await self._execute_cross_chain_access_trade(
                    rwa_token_address=to_token,
                    rwa_symbol=to_token_symbol,
                    rwa_amount=to_amount,
                    usdc_amount=from_amount,
                    user_email=user_email,
                )
            else:  # Market Maker
                result = await self._execute_market_maker_trade(
                    from_token=from_token,
                    to_token=to_token,
                    from_amount=from_amount,
                    to_amount=to_amount,
                )
            
            logger.info(
                f"Trade successful on {selected.platform}: {result.tx_hash}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Trade failed on {selected.platform}: {e}")
            
            # Try fallback if strategy allows
            if strategy == RoutingStrategy.BEST_PRICE or \
               strategy in [RoutingStrategy.CROSS_CHAIN_ACCESS_FIRST, RoutingStrategy.MARKET_MAKER_FIRST]:
                
                fallback_platform = "market_maker" if selected.platform == "cross_chain_access" else "cross_chain_access"
                fallback_option = market_maker_option if selected.platform == "cross_chain_access" else cross_chain_access_option
                
                if fallback_option.available:
                    logger.info(f"Attempting fallback to {fallback_platform}")
                    
                    try:
                        if fallback_platform == "cross_chain_access":
                            result = await self._execute_cross_chain_access_trade(
                                rwa_token_address=to_token,
                                rwa_symbol=to_token_symbol,
                                rwa_amount=to_amount,
                                usdc_amount=from_amount,
                                user_email=user_email,
                            )
                        else:  # Market Maker
                            result = await self._execute_market_maker_trade(
                                from_token=from_token,
                                to_token=to_token,
                                from_amount=from_amount,
                                to_amount=to_amount,
                            )
                        
                        logger.info(
                            f"Fallback successful on {fallback_platform}: {result.tx_hash}"
                        )
                        
                        return result
                        
                    except Exception as fallback_error:
                        logger.error(f"Fallback failed: {fallback_error}")
                        raise AllPlatformsFailedException(
                            f"Primary ({selected.platform}): {e}. "
                            f"Fallback ({fallback_platform}): {fallback_error}"
                        ) from fallback_error
            
            # No fallback available or allowed
            raise TradingException(f"Trade failed: {e}") from e
    
    async def _get_market_maker_option(
        self,
        from_token: str,
        to_token: str,
        from_amount: Optional[Decimal],
        to_amount: Optional[Decimal],
    ) -> PlatformOption:
        """Get Market Maker platform option with quote."""
        try:
            quote = await self.market_maker_client.get_quote(
                from_token=from_token,
                to_token=to_token,
                from_amount=from_amount,
                to_amount=to_amount,
            )
            return PlatformOption(platform="market_maker", quote=quote)
        except Exception as e:
            logger.warning(f"Market Maker quote failed: {e}")
            return PlatformOption(
                platform="market_maker",
                available=False,
                error=str(e)
            )
    
    async def _get_cross_chain_access_option(
        self,
        symbol: Optional[str],
        from_amount: Optional[Decimal],
        to_amount: Optional[Decimal],
    ) -> PlatformOption:
        """Get Cross-Chain Access platform option with quote."""
        if not symbol:
            return PlatformOption(
                platform="cross_chain_access",
                available=False,
                error="Symbol not provided"
            )
        
        try:
            quote = await self.cross_chain_access_client.get_quote(symbol)
            return PlatformOption(platform="cross_chain_access", quote=quote)
        except CrossChainAccessMarketClosedException as e:
            logger.warning(f"Cross-Chain Access market closed: {e}")
            return PlatformOption(
                platform="cross_chain_access",
                available=False,
                error="Market closed"
            )
        except Exception as e:
            logger.warning(f"Cross-Chain Access quote failed: {e}")
            return PlatformOption(
                platform="cross_chain_access",
                available=False,
                error=str(e)
            )
    
    async def _get_market_maker_quote(
        self,
        from_token: str,
        to_token: str,
        from_amount: Optional[Decimal],
        to_amount: Optional[Decimal],
    ) -> Optional[Quote]:
        """Get quote from Market Maker (helper for get_quotes)."""
        try:
            return await self.market_maker_client.get_quote(
                from_token=from_token,
                to_token=to_token,
                from_amount=from_amount,
                to_amount=to_amount,
            )
        except Exception as e:
            logger.warning(f"Market Maker quote failed: {e}")
            return None
    
    async def _get_cross_chain_access_quote(self, symbol: Optional[str]) -> Optional[Quote]:
        """Get quote from Cross-Chain Access (helper for get_quotes)."""
        if not symbol:
            return None
        
        try:
            return await self.cross_chain_access_client.get_quote(symbol)
        except Exception as e:
            logger.warning(f"Cross-Chain Access quote failed: {e}")
            return None
    
    async def _execute_market_maker_trade(
        self,
        from_token: str,
        to_token: str,
        from_amount: Optional[Decimal],
        to_amount: Optional[Decimal],
    ) -> TradeResult:
        """Execute trade on Market Maker platform."""
        return await self.market_maker_client.trade(
            from_token=from_token,
            to_token=to_token,
            from_amount=from_amount,
            to_amount=to_amount,
        )
    
    async def _execute_cross_chain_access_trade(
        self,
        rwa_token_address: str,
        rwa_symbol: str,
        rwa_amount: Optional[Decimal],
        usdc_amount: Optional[Decimal],
        user_email: str,
    ) -> TradeResult:
        """Execute trade on Cross-Chain Access platform."""
        if usdc_amount:
            # Buying with USDC
            return await self.cross_chain_access_client.buy(
                rwa_token_address=rwa_token_address,
                rwa_symbol=rwa_symbol,
                usdc_amount=usdc_amount,
                user_email=user_email,
            )
        else:
            # Selling RWA for USDC
            return await self.cross_chain_access_client.sell(
                rwa_token_address=rwa_token_address,
                rwa_symbol=rwa_symbol,
                rwa_amount=rwa_amount,
                user_email=user_email,
            )

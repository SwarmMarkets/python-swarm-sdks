"""Trading platform routing strategies."""

from enum import Enum
from typing import Optional
from decimal import Decimal
import logging

from swarm.shared.models import Quote
from .exceptions import NoLiquidityException

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """Platform routing strategy."""
    BEST_PRICE = "best_price"                                  # Choose platform with best price
    CROSS_CHAIN_ACCESS_FIRST = "cross_chain_access_first"      # Try Cross-Chain Access first, fallback to Market Maker
    MARKET_MAKER_FIRST = "market_maker_first"                  # Try Market Maker first, fallback to Cross-Chain Access
    CROSS_CHAIN_ACCESS_ONLY = "cross_chain_access_only"        # Only use Cross-Chain Access
    MARKET_MAKER_ONLY = "market_maker_only"                    # Only use Market Maker


class PlatformOption:
    """Represents a trading platform option with quote.
    
    Attributes:
        platform: Platform name ("cross_chain_access" or "market_maker")
        quote: Quote from this platform
        available: Whether platform is available
        error: Error message if unavailable
    """
    
    def __init__(
        self,
        platform: str,
        quote: Optional[Quote] = None,
        available: bool = True,
        error: Optional[str] = None,
    ):
        self.platform = platform
        self.quote = quote
        self.available = available
        self.error = error
    
    def get_effective_rate(self) -> Decimal:
        """Get effective rate for comparison.
        
        Returns:
            Rate (buy_amount / sell_amount)
        """
        if not self.quote:
            return Decimal("0")
        
        if self.quote.sell_amount == 0:
            return Decimal("0")
        
        return self.quote.buy_amount / self.quote.sell_amount


class Router:
    """Smart router for choosing optimal trading platform.
    
    Implements various routing strategies to select between Market Maker and Cross-Chain Access
    based on price, availability, and user preferences.
    """
    
    @staticmethod
    def select_platform(
        cross_chain_access_option: PlatformOption,
        market_maker_option: PlatformOption,
        strategy: RoutingStrategy,
        is_buy: bool,
    ) -> PlatformOption:
        """Select optimal platform based on strategy.
        
        Args:
            cross_chain_access_option: Cross-Chain Access platform option with quote
            market_maker_option: Market Maker platform option with quote
            strategy: Routing strategy to use
            is_buy: Whether this is a buy order (affects price comparison)
        
        Returns:
            Selected PlatformOption
        
        Raises:
            NoLiquidityException: If no platforms available
        """
        logger.info(f"Routing with strategy: {strategy.value}")
        
        # Check availability
        cross_chain_access_available = cross_chain_access_option.available and cross_chain_access_option.quote is not None
        market_maker_available = market_maker_option.available and market_maker_option.quote is not None
        
        if not cross_chain_access_available and not market_maker_available:
            errors = []
            if cross_chain_access_option.error:
                errors.append(f"Cross-Chain Access: {cross_chain_access_option.error}")
            if market_maker_option.error:
                errors.append(f"Market Maker: {market_maker_option.error}")
            
            raise NoLiquidityException(
                f"No platforms available. {'; '.join(errors)}"
            )
        
        # Strategy: CROSS_CHAIN_ACCESS_ONLY
        if strategy == RoutingStrategy.CROSS_CHAIN_ACCESS_ONLY:
            if not cross_chain_access_available:
                raise NoLiquidityException(
                    f"Cross-Chain Access not available: {cross_chain_access_option.error}"
                )
            logger.info("Selected: Cross-Chain Access (CROSS_CHAIN_ACCESS_ONLY strategy)")
            return cross_chain_access_option
        
        # Strategy: MARKET_MAKER_ONLY
        if strategy == RoutingStrategy.MARKET_MAKER_ONLY:
            if not market_maker_available:
                raise NoLiquidityException(
                    f"Market Maker not available: {market_maker_option.error}"
                )
            logger.info("Selected: Market Maker (MARKET_MAKER_ONLY strategy)")
            return market_maker_option
        
        # Strategy: CROSS_CHAIN_ACCESS_FIRST
        if strategy == RoutingStrategy.CROSS_CHAIN_ACCESS_FIRST:
            if cross_chain_access_available:
                logger.info("Selected: Cross-Chain Access (CROSS_CHAIN_ACCESS_FIRST strategy)")
                return cross_chain_access_option
            elif market_maker_available:
                logger.info("Selected: Market Maker (fallback from Cross-Chain Access)")
                return market_maker_option
        
        # Strategy: MARKET_MAKER_FIRST
        if strategy == RoutingStrategy.MARKET_MAKER_FIRST:
            if market_maker_available:
                logger.info("Selected: Market Maker (MARKET_MAKER_FIRST strategy)")
                return market_maker_option
            elif cross_chain_access_available:
                logger.info("Selected: Cross-Chain Access (fallback from Market Maker)")
                return cross_chain_access_option
        
        # Strategy: BEST_PRICE (default)
        if strategy == RoutingStrategy.BEST_PRICE:
            if cross_chain_access_available and not market_maker_available:
                logger.info("Selected: Cross-Chain Access (only available)")
                return cross_chain_access_option
            elif market_maker_available and not cross_chain_access_available:
                logger.info("Selected: Market Maker (only available)")
                return market_maker_option
            
            # Both available - compare prices
            cross_chain_access_rate = cross_chain_access_option.get_effective_rate()
            market_maker_rate = market_maker_option.get_effective_rate()
            
            logger.info(f"Comparing rates - Cross-Chain Access: {cross_chain_access_rate}, Market Maker: {market_maker_rate}")
            
            # For BUY orders: lower rate is better (less cost per token)
            # For SELL orders: higher rate is better (more return per token)
            if is_buy:
                if cross_chain_access_rate <= market_maker_rate:
                    logger.info(f"Selected: Cross-Chain Access (better buy rate: {cross_chain_access_rate})")
                    return cross_chain_access_option
                else:
                    logger.info(f"Selected: Market Maker (better buy rate: {market_maker_rate})")
                    return market_maker_option
            else:
                if cross_chain_access_rate >= market_maker_rate:
                    logger.info(f"Selected: Cross-Chain Access (better sell rate: {cross_chain_access_rate})")
                    return cross_chain_access_option
                else:
                    logger.info(f"Selected: Market Maker (better sell rate: {market_maker_rate})")
                    return market_maker_option
        
        # Fallback (shouldn't reach here)
        logger.warning("Routing fallback - selecting first available")
        return cross_chain_access_option if cross_chain_access_available else market_maker_option

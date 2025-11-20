"""Core Cross-Chain Access SDK for stock market trading."""

import asyncio
import logging
from decimal import Decimal
from datetime import datetime
from typing import Optional

from _shared.models import Network, Quote, TradeResult
from _shared.swarm_auth import SwarmAuth
from _shared.web3 import Web3Helper
from _shared.constants import USDC_ADDRESSES
from _shared.config import get_is_dev
from ..cross_chain_access import (
    CrossChainAccessAPIClient,
    OrderSide,
    MarketClosedException,
    AccountBlockedException,
    InsufficientFundsException,
)
from ..market_hours import MarketHours

logger = logging.getLogger(__name__)


# Token decimals for rounding
RWA_DECIMALS = 9
USDC_DECIMALS = 2


class CrossChainAccessClient:
    """Unified Cross-Chain Access trading client for stock market RWAs.
    
    This is the main entry point for Cross-Chain Access stock trading. It orchestrates:
    1. Authentication via SwarmAuth
    2. Market hours and account status validation
    3. Quote retrieval and amount calculation with slippage
    4. On-chain token transfers via Web3Helper
    5. Off-chain order submission via CrossChainAccessAPIClient
    
    Environment (dev/prod) is controlled via SWARM_COLLECTION_MODE env variable.
    
    Attributes:
        network: Network for this client instance
        cross_chain_access_api: Cross-Chain Access API client
        web3_helper: Web3 helper for blockchain operations
        auth: Optional SwarmAuth instance
        usdc_address: USDC token address for this network
        topup_address: Escrow address for token transfers
    
    Example:
        >>> # Context manager (preferred)
        >>> async with CrossChainAccessClient(
        ...     network=Network.POLYGON,
        ...     private_key="0x...",
        ...     user_email="user@example.com"
        ... ) as client:
        ...     result = await client.buy(
        ...         rwa_token_address="0xRWA...",
        ...         rwa_symbol="AAPL",
        ...         rwa_amount=Decimal("10"),
        ...         user_email="user@example.com"
        ...     )
        
        >>> # Manual lifecycle
        >>> client = CrossChainAccessClient(...)
        >>> await client.authenticate()
        >>> result = await client.buy(...)
        >>> await client.close()
    """
    
    # Slippage protection (1%)
    SLIPPAGE_PERCENTAGE = Decimal("1")
    
    def __init__(
        self,
        network: Network,
        private_key: str,
        user_email: Optional[str] = None,
        rpc_url: Optional[str] = None,
    ):
        """Initialize Cross-Chain Access client.
        
        Args:
            network: Network to trade on
            private_key: Private key for signing transactions
            user_email: Optional email for authentication
            rpc_url: Optional custom RPC URL
        """
        self.network = network
        
        # Initialize API client
        self.cross_chain_access_api = CrossChainAccessAPIClient()
        
        # Initialize Web3 helper
        self.web3_helper = Web3Helper(
            network=network,
            private_key=private_key,
            rpc_url=rpc_url,
        )
        
        # Initialize auth
        self.auth = SwarmAuth()
        self.user_email = user_email
        
        # Get USDC address for this network
        self.usdc_address = USDC_ADDRESSES.get(network)
        if not self.usdc_address:
            raise ValueError(f"USDC not available on {network.name}")
        
        # Topup address will be fetched lazily on first use
        self.topup_address: Optional[str] = None
        
        logger.info(
            f"Initialized Cross-Chain Access client for {network.name} "
            f"({'dev' if get_is_dev() else 'prod'} mode) "
            f"with account {self.web3_helper.account.address}"
        )
        logger.info(f"USDC address: {self.usdc_address}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.authenticate()
        await self._load_topup_address()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def authenticate(self):
        """Authenticate with Swarm platform.
        
        Uses the wallet's private key to sign authentication message.
        Sets the auth token for subsequent API calls.
        
        Raises:
            AuthenticationError: If authentication fails
        """
        logger.info("Authenticating with Swarm platform")
        
        # Verify with the Web3Helper's account (LocalAccount)
        tokens = await self.auth.verify(self.web3_helper.account)
        
        # Set token for API calls
        self.cross_chain_access_api.set_auth_token(tokens.access_token)
        
        logger.info("Successfully authenticated with Swarm platform")
    
    async def _load_topup_address(self):
        """Load topup address from remote configuration.
        
        This is called during initialization to fetch the address.
        """
        if not self.topup_address:
            from _shared.remote_config import get_config_fetcher
            from _shared.config import get_is_dev
            fetcher = await get_config_fetcher(is_dev=get_is_dev())
            self.topup_address = fetcher.get_topup_address()
            logger.info(f"Topup address loaded: {self.topup_address}")
    
    async def close(self):
        """Close all clients and cleanup resources."""
        if hasattr(self.cross_chain_access_api, 'close'):
            await self.cross_chain_access_api.close()
        
        # Close remote config fetcher sessions
        from _shared.remote_config import close_config_fetchers
        await close_config_fetchers()
        
        logger.info("Cross-Chain Access client closed")
    
    async def check_trading_availability(self) -> tuple[bool, str]:
        """Check if trading is currently available.
        
        Checks:
        - Market hours (14:30-21:00 UTC, weekdays)
        - Account status (not blocked)
        - Market status (open)
        
        Returns:
            Tuple of (is_available, message)
        
        Example:
            >>> is_available, message = await client.check_trading_availability()
            >>> if not is_available:
            ...     print(f"Trading not available: {message}")
        """
        # Ensure authentication before checking account status
        if not self.cross_chain_access_api.auth_token:
            logger.info("No auth token found, authenticating...")
            await self.authenticate()
        
        # Check market hours
        is_open, market_message = MarketHours.get_market_status()
        
        if not is_open:
            return False, market_message
        
        # Check account status
        try:
            status = await self.cross_chain_access_api.get_account_status()
            
            if not status.is_trading_allowed():
                reasons = []
                if status.account_blocked:
                    reasons.append("account blocked")
                if status.trading_blocked:
                    reasons.append("trading blocked")
                if status.transfers_blocked:
                    reasons.append("transfers blocked")
                if status.trade_suspended_by_user:
                    reasons.append("suspended by user")
                if not status.market_open:
                    reasons.append("market closed")
                
                return False, f"Trading not available: {', '.join(reasons)}"
            
            return True, "Trading is available"
            
        except Exception as e:
            logger.error(f"Failed to check account status: {e}")
            return False, f"Failed to check account status: {str(e)}"
    
    async def get_quote(self, rwa_symbol: str) -> Quote:
        """Get real-time quote for a symbol.
        
        Returns quote in unified SDK format for compatibility with other SDKs.
        
        Args:
            rwa_symbol: Trading symbol (e.g., "AAPL")
        
        Returns:
            Quote in SDK format
        
        Example:
            >>> quote = await client.get_quote("AAPL")
            >>> print(f"Buy at: ${quote.buy_amount / quote.sell_amount}")
        """
        cross_chain_access_quote = await self.cross_chain_access_api.get_asset_quote(rwa_symbol)
        
        # Convert to SDK Quote format
        # For Cross-Chain Access: sell USDC (1 unit) to get RWA at ask price, or
        # sell RWA (1 unit) to get USDC at bid price
        return Quote(
            sell_token_address=self.usdc_address,
            sell_amount=Decimal("1"),
            buy_token_address=rwa_symbol,  # Symbol as placeholder
            buy_amount=Decimal("1") / cross_chain_access_quote.ask_price,
            rate=cross_chain_access_quote.ask_price,
            source="cross_chain_access",
            timestamp=datetime.now(),
        )
    
    async def buy(
        self,
        rwa_token_address: str,
        rwa_symbol: str,
        user_email: str,
        rwa_amount: Optional[Decimal] = None,
        usdc_amount: Optional[Decimal] = None,
    ) -> TradeResult:
        """Buy RWA tokens with USDC via Cross-Chain Access stock market.
        
        Provide either rwa_amount OR usdc_amount, not both.
        
        Flow:
        1. Check market hours and account status
        2. Get real-time quote
        3. Calculate amounts with 1% slippage protection
        4. Validate buying power
        5. Transfer USDC to topup address
        6. Submit order to Cross-Chain Access API
        
        Args:
            rwa_token_address: RWA token contract address
            rwa_symbol: Trading symbol (e.g., "AAPL")
            user_email: User email for notifications
            rwa_amount: Amount of RWA tokens to buy (optional, accepts int/float/Decimal)
            usdc_amount: Amount of USDC to spend (optional, accepts int/float/Decimal)
        
        Returns:
            TradeResult with transaction details
        
        Raises:
            ValueError: If both or neither amounts provided
            MarketClosedException: If market is closed
            AccountBlockedException: If account is blocked
            InsufficientFundsException: If buying power insufficient
        
        Example:
            >>> result = await client.buy(
            ...     rwa_token_address="0xRWA...",
            ...     rwa_symbol="AAPL",
            ...     rwa_amount=Decimal("10"),
            ...     user_email="user@example.com"
            ... )
            >>> print(f"Bought 10 AAPL! TX: {result.tx_hash}")
        """
        # Validate amounts
        if (rwa_amount is not None and usdc_amount is not None) or \
           (rwa_amount is None and usdc_amount is None):
            raise ValueError(
                "Must provide either rwa_amount OR usdc_amount, not both"
            )
        
        # Convert to Decimal if needed (for user convenience)
        if rwa_amount is not None and not isinstance(rwa_amount, Decimal):
            rwa_amount = Decimal(str(rwa_amount))
        if usdc_amount is not None and not isinstance(usdc_amount, Decimal):
            usdc_amount = Decimal(str(usdc_amount))
        
        return await self._execute_trade(
            rwa_token_address=rwa_token_address,
            rwa_symbol=rwa_symbol,
            rwa_amount=rwa_amount,
            usdc_amount=usdc_amount,
            order_side=OrderSide.BUY,
            user_email=user_email,
        )
    
    async def sell(
        self,
        rwa_token_address: str,
        rwa_symbol: str,
        user_email: str,
        rwa_amount: Optional[Decimal] = None,
        usdc_amount: Optional[Decimal] = None,
    ) -> TradeResult:
        """Sell RWA tokens for USDC via Cross-Chain Access stock market.
        
        Provide either rwa_amount OR usdc_amount, not both.
        
        Flow:
        1. Check market hours and account status
        2. Get real-time quote
        3. Calculate amounts with 1% slippage protection
        4. Validate RWA token balance
        5. Transfer RWA tokens to topup address
        6. Submit order to Cross-Chain Access API
        
        Args:
            rwa_token_address: RWA token contract address
            rwa_symbol: Trading symbol (e.g., "AAPL")
            user_email: User email for notifications
            rwa_amount: Amount of RWA tokens to sell (optional, accepts int/float/Decimal)
            usdc_amount: Amount of USDC to receive (optional, accepts int/float/Decimal)
        
        Returns:
            TradeResult with transaction details
        
        Raises:
            ValueError: If both or neither amounts provided
            MarketClosedException: If market is closed
            AccountBlockedException: If account is blocked
            InsufficientFundsException: If RWA balance insufficient
        
        Example:
            >>> result = await client.sell(
            ...     rwa_token_address="0xRWA...",
            ...     rwa_symbol="AAPL",
            ...     rwa_amount=Decimal("10"),
            ...     user_email="user@example.com"
            ... )
            >>> print(f"Sold 10 AAPL! TX: {result.tx_hash}")
        """
        # Validate amounts
        if (rwa_amount is not None and usdc_amount is not None) or \
           (rwa_amount is None and usdc_amount is None):
            raise ValueError(
                "Must provide either rwa_amount OR usdc_amount, not both"
            )
        
        # Convert to Decimal if needed (for user convenience)
        if rwa_amount is not None and not isinstance(rwa_amount, Decimal):
            rwa_amount = Decimal(str(rwa_amount))
        if usdc_amount is not None and not isinstance(usdc_amount, Decimal):
            usdc_amount = Decimal(str(usdc_amount))
        
        return await self._execute_trade(
            rwa_token_address=rwa_token_address,
            rwa_symbol=rwa_symbol,
            rwa_amount=rwa_amount,
            usdc_amount=usdc_amount,
            order_side=OrderSide.SELL,
            user_email=user_email,
        )
    
    async def _execute_trade(
        self,
        rwa_token_address: str,
        rwa_symbol: str,
        rwa_amount: Optional[Decimal],
        usdc_amount: Optional[Decimal],
        order_side: OrderSide,
        user_email: str,
    ) -> TradeResult:
        """Execute a trade (internal method).
        
        Args:
            rwa_token_address: RWA token contract address
            rwa_symbol: Trading symbol
            rwa_amount: Amount of RWA tokens
            usdc_amount: Amount of USDC
            order_side: BUY or SELL
            user_email: User email
        
        Returns:
            TradeResult
        """
        logger.info(f"Starting {order_side.value} trade for {rwa_symbol}")
        
        # Step 0: Ensure authentication
        if not self.cross_chain_access_api.auth_token:
            logger.info("No auth token found, authenticating...")
            await self.authenticate()
        
        # Step 1: Check trading availability
        is_available, message = await self.check_trading_availability()
        if not is_available:
            if "market" in message.lower() or "closed" in message.lower():
                raise MarketClosedException(message)
            else:
                raise AccountBlockedException(message)
        
        # Step 2: Get real-time quote
        logger.info(f"Getting quote for {rwa_symbol}")
        cross_chain_access_quote = await self.cross_chain_access_api.get_asset_quote(rwa_symbol)
        price = cross_chain_access_quote.get_price_for_side(order_side)
        logger.info(f"Quote price: ${price}")
        
        # Step 3: Calculate amounts
        if order_side == OrderSide.BUY:
            if rwa_amount:
                # Calculate USDC needed
                final_usdc = rwa_amount * price
                final_rwa = rwa_amount
            else:
                # Calculate RWA receivable
                final_rwa = usdc_amount / price
                final_usdc = usdc_amount
        else:  # SELL
            if rwa_amount:
                # Calculate USDC receivable
                final_usdc = rwa_amount * price
                final_rwa = rwa_amount
            else:
                # Calculate RWA needed
                final_rwa = usdc_amount / price
                final_usdc = usdc_amount
        
        # Round amounts to proper decimal places
        final_rwa = final_rwa.quantize(Decimal(10) ** -RWA_DECIMALS)
        final_usdc = final_usdc.quantize(Decimal(10) ** -USDC_DECIMALS)
        
        logger.info(
            f"Calculated amounts - RWA: {final_rwa}, USDC: {final_usdc}"
        )
        
        # Step 4: Check funds/balance
        if order_side == OrderSide.BUY:
            # Check buying power
            funds = await self.cross_chain_access_api.get_account_funds()
            if not funds.has_sufficient_funds(final_usdc):
                raise InsufficientFundsException(
                    f"Insufficient buying power: need ${final_usdc}, "
                    f"have ${funds.buying_power}"
                )
            logger.info(f"Buying power check passed: ${funds.buying_power}")
            
            transfer_token = self.usdc_address
            transfer_amount = final_usdc
        else:  # SELL
            # Check RWA balance
            rwa_balance = self.web3_helper.get_balance(rwa_token_address)
            if rwa_balance < final_rwa:
                raise InsufficientFundsException(
                    f"Insufficient RWA balance: need {final_rwa}, "
                    f"have {rwa_balance}"
                )
            logger.info(f"RWA balance check passed: {rwa_balance}")
            
            transfer_token = rwa_token_address
            transfer_amount = final_rwa
        
        # Step 5: Ensure topup address is loaded
        if not self.topup_address:
            await self._load_topup_address()
        
        # Step 6: Transfer tokens to topup address
        logger.info(
            f"Transferring {transfer_amount} tokens to {self.topup_address}"
        )
        tx_hash = self.web3_helper.transfer_token(
            to_address=self.topup_address,
            token_address=transfer_token,
            amount=transfer_amount,
        )
        logger.info(f"Transfer successful: {tx_hash}")
        
        # Step 7: Create trading order
        logger.info("Creating trading order")
        order_response = await self.cross_chain_access_api.create_order(
            wallet=self.web3_helper.account.address,
            tx_hash=tx_hash,
            asset_address=rwa_token_address,
            asset_symbol=rwa_symbol,
            side=order_side,
            price=price,
            qty=final_rwa,
            notional=final_usdc,
            chain_id=self.network.value,
            user_email=user_email,
        )
        
        logger.info(f"Order created: {order_response.order_id}")
        
        # Step 7: Return result
        return TradeResult(
            tx_hash=tx_hash,
            order_id=order_response.order_id,
            sell_token_address=transfer_token,
            sell_amount=transfer_amount,
            buy_token_address=rwa_token_address if order_side == OrderSide.BUY else self.usdc_address,
            buy_amount=final_rwa if order_side == OrderSide.BUY else final_usdc,
            rate=price,
            source="cross_chain_access",
            timestamp=datetime.now(),
            network=self.network,
        )

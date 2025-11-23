"""Core Market Maker SDK combining RPQ Service and Web3 operations."""

import asyncio
from typing import Optional
from decimal import Decimal
from datetime import datetime
import logging

from swarm.shared.models import Network, Quote, TradeResult
from swarm.shared.swarm_auth import SwarmAuth
from swarm.shared.config import get_is_dev
from swarm.shared.remote_config import close_config_fetchers
from ..rpq_service import (
    RPQClient,
    NoOffersAvailableException,
    PricingType,
)
from ..market_maker_web3 import MarketMakerWeb3Client, MarketMakerWeb3Exception

logger = logging.getLogger(__name__)


class MarketMakerClient:
    """Unified Market Maker trading client combining RPQ API and Web3 operations.
    
    This is the main entry point for Market Maker trading. It orchestrates:
    1. Authentication via SwarmAuth
    2. Quote discovery via RPQClient
    3. On-chain execution via MarketMakerWeb3Client
    
    Environment (dev/prod) is controlled via SWARM_COLLECTION_MODE env variable.
    
    Attributes:
        network: Network for this client instance
        rpq_client: RPQ Service API client
        web3_client: Market Maker Web3 smart contract client
        auth: Optional SwarmAuth instance
    
    Example:
        >>> # Context manager (preferred)
        >>> async with MarketMakerClient(
        ...     network=Network.POLYGON,
        ...     private_key="0x...",
        ...     rpq_api_key="key123",
        ...     user_email="user@example.com"
        ... ) as client:
        ...     result = await client.trade(
        ...         from_token="0xUSDC...",
        ...         to_token="0xRWA...",
        ...         from_amount=Decimal("100")
        ...     )
        
        >>> # Manual lifecycle
        >>> client = MarketMakerClient(...)
        >>> await client.authenticate()
        >>> result = await client.trade(...)
        >>> await client.close()
    """
    
    def __init__(
        self,
        network: Network,
        private_key: str,
        rpq_api_key: str,
        user_email: Optional[str] = None,
        rpc_url: Optional[str] = None,
    ):
        """Initialize Market Maker client.
        
        Args:
            network: Network to trade on
            private_key: Private key for signing transactions
            rpq_api_key: API key for RPQ Service
            user_email: Optional email for authentication
            rpc_url: Optional custom RPC URL
        """
        self.network = network
        
        # Convert Network enum to string for RPQ client
        network_name = network.name.lower()  # POLYGON -> "polygon"
        
        # Initialize RPQ client
        self.rpq_client = RPQClient(
            network=network_name,
            api_key=rpq_api_key,
        )
        
        # Initialize Web3 client
        self.web3_client = MarketMakerWeb3Client(
            network=network,
            private_key=private_key,
            rpc_url=rpc_url,
        )
        
        # Initialize auth
        self.auth = SwarmAuth()
        self.user_email = user_email
        
        logger.info(
            f"Initialized Market Maker client for network {network.name} "
            f"({'dev' if get_is_dev() else 'prod'} mode) "
            f"with account {self.web3_client.account.address}"
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def authenticate(self):
        """Authenticate with Swarm platform.
        
        Uses the wallet's private key to sign authentication message.
        
        Raises:
            AuthenticationError: If authentication fails
        """
        logger.info("Authenticating with Swarm platform")
        
        # Verify with the Web3Client's account (LocalAccount)
        tokens = await self.auth.verify(self.web3_client.account)
        
        logger.info("Successfully authenticated with Swarm platform")
    
    async def close(self):
        """Close all clients and cleanup resources."""
        if hasattr(self.rpq_client, 'close'):
            await self.rpq_client.close()
        
        # Close remote config fetcher sessions
        await close_config_fetchers()
        
        logger.info("Market Maker client closed")
    
    async def get_quote(
        self,
        from_token: str,
        to_token: str,
        from_amount: Optional[Decimal] = None,
        to_amount: Optional[Decimal] = None,
    ) -> Quote:
        """Get a quote for trading tokens via Market Maker.
        
        Provide either from_amount OR to_amount, not both.
        
        Args:
            from_token: Token to sell
            to_token: Token to buy
            from_amount: Amount to sell (optional)
            to_amount: Amount to buy (optional)
        
        Returns:
            Quote with calculated amounts and rate
        
        Raises:
            NoOffersAvailableException: If no offers available
            ValueError: If both or neither amounts provided
        
        Example:
            >>> quote = await client.get_quote(
            ...     from_token="0xUSDC...",
            ...     to_token="0xRWA...",
            ...     from_amount=Decimal("100")
            ... )
            >>> print(f"You will receive {quote.buy_amount} RWA tokens")
        """
        return await self.rpq_client.get_quote(
            buy_asset_address=to_token,
            sell_asset_address=from_token,
            target_sell_amount=str(from_amount) if from_amount else None,
            target_buy_amount=str(to_amount) if to_amount else None,
        )
    
    async def trade(
        self,
        from_token: str,
        to_token: str,
        from_amount: Optional[Decimal] = None,
        to_amount: Optional[Decimal] = None,
        affiliate: Optional[str] = None,
    ) -> TradeResult:
        """Execute a Market Maker trade.
        
        This orchestrates the full trading flow:
        1. Get best offers from RPQ Service (now includes depositToWithdrawalRate)
        2. Use the selected offer with all necessary details
        3. Approve tokens if needed
        4. Execute trade on-chain with correct parameters
        
        Note: When taking an offer:
        - You PAY the withdrawal asset (what maker wants to receive)
        - You RECEIVE the deposit asset (what maker deposited)
        - from_token should match the offer's withdrawalAsset
        - to_token should match the offer's depositAsset
        
        Args:
            from_token: Token to sell (should be withdrawalAsset)
            to_token: Token to buy (should be depositAsset)
            from_amount: Amount to sell (optional)
            to_amount: Amount to buy (optional)
            affiliate: Optional affiliate address for fee sharing
        
        Returns:
            TradeResult with transaction details
        
        Raises:
            NoOffersAvailableException: If no offers available
            MarketMakerWeb3Exception: If on-chain execution fails
            ValueError: If both or neither amounts provided
        
        Example:
            >>> # Buy RWA by selling USDC
            >>> result = await client.trade(
            ...     from_token="0xUSDC...",  # withdrawalAsset - what you pay
            ...     to_token="0xRWA...",     # depositAsset - what you receive
            ...     from_amount=Decimal("100"),
            ...     affiliate=None
            ... )
            >>> print(f"Trade successful! TX: {result.tx_hash}")
        """
        try:
            logger.info(
                f"Starting Market Maker trade: {from_token} -> {to_token}"
            )
            
            # Step 1: Get best offers - now includes depositToWithdrawalRate in SelectedOffer
            best_offers_response = await self.rpq_client.get_best_offers(
                buy_asset_address=to_token,      # depositAsset - what we want to receive
                sell_asset_address=from_token,   # withdrawalAsset - what we'll pay
                target_sell_amount=str(from_amount) if from_amount else None,
                target_buy_amount=str(to_amount) if to_amount else None,
            )
            
            if not best_offers_response.result.selected_offers:
                raise NoOffersAvailableException(
                    "No suitable offers found for this trade"
                )
            
            # Use the first selected offer (best one) - it now has all the data we need
            selected_offer = best_offers_response.result.selected_offers[0]
            
            logger.info(
                f"Found best offer {selected_offer.id}: "
                f"Paying {selected_offer.withdrawal_amount_paid} at price {selected_offer.price_per_unit}"
            )
            
            # Get token decimals for normalization
            withdrawal_decimals = int(selected_offer.withdrawal_amount_paid_decimals)
            deposit_decimals = self.web3_client.web3_helper._get_token_decimals(to_token)
            
            # Amount to pay in smallest units (wei) - for on-chain transaction
            withdrawal_amount_paid_wei = Decimal(selected_offer.withdrawal_amount_paid)
            
            # Normalize withdrawal amount: wei / (10 ** decimals)
            withdrawal_amount_paid_normalized = withdrawal_amount_paid_wei / Decimal(10 ** withdrawal_decimals)
            
            # Step 2: Execute trade on-chain based on pricing type
            if selected_offer.pricing_type == PricingType.DYNAMIC_PRICING:
                # For dynamic offers, use depositToWithdrawalRate from SelectedOffer for slippage protection
                if not selected_offer.deposit_to_withdrawal_rate:
                    raise MarketMakerWeb3Exception(
                        f"Dynamic offer {selected_offer.id} missing depositToWithdrawalRate"
                    )
                
                max_rate = Decimal(selected_offer.deposit_to_withdrawal_rate)
                
                tx_hash = await self.web3_client.take_offer_dynamic(
                    offer_id=selected_offer.id,
                    withdrawal_token=from_token,
                    withdrawal_amount_paid=withdrawal_amount_paid_wei,
                    maximum_deposit_to_withdrawal_rate=max_rate,
                    affiliate=affiliate,
                )
            else:  # Fixed pricing
                tx_hash = await self.web3_client.take_offer_fixed(
                    offer_id=selected_offer.id,
                    withdrawal_token=from_token,
                    withdrawal_amount_paid=withdrawal_amount_paid_wei,
                    affiliate=affiliate,
                )
            
            # Calculate amount received:
            # price_per_unit is how much withdrawal token (USDC) you pay per 1 deposit token (RWA)
            # So: deposit_amount = withdrawal_amount / price_per_unit
            # Example: If 1 RWA costs 186.555 USDC, then 1 USDC buys 1/186.555 = 0.00536 RWA
            price_per_unit = Decimal(selected_offer.price_per_unit)
            
            # Calculate deposit amount: how much RWA we receive for the USDC we're paying
            deposit_amount_received_normalized = withdrawal_amount_paid_normalized / price_per_unit if price_per_unit > 0 else Decimal("0")
            
            # Step 3: Create result (with normalized amounts for display)
            result = TradeResult(
                tx_hash=tx_hash,
                order_id=selected_offer.id,
                sell_token_address=from_token,
                sell_amount=withdrawal_amount_paid_normalized,
                buy_token_address=to_token,
                buy_amount=deposit_amount_received_normalized,
                rate=price_per_unit,
                source="market_maker",
                timestamp=datetime.now(),
                network=self.network,
            )
            
            logger.info(
                f"Market Maker trade completed successfully! TX: {tx_hash}"
            )
            
            return result
            
        except NoOffersAvailableException:
            raise
        except MarketMakerWeb3Exception:
            raise
        except Exception as e:
            raise MarketMakerWeb3Exception(f"Trade execution failed: {e}") from e
    
    async def make_offer(
        self,
        sell_token: str,
        sell_amount: Decimal,
        buy_token: str,
        buy_amount: Decimal,
        is_dynamic: bool = False,
        expires_at: Optional[int] = None,
    ) -> TradeResult:
        """Create a new Market Maker offer.
        
        This allows you to become a liquidity provider by creating offers
        that others can take.
        
        Args:
            sell_token: Token you're offering to sell
            sell_amount: Amount you're selling
            buy_token: Token you want to buy
            buy_amount: Amount you want to receive
            is_dynamic: Create dynamic offer (uses price feeds)
            expires_at: Optional expiration timestamp
        
        Returns:
            TradeResult with offer creation details
        
        Raises:
            MarketMakerWeb3Exception: If offer creation fails
        
        Example:
            >>> result = await client.make_offer(
            ...     sell_token="0xRWA...",
            ...     sell_amount=Decimal("10"),
            ...     buy_token="0xUSDC...",
            ...     buy_amount=Decimal("1000")
            ... )
            >>> print(f"Offer created! ID: {result.order_id}")
        """
        logger.info(
            f"Creating Market Maker offer: {sell_amount} {sell_token} -> "
            f"{buy_amount} {buy_token}"
        )
        
        tx_hash, offer_id = await self.web3_client.make_offer(
            deposit_token=sell_token,
            deposit_amount=sell_amount,
            withdraw_token=buy_token,
            withdraw_amount=buy_amount,
            is_dynamic=is_dynamic,
            expires_at=expires_at,
        )
        
        # Calculate rate
        rate = buy_amount / sell_amount if sell_amount > 0 else Decimal("0")
        
        result = TradeResult(
            tx_hash=tx_hash,
            order_id=offer_id,
            sell_token_address=sell_token,
            sell_amount=sell_amount,
            buy_token_address=buy_token,
            buy_amount=buy_amount,
            rate=rate,
            source="market_maker",
            timestamp=datetime.now(),
            network=self.network,
        )
        
        logger.info(f"Offer created successfully! ID: {offer_id}, TX: {tx_hash}")
        
        return result
    
    async def cancel_offer(self, offer_id: str) -> str:
        """Cancel an existing offer.
        
        Only the offer creator can cancel their own offers.
        
        Args:
            offer_id: Offer ID to cancel
        
        Returns:
            Transaction hash
        
        Raises:
            UnauthorizedError: If not the offer creator
            MarketMakerWeb3Exception: If cancellation fails
        
        Example:
            >>> tx_hash = await client.cancel_offer(offer_id="12345")
        """
        logger.info(f"Cancelling offer {offer_id}")
        
        tx_hash = await self.web3_client.cancel_offer(offer_id)
        
        logger.info(f"Offer cancelled successfully! TX: {tx_hash}")
        
        return tx_hash

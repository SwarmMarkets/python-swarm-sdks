"""Cross-Chain Access Stock Trading API client."""

import logging
from datetime import datetime
from typing import Dict, Any
from decimal import Decimal

from _shared.base_client import BaseAPIClient, APIException
from _shared.models import Network
from _shared.config import get_cross_chain_access_api_url, get_internal_worker_id, get_is_dev
from .models import (
    CrossChainAccessQuote,
    AccountStatus,
    AccountFunds,
    OrderSide,
    CrossChainAccessOrderResponse,
)
from .exceptions import (
    QuoteUnavailableException,
    OrderFailedException,
    InvalidSymbolException,
)

logger = logging.getLogger(__name__)


class CrossChainAccessAPIClient(BaseAPIClient):
    """Client for interacting with Cross-Chain Access Stock Trading API.
    
    This client handles all HTTP interactions with the Cross-Chain Access API endpoints
    for stock market trading, including quotes, account status, and order creation.
    Environment (dev/prod) is controlled via SWARM_COLLECTION_MODE env variable.
    
    Example:
        >>> client = CrossChainAccessAPIClient()
        >>> client.set_auth_token(token)
        >>> quote = await client.get_asset_quote("AAPL")
    """

    def __init__(self):
        """Initialize Cross-Chain Access API client.
        
        Environment is determined by SWARM_COLLECTION_MODE env variable.
        """
        super().__init__(base_url=get_cross_chain_access_api_url())
        
        logger.info(
            f"Initialized Cross-Chain Access API client ({'dev' if get_is_dev() else 'prod'} mode)"
        )

    async def get_account_status(self) -> AccountStatus:
        """Get trading account status.

        Returns:
            AccountStatus with trading permissions

        Raises:
            APIException: If request fails or authentication missing
        
        Example:
            >>> status = await client.get_account_status()
            >>> if status.is_trading_allowed():
            ...     print("Trading is allowed")
        """
        if not self.auth_token:
            raise APIException(
                message="Authentication token required for getting account status",
                status_code=401
            )
        
        try:
            response = await self._make_request("GET", "/status")
            attrs = response.get("data", {}).get("attributes", {})
            
            status = AccountStatus(
                account_blocked=attrs.get("account_blocked", False),
                trading_blocked=attrs.get("trading_blocked", False),
                transfers_blocked=attrs.get("transfers_blocked", False),
                trade_suspended_by_user=attrs.get("trade_suspended_by_user", False),
                market_open=attrs.get("market_open", False),
                account_status=attrs.get("account_status", "UNKNOWN"),
            )
            
            logger.debug(f"Account status: {status.account_status}, trading allowed: {status.is_trading_allowed()}")
            
            return status
            
        except APIException as e:
            logger.error(f"Failed to get account status: {e}")
            raise

    async def get_account_funds(self) -> AccountFunds:
        """Get trading account funds and buying power.

        Returns:
            AccountFunds with buying power details

        Raises:
            APIException: If request fails or authentication missing
        
        Example:
            >>> funds = await client.get_account_funds()
            >>> print(f"Buying power: ${funds.buying_power}")
        """
        if not self.auth_token:
            raise APIException(
                message="Authentication token required for getting account funds",
                status_code=401
            )
        
        try:
            response = await self._make_request("GET", "/funds")
            attrs = response.get("data", {}).get("attributes", {})
            
            funds = AccountFunds(
                cash=Decimal(str(attrs.get("cash", 0))),
                buying_power=Decimal(str(attrs.get("buying_power", 0))),
                day_trading_buying_power=Decimal(str(attrs.get("day_trading_buying_power", 0))),
                effective_buying_power=Decimal(str(attrs.get("effective_buying_power", 0))),
                non_margin_buying_power=Decimal(str(attrs.get("non_margin_buying_power", 0))),
                reg_t_buying_power=Decimal(str(attrs.get("reg_t_buying_power", 0))),
            )
            
            logger.debug(f"Account funds - buying power: ${funds.buying_power}")
            
            return funds
            
        except APIException as e:
            logger.error(f"Failed to get account funds: {e}")
            raise

    async def get_asset_quote(self, symbol: str) -> CrossChainAccessQuote:
        """Get real-time quote for a trading symbol.

        Args:
            symbol: Trading symbol (e.g., "AAPL")

        Returns:
            CrossChainAccessQuote with bid/ask prices

        Raises:
            QuoteUnavailableException: If quote cannot be retrieved
            InvalidSymbolException: If symbol is invalid
            APIException: If request fails
        
        Example:
            >>> quote = await client.get_asset_quote("AAPL")
            >>> print(f"Ask: ${quote.ask_price}, Bid: ${quote.bid_price}")
        """
        try:
            params = {
                "symbol": symbol.upper(),
                "currency": "usd",
            }
            
            response = await self._make_request("GET", "/asset-quote", params=params)
            attrs = response.get("data", {}).get("attributes", {})
            
            # Parse timestamp
            timestamp_str = attrs.get("timestamp", "")
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except Exception:
                timestamp = datetime.utcnow()
            
            quote = CrossChainAccessQuote(
                bid_price=Decimal(str(attrs.get("bidPrice", 0))),
                ask_price=Decimal(str(attrs.get("askPrice", 0))),
                bid_size=Decimal(str(attrs.get("bidSize", 0))),
                ask_size=Decimal(str(attrs.get("askSize", 0))),
                timestamp=timestamp,
                bid_exchange=attrs.get("bidExchange", ""),
                ask_exchange=attrs.get("askExchange", ""),
            )
            
            logger.info(
                f"Retrieved quote for {symbol}: "
                f"bid=${quote.bid_price}, ask=${quote.ask_price}"
            )
            
            return quote
            
        except APIException as e:
            if e.status_code == 404:
                raise InvalidSymbolException(
                    f"Invalid trading symbol: {symbol}"
                ) from e
            elif e.status_code == 400:
                raise QuoteUnavailableException(
                    f"Quote unavailable for {symbol}: {e.message}"
                ) from e
            raise QuoteUnavailableException(
                f"Failed to get quote for {symbol}: {e}"
            ) from e

    async def create_order(
        self,
        wallet: str,
        tx_hash: str,
        asset_address: str,
        asset_symbol: str,
        side: OrderSide,
        price: Decimal,
        qty: Decimal,
        notional: Decimal,
        chain_id: int,
        target_chain_id: int,
        user_email: str,
    ) -> CrossChainAccessOrderResponse:
        """Create a trading order on Cross-Chain Access.

        This submits an order after the on-chain token transfer has been completed.
        The tx_hash from the blockchain transfer is required.

        Args:
            wallet: User wallet address
            tx_hash: Blockchain transaction hash (from token transfer)
            asset_address: RWA token contract address
            asset_symbol: Trading symbol (e.g., "AAPL")
            side: Order side (BUY/SELL)
            price: Locked price per unit
            qty: RWA quantity (for SELL) or quantity to receive (for BUY)
            notional: USDC amount
            chain_id: Blockchain network ID
            target_chain_id: Blockhain network ID where user will receive asset (optional, by default chain_id will be used)
            user_email: User email for notifications

        Returns:
            CrossChainAccessOrderResponse with order details

        Raises:
            OrderFailedException: If order creation fails
            APIException: If authentication missing or request fails
        
        Example:
            >>> order = await client.create_order(
            ...     wallet="0x...",
            ...     tx_hash="0xabc...",
            ...     asset_address="0xRWA...",
            ...     asset_symbol="AAPL",
            ...     side=OrderSide.BUY,
            ...     price=Decimal("150.50"),
            ...     qty=Decimal("10"),
            ...     notional=Decimal("1505"),
            ...     chain_id=137,
            ...     target_chain_id=56,
            ...     user_email="user@example.com"
            ... )
        """
        if not self.auth_token:
            raise APIException(
                message="Authentication token required for creating orders",
                status_code=401
            )
        
        try:
            data = {
                "data": {
                    "attributes": {
                        "wallet": wallet.lower(),
                        "tx_hash": tx_hash,
                        "asset": asset_address.lower(),
                        "asset_symbol": asset_symbol.upper(),
                        "side": side.value,
                        "price": float(price),
                        "qty": float(qty),
                        "notional": float(notional),
                        "chain_id": chain_id,
                        "target_chain_id": target_chain_id,
                        "user_email": user_email,
                    }
                }
            }
            
            import json
            
            logger.info(
                f"Creating {side.value} order for {qty} {asset_symbol} "
                f"at ${price} (tx: {tx_hash[:10]}...)"
            )
            
            response = await self._make_request("POST", "/orders", data=data)
            
            # Parse order response
            order_data = response.get("data", {})
            order_attrs = order_data.get("attributes", {})
            
            # Parse timestamps
            created_at_str = order_attrs.get("created_at", "")
            filled_at_str = order_attrs.get("filled_at")
            
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            except Exception:
                created_at = datetime.utcnow()
            
            filled_at = None
            if filled_at_str:
                try:
                    filled_at = datetime.fromisoformat(filled_at_str.replace("Z", "+00:00"))
                except Exception:
                    pass
            
            order = CrossChainAccessOrderResponse(
                order_id=order_data.get("id", "unknown"),
                symbol=order_attrs.get("symbol", asset_symbol),
                side=order_attrs.get("side", side.value),
                quantity=Decimal(str(order_attrs.get("qty", qty))),
                filled_qty=Decimal(str(order_attrs.get("filled_qty", 0))),
                status=order_attrs.get("status", "pending"),
                created_at=created_at,
                filled_at=filled_at,
            )
            
            logger.info(
                f"Order created successfully: {order.order_id} "
                f"(status: {order.status})"
            )
            
            return order
            
        except APIException as e:
            print(e)
            logger.error(f"Failed to create order: {e}")
            raise OrderFailedException(
                f"Order creation failed: {e.message}"
            ) from e

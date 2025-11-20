"""Data models for Cross-Chain Access Stock Trading API."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any
from enum import Enum


class OrderSide(str, Enum):
    """Trading order side."""
    BUY = "buy"
    SELL = "sell"


@dataclass
class CrossChainAccessQuote:
    """Real-time market quote from Cross-Chain Access API.
    
    Attributes:
        bid_price: Best bid price
        ask_price: Best ask price
        bid_size: Size at bid
        ask_size: Size at ask
        timestamp: Quote timestamp
        bid_exchange: Exchange for bid
        ask_exchange: Exchange for ask
    """
    bid_price: Decimal
    ask_price: Decimal
    bid_size: Decimal
    ask_size: Decimal
    timestamp: datetime
    bid_exchange: str = ""
    ask_exchange: str = ""

    def get_price_for_side(self, side: OrderSide) -> Decimal:
        """Get the appropriate price for the order side.
        
        Args:
            side: BUY or SELL
        
        Returns:
            Ask price for buy orders, bid price for sell orders
        """
        return self.ask_price if side == OrderSide.BUY else self.bid_price


@dataclass
class AccountStatus:
    """Trading account status from Cross-Chain Access API.
    
    Attributes:
        account_blocked: Whether account is blocked
        trading_blocked: Whether trading is blocked
        transfers_blocked: Whether transfers are blocked
        trade_suspended_by_user: Whether user suspended trading
        market_open: Whether market is currently open
        account_status: Status string (e.g., "ACTIVE")
    """
    account_blocked: bool
    trading_blocked: bool
    transfers_blocked: bool
    trade_suspended_by_user: bool
    market_open: bool
    account_status: str = "UNKNOWN"

    def is_trading_allowed(self) -> bool:
        """Check if trading is currently allowed.
        
        Returns:
            True if all trading checks pass
        """
        return (
            not self.account_blocked
            and not self.trading_blocked
            and not self.transfers_blocked
            and not self.trade_suspended_by_user
            and self.market_open
        )


@dataclass
class AccountFunds:
    """Trading account funds from Cross-Chain Access API.
    
    Attributes:
        cash: Available cash
        buying_power: Total buying power
        day_trading_buying_power: Day trading buying power
        effective_buying_power: Effective buying power
        non_margin_buying_power: Non-margin buying power
        reg_t_buying_power: Regulation T buying power
    """
    cash: Decimal
    buying_power: Decimal
    day_trading_buying_power: Decimal
    effective_buying_power: Decimal
    non_margin_buying_power: Decimal = Decimal("0")
    reg_t_buying_power: Decimal = Decimal("0")

    def has_sufficient_funds(self, required_amount: Decimal) -> bool:
        """Check if account has sufficient buying power.
        
        Args:
            required_amount: Required USDC amount
        
        Returns:
            True if buying power >= required amount
        """
        return self.buying_power >= required_amount


@dataclass
class CalculatedAmounts:
    """Calculated trade amounts with slippage protection.
    
    Attributes:
        rwa_amount: Amount of RWA tokens
        usdc_amount: Amount of USDC
        price: Locked price per unit
        side: Order side (BUY/SELL)
    """
    rwa_amount: Decimal
    usdc_amount: Decimal
    price: Decimal
    side: OrderSide


@dataclass
class CrossChainAccessTradeParams:
    """Parameters for executing an Cross-Chain Access trade.
    
    Attributes:
        rwa_token_address: RWA token contract address
        rwa_symbol: Trading symbol (e.g., "AAPL")
        order_side: BUY or SELL
        rwa_amount: Amount of RWA tokens
        usdc_amount: Amount of USDC
        locked_price: Price locked for this trade
        user_email: User's email address
    """
    rwa_token_address: str
    rwa_symbol: str
    order_side: OrderSide
    rwa_amount: Decimal
    usdc_amount: Decimal
    locked_price: Decimal
    user_email: str


@dataclass
class CrossChainAccessOrderResponse:
    """Response from Cross-Chain Access order creation.
    
    Attributes:
        order_id: Unique order identifier
        symbol: Trading symbol
        side: Order side
        quantity: Order quantity
        filled_qty: Filled quantity
        status: Order status
        created_at: Creation timestamp
        filled_at: Fill timestamp (if filled)
    """
    order_id: str
    symbol: str
    side: str
    quantity: Decimal
    filled_qty: Decimal
    status: str
    created_at: datetime
    filled_at: datetime | None = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": str(self.quantity),
            "filled_qty": str(self.filled_qty),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
        }

"""Shared models for Swarm Collection."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class Network(Enum):
    """Supported blockchain networks."""
    ETHEREUM = 1
    POLYGON = 137
    BASE = 8453
    BSC = 56


@dataclass
class Quote:
    """
    Unified quote model for trading services.
    
    This model is used by both Cross-Chain Access and Market Maker SDKs to provide
    consistent pricing information.
    
    All amounts are in normalized decimal units (e.g., 1.5 for 1.5 USDC).
    """
    sell_token_address: str
    buy_token_address: str
    sell_amount: Decimal      # Amount to sell (normalized)
    buy_amount: Decimal       # Amount to receive (normalized)
    rate: Decimal             # Exchange rate (buy_amount / sell_amount)
    source: str               # Service that provided quote ("cross_chain_access" or "market_maker")
    timestamp: datetime       # When quote was generated
    
    @property
    def price_per_unit(self) -> Decimal:
        """
        Price of one unit of buy token in terms of sell token.
        
        Returns:
            Decimal: buy_amount / sell_amount
        """
        if self.sell_amount == 0:
            return Decimal(0)
        return self.buy_amount / self.sell_amount
    
    @property
    def inverse_rate(self) -> Decimal:
        """
        Inverse exchange rate (sell_amount / buy_amount).
        
        Useful for displaying price in opposite direction.
        """
        if self.buy_amount == 0:
            return Decimal(0)
        return self.sell_amount / self.buy_amount
    
    def __str__(self) -> str:
        """Human-readable quote representation."""
        return (
            f"Quote({self.source}): "
            f"Sell {self.sell_amount} → Buy {self.buy_amount} "
            f"(rate: {self.rate:.6f})"
        )


@dataclass
class TradeResult:
    """
    Result of a completed trade.
    
    This model captures the outcome of a trade execution,
    including on-chain transaction details and order information.
    """
    tx_hash: str                  # Blockchain transaction hash
    order_id: Optional[str]       # Order ID (if applicable)
    sell_token_address: str
    buy_token_address: str
    sell_amount: Decimal          # Actual amount sold (normalized)
    buy_amount: Decimal           # Actual amount received (normalized)
    rate: Decimal                 # Execution rate
    source: str                   # Service used ("cross_chain_access" or "market_maker")
    timestamp: datetime           # Execution timestamp
    network: Network              # Blockchain network
    status: str = "completed"     # Trade status
    
    def __str__(self) -> str:
        """Human-readable trade result."""
        return (
            f"Trade({self.source}): "
            f"Sold {self.sell_amount} for {self.buy_amount} "
            f"on {self.network.name} "
            f"(tx: {self.tx_hash[:10]}...)"
        )

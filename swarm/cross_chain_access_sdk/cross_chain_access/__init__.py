"""Cross-Chain Access API client package."""

from .client import CrossChainAccessAPIClient
from .models import (
    CrossChainAccessQuote,
    AccountStatus,
    AccountFunds,
    CalculatedAmounts,
    CrossChainAccessTradeParams,
    CrossChainAccessOrderResponse,
    OrderSide,
)
from .exceptions import (
    CrossChainAccessException,
    MarketClosedException,
    AccountBlockedException,
    InsufficientFundsException,
    QuoteUnavailableException,
    OrderFailedException,
    InvalidSymbolException,
)

__all__ = [
    # Client
    "CrossChainAccessAPIClient",
    # Models
    "CrossChainAccessQuote",
    "AccountStatus",
    "AccountFunds",
    "CalculatedAmounts",
    "CrossChainAccessTradeParams",
    "CrossChainAccessOrderResponse",
    "OrderSide",
    # Exceptions
    "CrossChainAccessException",
    "MarketClosedException",
    "AccountBlockedException",
    "InsufficientFundsException",
    "QuoteUnavailableException",
    "OrderFailedException",
    "InvalidSymbolException",
]

"""Exceptions for Cross-Chain Access trading operations."""


class CrossChainAccessException(Exception):
    """Base exception for Cross-Chain Access errors."""
    pass


class MarketClosedException(CrossChainAccessException):
    """Raised when attempting to trade outside market hours."""
    pass


class AccountBlockedException(CrossChainAccessException):
    """Raised when account is blocked from trading."""
    pass


class InsufficientFundsException(CrossChainAccessException):
    """Raised when account has insufficient buying power."""
    pass


class QuoteUnavailableException(CrossChainAccessException):
    """Raised when quote cannot be retrieved."""
    pass


class OrderFailedException(CrossChainAccessException):
    """Raised when order submission fails."""
    pass


class InvalidSymbolException(CrossChainAccessException):
    """Raised when trading symbol is invalid."""
    pass

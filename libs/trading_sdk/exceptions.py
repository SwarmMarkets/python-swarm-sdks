"""Exceptions for Trading SDK."""


class TradingException(Exception):
    """Base exception for Trading SDK errors."""
    pass


class NoLiquidityException(TradingException):
    """Raised when no liquidity available on any platform."""
    pass


class AllPlatformsFailedException(TradingException):
    """Raised when all trading platforms fail."""
    pass


class InvalidRoutingStrategyException(TradingException):
    """Raised when routing strategy is invalid."""
    pass

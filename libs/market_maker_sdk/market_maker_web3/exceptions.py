"""Exceptions for Market Maker Web3 operations."""


class MarketMakerWeb3Exception(Exception):
    """Base exception for Market Maker Web3 errors."""
    pass


class OfferNotFoundError(MarketMakerWeb3Exception):
    """Raised when offer doesn't exist on-chain."""
    pass


class OfferInactiveError(MarketMakerWeb3Exception):
    """Raised when trying to take an inactive offer."""
    pass


class InsufficientOfferBalanceError(MarketMakerWeb3Exception):
    """Raised when offer maker has insufficient balance."""
    pass


class OfferExpiredError(MarketMakerWeb3Exception):
    """Raised when offer has expired."""
    pass


class UnauthorizedError(MarketMakerWeb3Exception):
    """Raised when caller is not authorized for operation."""
    pass

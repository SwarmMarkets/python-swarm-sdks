"""Exceptions for Market Maker RPQ Service."""


class RPQServiceException(Exception):
    """Base exception for RPQ Service errors."""
    pass


class NoOffersAvailableException(RPQServiceException):
    """Raised when no offers are available for the requested pair."""
    pass


class InvalidTokenPairException(RPQServiceException):
    """Raised when token pair is not supported."""
    pass


class QuoteUnavailableException(RPQServiceException):
    """Raised when quote cannot be generated."""
    pass


class PriceFeedNotFoundException(RPQServiceException):
    """Raised when price feed is not found."""
    pass

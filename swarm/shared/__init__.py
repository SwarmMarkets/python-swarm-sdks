"""Shared package for Swarm Collection SDKs."""

from .models import Network, Quote, TradeResult
from .base_client import BaseAPIClient, APIException
from .constants import USDC_ADDRESSES, TOKEN_DECIMALS
from .swarm_auth import (
    SwarmAuth,
    AuthTokens,
    InMemoryStorage,
    TokenStorageInterface,
    SigningTimeoutError,
    AuthenticationError,
)
from .web3 import (
    Web3Helper,
    Web3Exception,
    InsufficientBalanceException,
    TransactionFailedException,
    InsufficientAllowanceException,
    NetworkNotSupportedException,
)

__all__ = [
    # Models
    "Network",
    "Quote", 
    "TradeResult",
    # Base client
    "BaseAPIClient",
    "APIException",
    # Constants
    "USDC_ADDRESSES",
    "TOKEN_DECIMALS",
    # Authentication
    "SwarmAuth",
    "AuthTokens",
    "InMemoryStorage",
    "TokenStorageInterface",
    "SigningTimeoutError",
    "AuthenticationError",
    # Web3
    "Web3Helper",
    "Web3Exception",
    "InsufficientBalanceException",
    "TransactionFailedException",
    "InsufficientAllowanceException",
    "NetworkNotSupportedException",
]

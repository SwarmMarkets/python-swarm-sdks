"""Market Maker SDK - Decentralized OTC trading for Swarm RWAs.

This SDK provides a unified interface for trading Real World Assets (RWAs)
through Swarm's decentralized Market Maker platform, combining:
- RPQ Service API for offer discovery and quotes
- Web3 smart contract interactions for on-chain execution

Example:
    >>> from market_maker_sdk import MarketMakerClient
    >>> from shared.models import Network
    >>> from decimal import Decimal
    >>> 
    >>> async with MarketMakerClient(
    ...     network=Network.POLYGON,
    ...     private_key="0x...",
    ...     rpq_api_key="your-key",
    ...     user_email="user@example.com"
    ... ) as client:
    ...     # Get a quote
    ...     quote = await client.get_quote(
    ...         from_token="0xUSDC...",
    ...         to_token="0xRWA...",
    ...         from_amount=Decimal("100")
    ...     )
    ...     
    ...     # Execute trade
    ...     result = await client.trade(
    ...         from_token="0xUSDC...",
    ...         to_token="0xRWA...",
    ...         from_amount=Decimal("100")
    ...     )
    ...     print(f"Trade successful! TX: {result.tx_hash}")
"""

from .sdk import MarketMakerClient
from .rpq_service import (
    RPQClient,
    Offer,
    BestOffersResponse,
    BestOffersResult,
    SelectedOffer,
    PriceFeedsResponse,
    QuoteRequest,
    QuoteResponse,
    OfferType,
    OfferStatus,
    Asset,
    OfferPrice,
    PricingType,
    PercentageType,
    AssetType,
)
from .market_maker_web3 import (
    MarketMakerWeb3Client,
    MarketMakerWeb3Exception,
    OfferNotFoundError,
    OfferInactiveError,
)

__version__ = "0.1.0"

__all__ = [
    # Main client
    "MarketMakerClient",
    # RPQ Service
    "RPQClient",
    "Offer",
    "BestOffersResponse",
    "BestOffersResult",
    "SelectedOffer",
    "PriceFeedsResponse",
    "QuoteRequest",
    "QuoteResponse",
    "OfferType",
    "OfferStatus",
    "Asset",
    "OfferPrice",
    "PricingType",
    "PercentageType",
    "AssetType",
    # Web3
    "MarketMakerWeb3Client",
    "MarketMakerWeb3Exception",
    "OfferNotFoundError",
    "OfferInactiveError",
]

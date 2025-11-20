"""Data models for Market Maker RPQ Service API responses."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
from decimal import Decimal


class OfferType(str, Enum):
    """Offer type enumeration."""
    PARTIAL_OFFER = "PartialOffer"
    BLOCK_OFFER = "BlockOffer"


class OfferStatus(str, Enum):
    """Offer status enumeration."""
    NOT_TAKEN = "NotTaken"
    PARTIALLY_TAKEN = "PartiallyTaken"
    TAKEN = "Taken"


class PricingType(str, Enum):
    """Pricing type enumeration."""
    FIXED_PRICING = "FixedPricing"
    DYNAMIC_PRICING = "DynamicPricing"


class PercentageType(str, Enum):
    """Percentage type enumeration."""
    PLUS = "Plus"
    MINUS = "Minus"


class AssetType(str, Enum):
    """Asset type enumeration."""
    SECURITY = "Security"
    NO_TYPE = "NoType"
    GOLD = "Gold"


@dataclass
class OfferPrice:
    """Represents offer pricing information.
    
    Attributes:
        id: Price ID
        percentage: Percentage adjustment (optional)
        percentage_type: Plus or Minus (optional)
        pricing_type: Fixed or Dynamic pricing
        unit_price: Fixed unit price (optional)
        deposit_asset_price: Deposit asset price feed info (optional)
        withdrawal_asset_price: Withdrawal asset price feed info (optional)
    """
    id: str
    pricing_type: PricingType
    percentage: Optional[float] = None
    percentage_type: Optional[PercentageType] = None
    unit_price: Optional[str] = None
    deposit_asset_price: Optional[Dict[str, str]] = None
    withdrawal_asset_price: Optional[Dict[str, str]] = None


@dataclass
class Asset:
    """Represents an asset in an offer.
    
    Attributes:
        id: Asset ID
        name: Asset name
        symbol: Asset symbol
        address: Contract address
        decimals: Token decimals (optional)
        token_id: Token ID for NFTs (optional)
        asset_type: Type of asset
        kya: KYA identifier (optional)
        token_standard: Token standard (e.g., "ERC20")
        traded_volume: Total traded volume
    """
    id: str
    name: str
    symbol: str
    address: str
    token_standard: str
    traded_volume: str
    asset_type: AssetType = AssetType.NO_TYPE
    decimals: Optional[int] = None
    token_id: Optional[int] = None
    kya: Optional[str] = None


@dataclass
class Offer:
    """Represents a Market Maker offer from RPQ API.
    
    Attributes:
        id: Unique offer identifier
        maker: Wallet address of offer creator
        amount_in: Amount of deposit asset (in smallest units)
        amount_out: Amount of withdrawal asset (in smallest units)
        available_amount: Available amount for partial fills
        deposit_asset: Asset being deposited (sold)
        withdrawal_asset: Asset being withdrawn (bought)
        offer_type: PartialOffer or BlockOffer
        offer_status: Current offer status
        offer_price: Pricing information
        is_auth: Whether offer requires authorization
        terms: Offer terms (optional)
        timelock_period: Timelock period in seconds
        comms_link: Communication link (optional)
        authorization_addresses: List of authorized addresses (optional)
        expiry_timestamp: Expiration timestamp
        deposit_to_withdrawal_rate: Exchange rate (optional)
    """
    id: str
    maker: str
    amount_in: str
    amount_out: str
    available_amount: str
    deposit_asset: Asset
    withdrawal_asset: Asset
    offer_type: OfferType
    offer_status: OfferStatus
    offer_price: OfferPrice
    is_auth: bool
    timelock_period: str
    expiry_timestamp: str
    terms: Optional[Any] = None
    comms_link: Optional[str] = None
    authorization_addresses: Optional[List[str]] = None
    deposit_to_withdrawal_rate: Optional[str] = None


@dataclass
class SelectedOffer:
    """Represents a selected offer in best offers response.
    
    Attributes:
        id: Offer ID
        withdrawal_amount_paid: Amount paid in withdrawal asset (what taker pays) in smallest units (wei)
        withdrawal_amount_paid_decimals: Number of decimals for the withdrawal token (e.g., 6 for USDC, 18 for ETH)
        offer_type: PartialOffer or BlockOffer
        maker: Maker address
        price_per_unit: Price per unit (deposit tokens per withdrawal token, in wei)
        pricing_type: Fixed or Dynamic pricing
        deposit_to_withdrawal_rate: Exchange rate for dynamic offers (optional, in withdrawal token decimals)
    """
    id: str
    withdrawal_amount_paid: str
    withdrawal_amount_paid_decimals: str
    offer_type: OfferType
    maker: str
    price_per_unit: str
    pricing_type: PricingType
    deposit_to_withdrawal_rate: Optional[str] = None


@dataclass
class BestOffersResult:
    """Result from best offers endpoint.
    
    Attributes:
        success: Whether the operation was successful
        target_amount: Target amount requested
        total_withdrawal_amount_paid: Total withdrawal amount that will be paid
        selected_offers: List of selected offers
        mode: Whether this is a buy or sell operation
    """
    success: bool
    target_amount: str
    total_withdrawal_amount_paid: str
    selected_offers: List[SelectedOffer]
    mode: str  # "buy" or "sell"


@dataclass
class BestOffersResponse:
    """Response from best offers endpoint.
    
    Attributes:
        success: Whether the API call was successful
        result: Best offers result
    """
    success: bool
    result: BestOffersResult


@dataclass
class PriceFeed:
    """Represents a price feed for dynamic offers.
    
    Attributes:
        contract_address: Asset contract address
        price_feed_address: Price feed contract address
    """
    contract_address: str
    price_feed_address: str


@dataclass
class PriceFeedsResponse:
    """Response from price feeds endpoint.
    
    Attributes:
        success: Whether the API call was successful
        price_feeds: Dictionary mapping contract addresses to price feed addresses
    """
    success: bool
    price_feeds: Dict[str, str]


@dataclass
class QuoteRequest:
    """Request parameters for getting a quote.
    
    Attributes:
        buy_asset_address: Address of asset to buy
        sell_asset_address: Address of asset to sell
        network: Network name (polygon, base, ethereum)
        target_sell_amount: Amount to sell (optional, human-readable)
        target_buy_amount: Amount to buy (optional, human-readable)
    """
    buy_asset_address: str
    sell_asset_address: str
    network: str = "polygon"
    target_sell_amount: Optional[str] = None
    target_buy_amount: Optional[str] = None


@dataclass
class QuoteResponse:
    """Response from quote endpoint.
    
    Attributes:
        success: Whether sufficient liquidity is available
        buy_asset_address: Address of asset to buy
        sell_asset_address: Address of asset to sell
        sell_amount: Amount to sell (optional)
        buy_amount: Amount to buy in smallest units (optional)
        average_price: Average price per unit across all offers
    """
    success: bool
    buy_asset_address: str
    sell_asset_address: str
    average_price: str
    sell_amount: Optional[str] = None
    buy_amount: Optional[str] = None

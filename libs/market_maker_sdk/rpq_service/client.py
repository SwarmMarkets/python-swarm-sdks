"""RPQ Service API client for Market Maker offers and quotes."""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
import logging

from _shared.base_client import BaseAPIClient, APIException
from _shared.models import Quote
from .models import (
    Offer,
    BestOffersResponse,
    BestOffersResult,
    SelectedOffer,
    PriceFeedsResponse,
    QuoteRequest,
    QuoteResponse,
    OfferType,
    OfferStatus,
    OfferPrice,
    Asset,
    PricingType,
    PercentageType,
    AssetType,
)
from .exceptions import (
    RPQServiceException,
    NoOffersAvailableException,
    InvalidTokenPairException,
    QuoteUnavailableException,
    PriceFeedNotFoundException,
)

logger = logging.getLogger(__name__)


class RPQClient(BaseAPIClient):
    """Client for interacting with Market Maker RPQ Service API.
    
    Provides methods to:
    - Get all offers for a token pair
    - Get best offers (optimal buy/sell)
    - Get quotes for trading
    - Get price feeds for dynamic offers
    
    Attributes:
        network: Network name (polygon, base, ethereum)
        api_key: API key for RPQ service authentication
    
    Example:
        >>> client = RPQClient(network="polygon", api_key="your-api-key")
        >>> offers = await client.get_offers(
        ...     buy_asset_address="0x...",
        ...     sell_asset_address="0x..."
        ... )
    """
    
    BASE_URL = "https://rfq.swarm.com/v1/client"
    
    def __init__(self, network: str = "polygon", api_key: Optional[str] = None):
        """Initialize RPQ client.
        
        Args:
            network: Network name (polygon, base, ethereum). Default: polygon
            api_key: API key for authentication (required for some endpoints)
        """
        super().__init__(base_url=self.BASE_URL)
        self.network = network
        self.api_key = api_key
        
        # Set API key in headers if provided
        if api_key:
            self._headers["X-API-Key"] = api_key
    
    async def get_offers(
        self,
        buy_asset_address: Optional[str] = None,
        sell_asset_address: Optional[str] = None,
        page: int = 0,
        limit: int = 100,
    ) -> List[Offer]:
        """Get all available offers filtered by network and optionally by assets.
        
        Args:
            buy_asset_address: Filter by asset to buy (optional)
            sell_asset_address: Filter by asset to sell (optional)
            page: Page number (default: 0)
            limit: Number of offers per page (default: 100)
        
        Returns:
            List of matching offers
        
        Raises:
            NoOffersAvailableException: If no offers found
            APIException: If API request fails (requires X-API-Key header)
        
        Example:
            >>> offers = await client.get_offers(
            ...     buy_asset_address="0x7ceB23fd6bc0add59E62ac25578270cFf1b9f619",
            ...     sell_asset_address="0x3c499c542cef5E3811e1192ce70d8cC03d5c3359",
            ...     limit=10
            ... )
        """
        if not self.api_key:
            raise RPQServiceException("API key is required for get_offers endpoint")
        
        try:
            params: Dict[str, Any] = {
                "network": self.network,
                "page": page,
                "limit": limit,
            }
            
            if buy_asset_address:
                params["buyAssetAddress"] = buy_asset_address.lower()
            
            if sell_asset_address:
                params["sellAssetAddress"] = sell_asset_address.lower()
            
            response = await self._make_request("GET", "/dotc_offers", params=params)
            
            # Parse offers from response
            offers_data = response.get("offers", [])
            
            if not offers_data:
                raise NoOffersAvailableException(
                    f"No offers available for the given parameters on network {self.network}"
                )
            
            offers = []
            for offer_dict in offers_data:
                offer = self._parse_offer(offer_dict)
                offers.append(offer)
            
            logger.info(
                f"Retrieved {len(offers)} offers on {self.network}"
            )
            
            return offers
            
        except APIException as e:
            if e.status_code == 401:
                raise RPQServiceException("Invalid or missing API key") from e
            elif e.status_code == 429:
                raise RPQServiceException("Monthly rate limit reached") from e
            raise RPQServiceException(f"Failed to get offers: {e}") from e
    
    async def get_best_offers(
        self,
        buy_asset_address: str,
        sell_asset_address: str,
        target_sell_amount: Optional[str] = None,
        target_buy_amount: Optional[str] = None,
    ) -> BestOffersResponse:
        """Get the best sequence of offers to reach a target amount.
        
        Given a pair of tokens and a target amount, finds the optimal combination
        of offers that covers the target amount while maximizing efficiency.
        
        Args:
            buy_asset_address: Address of asset to buy (receive)
            sell_asset_address: Address of asset to sell (give up)
            target_sell_amount: Target amount to sell in normal decimal units (optional)
            target_buy_amount: Target amount to buy in normal decimal units (optional)
        
        Returns:
            BestOffersResponse with selected offers and amounts
        
        Raises:
            NoOffersAvailableException: If no offers available
            ValueError: If both or neither target amounts are specified
            APIException: If API request fails
        
        Example:
            >>> best = await client.get_best_offers(
            ...     buy_asset_address="0x7ceB23fd6bc0add59E62ac25578270cFf1b9f619",
            ...     sell_asset_address="0x3c499c542cef5E3811e1192ce70d8cC03d5c3359",
            ...     target_sell_amount="100"
            ... )
            >>> print(f"Total taken: {best.result.total_withdrawal_amount_paid}")
        """
        # Validate that exactly one target amount is specified
        if target_sell_amount and target_buy_amount:
            raise ValueError("Specify either target_sell_amount OR target_buy_amount, not both")
        
        if not target_sell_amount and not target_buy_amount:
            raise ValueError("Must specify either target_sell_amount OR target_buy_amount")
        
        try:
            params: Dict[str, Any] = {
                "network": self.network,
                "buyAssetAddress": buy_asset_address.lower(),
                "sellAssetAddress": sell_asset_address.lower(),
            }
            
            if target_sell_amount:
                params["targetSellAmount"] = target_sell_amount
            
            if target_buy_amount:
                params["targetBuyAmount"] = target_buy_amount
            
            response = await self._make_request("GET", "/dotc_offers/best", params=params)
            
            # Parse response
            result_data = response.get("result", {})
            
            if not result_data:
                raise NoOffersAvailableException(
                    f"No offers available for {sell_asset_address} -> {buy_asset_address}"
                )
            
            # Parse selected offers
            selected_offers = []
            for offer_dict in result_data.get("selectedOffers", []):
                selected_offer = SelectedOffer(
                    id=offer_dict["id"],
                    withdrawal_amount_paid=offer_dict["withdrawalAmountPaid"],
                    withdrawal_amount_paid_decimals=offer_dict["withdrawalAmountPaidDecimals"],
                    offer_type=OfferType(offer_dict["offerType"]),
                    maker=offer_dict["maker"],
                    price_per_unit=offer_dict["pricePerUnit"],
                    pricing_type=PricingType(offer_dict["pricingType"]),
                    deposit_to_withdrawal_rate=offer_dict.get("depositToWithdrawalRate"),
                )
                selected_offers.append(selected_offer)
            
            result = BestOffersResult(
                success=result_data["success"],
                target_amount=result_data["targetAmount"],
                total_withdrawal_amount_paid=result_data["totalWithdrawalAmountPaid"],
                selected_offers=selected_offers,
                mode=result_data["mode"],
            )
            
            best_offers_response = BestOffersResponse(
                success=response["success"],
                result=result,
            )
            
            logger.info(
                f"Retrieved best offers for {sell_asset_address} -> {buy_asset_address}: "
                f"{result.total_withdrawal_amount_paid}/{result.target_amount}"
            )
            
            return best_offers_response
            
        except APIException as e:
            if e.status_code == 400:
                raise RPQServiceException(f"Invalid request parameters: {e.message}") from e
            raise RPQServiceException(f"Failed to get best offers: {e}") from e
    
    async def _request_quote(self, quote_request: QuoteRequest) -> QuoteResponse:
        """Get a raw quote from RPQ API.
        
        Private method that returns the raw RPQ API response.
        For SDK usage, prefer the public get_quote() method instead.
        
        Provide either target_sell_amount OR target_buy_amount, not both.
        The service will calculate the best price based on available offers.
        
        Args:
            quote_request: Quote parameters
        
        Returns:
            QuoteResponse with calculated amounts and average price
        
        Raises:
            QuoteUnavailableException: If quote cannot be generated
            APIException: If API request fails (requires X-API-Key header)
        """
        if not self.api_key:
            raise RPQServiceException("API key is required for get_quote endpoint")
        
        try:
            # Validate request
            if quote_request.target_sell_amount and quote_request.target_buy_amount:
                raise ValueError(
                    "Provide either target_sell_amount OR target_buy_amount, not both"
                )
            
            params: Dict[str, Any] = {
                "buyAssetAddress": quote_request.buy_asset_address.lower(),
                "sellAssetAddress": quote_request.sell_asset_address.lower(),
                "network": quote_request.network,
            }
            
            if quote_request.target_sell_amount:
                params["targetSellAmount"] = quote_request.target_sell_amount
            
            if quote_request.target_buy_amount:
                params["targetBuyAmount"] = quote_request.target_buy_amount
            
            response = await self._make_request("GET", "/dotc_offers/quote", params=params)
            
            # Parse quote response
            quote_response = QuoteResponse(
                success=response["success"],
                buy_asset_address=response["buyAssetAddress"],
                sell_asset_address=response["sellAssetAddress"],
                average_price=response["averagePrice"],
                sell_amount=response.get("sellAmount"),
                buy_amount=response.get("buyAmount"),
            )
            
            logger.info(
                f"Retrieved quote: {quote_response.sell_amount or 'N/A'} "
                f"{quote_request.sell_asset_address} -> "
                f"{quote_response.buy_amount or 'N/A'} {quote_request.buy_asset_address}"
            )
            
            return quote_response
            
        except APIException as e:
            if e.status_code == 400:
                raise QuoteUnavailableException(
                    f"Quote unavailable: {e.message}"
                ) from e
            elif e.status_code == 401:
                raise RPQServiceException("Invalid or missing API key") from e
            elif e.status_code == 429:
                raise RPQServiceException("Monthly rate limit reached") from e
            raise RPQServiceException(f"Failed to get quote: {e}") from e
    
    async def get_price_feeds(self) -> PriceFeedsResponse:
        """Get all available price feeds for the network.
        
        Price feeds are used to create dynamic offers.
        
        Returns:
            PriceFeedsResponse with mapping of contract addresses to price feed addresses
        
        Raises:
            PriceFeedNotFoundException: If no feeds found
            APIException: If API request fails
        
        Example:
            >>> feeds = await client.get_price_feeds()
            >>> print(f"Found {len(feeds.price_feeds)} price feeds")
            >>> # Get price feed for USDC
            >>> usdc_feed = feeds.price_feeds.get("0x3c499c542cef5e3811e1192ce70d8cc03d5c3359")
        """
        try:
            params: Dict[str, Any] = {
                "network": self.network,
            }
            
            response = await self._make_request("GET", "/all_price_feeds", params=params)
            
            price_feeds = response.get("priceFeeds", {})
            
            if not price_feeds:
                raise PriceFeedNotFoundException(
                    f"No price feeds found for network {self.network}"
                )
            
            price_feeds_response = PriceFeedsResponse(
                success=response["success"],
                price_feeds=price_feeds,
            )
            
            logger.info(f"Retrieved {len(price_feeds)} price feeds for {self.network}")
            
            return price_feeds_response
            
        except APIException as e:
            raise RPQServiceException(f"Failed to get price feeds: {e}") from e
    
    def _parse_offer(self, offer_dict: Dict[str, Any]) -> Offer:
        """Parse offer dictionary into Offer dataclass.
        
        Args:
            offer_dict: Raw offer data from API
        
        Returns:
            Parsed Offer object
        """
        # Parse deposit asset
        deposit_asset_data = offer_dict["depositAsset"]
        deposit_asset = Asset(
            id=deposit_asset_data["id"],
            name=deposit_asset_data["name"],
            symbol=deposit_asset_data["symbol"],
            address=deposit_asset_data["address"],
            token_standard=deposit_asset_data["tokenStandard"],
            traded_volume=deposit_asset_data["tradedVolume"],
            asset_type=AssetType(deposit_asset_data.get("assetType", "NoType")),
            decimals=deposit_asset_data.get("decimals"),
            token_id=deposit_asset_data.get("tokenId"),
            kya=deposit_asset_data.get("kya"),
        )
        
        # Parse withdrawal asset
        withdrawal_asset_data = offer_dict["withdrawalAsset"]
        withdrawal_asset = Asset(
            id=withdrawal_asset_data["id"],
            name=withdrawal_asset_data["name"],
            symbol=withdrawal_asset_data["symbol"],
            address=withdrawal_asset_data["address"],
            token_standard=withdrawal_asset_data["tokenStandard"],
            traded_volume=withdrawal_asset_data["tradedVolume"],
            asset_type=AssetType(withdrawal_asset_data.get("assetType", "NoType")),
            decimals=withdrawal_asset_data.get("decimals"),
            token_id=withdrawal_asset_data.get("tokenId"),
            kya=withdrawal_asset_data.get("kya"),
        )
        
        # Parse offer price
        offer_price_data = offer_dict["offerPrice"]
        offer_price = OfferPrice(
            id=offer_price_data["id"],
            pricing_type=PricingType(offer_price_data["pricingType"]),
            percentage=offer_price_data.get("percentage"),
            percentage_type=(
                PercentageType(offer_price_data["percentageType"])
                if offer_price_data.get("percentageType")
                else None
            ),
            unit_price=offer_price_data.get("unitPrice"),
            deposit_asset_price=offer_price_data.get("depositAssetPrice"),
            withdrawal_asset_price=offer_price_data.get("withdrawalAssetPrice"),
        )
        
        return Offer(
            id=offer_dict["id"],
            maker=offer_dict["maker"],
            amount_in=offer_dict["amountIn"],
            amount_out=offer_dict["amountOut"],
            available_amount=offer_dict["availableAmount"],
            deposit_asset=deposit_asset,
            withdrawal_asset=withdrawal_asset,
            offer_type=OfferType(offer_dict["offerType"]),
            offer_status=OfferStatus(offer_dict["offerStatus"]),
            offer_price=offer_price,
            is_auth=offer_dict["isAuth"],
            timelock_period=offer_dict["timelockPeriod"],
            expiry_timestamp=offer_dict["expiryTimestamp"],
            terms=offer_dict.get("terms"),
            comms_link=offer_dict.get("commsLink"),
            authorization_addresses=offer_dict.get("authorizationAddresses"),
            deposit_to_withdrawal_rate=offer_dict.get("depositToWithdrawalRate"),
        )
    
    async def get_quote(
        self,
        buy_asset_address: str,
        sell_asset_address: str,
        target_sell_amount: Optional[str] = None,
        target_buy_amount: Optional[str] = None,
    ) -> Quote:
        """Get a quote for trading tokens.
        
        Returns a quote in the SDK's unified Quote format.
        Provide either target_sell_amount OR target_buy_amount, not both.
        
        Args:
            buy_asset_address: Address of asset to buy
            sell_asset_address: Address of asset to sell
            target_sell_amount: Amount to sell (optional, human-readable)
            target_buy_amount: Amount to buy (optional, human-readable)
        
        Returns:
            Quote in SDK format with calculated amounts and rate
        
        Raises:
            QuoteUnavailableException: If quote cannot be generated
            ValueError: If both or neither amounts are specified
            APIException: If API request fails
        
        Example:
            >>> quote = await client.get_quote(
            ...     buy_asset_address="0x7ceB23fd6bc0add59E62ac25578270cFf1b9f619",
            ...     sell_asset_address="0x3c499c542cef5E3811e1192ce70d8cC03d5c3359",
            ...     target_sell_amount="100"
            ... )
            >>> print(f"You'll receive: {quote.buy_amount} tokens")
        """
        request = QuoteRequest(
            buy_asset_address=buy_asset_address,
            sell_asset_address=sell_asset_address,
            target_sell_amount=target_sell_amount,
            target_buy_amount=target_buy_amount,
            network=self.network,
        )
        
        rpq_quote = await self._request_quote(request)
        
        # Convert amounts to Decimal (they are in human-readable format from API)
        sell_amount = Decimal(rpq_quote.sell_amount) if rpq_quote.sell_amount else Decimal("0")
        buy_amount = Decimal(rpq_quote.buy_amount) if rpq_quote.buy_amount else Decimal("0")
        
        # Calculate rate from normalized amounts (buy_amount / sell_amount)
        # Don't use average_price directly as it may be in wei units
        rate = buy_amount / sell_amount if sell_amount > 0 else Decimal("0")
        
        # Convert to SDK Quote format
        # For Market Maker: sell token = deposit token, buy token = withdrawal token
        return Quote(
            sell_token_address=rpq_quote.sell_asset_address,
            sell_amount=sell_amount,
            buy_token_address=rpq_quote.buy_asset_address,
            buy_amount=buy_amount,
            rate=rate,
            source="Market Maker RPQ",
            timestamp=datetime.now(),  # Use current time since API doesn't return it
        )

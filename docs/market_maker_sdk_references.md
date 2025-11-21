# Market Maker SDK API Documentation

## Table of Contents

### Core Classes

- [MarketMakerClient](#marketmakerclient) - Main SDK entry point
  - [Constructor](#constructor)
  - [authenticate()](#authenticate)
  - [get_quote()](#get_quote)
  - [trade()](#trade)
  - [make_offer()](#make_offer)
  - [cancel_offer()](#cancel_offer)
  - [close()](#close)
- [RPQClient](#rpqclient) - RPQ Service API client
  - [Constructor](#constructor-1)
  - [get_offers()](#get_offers)
  - [get_best_offers()](#get_best_offers)
  - [get_quote()](#get_quote-1)
  - [get_price_feeds()](#get_price_feeds)
- [MarketMakerWeb3Client](#marketmakerweb3client) - Smart contract client
  - [Constructor](#constructor-2)
  - [take_offer_fixed()](#take_offer_fixed)
  - [take_offer_dynamic()](#take_offer_dynamic)
  - [make_offer()](#make_offer-1)
  - [cancel_offer()](#cancel_offer-1)
  - [get_offer_details()](#get_offer_details)

### Data Models

- [Offer](#offer)
- [SelectedOffer](#selectedoffer)
- [BestOffersResponse](#bestoffersresponse)
- [Quote](#quote)
- [QuoteResponse](#quoteresponse)
- [TradeResult](#traderesult)
- [Asset](#asset)
- [OfferPrice](#offerprice)
- [PriceFeedsResponse](#pricefeedsresponse)

### Enumerations

- [OfferType](#offertype)
- [OfferStatus](#offerstatus)
- [PricingType](#pricingtype)
- [PercentageType](#percentagetype)
- [AssetType](#assettype)

### Exceptions

- [Exception Hierarchy](#exception-hierarchy)
- [RPQServiceException](#rpqserviceexception)
- [NoOffersAvailableException](#nooffersavailableexception)
- [QuoteUnavailableException](#quoteunavailableexception)
- [InvalidTokenPairException](#invalidtokenpairexception)
- [PriceFeedNotFoundException](#pricefeednotfoundexception)
- [MarketMakerWeb3Exception](#marketmakerweb3exception)
- [OfferNotFoundError](#offernotfounderror)
- [OfferInactiveError](#offerinactiveerror)
- [InsufficientOfferBalanceError](#insufficientofferbalanceerror)
- [OfferExpiredError](#offerexpirederror)
- [UnauthorizedError](#unauthorizederror)

### Additional Resources

- [Supported Networks](#supported-networks)
- [Contract Addresses](#contract-addresses)

---

## MarketMakerClient

**Location**: `swarm/market_maker_sdk/sdk/client.py`

The main entry point for Market Maker trading operations. Orchestrates authentication, quote discovery via RPQ Service, and on-chain execution via smart contracts.

### Constructor

```python
MarketMakerClient(
    network: Network,
    private_key: str,
    rpq_api_key: str,
    user_email: Optional[str] = None,
    rpc_url: Optional[str] = None,
)
```

**Parameters**:

| Parameter     | Type      | Required | Description                                        |
| ------------- | --------- | -------- | -------------------------------------------------- |
| `network`     | `Network` | ✅       | Blockchain network (e.g., `Network.POLYGON`)       |
| `private_key` | `str`     | ✅       | Wallet private key (with `0x` prefix)              |
| `rpq_api_key` | `str`     | ✅       | API key for RPQ Service                            |
| `user_email`  | `str`     | ❌       | User email for authentication (optional)           |
| `rpc_url`     | `str`     | ❌       | Custom RPC endpoint (uses default if not provided) |

**Attributes**:

- `network`: Active blockchain network
- `rpq_client`: Instance of `RPQClient` for offer discovery
- `web3_client`: Instance of `MarketMakerWeb3Client` for on-chain operations
- `auth`: Instance of `SwarmAuth` for authentication
- `user_email`: User email for authentication

**Example**:

```python
from swarm.market_maker_sdk import MarketMakerClient
from swarm.shared.models import Network

# Using async context manager (recommended)
async with MarketMakerClient(
    network=Network.POLYGON,
    private_key="0x...",
    rpq_api_key="your_key",
    user_email="user@example.com"
) as client:
    result = await client.trade(
        from_token="0xUSDC...",
        to_token="0xRWA...",
        from_amount=Decimal("100")
    )
    print(f"Trade complete: {result.tx_hash}")
```

---

### authenticate()

Authenticate with the Swarm platform using wallet signature.

```python
async def authenticate() -> None
```

**Returns**: `None`

**Raises**:

- `AuthenticationError`: If authentication fails

**Description**:

Uses the wallet's private key to sign an authentication message and obtains an access token. Called automatically when using async context manager.

**Example**:

```python
client = MarketMakerClient(network=Network.POLYGON, private_key="0x...", rpq_api_key="key")
await client.authenticate()
# Now ready to make authenticated API calls
```

---

### get_quote()

Get a quote for trading tokens via Market Maker.

```python
async def get_quote(
    from_token: str,
    to_token: str,
    from_amount: Optional[Decimal] = None,
    to_amount: Optional[Decimal] = None,
) -> Quote
```

**Parameters**:

| Parameter     | Type      | Required | Description                                  |
| ------------- | --------- | -------- | -------------------------------------------- |
| `from_token`  | `str`     | ✅       | Token address to sell                        |
| `to_token`    | `str`     | ✅       | Token address to buy                         |
| `from_amount` | `Decimal` | ⚠️       | Amount to sell (either this or `to_amount`)  |
| `to_amount`   | `Decimal` | ⚠️       | Amount to buy (either this or `from_amount`) |

**⚠️ Important**: Provide **either** `from_amount` **OR** `to_amount`, not both.

**Returns**: `Quote`

Returns a normalized `Quote` object with:

- `sell_token_address`: Token being sold
- `sell_amount`: Amount being sold (normalized)
- `buy_token_address`: Token being bought
- `buy_amount`: Amount being bought (normalized)
- `rate`: Exchange rate (buy_amount / sell_amount)
- `source`: `"Market Maker RPQ"`
- `timestamp`: Current time

**Raises**:

- `NoOffersAvailableException`: If no offers available
- `QuoteUnavailableException`: If quote cannot be calculated
- `ValueError`: If both or neither amounts provided

**Example**:

```python
# Get quote for spending 100 USDC
quote = await client.get_quote(
    from_token="0xUSDC...",
    to_token="0xRWA...",
    from_amount=Decimal("100")
)
print(f"You'll receive {quote.buy_amount} RWA tokens")

# Or get quote for buying 10 RWA tokens
quote = await client.get_quote(
    from_token="0xUSDC...",
    to_token="0xRWA...",
    to_amount=Decimal("10")
)
print(f"You'll pay {quote.sell_amount} USDC")
```

---

### trade()

Execute a Market Maker trade by taking offers.

```python
async def trade(
    from_token: str,
    to_token: str,
    from_amount: Optional[Decimal] = None,
    to_amount: Optional[Decimal] = None,
    affiliate: Optional[str] = None,
) -> TradeResult
```

**Parameters**:

| Parameter     | Type      | Required | Description                                  |
| ------------- | --------- | -------- | -------------------------------------------- |
| `from_token`  | `str`     | ✅       | Token to sell (withdrawal asset)             |
| `to_token`    | `str`     | ✅       | Token to buy (deposit asset)                 |
| `from_amount` | `Decimal` | ⚠️       | Amount to sell (either this or `to_amount`)  |
| `to_amount`   | `Decimal` | ⚠️       | Amount to buy (either this or `from_amount`) |
| `affiliate`   | `str`     | ❌       | Optional affiliate address for fee sharing   |

**⚠️ Important**: Provide **either** `from_amount` **OR** `to_amount`, not both.

**Returns**: `TradeResult`

Contains:

- `tx_hash`: Blockchain transaction hash
- `order_id`: Offer ID that was taken
- `sell_token_address`: Token sold
- `sell_amount`: Amount sold (normalized)
- `buy_token_address`: Token bought
- `buy_amount`: Amount bought (normalized)
- `rate`: Exchange rate
- `source`: `"market_maker"`
- `timestamp`: Trade execution time
- `network`: Network used

**Trade Flow**:

1. 🔍 **Get best offers** - Queries RPQ Service
2. ✅ **Approve tokens** - Allows contract to spend withdrawal tokens
3. 📊 **Detect pricing type** - Fixed or dynamic
4. 🔗 **Execute on-chain** - Calls appropriate contract function
5. ⏳ **Wait for confirmation** - Returns after transaction is mined

**Raises**:

| Exception                       | Condition                        |
| ------------------------------- | -------------------------------- |
| `ValueError`                    | Both or neither amounts provided |
| `NoOffersAvailableException`    | No offers available              |
| `OfferNotFoundError`            | Offer doesn't exist              |
| `OfferInactiveError`            | Offer is not active              |
| `InsufficientOfferBalanceError` | Maker has insufficient balance   |
| `OfferExpiredError`             | Offer has expired                |
| `MarketMakerWeb3Exception`      | On-chain execution failed        |

**Example**:

```python
from decimal import Decimal

# Buy RWA by selling 100 USDC
result = await client.trade(
    from_token="0xUSDC...",
    to_token="0xRWA...",
    from_amount=Decimal("100")
)
print(f"Bought {result.buy_amount} RWA for ${result.sell_amount} USDC")
print(f"TX Hash: {result.tx_hash}")
print(f"Offer ID: {result.order_id}")

# Or buy 10 RWA tokens (spend whatever needed)
result = await client.trade(
    from_token="0xUSDC...",
    to_token="0xRWA...",
    to_amount=Decimal("10")
)

# With affiliate
result = await client.trade(
    from_token="0xUSDC...",
    to_token="0xRWA...",
    from_amount=Decimal("100"),
    affiliate="0xAffiliate..."
)
```

---

### make_offer()

Create a new Market Maker offer.

```python
async def make_offer(
    sell_token: str,
    sell_amount: Decimal,
    buy_token: str,
    buy_amount: Decimal,
    is_dynamic: bool = False,
    expires_at: Optional[int] = None,
) -> TradeResult
```

**Parameters**:

| Parameter     | Type      | Required | Description                                               |
| ------------- | --------- | -------- | --------------------------------------------------------- |
| `sell_token`  | `str`     | ✅       | Token you're offering to sell (deposit asset)             |
| `sell_amount` | `Decimal` | ✅       | Amount you're selling (normalized)                        |
| `buy_token`   | `str`     | ✅       | Token you want to buy (withdrawal asset)                  |
| `buy_amount`  | `Decimal` | ✅       | Amount you want to receive (normalized)                   |
| `is_dynamic`  | `bool`    | ❌       | Create dynamic offer using price feeds (default: `False`) |
| `expires_at`  | `int`     | ❌       | Optional expiration timestamp (0 = no expiry)             |

**Returns**: `TradeResult`

Contains:

- `tx_hash`: Blockchain transaction hash
- `order_id`: Created offer ID
- `sell_token_address`: Token deposited
- `sell_amount`: Amount deposited
- `buy_token_address`: Token requested
- `buy_amount`: Amount requested
- `rate`: Exchange rate (buy_amount / sell_amount)
- `source`: `"market_maker"`
- `timestamp`: Offer creation time
- `network`: Network used

**Raises**:

- `MarketMakerWeb3Exception`: If offer creation fails
- `Web3Exception`: If blockchain operation fails

**Example**:

```python
from decimal import Decimal
from datetime import datetime, timedelta

# Create fixed-price offer
result = await client.make_offer(
    sell_token="0xRWA...",      # Offering 10 RWA
    sell_amount=Decimal("10"),
    buy_token="0xUSDC...",      # Want 1000 USDC
    buy_amount=Decimal("1000")
)
print(f"Offer created! ID: {result.order_id}, TX: {result.tx_hash}")

# Create dynamic offer
result = await client.make_offer(
    sell_token="0xRWA...",
    sell_amount=Decimal("10"),
    buy_token="0xUSDC...",
    buy_amount=Decimal("1000"),
    is_dynamic=True  # Use price feeds
)

# With expiration (7 days)
expires_at = int((datetime.now() + timedelta(days=7)).timestamp())
result = await client.make_offer(
    sell_token="0xRWA...",
    sell_amount=Decimal("10"),
    buy_token="0xUSDC...",
    buy_amount=Decimal("1000"),
    expires_at=expires_at
)
```

---

### cancel_offer()

Cancel an existing offer.

```python
async def cancel_offer(offer_id: str) -> str
```

**Parameters**:

| Parameter  | Type  | Required | Description        |
| ---------- | ----- | -------- | ------------------ |
| `offer_id` | `str` | ✅       | Offer ID to cancel |

**Returns**: `str`

Transaction hash of the cancellation transaction.

**Raises**:

- `OfferNotFoundError`: If offer doesn't exist
- `UnauthorizedError`: If caller is not the offer creator
- `MarketMakerWeb3Exception`: If cancellation fails

**Example**:

```python
tx_hash = await client.cancel_offer(offer_id="12345")
print(f"Offer cancelled! TX: {tx_hash}")
```

---

### close()

Close all clients and cleanup resources.

```python
async def close() -> None
```

**Returns**: `None`

**Description**:

Properly closes HTTP clients and cleans up resources. Called automatically when using async context manager.

**Example**:

```python
client = MarketMakerClient(...)
await client.authenticate()
try:
    result = await client.trade(...)
finally:
    await client.close()  # Manual cleanup
```

---

## RPQClient

**Location**: `swarm/market_maker_sdk/rpq_service/client.py`

Client for interacting with Market Maker RPQ (Request for Quote) Service API. Provides market data and offer discovery.

### Constructor

```python
RPQClient(network: str = "polygon", api_key: Optional[str] = None)
```

**Parameters**:

| Parameter | Type  | Required | Description                                                            |
| --------- | ----- | -------- | ---------------------------------------------------------------------- |
| `network` | `str` | ❌       | Network name: "polygon", "ethereum", "base", etc. (default: "polygon") |
| `api_key` | `str` | ⚠️       | API key for authentication (required for most endpoints)               |

**Base URL**: `https://rfq.swarm.com/v1/client`

**Example**:

```python
from swarm.market_maker_sdk.rpq_service import RPQClient

client = RPQClient(network="polygon", api_key="your-api-key")
offers = await client.get_offers(
    buy_asset_address="0x...",
    sell_asset_address="0x..."
)
```

---

### get_offers()

Get all available offers filtered by network and optionally by assets.

```python
async def get_offers(
    buy_asset_address: Optional[str] = None,
    sell_asset_address: Optional[str] = None,
    page: int = 0,
    limit: int = 100,
) -> List[Offer]
```

**Parameters**:

| Parameter            | Type  | Required | Description                                        |
| -------------------- | ----- | -------- | -------------------------------------------------- |
| `buy_asset_address`  | `str` | ❌       | Filter by asset to buy (optional)                  |
| `sell_asset_address` | `str` | ❌       | Filter by asset to sell (optional)                 |
| `page`               | `int` | ❌       | Page number (default: 0)                           |
| `limit`              | `int` | ❌       | Number of offers per page (default: 100, max: 100) |

**Returns**: `List[Offer]`

List of matching offers with full details including pricing, availability, and assets.

**Raises**:

| Exception                    | Status Code | Condition                  |
| ---------------------------- | ----------- | -------------------------- |
| `NoOffersAvailableException` | N/A         | No offers found            |
| `RPQServiceException`        | 401         | Invalid or missing API key |
| `RPQServiceException`        | 429         | Monthly rate limit reached |
| `APIException`               | Other       | Request failed             |

**Example**:

```python
# Get all offers for token pair
offers = await client.get_offers(
    buy_asset_address="0x7ceB23fd6bc0add59E62ac25578270cFf1b9f619",  # WETH
    sell_asset_address="0x3c499c542cef5E3811e1192ce70d8cC03d5c3359",  # USDC
    limit=10
)

for offer in offers:
    print(f"Offer {offer.id}: {offer.amount_in} -> {offer.amount_out}")
    print(f"  Type: {offer.offer_type.value}")
    print(f"  Status: {offer.offer_status.value}")
    print(f"  Available: {offer.available_amount}")
```

---

### get_best_offers()

Get the best sequence of offers to reach a target amount.

```python
async def get_best_offers(
    buy_asset_address: str,
    sell_asset_address: str,
    target_sell_amount: Optional[str] = None,
    target_buy_amount: Optional[str] = None,
) -> BestOffersResponse
```

**Parameters**:

| Parameter            | Type  | Required | Description                                                                        |
| -------------------- | ----- | -------- | ---------------------------------------------------------------------------------- |
| `buy_asset_address`  | `str` | ✅       | Address of asset to buy (receive)                                                  |
| `sell_asset_address` | `str` | ✅       | Address of asset to sell (give up)                                                 |
| `target_sell_amount` | `str` | ⚠️       | Target amount to sell in normal decimal units (either this or `target_buy_amount`) |
| `target_buy_amount`  | `str` | ⚠️       | Target amount to buy in normal decimal units (either this or `target_sell_amount`) |

**⚠️ Important**: Provide **either** `target_sell_amount` **OR** `target_buy_amount`, not both.

**Returns**: `BestOffersResponse`

Contains:

- `success`: Whether operation succeeded
- `result`: `BestOffersResult` with:
  - `success`: Whether sufficient liquidity found
  - `target_amount`: Target amount requested
  - `total_withdrawal_amount_paid`: Total amount that will be paid
  - `selected_offers`: List of `SelectedOffer` objects
  - `mode`: `"buy"` or `"sell"`

**Raises**:

- `NoOffersAvailableException`: If no offers available
- `ValueError`: If both or neither target amounts specified
- `RPQServiceException`: If API request fails

**Example**:

```python
# Find best offers to spend 100 USDC
best = await client.get_best_offers(
    buy_asset_address="0x7ceB23fd6bc0add59E62ac25578270cFf1b9f619",
    sell_asset_address="0x3c499c542cef5E3811e1192ce70d8cC03d5c3359",
    target_sell_amount="100"
)

print(f"Success: {best.result.success}")
print(f"Total to pay: {best.result.total_withdrawal_amount_paid}")
print(f"Selected {len(best.result.selected_offers)} offer(s)")

for offer in best.result.selected_offers:
    print(f"\nOffer {offer.id}:")
    print(f"  Amount: {offer.withdrawal_amount_paid}")
    print(f"  Price: {offer.price_per_unit}")
    print(f"  Type: {offer.pricing_type.value}")
```

---

### get_quote()

Get a quote for trading tokens.

```python
async def get_quote(
    buy_asset_address: str,
    sell_asset_address: str,
    target_sell_amount: Optional[str] = None,
    target_buy_amount: Optional[str] = None,
) -> Quote
```

**Parameters**:

| Parameter            | Type  | Required | Description                                                                 |
| -------------------- | ----- | -------- | --------------------------------------------------------------------------- |
| `buy_asset_address`  | `str` | ✅       | Address of asset to buy                                                     |
| `sell_asset_address` | `str` | ✅       | Address of asset to sell                                                    |
| `target_sell_amount` | `str` | ⚠️       | Amount to sell in normal decimal units (either this or `target_buy_amount`) |
| `target_buy_amount`  | `str` | ⚠️       | Amount to buy in normal decimal units (either this or `target_sell_amount`) |

**⚠️ Important**: Provide **either** `target_sell_amount` **OR** `target_buy_amount`, not both.

**Returns**: `Quote`

Returns a normalized `Quote` object in SDK format with:

- `sell_token_address`: Token being sold
- `sell_amount`: Amount being sold (Decimal, normalized)
- `buy_token_address`: Token being bought
- `buy_amount`: Amount being bought (Decimal, normalized)
- `rate`: Exchange rate (buy_amount / sell_amount)
- `source`: `"Market Maker RPQ"`
- `timestamp`: Current time

**Raises**:

- `QuoteUnavailableException`: If quote cannot be generated
- `ValueError`: If both or neither amounts specified
- `RPQServiceException`: If API request fails (401, 429, etc.)

**Example**:

```python
# Get quote for spending 50 USDC
quote = await client.get_quote(
    buy_asset_address="0x7ceB23fd6bc0add59E62ac25578270cFf1b9f619",
    sell_asset_address="0x3c499c542cef5E3811e1192ce70d8cC03d5c3359",
    target_sell_amount="50"
)

print(f"You'll receive: {quote.buy_amount} tokens")
print(f"Rate: {quote.rate}")
```

---

### get_price_feeds()

Get all available price feeds for the network.

```python
async def get_price_feeds() -> PriceFeedsResponse
```

**Returns**: `PriceFeedsResponse`

Contains:

- `success`: Whether operation succeeded
- `price_feeds`: Dictionary mapping contract addresses to price feed addresses

**Raises**:

- `PriceFeedNotFoundException`: If no feeds found
- `RPQServiceException`: If API request fails

**Example**:

```python
feeds = await client.get_price_feeds()
print(f"Found {len(feeds.price_feeds)} price feeds")

# Get price feed for specific token
usdc_address = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
usdc_feed = feeds.price_feeds.get(usdc_address.lower())
print(f"USDC price feed: {usdc_feed}")
```

---

## MarketMakerWeb3Client

**Location**: `swarm/market_maker_sdk/market_maker_web3/client.py`

Client for interacting with Market Maker smart contracts. Handles on-chain offer execution, creation, and cancellation.

### Constructor

```python
MarketMakerWeb3Client(
    network: Network,
    private_key: str,
    rpc_url: Optional[str] = None,
)
```

**Parameters**:

| Parameter     | Type      | Required | Description                                        |
| ------------- | --------- | -------- | -------------------------------------------------- |
| `network`     | `Network` | ✅       | Blockchain network                                 |
| `private_key` | `str`     | ✅       | Wallet private key (with `0x` prefix)              |
| `rpc_url`     | `str`     | ❌       | Custom RPC endpoint (uses default if not provided) |

**Attributes**:

- `network`: Network for this client instance
- `web3_helper`: `Web3Helper` for blockchain operations
- `contract`: Market Maker Manager contract instance
- `account`: User's wallet account (LocalAccount)

**Example**:

```python
from swarm.market_maker_sdk.market_maker_web3 import MarketMakerWeb3Client
from swarm.shared.models import Network

client = MarketMakerWeb3Client(
    network=Network.POLYGON,
    private_key="0x..."
)

tx_hash = await client.take_offer_fixed(
    offer_id="12345",
    withdrawal_token="0xUSDC...",
    withdrawal_amount_paid=Decimal("100500000"),  # 100.5 USDC in wei
    affiliate=None
)
```

---

### take_offer_fixed()

Take a fixed-price offer.

```python
async def take_offer_fixed(
    offer_id: str,
    withdrawal_token: str,
    withdrawal_amount_paid: Decimal,
    affiliate: Optional[str] = None,
) -> str
```

**Parameters**:

| Parameter                | Type      | Required | Description                                         |
| ------------------------ | --------- | -------- | --------------------------------------------------- |
| `offer_id`               | `str`     | ✅       | Unique offer identifier (hex or decimal string)     |
| `withdrawal_token`       | `str`     | ✅       | Token address to pay (maker's withdrawal asset)     |
| `withdrawal_amount_paid` | `Decimal` | ✅       | Amount to pay in smallest units (wei, from RPQ API) |
| `affiliate`              | `str`     | ❌       | Optional affiliate address (None = zero address)    |

**Returns**: `str`

Transaction hash (0x...)

**Raises**:

- `OfferNotFoundError`: If offer doesn't exist
- `OfferInactiveError`: If offer is not active
- `InsufficientOfferBalanceError`: If maker has insufficient balance
- `Web3Exception`: If blockchain operation fails

**Example**:

```python
# Take a fixed offer - pay 100.5 USDC (in wei)
tx_hash = await client.take_offer_fixed(
    offer_id="12345",
    withdrawal_token="0x3c499c542cef5E3811e1192ce70d8cC03d5c3359",
    withdrawal_amount_paid=Decimal("100500000"),  # 100.5 USDC (6 decimals)
    affiliate=None
)
print(f"Transaction: {tx_hash}")
```

---

### take_offer_dynamic()

Take a dynamic-price offer with slippage protection.

```python
async def take_offer_dynamic(
    offer_id: str,
    withdrawal_token: str,
    withdrawal_amount_paid: Decimal,
    maximum_deposit_to_withdrawal_rate: Decimal,
    affiliate: Optional[str] = None,
) -> str
```

**Parameters**:

| Parameter                            | Type      | Required | Description                                               |
| ------------------------------------ | --------- | -------- | --------------------------------------------------------- |
| `offer_id`                           | `str`     | ✅       | Unique offer identifier (hex or decimal string)           |
| `withdrawal_token`                   | `str`     | ✅       | Token address to pay (maker's withdrawal asset)           |
| `withdrawal_amount_paid`             | `Decimal` | ✅       | Amount to pay in smallest units (wei, from RPQ API)       |
| `maximum_deposit_to_withdrawal_rate` | `Decimal` | ✅       | Max on-chain rate to accept (from RPQ API, set 0 to skip) |
| `affiliate`                          | `str`     | ❌       | Optional affiliate address (None = zero address)          |

**Returns**: `str`

Transaction hash (0x...)

**Raises**:

- `OfferNotFoundError`: If offer doesn't exist
- `OfferInactiveError`: If offer is not active
- `Web3Exception`: If blockchain operation fails or price exceeds max rate

**Example**:

```python
# Take a dynamic offer with slippage protection
tx_hash = await client.take_offer_dynamic(
    offer_id="67890",
    withdrawal_token="0x3c499c542cef5E3811e1192ce70d8cC03d5c3359",
    withdrawal_amount_paid=Decimal("50250000"),  # 50.25 USDC
    maximum_deposit_to_withdrawal_rate=Decimal("1050000"),  # From API
    affiliate=None
)
print(f"Transaction: {tx_hash}")
```

---

### make_offer()

Create a new Market Maker offer on-chain.

```python
async def make_offer(
    deposit_token: str,
    deposit_amount: Decimal,
    withdraw_token: str,
    withdraw_amount: Decimal,
    is_dynamic: bool = False,
    expires_at: Optional[int] = None,
) -> tuple[str, str]
```

**Parameters**:

| Parameter         | Type      | Required | Description                                        |
| ----------------- | --------- | -------- | -------------------------------------------------- |
| `deposit_token`   | `str`     | ✅       | Token to deposit                                   |
| `deposit_amount`  | `Decimal` | ✅       | Amount to deposit (normalized)                     |
| `withdraw_token`  | `str`     | ✅       | Token to withdraw                                  |
| `withdraw_amount` | `Decimal` | ✅       | Amount to withdraw (normalized)                    |
| `is_dynamic`      | `bool`    | ❌       | Whether to create dynamic offer (default: `False`) |
| `expires_at`      | `int`     | ❌       | Optional expiration timestamp (0 = no expiry)      |

**Returns**: `tuple[str, str]`

Tuple of (transaction_hash, offer_id)

**Raises**:

- `MarketMakerWeb3Exception`: If offer creation fails
- `Web3Exception`: If blockchain operation fails

**Example**:

```python
from decimal import Decimal

# Create fixed offer
tx_hash, offer_id = await client.make_offer(
    deposit_token="0xRWA...",
    deposit_amount=Decimal("10"),
    withdraw_token="0xUSDC...",
    withdraw_amount=Decimal("1000"),
    is_dynamic=False
)
print(f"Offer {offer_id} created: {tx_hash}")

# Create dynamic offer with expiration
from datetime import datetime, timedelta
expires_at = int((datetime.now() + timedelta(days=7)).timestamp())

tx_hash, offer_id = await client.make_offer(
    deposit_token="0xRWA...",
    deposit_amount=Decimal("10"),
    withdraw_token="0xUSDC...",
    withdraw_amount=Decimal("1000"),
    is_dynamic=True,
    expires_at=expires_at
)
```

---

### cancel_offer()

Cancel an existing offer on-chain.

```python
async def cancel_offer(offer_id: str) -> str
```

**Parameters**:

| Parameter  | Type  | Required | Description                                |
| ---------- | ----- | -------- | ------------------------------------------ |
| `offer_id` | `str` | ✅       | Offer ID to cancel (hex or decimal string) |

**Returns**: `str`

Transaction hash (0x...)

**Raises**:

- `OfferNotFoundError`: If offer doesn't exist
- `UnauthorizedError`: If caller is not the maker
- `Web3Exception`: If blockchain operation fails

**Example**:

```python
tx_hash = await client.cancel_offer(offer_id="12345")
print(f"Offer cancelled: {tx_hash}")
```

---

### get_offer_details()

Get on-chain details for an offer.

```python
async def get_offer_details(offer_id: str) -> Dict[str, Any]
```

**Parameters**:

| Parameter  | Type  | Required | Description                               |
| ---------- | ----- | -------- | ----------------------------------------- |
| `offer_id` | `str` | ✅       | Offer ID to query (hex or decimal string) |

**Returns**: `Dict[str, Any]`

Dictionary with offer details:

- `maker`: Maker address
- `deposit_token`: Deposit token address
- `deposit_amount`: Deposit amount (in wei)
- `withdraw_token`: Withdrawal token address
- `withdraw_amount`: Withdrawal amount (in wei)
- `is_active`: Whether offer is active
- `is_dynamic`: Whether offer uses dynamic pricing
- `expires_at`: Expiration timestamp

**Raises**:

- `OfferNotFoundError`: If offer doesn't exist
- `MarketMakerWeb3Exception`: If query fails

**Example**:

```python
details = await client.get_offer_details("12345")
print(f"Maker: {details['maker']}")
print(f"Active: {details['is_active']}")
print(f"Dynamic: {details['is_dynamic']}")
```

---

## Data Models

### Offer

**Location**: `swarm/market_maker_sdk/rpq_service/models.py`

Represents a complete Market Maker offer from RPQ API.

**Fields**:

| Field                        | Type          | Description                                 |
| ---------------------------- | ------------- | ------------------------------------------- |
| `id`                         | `str`         | Unique offer identifier                     |
| `maker`                      | `str`         | Wallet address of offer creator             |
| `amount_in`                  | `str`         | Amount of deposit asset (smallest units)    |
| `amount_out`                 | `str`         | Amount of withdrawal asset (smallest units) |
| `available_amount`           | `str`         | Available amount for partial fills          |
| `deposit_asset`              | `Asset`       | Asset being deposited                       |
| `withdrawal_asset`           | `Asset`       | Asset being withdrawn                       |
| `offer_type`                 | `OfferType`   | `PartialOffer` or `BlockOffer`              |
| `offer_status`               | `OfferStatus` | Current status                              |
| `offer_price`                | `OfferPrice`  | Pricing information                         |
| `is_auth`                    | `bool`        | Whether requires authorization              |
| `timelock_period`            | `str`         | Timelock period in seconds                  |
| `expiry_timestamp`           | `str`         | Expiration timestamp                        |
| `terms`                      | `Any`         | Offer terms (optional)                      |
| `comms_link`                 | `str`         | Communication link (optional)               |
| `authorization_addresses`    | `List[str]`   | Authorized addresses (optional)             |
| `deposit_to_withdrawal_rate` | `str`         | Exchange rate (optional)                    |

---

### SelectedOffer

**Location**: `swarm/market_maker_sdk/rpq_service/models.py`

Represents a selected offer in best offers response.

**Fields**:

| Field                             | Type          | Description                                 |
| --------------------------------- | ------------- | ------------------------------------------- |
| `id`                              | `str`         | Offer ID                                    |
| `withdrawal_amount_paid`          | `str`         | Amount paid in withdrawal asset (wei)       |
| `withdrawal_amount_paid_decimals` | `str`         | Decimals for withdrawal token               |
| `offer_type`                      | `OfferType`   | `PartialOffer` or `BlockOffer`              |
| `maker`                           | `str`         | Maker address                               |
| `price_per_unit`                  | `str`         | Price per unit (wei)                        |
| `pricing_type`                    | `PricingType` | `FixedPricing` or `DynamicPricing`          |
| `deposit_to_withdrawal_rate`      | `str`         | Exchange rate for dynamic offers (optional) |

---

### BestOffersResponse

**Location**: `swarm/market_maker_sdk/rpq_service/models.py`

Response from best offers endpoint.

**Fields**:

| Field     | Type               | Description                |
| --------- | ------------------ | -------------------------- |
| `success` | `bool`             | Whether API call succeeded |
| `result`  | `BestOffersResult` | Best offers result         |

**BestOffersResult Fields**:

| Field                          | Type                  | Description                        |
| ------------------------------ | --------------------- | ---------------------------------- |
| `success`                      | `bool`                | Whether sufficient liquidity found |
| `target_amount`                | `str`                 | Target amount requested            |
| `total_withdrawal_amount_paid` | `str`                 | Total amount to be paid            |
| `selected_offers`              | `List[SelectedOffer]` | Selected offers                    |
| `mode`                         | `str`                 | `"buy"` or `"sell"`                |

---

### Quote

**Location**: `swarm/shared/models.py`

Normalized quote format used across all SDKs.

**Fields**:

| Field                | Type       | Description         |
| -------------------- | ---------- | ------------------- |
| `sell_token_address` | `str`      | Token being sold    |
| `sell_amount`        | `Decimal`  | Amount being sold   |
| `buy_token_address`  | `str`      | Token being bought  |
| `buy_amount`         | `Decimal`  | Amount being bought |
| `rate`               | `Decimal`  | Exchange rate       |
| `source`             | `str`      | Platform source     |
| `timestamp`          | `datetime` | Quote timestamp     |

---

### QuoteResponse

**Location**: `swarm/market_maker_sdk/rpq_service/models.py`

Raw response from RPQ quote endpoint.

**Fields**:

| Field                | Type   | Description                            |
| -------------------- | ------ | -------------------------------------- |
| `success`            | `bool` | Whether sufficient liquidity available |
| `buy_asset_address`  | `str`  | Address of asset to buy                |
| `sell_asset_address` | `str`  | Address of asset to sell               |
| `average_price`      | `str`  | Average price per unit                 |
| `sell_amount`        | `str`  | Amount to sell (optional)              |
| `buy_amount`         | `str`  | Amount to buy (optional)               |

---

### TradeResult

**Location**: `swarm/shared/models.py`

Normalized trade result format used across all SDKs.

**Fields**:

| Field                | Type       | Description                 |
| -------------------- | ---------- | --------------------------- |
| `tx_hash`            | `str`      | Blockchain transaction hash |
| `order_id`           | `str`      | Platform order/offer ID     |
| `sell_token_address` | `str`      | Token sold                  |
| `sell_amount`        | `Decimal`  | Amount sold                 |
| `buy_token_address`  | `str`      | Token bought                |
| `buy_amount`         | `Decimal`  | Amount bought               |
| `rate`               | `Decimal`  | Exchange rate               |
| `source`             | `str`      | Platform (`"market_maker"`) |
| `timestamp`          | `datetime` | Trade timestamp             |
| `network`            | `Network`  | Blockchain network          |

---

### Asset

**Location**: `swarm/market_maker_sdk/rpq_service/models.py`

Represents an asset in an offer.

**Fields**:

| Field            | Type        | Description                    |
| ---------------- | ----------- | ------------------------------ |
| `id`             | `str`       | Asset ID                       |
| `name`           | `str`       | Asset name                     |
| `symbol`         | `str`       | Asset symbol                   |
| `address`        | `str`       | Contract address               |
| `decimals`       | `int`       | Token decimals (optional)      |
| `token_id`       | `int`       | Token ID for NFTs (optional)   |
| `asset_type`     | `AssetType` | Type of asset                  |
| `kya`            | `str`       | KYA identifier (optional)      |
| `token_standard` | `str`       | Token standard (e.g., "ERC20") |
| `traded_volume`  | `str`       | Total traded volume            |

---

### OfferPrice

**Location**: `swarm/market_maker_sdk/rpq_service/models.py`

Represents offer pricing information.

**Fields**:

| Field                    | Type             | Description                            |
| ------------------------ | ---------------- | -------------------------------------- |
| `id`                     | `str`            | Price ID                               |
| `pricing_type`           | `PricingType`    | `FixedPricing` or `DynamicPricing`     |
| `percentage`             | `float`          | Percentage adjustment (optional)       |
| `percentage_type`        | `PercentageType` | `Plus` or `Minus` (optional)           |
| `unit_price`             | `str`            | Fixed unit price (optional)            |
| `deposit_asset_price`    | `Dict[str, str]` | Deposit asset price feed (optional)    |
| `withdrawal_asset_price` | `Dict[str, str]` | Withdrawal asset price feed (optional) |

---

### PriceFeedsResponse

**Location**: `swarm/market_maker_sdk/rpq_service/models.py`

Response from price feeds endpoint.

**Fields**:

| Field         | Type             | Description                                           |
| ------------- | ---------------- | ----------------------------------------------------- |
| `success`     | `bool`           | Whether API call succeeded                            |
| `price_feeds` | `Dict[str, str]` | Mapping of contract addresses to price feed addresses |

---

## Enumerations

### OfferType

**Location**: `swarm/market_maker_sdk/rpq_service/models.py`

```python
class OfferType(str, Enum):
    PARTIAL_OFFER = "PartialOffer"  # Can be taken in parts
    BLOCK_OFFER = "BlockOffer"      # Must be taken all at once
```

---

### OfferStatus

**Location**: `swarm/market_maker_sdk/rpq_service/models.py`

```python
class OfferStatus(str, Enum):
    NOT_TAKEN = "NotTaken"              # Not taken yet
    PARTIALLY_TAKEN = "PartiallyTaken"  # Partially filled
    TAKEN = "Taken"                     # Fully taken
```

---

### PricingType

**Location**: `swarm/market_maker_sdk/rpq_service/models.py`

```python
class PricingType(str, Enum):
    FIXED_PRICING = "FixedPricing"      # Fixed price
    DYNAMIC_PRICING = "DynamicPricing"  # Uses price feeds
```

---

### PercentageType

**Location**: `swarm/market_maker_sdk/rpq_service/models.py`

```python
class PercentageType(str, Enum):
    PLUS = "Plus"    # Add percentage
    MINUS = "Minus"  # Subtract percentage
```

---

### AssetType

**Location**: `swarm/market_maker_sdk/rpq_service/models.py`

```python
class AssetType(str, Enum):
    SECURITY = "Security"
    NO_TYPE = "NoType"
    GOLD = "Gold"
```

---

## Exceptions

### Exception Hierarchy

```
RPQServiceException (base)
├── NoOffersAvailableException
├── InvalidTokenPairException
├── QuoteUnavailableException
└── PriceFeedNotFoundException

MarketMakerWeb3Exception (base)
├── OfferNotFoundError
├── OfferInactiveError
├── InsufficientOfferBalanceError
├── OfferExpiredError
└── UnauthorizedError
```

---

### RPQServiceException

**Location**: `swarm/market_maker_sdk/rpq_service/exceptions.py`

Base exception for all RPQ Service-related errors.

---

### NoOffersAvailableException

Raised when no offers are available for the requested token pair.

**Example**:

```python
try:
    offers = await client.rpq_client.get_offers(
        buy_asset_address="0x...",
        sell_asset_address="0x..."
    )
except NoOffersAvailableException as e:
    print(f"No offers available: {e}")
    # Try creating your own offer
```

---

### QuoteUnavailableException

Raised when quote cannot be generated (insufficient liquidity, invalid parameters, etc.).

---

### InvalidTokenPairException

Raised when token pair is not supported.

---

### PriceFeedNotFoundException

Raised when price feed is not found for a token.

---

### MarketMakerWeb3Exception

**Location**: `swarm/market_maker_sdk/market_maker_web3/exceptions.py`

Base exception for all Market Maker Web3-related errors.

---

### OfferNotFoundError

Raised when offer doesn't exist on-chain.

**Possible Causes**:

- Invalid offer ID
- Offer was already taken
- Offer was cancelled

---

### OfferInactiveError

Raised when trying to take an inactive offer.

**Possible Causes**:

- Offer was cancelled
- Offer was fully taken
- Offer is paused

---

### InsufficientOfferBalanceError

Raised when offer maker has insufficient token balance.

---

### OfferExpiredError

Raised when offer has expired.

---

### UnauthorizedError

Raised when caller is not authorized for the operation.

**Possible Causes**:

- Trying to cancel someone else's offer
- Trying to take an authorized-only offer without permission

---

## Supported Networks

Market Maker SDK works on networks with deployed contracts:

| Network  | Chain ID | Supported | Contract Loaded Dynamically |
| -------- | -------- | --------- | --------------------------- |
| Polygon  | 137      | ✅        | Yes                         |
| Ethereum | 1        | ✅        | Yes                         |
| Arbitrum | 42161    | ✅        | Yes                         |
| Base     | 8453     | ✅        | Yes                         |
| Optimism | 10       | ✅        | Yes                         |

---

## Contract Addresses

Market Maker Manager contract addresses are loaded dynamically from remote config based on environment (dev/prod) and network.

**Environment Control**:

```bash
# Development mode (default)
export SWARM_COLLECTION_MODE=dev

# Production mode
export SWARM_COLLECTION_MODE=prod
```

Contract addresses are fetched automatically when the `MarketMakerWeb3Client` is first used. If a contract is not deployed on the specified network, a `MarketMakerWeb3Exception` will be raised.

---

**Happy Trading! 🚀**

_Last Updated: November 20, 2025_

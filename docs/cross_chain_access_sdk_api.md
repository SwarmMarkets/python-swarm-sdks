# Cross-Chain Access SDK API Documentation

## Table of Contents

### Core Classes

- [CrossChainAccessClient](#cross_chain_accessclient) - Main SDK entry point
  - [Constructor](#constructor)
  - [authenticate()](#authenticate)
  - [check_trading_availability()](#check_trading_availability)
  - [get_quote()](#get_quote)
  - [buy()](#buy)
  - [sell()](#sell)
  - [close()](#close)
- [CrossChainAccessAPIClient](#cross_chain_accessapiclient) - HTTP API client
  - [Constructor](#constructor-1)
  - [get_account_status()](#get_account_status)
  - [get_account_funds()](#get_account_funds)
  - [get_asset_quote()](#get_asset_quote)
  - [create_order()](#create_order)
- [MarketHours](#markethours) - Market timing utilities
  - [Market Schedule](#market-schedule)
  - [is_market_open()](#is_market_open)
  - [time_until_open()](#time_until_open)
  - [time_until_close()](#time_until_close)
  - [get_market_status()](#get_market_status)

### Data Models

- [Quote](#quote)
- [TradeResult](#traderesult)
- [OrderSide](#orderside)
- [AccountStatus](#accountstatus)
- [AccountFunds](#accountfunds)
- [Cross-Chain AccessQuote](#cross_chain_accessquote)
- [Cross-Chain AccessOrderResponse](#cross_chain_accessorderresponse)

### Exceptions

- [Exception Hierarchy](#exception-hierarchy)
- [CrossChainAccessException](#cross_chain_accessexception)
- [MarketClosedException](#marketclosedexception)
- [AccountBlockedException](#accountblockedexception)
- [InsufficientFundsException](#insufficientfundsexception)
- [QuoteUnavailableException](#quoteunavailableexception)
- [OrderFailedException](#orderfailedexception)
- [InvalidSymbolException](#invalidsymbolexception)

### Additional Resources

- [Supported Networks](#supported-networks)
- [Rate Limits & Performance](#rate-limits--performance)

---

## CrossChainAccessClient

**Location**: `cross_chain_access_sdk/sdk/client.py`

The main entry point for Cross-Chain Access stock trading operations. Orchestrates authentication, market validation, on-chain transfers, and order submission.

### Constructor

```python
CrossChainAccessClient(
    network: Network,
    private_key: str,
    user_email: Optional[str] = None,
    rpc_url: Optional[str] = None,
    is_dev: bool = False,
)
```

**Parameters**:

| Parameter     | Type      | Required | Description                                        |
| ------------- | --------- | -------- | -------------------------------------------------- |
| `network`     | `Network` | ✅       | Blockchain network (e.g., `Network.POLYGON`)       |
| `private_key` | `str`     | ✅       | Wallet private key (with `0x` prefix)              |
| `user_email`  | `str`     | ❌       | User email for notifications                       |
| `rpc_url`     | `str`     | ❌       | Custom RPC endpoint (uses default if not provided) |
| `is_dev`      | `bool`    | ❌       | Use development endpoints (default: `False`)       |

**Attributes**:

- `network`: Active blockchain network
- `is_dev`: Whether using dev environment
- `cross_chain_access_api`: Instance of `CrossChainAccessAPIClient`
- `web3_helper`: Instance of `Web3Helper` for blockchain operations
- `auth`: Instance of `SwarmAuth` for authentication
- `usdc_address`: USDC token address for the network
- `topup_address`: Escrow address for token transfers

**Example**:

```python
from cross_chain_access_sdk.sdk import CrossChainAccessClient
from shared.models import Network

# Using async context manager (recommended)
async with CrossChainAccessClient(
    network=Network.POLYGON,
    private_key="0x...",
    user_email="user@example.com"
) as client:
    result = await client.buy(
        rwa_token_address="0xRWA...",
        rwa_symbol="AAPL",
        rwa_amount=Decimal("10"),
        user_email="user@example.com"
    )
    print(f"Trade complete: {result.tx_hash}")
```

**Raises**:

- `ValueError`: If USDC not available on specified network

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

Uses the wallet's private key to sign an authentication message and obtains an access token. The token is automatically set for subsequent API calls.

**Example**:

```python
client = CrossChainAccessClient(network=Network.POLYGON, private_key="0x...")
await client.authenticate()
# Now ready to make authenticated API calls
```

---

### check_trading_availability()

Check if trading is currently available by validating market hours and account status.

```python
async def check_trading_availability() -> tuple[bool, str]
```

**Returns**: `tuple[bool, str]`

- `bool`: Whether trading is available
- `str`: Human-readable status message

**Checks**:

1. Market hours (14:30-21:00 UTC, Monday-Friday)
2. Account not blocked
3. Trading not suspended
4. Transfers not blocked
5. Market is open

**Example**:

```python
is_available, message = await client.check_trading_availability()
if not is_available:
    print(f"Cannot trade: {message}")
else:
    print(f"Ready to trade: {message}")
```

**Possible Messages**:

- `"Trading is available"` - All checks passed
- `"Market is closed. Opens in 5h 30m"` - Outside market hours
- `"Trading not available: account blocked"` - Account issues
- `"Trading not available: trading blocked, transfers blocked"` - Multiple issues

---

### get_quote()

Get real-time quote for a trading symbol.

```python
async def get_quote(rwa_symbol: str) -> Quote
```

**Parameters**:

| Parameter    | Type  | Required | Description                     |
| ------------ | ----- | -------- | ------------------------------- |
| `rwa_symbol` | `str` | ✅       | Trading symbol (e.g., `"AAPL"`) |

**Returns**: `Quote`

Returns a normalized `Quote` object with the following fields:

- `sell_token_address`: USDC address
- `sell_amount`: Decimal("1")
- `buy_token_address`: Symbol as placeholder
- `buy_amount`: Calculated from ask price
- `rate`: Ask price per unit
- `source`: `"cross_chain_access"`
- `timestamp`: Current time

**Raises**:

- `QuoteUnavailableException`: If quote cannot be retrieved
- `InvalidSymbolException`: If symbol is invalid

**Example**:

```python
quote = await client.get_quote("AAPL")
print(f"Price: ${quote.rate}")
print(f"1 USDC buys: {quote.buy_amount} shares")
```

---

### buy()

Buy RWA tokens with USDC via Cross-Chain Access stock market.

```python
async def buy(
    rwa_token_address: str,
    rwa_symbol: str,
    user_email: str,
    rwa_amount: Optional[Decimal] = None,
    usdc_amount: Optional[Decimal] = None,
) -> TradeResult
```

**Parameters**:

| Parameter           | Type      | Required | Description                                                |
| ------------------- | --------- | -------- | ---------------------------------------------------------- |
| `rwa_token_address` | `str`     | ✅       | RWA token contract address                                 |
| `rwa_symbol`        | `str`     | ✅       | Trading symbol (e.g., `"AAPL"`)                            |
| `user_email`        | `str`     | ✅       | User email for notifications                               |
| `rwa_amount`        | `Decimal` | ⚠️       | Amount of RWA tokens to buy (either this or `usdc_amount`) |
| `usdc_amount`       | `Decimal` | ⚠️       | Amount of USDC to spend (either this or `rwa_amount`)      |

**⚠️ Important**: Provide **either** `rwa_amount` **OR** `usdc_amount`, not both.

**Returns**: `TradeResult`

Contains:

- `tx_hash`: Blockchain transaction hash
- `order_id`: Cross-Chain Access order ID
- `sell_token_address`: USDC address
- `sell_amount`: USDC spent
- `buy_token_address`: RWA token address
- `buy_amount`: RWA tokens received
- `rate`: Locked price
- `source`: `"cross_chain_access"`
- `timestamp`: Trade execution time
- `network`: Network used

**Trade Flow**:

1. ✅ Check market hours and account status
2. 📈 Get real-time quote
3. 🧮 Calculate amounts with 1% slippage protection
4. 💰 Validate buying power
5. 🔗 Transfer USDC to escrow address
6. 📋 Submit order to Cross-Chain Access API

**Raises**:

| Exception                    | Condition                        |
| ---------------------------- | -------------------------------- |
| `ValueError`                 | Both or neither amounts provided |
| `MarketClosedException`      | Market is closed                 |
| `AccountBlockedException`    | Account is blocked               |
| `InsufficientFundsException` | Insufficient buying power        |
| `OrderFailedException`       | Order submission failed          |

**Example**:

```python
from decimal import Decimal

# Buy 10 AAPL shares
result = await client.buy(
    rwa_token_address="0x1234...",
    rwa_symbol="AAPL",
    rwa_amount=Decimal("10"),
    user_email="user@example.com"
)
print(f"Bought {result.buy_amount} AAPL for ${result.sell_amount} USDC")
print(f"TX Hash: {result.tx_hash}")
print(f"Order ID: {result.order_id}")

# Alternatively, specify USDC amount
result = await client.buy(
    rwa_token_address="0x1234...",
    rwa_symbol="AAPL",
    usdc_amount=Decimal("1000"),  # Spend $1000 USDC
    user_email="user@example.com"
)
```

---

### sell()

Sell RWA tokens for USDC via Cross-Chain Access stock market.

```python
async def sell(
    rwa_token_address: str,
    rwa_symbol: str,
    user_email: str,
    rwa_amount: Optional[Decimal] = None,
    usdc_amount: Optional[Decimal] = None,
) -> TradeResult
```

**Parameters**:

| Parameter           | Type      | Required | Description                                                 |
| ------------------- | --------- | -------- | ----------------------------------------------------------- |
| `rwa_token_address` | `str`     | ✅       | RWA token contract address                                  |
| `rwa_symbol`        | `str`     | ✅       | Trading symbol (e.g., `"AAPL"`)                             |
| `user_email`        | `str`     | ✅       | User email for notifications                                |
| `rwa_amount`        | `Decimal` | ⚠️       | Amount of RWA tokens to sell (either this or `usdc_amount`) |
| `usdc_amount`       | `Decimal` | ⚠️       | Amount of USDC to receive (either this or `rwa_amount`)     |

**⚠️ Important**: Provide **either** `rwa_amount` **OR** `usdc_amount`, not both.

**Returns**: `TradeResult`

Contains:

- `tx_hash`: Blockchain transaction hash
- `order_id`: Cross-Chain Access order ID
- `sell_token_address`: RWA token address
- `sell_amount`: RWA tokens sold
- `buy_token_address`: USDC address
- `buy_amount`: USDC received
- `rate`: Locked price
- `source`: `"cross_chain_access"`
- `timestamp`: Trade execution time
- `network`: Network used

**Trade Flow**:

1. ✅ Check market hours and account status
2. 📈 Get real-time quote
3. 🧮 Calculate amounts with 1% slippage protection
4. 🏦 Validate RWA token balance
5. 🔗 Transfer RWA tokens to escrow address
6. 📋 Submit order to Cross-Chain Access API

**Raises**:

| Exception                    | Condition                        |
| ---------------------------- | -------------------------------- |
| `ValueError`                 | Both or neither amounts provided |
| `MarketClosedException`      | Market is closed                 |
| `AccountBlockedException`    | Account is blocked               |
| `InsufficientFundsException` | Insufficient RWA balance         |
| `OrderFailedException`       | Order submission failed          |

**Example**:

```python
from decimal import Decimal

# Sell 5 AAPL shares
result = await client.sell(
    rwa_token_address="0x1234...",
    rwa_symbol="AAPL",
    rwa_amount=Decimal("5"),
    user_email="user@example.com"
)
print(f"Sold {result.sell_amount} AAPL for ${result.buy_amount} USDC")
print(f"TX Hash: {result.tx_hash}")
print(f"Order ID: {result.order_id}")

# Alternatively, target USDC amount
result = await client.sell(
    rwa_token_address="0x1234...",
    rwa_symbol="AAPL",
    usdc_amount=Decimal("500"),  # Receive $500 USDC
    user_email="user@example.com"
)
```

---

### close()

Close all clients and cleanup resources.

```python
async def close() -> None
```

**Returns**: `None`

**Description**:

Properly closes the HTTP client and cleans up resources. Called automatically when using async context manager.

**Example**:

```python
client = CrossChainAccessClient(...)
await client.authenticate()
try:
    result = await client.buy(...)
finally:
    await client.close()  # Manual cleanup
```

---

## CrossChainAccessAPIClient

**Location**: `cross_chain_access_sdk/cross_chain_access/client.py`

Low-level HTTP client for interacting with Cross-Chain Access Stock Trading API endpoints.

### Constructor

```python
CrossChainAccessAPIClient(is_dev: bool = False)
```

**Parameters**:

| Parameter | Type   | Required | Description                                     |
| --------- | ------ | -------- | ----------------------------------------------- |
| `is_dev`  | `bool` | ❌       | Use development API endpoint (default: `False`) |

**Endpoints**:

- **Development**: `https://stock-trading-api.dev.swarm.com/stock-trading`
- **Production**: `https://stock-trading-api.app.swarm.com/stock-trading`

**Example**:

```python
from cross_chain_access_sdk.cross_chain_access import CrossChainAccessAPIClient

client = CrossChainAccessAPIClient(is_dev=True)
client.set_auth_token("your_token")
quote = await client.get_asset_quote("AAPL")
```

---

### get_account_status()

Get trading account status and permissions.

```python
async def get_account_status() -> AccountStatus
```

**Returns**: `AccountStatus`

Fields:

- `account_blocked`: Whether account is blocked
- `trading_blocked`: Whether trading is blocked
- `transfers_blocked`: Whether transfers are blocked
- `trade_suspended_by_user`: Whether user suspended trading
- `market_open`: Whether market is currently open
- `account_status`: Status string (e.g., `"ACTIVE"`)

**Raises**:

- `APIException(401)`: If authentication token missing

**Example**:

```python
status = await client.get_account_status()
if status.is_trading_allowed():
    print("All systems go!")
else:
    print(f"Status: {status.account_status}")
```

---

### get_account_funds()

Get trading account funds and buying power.

```python
async def get_account_funds() -> AccountFunds
```

**Returns**: `AccountFunds`

Fields:

- `cash`: Available cash
- `buying_power`: Total buying power
- `day_trading_buying_power`: Day trading buying power
- `effective_buying_power`: Effective buying power
- `non_margin_buying_power`: Non-margin buying power
- `reg_t_buying_power`: Regulation T buying power

**Raises**:

- `APIException(401)`: If authentication token missing

**Example**:

```python
funds = await client.get_account_funds()
print(f"Buying power: ${funds.buying_power}")
if funds.has_sufficient_funds(Decimal("1000")):
    print("Can afford $1000 trade")
```

---

### get_asset_quote()

Get real-time quote for a trading symbol.

```python
async def get_asset_quote(symbol: str) -> Cross-Chain AccessQuote
```

**Parameters**:

| Parameter | Type  | Required | Description                     |
| --------- | ----- | -------- | ------------------------------- |
| `symbol`  | `str` | ✅       | Trading symbol (e.g., `"AAPL"`) |

**Returns**: `Cross-Chain AccessQuote`

Fields:

- `bid_price`: Best bid price
- `ask_price`: Best ask price
- `bid_size`: Size at bid
- `ask_size`: Size at ask
- `timestamp`: Quote timestamp
- `bid_exchange`: Exchange for bid
- `ask_exchange`: Exchange for ask

**Raises**:

| Exception                   | Status Code | Condition              |
| --------------------------- | ----------- | ---------------------- |
| `InvalidSymbolException`    | 404         | Invalid trading symbol |
| `QuoteUnavailableException` | 400         | Quote unavailable      |
| `APIException`              | Other       | Request failed         |

**Example**:

```python
quote = await client.get_asset_quote("AAPL")
print(f"Bid: ${quote.bid_price}, Ask: ${quote.ask_price}")
print(f"Spread: ${quote.ask_price - quote.bid_price}")

# Get price for specific side
buy_price = quote.get_price_for_side(OrderSide.BUY)  # Returns ask
sell_price = quote.get_price_for_side(OrderSide.SELL)  # Returns bid
```

---

### create_order()

Create a trading order on Cross-Chain Access after on-chain transfer.

```python
async def create_order(
    wallet: str,
    tx_hash: str,
    asset_address: str,
    asset_symbol: str,
    side: OrderSide,
    price: Decimal,
    qty: Decimal,
    notional: Decimal,
    chain_id: int,
    target_chain_id: int,
    user_email: str,
) -> Cross-Chain AccessOrderResponse
```

**Parameters**:

| Parameter         | Type        | Required | Description                         |
| ----------------- | ----------- | -------- | ----------------------------------- |
| `wallet`          | `str`       | ✅       | User wallet address                 |
| `tx_hash`         | `str`       | ✅       | Blockchain transaction hash         |
| `asset_address`   | `str`       | ✅       | RWA token contract address          |
| `asset_symbol`    | `str`       | ✅       | Trading symbol (e.g., `"AAPL"`)     |
| `side`            | `OrderSide` | ✅       | `OrderSide.BUY` or `OrderSide.SELL` |
| `price`           | `Decimal`   | ✅       | Locked price per unit               |
| `qty`             | `Decimal`   | ✅       | RWA quantity                        |
| `notional`        | `Decimal`   | ✅       | USDC amount                         |
| `chain_id`        | `int`       | ✅       | Source blockchain network ID        |
| `target_chain_id` | `int`       | ✅       | Target blockchain network ID        |
| `user_email`      | `str`       | ✅       | User email for notifications        |

**Returns**: `Cross-Chain AccessOrderResponse`

Fields:

- `order_id`: Unique order identifier
- `symbol`: Trading symbol
- `side`: Order side (`"buy"` or `"sell"`)
- `quantity`: Order quantity
- `filled_qty`: Filled quantity
- `status`: Order status (e.g., `"pending"`, `"filled"`)
- `created_at`: Creation timestamp
- `filled_at`: Fill timestamp (if filled)

**Raises**:

| Exception              | Condition                    |
| ---------------------- | ---------------------------- |
| `APIException(401)`    | Authentication token missing |
| `OrderFailedException` | Order creation failed        |

**Example**:

```python
order = await client.create_order(
    wallet="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    tx_hash="0xabc123...",
    asset_address="0x1234...",
    asset_symbol="AAPL",
    side=OrderSide.BUY,
    price=Decimal("150.50"),
    qty=Decimal("10"),
    notional=Decimal("1505"),
    chain_id=137,
    target_chain_id=137,
    user_email="user@example.com"
)
print(f"Order {order.order_id} created with status: {order.status}")
```

---

## MarketHours

**Location**: `cross_chain_access_sdk/market_hours/market_hours.py`

Static utility class for checking US stock market hours.

### Market Schedule

- **Open**: 14:30 UTC (9:30 AM EST)
- **Close**: 21:00 UTC (4:00 PM EST)
- **Days**: Monday - Friday (weekdays only)

---

### is_market_open()

Check if market is currently open.

```python
@staticmethod
def is_market_open(dt: Optional[datetime] = None) -> bool
```

**Parameters**:

| Parameter | Type       | Required | Description                                      |
| --------- | ---------- | -------- | ------------------------------------------------ |
| `dt`      | `datetime` | ❌       | Datetime to check (defaults to current UTC time) |

**Returns**: `bool`

`True` if market is open (weekday between 14:30-21:00 UTC), `False` otherwise.

**Example**:

```python
from cross_chain_access_sdk.market_hours import MarketHours
from datetime import datetime
import pytz

# Check current time
if MarketHours.is_market_open():
    print("Market is open now!")

# Check specific time
dt = datetime(2025, 11, 3, 15, 0, tzinfo=pytz.UTC)  # Monday 15:00 UTC
if MarketHours.is_market_open(dt):
    print("Market was open at that time")
```

---

### time_until_open()

Calculate time until market opens.

```python
@staticmethod
def time_until_open(dt: Optional[datetime] = None) -> timedelta
```

**Parameters**:

| Parameter | Type       | Required | Description                                      |
| --------- | ---------- | -------- | ------------------------------------------------ |
| `dt`      | `datetime` | ❌       | Datetime to check (defaults to current UTC time) |

**Returns**: `timedelta`

Time until market opens. Returns `timedelta(0)` if market is already open.

**Example**:

```python
time_left = MarketHours.time_until_open()
hours = time_left.total_seconds() / 3600
print(f"Market opens in {hours:.1f} hours")
```

---

### time_until_close()

Calculate time until market closes.

```python
@staticmethod
def time_until_close(dt: Optional[datetime] = None) -> timedelta
```

**Parameters**:

| Parameter | Type       | Required | Description                                      |
| --------- | ---------- | -------- | ------------------------------------------------ |
| `dt`      | `datetime` | ❌       | Datetime to check (defaults to current UTC time) |

**Returns**: `timedelta`

Time until market closes. Returns `timedelta(0)` if market is closed.

**Example**:

```python
time_left = MarketHours.time_until_close()
hours = time_left.total_seconds() / 3600
print(f"Market closes in {hours:.1f} hours")
```

---

### get_market_status()

Get market status with human-readable message.

```python
@staticmethod
def get_market_status(dt: Optional[datetime] = None) -> Tuple[bool, str]
```

**Parameters**:

| Parameter | Type       | Required | Description                                      |
| --------- | ---------- | -------- | ------------------------------------------------ |
| `dt`      | `datetime` | ❌       | Datetime to check (defaults to current UTC time) |

**Returns**: `Tuple[bool, str]`

- `bool`: Whether market is open
- `str`: Human-readable status message

**Example**:

```python
is_open, message = MarketHours.get_market_status()
print(message)
# Output: "Market is open. Closes in 3h 45m"
# Or: "Market is closed. Opens in 12h 30m"
```

---

## Data Models

### Quote

**Location**: `shared/models.py`

Normalized quote format used across all SDKs.

**Fields**:

| Field                | Type       | Description           |
| -------------------- | ---------- | --------------------- |
| `sell_token_address` | `str`      | Token being sold      |
| `sell_amount`        | `Decimal`  | Amount being sold     |
| `buy_token_address`  | `str`      | Token being bought    |
| `buy_amount`         | `Decimal`  | Amount being bought   |
| `rate`               | `Decimal`  | Exchange rate         |
| `source`             | `str`      | Platform (`"cross_chain_access"`) |
| `timestamp`          | `datetime` | Quote timestamp       |

---

### TradeResult

**Location**: `shared/models.py`

Normalized trade result format used across all SDKs.

**Fields**:

| Field                | Type       | Description                 |
| -------------------- | ---------- | --------------------------- |
| `tx_hash`            | `str`      | Blockchain transaction hash |
| `order_id`           | `str`      | Platform order ID           |
| `sell_token_address` | `str`      | Token sold                  |
| `sell_amount`        | `Decimal`  | Amount sold                 |
| `buy_token_address`  | `str`      | Token bought                |
| `buy_amount`         | `Decimal`  | Amount bought               |
| `rate`               | `Decimal`  | Exchange rate               |
| `source`             | `str`      | Platform (`"cross_chain_access"`)       |
| `timestamp`          | `datetime` | Trade timestamp             |
| `network`            | `Network`  | Blockchain network          |

---

### OrderSide

**Location**: `cross_chain_access_sdk/cross_chain_access/models.py`

Enum for trade direction.

```python
class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"
```

---

### AccountStatus

**Location**: `cross_chain_access_sdk/cross_chain_access/models.py`

**Fields**:

| Field                     | Type   | Description                      |
| ------------------------- | ------ | -------------------------------- |
| `account_blocked`         | `bool` | Account is blocked               |
| `trading_blocked`         | `bool` | Trading is blocked               |
| `transfers_blocked`       | `bool` | Transfers are blocked            |
| `trade_suspended_by_user` | `bool` | User suspended trading           |
| `market_open`             | `bool` | Market is open                   |
| `account_status`          | `str`  | Status string (e.g., `"ACTIVE"`) |

**Methods**:

- `is_trading_allowed() -> bool`: Returns `True` if all checks pass

---

### AccountFunds

**Location**: `cross_chain_access_sdk/cross_chain_access/models.py`

**Fields**:

| Field                      | Type      | Description               |
| -------------------------- | --------- | ------------------------- |
| `cash`                     | `Decimal` | Available cash            |
| `buying_power`             | `Decimal` | Total buying power        |
| `day_trading_buying_power` | `Decimal` | Day trading buying power  |
| `effective_buying_power`   | `Decimal` | Effective buying power    |
| `non_margin_buying_power`  | `Decimal` | Non-margin buying power   |
| `reg_t_buying_power`       | `Decimal` | Regulation T buying power |

**Methods**:

- `has_sufficient_funds(required_amount: Decimal) -> bool`: Check if buying power is sufficient

---

### Cross-Chain AccessQuote

**Location**: `cross_chain_access_sdk/cross_chain_access/models.py`

**Fields**:

| Field          | Type       | Description      |
| -------------- | ---------- | ---------------- |
| `bid_price`    | `Decimal`  | Best bid price   |
| `ask_price`    | `Decimal`  | Best ask price   |
| `bid_size`     | `Decimal`  | Size at bid      |
| `ask_size`     | `Decimal`  | Size at ask      |
| `timestamp`    | `datetime` | Quote timestamp  |
| `bid_exchange` | `str`      | Exchange for bid |
| `ask_exchange` | `str`      | Exchange for ask |

**Methods**:

- `get_price_for_side(side: OrderSide) -> Decimal`: Returns ask for BUY, bid for SELL

---

### Cross-Chain AccessOrderResponse

**Location**: `cross_chain_access_sdk/cross_chain_access/models.py`

**Fields**:

| Field        | Type               | Description                      |
| ------------ | ------------------ | -------------------------------- |
| `order_id`   | `str`              | Unique order identifier          |
| `symbol`     | `str`              | Trading symbol                   |
| `side`       | `str`              | Order side (`"buy"` or `"sell"`) |
| `quantity`   | `Decimal`          | Order quantity                   |
| `filled_qty` | `Decimal`          | Filled quantity                  |
| `status`     | `str`              | Order status                     |
| `created_at` | `datetime`         | Creation timestamp               |
| `filled_at`  | `datetime \| None` | Fill timestamp                   |

**Methods**:

- `to_dict() -> Dict[str, Any]`: Convert to dictionary

---

## Exceptions

### Exception Hierarchy

```
CrossChainAccessException (base)
├── MarketClosedException
├── AccountBlockedException
├── InsufficientFundsException
├── QuoteUnavailableException
├── OrderFailedException
└── InvalidSymbolException
```

---

### CrossChainAccessException

**Location**: `cross_chain_access_sdk/cross_chain_access/exceptions.py`

Base exception for all Cross-Chain Access-related errors.

---

### MarketClosedException

Raised when attempting to trade outside market hours (14:30-21:00 UTC, weekdays).

**Example**:

```python
try:
    result = await client.buy(...)
except MarketClosedException as e:
    print(f"Market is closed: {e}")
    is_open, msg = MarketHours.get_market_status()
    print(msg)
```

---

### AccountBlockedException

Raised when account is blocked from trading due to restrictions.

**Possible Causes**:

- Account blocked
- Trading blocked
- Transfers blocked
- Trade suspended by user

---

### InsufficientFundsException

Raised when account lacks sufficient funds for a trade.

**Cases**:

- **BUY**: Insufficient buying power for USDC required
- **SELL**: Insufficient RWA token balance

**Example**:

```python
try:
    result = await client.buy(
        rwa_symbol="AAPL",
        usdc_amount=Decimal("10000"),  # $10,000
        ...
    )
except InsufficientFundsException as e:
    print(f"Not enough funds: {e}")
    funds = await client.cross_chain_access_api.get_account_funds()
    print(f"Available: ${funds.buying_power}")
```

---

### QuoteUnavailableException

Raised when real-time quote cannot be retrieved.

**Possible Causes**:

- Symbol temporarily unavailable
- API error
- Network issues

---

### OrderFailedException

Raised when order submission to Cross-Chain Access API fails.

**Possible Causes**:

- API error
- Invalid order parameters
- Backend rejection

---

### InvalidSymbolException

Raised when trading symbol is invalid or not supported.

**Example**:

```python
try:
    quote = await client.get_quote("INVALID")
except InvalidSymbolException as e:
    print(f"Invalid symbol: {e}")
```

---

## Supported Networks

Cross-Chain Access SDK works on networks with USDC support:

- ✅ Polygon (137)
- ✅ Ethereum (1)
- ✅ BSC (56)
- ✅ Base (8453)

USDC addresses are automatically configured per network.

---

## Rate Limits & Performance

- **Market Hours**: 14:30-21:00 UTC only
- **Order Processing**: Near real-time (depends on blockchain)
- **Quote Refresh**: Real-time via API
- **Retry Logic**: 3 attempts with exponential backoff (via `BaseAPIClient`)

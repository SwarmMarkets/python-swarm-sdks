# Trading SDK API Documentation

## Table of Contents

### Core Classes

- [TradingClient](#tradingclient) - Main unified trading client
  - [Constructor](#constructor)
  - [get_quotes()](#get_quotes)
  - [trade()](#trade)
  - [close()](#close)
- [Router](#router) - Smart routing engine
  - [select_platform()](#select_platform)

### Data Models

- [PlatformOption](#platformoption)
- [Quote](#quote)
- [TradeResult](#traderesult)

### Enumerations

- [RoutingStrategy](#routingstrategy)

### Exceptions

- [Exception Hierarchy](#exception-hierarchy)
- [TradingException](#tradingexception)
- [NoLiquidityException](#noliquidityexception)
- [AllPlatformsFailedException](#allplatformsfailedexception)
- [InvalidRoutingStrategyException](#invalidroutingstrategyexception)

### Additional Resources

- [Supported Networks](#supported-networks)
- [Platform Selection Logic](#platform-selection-logic)
- [Performance Considerations](#performance-considerations)

---

## TradingClient

**Location**: `swarm/trading_sdk/sdk/client.py`

The main entry point for unified multi-platform trading. Orchestrates quote aggregation, smart routing, and trade execution across Market Maker and Cross-Chain Access platforms.

### Constructor

```python
TradingClient(
    network: Network,
    private_key: str,
    rpq_api_key: str,
    user_email: Optional[str] = None,
    rpc_url: Optional[str] = None,
    routing_strategy: RoutingStrategy = RoutingStrategy.BEST_PRICE,
)
```

**Parameters**:

| Parameter          | Type              | Required | Description                                                  |
| ------------------ | ----------------- | -------- | ------------------------------------------------------------ |
| `network`          | `Network`         | ✅       | Blockchain network (e.g., `Network.POLYGON`)                 |
| `private_key`      | `str`             | ✅       | Wallet private key (with `0x` prefix)                        |
| `rpq_api_key`      | `str`             | ✅       | API key for Market Maker RPQ Service                         |
| `user_email`       | `str`             | ❌       | User email for Cross-Chain Access (optional but recommended) |
| `rpc_url`          | `str`             | ❌       | Custom RPC endpoint (uses default if not provided)           |
| `routing_strategy` | `RoutingStrategy` | ❌       | Default routing strategy (default: `BEST_PRICE`)             |

**Attributes**:

- `network`: Active blockchain network
- `routing_strategy`: Default routing strategy for trades
- `market_maker_client`: Instance of `MarketMakerClient`
- `cross_chain_access_client`: Instance of `CrossChainAccessClient`

**Example**:

```python
from swarm.trading_sdk import TradingClient, RoutingStrategy
from swarm.shared.models import Network

# Using async context manager (recommended)
async with TradingClient(
    network=Network.POLYGON,
    private_key="0x...",
    rpq_api_key="your_key",
    user_email="user@example.com",
    routing_strategy=RoutingStrategy.BEST_PRICE
) as client:
    result = await client.trade(
        from_token="0xUSDC...",
        to_token="0xRWA...",
        from_amount=Decimal("100"),
        to_token_symbol="AAPL",
        user_email="user@example.com"
    )
    print(f"Traded via {result.source}! TX: {result.tx_hash}")
```

**Raises**:

- `ValueError`: If invalid parameters provided

---

### get_quotes()

Get quotes from all available platforms.

```python
async def get_quotes(
    from_token: str,
    to_token: str,
    from_amount: Optional[Decimal] = None,
    to_amount: Optional[Decimal] = None,
    to_token_symbol: Optional[str] = None,
) -> dict[str, Optional[Quote]]
```

**Parameters**:

| Parameter         | Type      | Required | Description                                          |
| ----------------- | --------- | -------- | ---------------------------------------------------- |
| `from_token`      | `str`     | ✅       | Token address to sell                                |
| `to_token`        | `str`     | ✅       | Token address to buy                                 |
| `from_amount`     | `Decimal` | ⚠️       | Amount to sell (either this or `to_amount`)          |
| `to_amount`       | `Decimal` | ⚠️       | Amount to buy (either this or `from_amount`)         |
| `to_token_symbol` | `str`     | ❌       | Token symbol for Cross-Chain Access (e.g., `"AAPL"`) |

**⚠️ Important**: Provide **either** `from_amount` **OR** `to_amount`, not both.

**Returns**: `dict[str, Optional[Quote]]`

Dictionary with platform names as keys:

```python
{
    "market_maker": Quote or None,
    "cross_chain_access": Quote or None
}
```

**Description**:

Fetches quotes from both platforms in parallel. If a platform is unavailable or fails to provide a quote, its value will be `None`. This method never raises exceptions - it returns `None` for unavailable platforms.

**Example**:

```python
# Get quotes from all platforms
quotes = await client.get_quotes(
    from_token="0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",  # USDC
    to_token="0xRWA...",
    from_amount=Decimal("100"),
    to_token_symbol="AAPL"  # Required for Cross-Chain Access
)

# Check availability and compare
if quotes["market_maker"]:
    print(f"Market Maker: ${quotes['market_maker'].rate}")
    print(f"  You'll get: {quotes['market_maker'].buy_amount} tokens")
else:
    print("Market Maker: Not available")

if quotes["cross_chain_access"]:
    print(f"Cross-Chain Access: ${quotes['cross_chain_access'].rate}")
    print(f"  You'll get: {quotes['cross_chain_access'].buy_amount} tokens")
else:
    print("Cross-Chain Access: Not available")

# Calculate potential savings
if quotes["market_maker"] and quotes["cross_chain_access"]:
    mm_rate = quotes["market_maker"].rate
    cc_rate = quotes["cross_chain_access"].rate

    if mm_rate < cc_rate:
        savings = (cc_rate - mm_rate) * 100  # For 100 USDC
        print(f"Market Maker saves ${savings}")
    else:
        savings = (mm_rate - cc_rate) * 100
        print(f"Cross-Chain Access saves ${savings}")
```

---

### trade()

Execute a trade with smart routing between platforms.

```python
async def trade(
    from_token: str,
    to_token: str,
    user_email: str,
    from_amount: Optional[Decimal] = None,
    to_amount: Optional[Decimal] = None,
    to_token_symbol: Optional[str] = None,
    routing_strategy: Optional[RoutingStrategy] = None,
) -> TradeResult
```

**Parameters**:

| Parameter          | Type              | Required | Description                                                                                        |
| ------------------ | ----------------- | -------- | -------------------------------------------------------------------------------------------------- |
| `from_token`       | `str`             | ✅       | Token address to sell                                                                              |
| `to_token`         | `str`             | ✅       | Token address to buy                                                                               |
| `user_email`       | `str`             | ✅       | User email for notifications                                                                       |
| `from_amount`      | `Decimal`         | ⚠️       | Amount to sell (either this or `to_amount`)                                                        |
| `to_amount`        | `Decimal`         | ⚠️       | Amount to buy (either this or `from_amount`)                                                       |
| `to_token_symbol`  | `str`             | ❌       | Token symbol for Cross-Chain Access (required if Cross-Chain Access might be used, e.g., `"AAPL"`) |
| `routing_strategy` | `RoutingStrategy` | ❌       | Override default routing strategy for this trade                                                   |

**⚠️ Important**: Provide **either** `from_amount` **OR** `to_amount`, not both.

**Returns**: `TradeResult`

Contains:

- `tx_hash`: Blockchain transaction hash
- `order_id`: Platform-specific order/offer ID
- `sell_token_address`: Token sold
- `sell_amount`: Amount sold (normalized)
- `buy_token_address`: Token bought
- `buy_amount`: Amount bought (normalized)
- `rate`: Exchange rate
- `source`: Platform used (`"market_maker"` or `"cross_chain_access"`)
- `timestamp`: Trade execution time
- `network`: Network used

**Trade Flow**:

1. **Get platform options** - Fetches quotes from both platforms in parallel
2. **Check availability** - Validates which platforms are accessible
3. **Apply routing strategy** - Selects optimal platform based on strategy
4. **Execute trade** - Runs trade on selected platform
5. **Fallback (if applicable)** - If primary fails and strategy allows, tries alternative
6. **Return result** - Returns `TradeResult` or raises exception

**Raises**:

| Exception                     | Condition                        |
| ----------------------------- | -------------------------------- |
| `ValueError`                  | Both or neither amounts provided |
| `NoLiquidityException`        | No platforms available           |
| `AllPlatformsFailedException` | Both primary and fallback failed |
| `TradingException`            | Generic trading error            |

**Example**:

```python
from decimal import Decimal

# Basic trade with BEST_PRICE (default)
result = await client.trade(
    from_token="0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",  # USDC
    to_token="0xRWA...",
    from_amount=Decimal("100"),
    to_token_symbol="AAPL",
    user_email="user@example.com"
)

print(f"Trade successful!")
print(f"Platform used: {result.source}")
print(f"TX Hash: {result.tx_hash}")
print(f"Spent: {result.sell_amount} USDC")
print(f"Received: {result.buy_amount} AAPL")
print(f"Rate: ${result.rate}")

# Override routing strategy for this trade
result = await client.trade(
    from_token="0xUSDC...",
    to_token="0xRWA...",
    from_amount=Decimal("100"),
    to_token_symbol="AAPL",
    user_email="user@example.com",
    routing_strategy=RoutingStrategy.MARKET_MAKER_ONLY  # Force Market Maker
)

# Specify buy amount instead of sell amount
result = await client.trade(
    from_token="0xUSDC...",
    to_token="0xRWA...",
    to_amount=Decimal("10"),  # Buy exactly 10 tokens
    to_token_symbol="AAPL",
    user_email="user@example.com"
)
```

**Fallback Behavior**:

Fallback is attempted only for strategies that allow it:

| Strategy                   | Primary Fails? | Tries Fallback? |
| -------------------------- | -------------- | --------------- |
| `BEST_PRICE`               | Yes            | ✅ Yes          |
| `CROSS_CHAIN_ACCESS_FIRST` | Yes            | ✅ Yes          |
| `MARKET_MAKER_FIRST`       | Yes            | ✅ Yes          |
| `CROSS_CHAIN_ACCESS_ONLY`  | Yes            | ❌ No           |
| `MARKET_MAKER_ONLY`        | Yes            | ❌ No           |

**Quote Failures vs Trade Failures**:

- **Quote failure**: Platform is not included in routing (no gas cost)
- **Trade failure**: Transaction reverted on-chain (gas is spent)

The SDK tries to avoid on-chain failures by validating availability first.

---

### close()

Close all clients and cleanup resources.

```python
async def close() -> None
```

**Returns**: `None`

**Description**:

Properly closes both Market Maker and Cross-Chain Access clients, including HTTP clients and remote config fetchers. Called automatically when using async context manager.

**Example**:

```python
client = TradingClient(...)
try:
    result = await client.trade(...)
finally:
    await client.close()  # Manual cleanup
```

---

## Router

**Location**: `swarm/trading_sdk/routing.py`

Smart router for choosing optimal trading platform based on availability, pricing, and user preferences.

### select_platform()

Select optimal platform based on routing strategy.

```python
@staticmethod
def select_platform(
    cross_chain_access_option: PlatformOption,
    market_maker_option: PlatformOption,
    strategy: RoutingStrategy,
    is_buy: bool,
) -> PlatformOption
```

**Parameters**:

| Parameter                   | Type              | Required | Description                                            |
| --------------------------- | ----------------- | -------- | ------------------------------------------------------ |
| `cross_chain_access_option` | `PlatformOption`  | ✅       | Cross-Chain Access platform option with quote          |
| `market_maker_option`       | `PlatformOption`  | ✅       | Market Maker platform option with quote                |
| `strategy`                  | `RoutingStrategy` | ✅       | Routing strategy to apply                              |
| `is_buy`                    | `bool`            | ✅       | Whether this is a buy order (affects price comparison) |

**Returns**: `PlatformOption`

Selected platform option.

**Raises**:

- `NoLiquidityException`: If no platforms available based on strategy

**Description**:

Core routing logic that implements all routing strategies. Makes intelligent decisions based on:

1. **Platform availability** - Checks if platforms have valid quotes
2. **User strategy** - Applies the specified routing preference
3. **Price comparison** - For `BEST_PRICE`, compares rates intelligently
4. **Buy vs Sell** - Uses correct comparison logic for order direction

**Price Comparison Logic**:

```python
# For BUY orders (spending USDC to get tokens)
# Lower rate = better (less USDC per token)
if is_buy:
    better = rate_a < rate_b

# For SELL orders (selling tokens for USDC)
# Higher rate = better (more USDC per token)
else:
    better = rate_a > rate_b
```

**Example**:

```python
from swarm.trading_sdk.routing import Router, PlatformOption, RoutingStrategy

# Create platform options
market_maker_option = PlatformOption(
    platform="market_maker",
    quote=market_maker_quote,
    available=True
)

cross_chain_access_option = PlatformOption(
    platform="cross_chain_access",
    quote=cross_chain_access_quote,
    available=True
)

# Select platform
selected = Router.select_platform(
    cross_chain_access_option=cross_chain_access_option,
    market_maker_option=market_maker_option,
    strategy=RoutingStrategy.BEST_PRICE,
    is_buy=True  # This is a buy order
)

print(f"Selected: {selected.platform}")
print(f"Rate: {selected.quote.rate}")
```

**Strategy Implementation**:

```python
# BEST_PRICE: Compare rates, select cheaper (for buys) or better (for sells)
if strategy == RoutingStrategy.BEST_PRICE:
    if is_buy:
        return min(options, key=lambda o: o.get_effective_rate())
    else:
        return max(options, key=lambda o: o.get_effective_rate())

# CROSS_CHAIN_ACCESS_FIRST: Try Cross-Chain Access, fallback to Market Maker
if strategy == RoutingStrategy.CROSS_CHAIN_ACCESS_FIRST:
    return cross_chain_access_option if cross_chain_access_option.available else market_maker_option

# MARKET_MAKER_FIRST: Try Market Maker, fallback to Cross-Chain Access
if strategy == RoutingStrategy.MARKET_MAKER_FIRST:
    return market_maker_option if market_maker_option.available else cross_chain_access_option

# CROSS_CHAIN_ACCESS_ONLY: Only Cross-Chain Access, fail if unavailable
if strategy == RoutingStrategy.CROSS_CHAIN_ACCESS_ONLY:
    if not cross_chain_access_option.available:
        raise NoLiquidityException("Cross-Chain Access not available")
    return cross_chain_access_option

# MARKET_MAKER_ONLY: Only Market Maker, fail if unavailable
if strategy == RoutingStrategy.MARKET_MAKER_ONLY:
    if not market_maker_option.available:
        raise NoLiquidityException("Market Maker not available")
    return market_maker_option
```

---

## Data Models

### PlatformOption

**Location**: `swarm/trading_sdk/routing.py`

Represents a trading platform option with quote and availability status.

**Fields**:

| Field       | Type    | Description                                                |
| ----------- | ------- | ---------------------------------------------------------- |
| `platform`  | `str`   | Platform name (`"cross_chain_access"` or `"market_maker"`) |
| `quote`     | `Quote` | Quote from this platform (optional)                        |
| `available` | `bool`  | Whether platform is available (default: `True`)            |
| `error`     | `str`   | Error message if unavailable (optional)                    |

**Methods**:

```python
def get_effective_rate() -> Decimal:
    """Get effective rate for comparison.

    Returns:
        Rate (buy_amount / sell_amount)
    """
```

**Example**:

```python
# Create platform option
option = PlatformOption(
    platform="market_maker",
    quote=quote,
    available=True
)

# Get rate for comparison
rate = option.get_effective_rate()
print(f"Rate: {rate}")

# Unavailable platform
unavailable_option = PlatformOption(
    platform="cross_chain_access",
    available=False,
    error="Market is closed"
)
```

---

### Quote

**Location**: `swarm/shared/models.py`

Normalized quote format used across all SDKs.

**Fields**:

| Field                | Type       | Description                                                  |
| -------------------- | ---------- | ------------------------------------------------------------ |
| `sell_token_address` | `str`      | Token being sold                                             |
| `sell_amount`        | `Decimal`  | Amount being sold (normalized)                               |
| `buy_token_address`  | `str`      | Token being bought                                           |
| `buy_amount`         | `Decimal`  | Amount being bought (normalized)                             |
| `rate`               | `Decimal`  | Exchange rate (buy_amount / sell_amount)                     |
| `source`             | `str`      | Platform source (`"market_maker"` or `"cross_chain_access"`) |
| `timestamp`          | `datetime` | Quote timestamp                                              |

---

### TradeResult

**Location**: `swarm/shared/models.py`

Normalized trade result format used across all SDKs.

**Fields**:

| Field                | Type       | Description                                                |
| -------------------- | ---------- | ---------------------------------------------------------- |
| `tx_hash`            | `str`      | Blockchain transaction hash                                |
| `order_id`           | `str`      | Platform-specific order/offer ID                           |
| `sell_token_address` | `str`      | Token sold                                                 |
| `sell_amount`        | `Decimal`  | Amount sold (normalized)                                   |
| `buy_token_address`  | `str`      | Token bought                                               |
| `buy_amount`         | `Decimal`  | Amount bought (normalized)                                 |
| `rate`               | `Decimal`  | Exchange rate                                              |
| `source`             | `str`      | Platform used (`"market_maker"` or `"cross_chain_access"`) |
| `timestamp`          | `datetime` | Trade execution time                                       |
| `network`            | `Network`  | Blockchain network                                         |

---

## Enumerations

### RoutingStrategy

**Location**: `swarm/trading_sdk/routing.py`

Defines how the router selects between platforms.

```python
class RoutingStrategy(str, Enum):
    BEST_PRICE = "best_price"
    # Compares prices and selects platform with best rate
    # Falls back if primary fails

    CROSS_CHAIN_ACCESS_FIRST = "cross_chain_access_first"
    # Tries Cross-Chain Access first
    # Falls back to Market Maker if unavailable

    MARKET_MAKER_FIRST = "market_maker_first"
    # Tries Market Maker first
    # Falls back to Cross-Chain Access if unavailable

    CROSS_CHAIN_ACCESS_ONLY = "cross_chain_access_only"
    # Only uses Cross-Chain Access
    # Fails if unavailable (no fallback)

    MARKET_MAKER_ONLY = "market_maker_only"
    # Only uses Market Maker
    # Fails if unavailable (no fallback)
```

**Strategy Comparison**:

| Strategy                   | Compares Prices? | Has Fallback? | Best For                      |
| -------------------------- | ---------------- | ------------- | ----------------------------- |
| `BEST_PRICE`               | ✅ Yes           | ✅ Yes        | Optimal pricing (recommended) |
| `CROSS_CHAIN_ACCESS_FIRST` | ❌ No            | ✅ Yes        | Stock market preference       |
| `MARKET_MAKER_FIRST`       | ❌ No            | ✅ Yes        | P2P preference                |
| `CROSS_CHAIN_ACCESS_ONLY`  | ❌ No            | ❌ No         | Stock market only             |
| `MARKET_MAKER_ONLY`        | ❌ No            | ❌ No         | P2P only                      |

---

## Exceptions

### Exception Hierarchy

```
TradingException (base)
├── NoLiquidityException
├── AllPlatformsFailedException
└── InvalidRoutingStrategyException
```

---

### TradingException

**Location**: `swarm/trading_sdk/exceptions.py`

Base exception for all Trading SDK-related errors.

---

### NoLiquidityException

Raised when no liquidity available on any platform based on routing strategy.

**Possible Causes**:

- No platforms have quotes
- Selected platform(s) unavailable
- Market closed (Cross-Chain Access)
- No offers (Market Maker)

**Example**:

```python
try:
    result = await client.trade(...)
except NoLiquidityException as e:
    print(f"No liquidity: {e}")
    # Error message includes platform-specific details
    # e.g., "No platforms available. Cross-Chain Access: Market closed; Market Maker: No offers"
```

---

### AllPlatformsFailedException

Raised when all trading platforms fail to execute trade.

This occurs when:

1. Primary platform fails to execute
2. Fallback platform also fails
3. Strategy allows fallback (BEST_PRICE, CROSS_CHAIN_ACCESS_FIRST, MARKET_MAKER_FIRST)

**Error Message Format**:

```
Primary (market_maker): [error details]. Fallback (cross_chain_access): [error details]
```

**Example**:

```python
try:
    result = await client.trade(...)
except AllPlatformsFailedException as e:
    print(f"All platforms failed: {e}")
    # Both primary and fallback attempts failed
    # Check error details for both platforms
```

---

### InvalidRoutingStrategyException

Raised when routing strategy is invalid or not recognized.

This is typically a programming error rather than a runtime error.

---

## Supported Networks

Trading SDK works on networks supported by both underlying platforms:

| Network  | Chain ID | Market Maker | Cross-Chain Access | Trading SDK |
| -------- | -------- | ------------ | ------------------ | ----------- |
| Polygon  | 137      | ✅           | ✅                 | ✅ Both     |
| Ethereum | 1        | ✅           | ✅                 | ✅ Both     |
| Arbitrum | 42161    | ✅           | ❌                 | ✅ MM only  |
| Base     | 8453     | ✅           | ✅                 | ✅ Both     |
| Optimism | 10       | ✅           | ❌                 | ✅ MM only  |

On networks where only one platform is available, the SDK automatically uses that platform regardless of routing strategy.

---

## Platform Selection Logic

### Decision Flow

```
1. Check Cross-Chain Access availability
   ├─ Market hours? (14:30-21:00 UTC, weekdays)
   ├─ Symbol provided?
   ├─ Quote available?
   └─ Result: Available or Unavailable

2. Check Market Maker availability
   ├─ Offers exist?
   ├─ Quote available?
   └─ Result: Available or Unavailable

3. Apply routing strategy
   ├─ BEST_PRICE → Compare rates
   ├─ CROSS_CHAIN_ACCESS_FIRST → Try Cross-Chain Access, fallback Market Maker
   ├─ MARKET_MAKER_FIRST → Try Market Maker, fallback Cross-Chain Access
   ├─ CROSS_CHAIN_ACCESS_ONLY → Only Cross-Chain Access
   └─ MARKET_MAKER_ONLY → Only Market Maker

4. Execute on selected platform

5. If primary fails and strategy allows:
   ├─ Log primary error
   ├─ Select fallback platform
   └─ Execute on fallback

6. Return result or raise exception
```

### Rate Comparison Details

For `BEST_PRICE` strategy:

**BUY Orders** (spending USDC to get tokens):

```python
rate = buy_amount / sell_amount  # tokens per USDC
better_platform = min(platforms, key=rate)  # Lower is better
```

**Example**:

- Market Maker: 1 USDC → 0.010 RWA (rate: 0.010)
- Cross-Chain Access: 1 USDC → 0.012 RWA (rate: 0.012)
- **Winner**: Cross-Chain Access (more tokens per USDC) ✅

**SELL Orders** (selling tokens for USDC):

```python
rate = buy_amount / sell_amount  # USDC per token
better_platform = max(platforms, key=rate)  # Higher is better
```

**Example**:

- Market Maker: 1 RWA → 100 USDC (rate: 100)
- Cross-Chain Access: 1 RWA → 98 USDC (rate: 98)
- **Winner**: Market Maker (more USDC per token) ✅

---

## Performance Considerations

### Quote Fetching

Quotes are fetched in **parallel** from both platforms:

```python
# Parallel execution (fast)
market_maker_task = get_market_maker_quote()
cross_chain_access_task = get_cross_chain_access_quote()
results = await asyncio.gather(market_maker_task, cross_chain_access_task)

# Total time ≈ max(market_maker_time, cross_chain_access_time)
# Not: market_maker_time + cross_chain_access_time
```

**Typical quote times**:

- Market Maker: 100-300ms (RPQ API)
- Cross-Chain Access: 50-150ms (Stock API)
- **Total**: ~300ms (parallel execution)

### Trade Execution

Trade execution time depends on selected platform:

**Market Maker**:

- Blockchain transaction only
- Time: 2-30 seconds (depends on network)
- Gas: Variable by network

**Cross-Chain Access**:

- On-chain transfer + API order submission
- Time: 2-30 seconds (blockchain) + 1-2 seconds (API)
- Gas: Variable by network

### Fallback Overhead

If primary platform fails:

**Quote failure** (no gas cost):

- Time: +0ms (already fetched in parallel)
- Cost: $0 (no transaction)

**Trade failure** (after on-chain submission):

- Time: +2-30 seconds (new transaction)
- Cost: Gas for failed transaction + gas for successful fallback

### Optimization Tips

1. **Reuse client instances** - Don't create new clients for each trade
2. **Use BEST_PRICE** - Gets quotes from both platforms anyway
3. **Provide to_token_symbol** - Enables Cross-Chain Access quotes
4. **Monitor errors** - Adjust strategy if one platform consistently fails

---

**Happy Trading! 🚀**

_Last Updated: November 20, 2025_

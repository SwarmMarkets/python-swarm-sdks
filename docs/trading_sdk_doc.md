# Trading SDK User Guide

Welcome to the **Trading SDK**! This is the **ultimate unified trading solution** that combines Market Maker and Cross-Chain Access into a single, intelligent interface. Get the best price automatically with smart routing, fallback protection, and multi-platform liquidity aggregation.

## Table of Contents

1. [Why Use Trading SDK?](#why-use-trading-sdk)
2. [Prerequisites](#prerequisites)
3. [Supported Networks](#supported-networks)
4. [Installation](#installation)
5. [Initializing the SDK](#initializing-the-sdk)
6. [Understanding Smart Routing](#understanding-smart-routing)
7. [Routing Strategies](#routing-strategies)
   - [BEST_PRICE (Recommended)](#best_price-recommended)
   - [Platform-First Strategies](#platform-first-strategies)
   - [Platform-Only Strategies](#platform-only-strategies)
8. [Getting Quotes](#getting-quotes)
9. [Trading with Smart Routing](#trading-with-smart-routing)
10. [Platform Comparison](#platform-comparison)
11. [Error Handling](#error-handling)
12. [Complete Example](#complete-example)
13. [When to Use Which SDK](#when-to-use-which-sdk)
14. [API Reference](#api-reference)

---

## Why Use Trading SDK?

The Trading SDK is the **highest-level SDK** in the Swarm Collection, providing the **best of both worlds**:

### 🎯 Key Advantages

| Feature                  | Trading SDK         | Market Maker SDK   | Cross-Chain Access SDK |
| ------------------------ | ------------------- | ------------------ | ---------------------- |
| **Smart Routing**        | ✅ Automatic        | ❌ Manual          | ❌ Manual              |
| **Price Comparison**     | ✅ Real-time        | ❌ No              | ❌ No                  |
| **Auto Fallback**        | ✅ Built-in         | ❌ No              | ❌ No                  |
| **24/7 Availability**    | ✅ Via Market Maker | ✅ Yes             | ❌ Market hours only   |
| **Best Price Guarantee** | ✅ Compares both    | ❌ Single platform | ❌ Single platform     |
| **Unified Interface**    | ✅ One method       | ❌ Separate        | ❌ Separate            |

### 💡 Smart Routing Benefits

1. **Automatic Price Optimization** - Always get the best available price
2. **Fallback Protection** - If one platform fails, automatically try the other
3. **Simplified Development** - One `trade()` method for all platforms
4. **Liquidity Aggregation** - Access combined liquidity from both platforms
5. **Flexible Strategies** - Choose routing behavior based on your needs

### ⚠️ Trade-offs

The Trading SDK is powerful but has some limitations:

| What You Gain           | What You Lose                                          |
| ----------------------- | ------------------------------------------------------ |
| ✅ Automatic routing    | ❌ No direct offer creation (Market Maker feature)     |
| ✅ Price comparison     | ❌ No direct offer cancellation (Market Maker feature) |
| ✅ Simplified API       | ❌ Less fine-grained control                           |
| ✅ Best price selection | ❌ Requires both platform credentials                  |

> 💡 **Use Trading SDK** when you want the best price and simplicity. Use individual SDKs when you need specialized features like creating liquidity offers.

---

## Prerequisites

Before you can use the Trading SDK:

### 1. Required Items

You'll need:

- **Python 3.8+** installed on your system
- A **wallet with a private key**
- **Tokens to trade** (e.g., USDC, RWA tokens)
- **Gas tokens** (MATIC, ETH, etc.) for transaction fees
- **RPQ API Key** - Required for Market Maker quotes
- **User email** - Required for Cross-Chain Access

### 2. Platform Requirements

Since Trading SDK uses both platforms, you may need:

**For Cross-Chain Access:**

- ✅ **KYC verification** at [https://dotc.eth.limo/](https://dotc.eth.limo/)
- ⏰ **Aware of market hours** (14:30-21:00 UTC, weekdays)

**For Market Maker:**

- ✅ **RPQ API Key** for quote access
- 🔄 **24/7 availability** (no restrictions)

> 💡 **Good News**: Trading SDK works even if only ONE platform is available! If you haven't completed KYC, it will automatically use Market Maker.

### 3. Environment Setup

Optionally set the environment mode:

```bash
# Development mode (default)
export SWARM_COLLECTION_MODE=dev

# Production mode
export SWARM_COLLECTION_MODE=prod
```

---

## Supported Networks

The Trading SDK works on all networks supported by both underlying platforms:

### Available Networks

| Network  | Chain ID | Gas Token | Market Maker | Cross-Chain Access |
| -------- | -------- | --------- | ------------ | ------------------ |
| Polygon  | 137      | MATIC     | ✅           | ✅                 |
| Ethereum | 1        | ETH       | ✅           | ✅                 |
| Arbitrum | 42161    | ETH       | ✅           | ❌                 |
| Base     | 8453     | ETH       | ✅           | ✅                 |
| Optimism | 10       | ETH       | ✅           | ❌                 |

> 💡 **Note**: On networks where only one platform is available, the SDK automatically uses that platform.

---

## Installation

Install the Swarm Collection SDK package:

```bash
pip install swarm-collection
```

Or install from source:

```bash
git clone https://github.com/your-org/swarm-collection.git
cd swarm-collection
pip install -e .
```

---

## Initializing the SDK

Setting up the Trading SDK is straightforward:

### Basic Setup

```python
from swarm.trading_sdk import TradingClient, RoutingStrategy
from swarm.shared.models import Network

# Initialize with smart routing
async with TradingClient(
    network=Network.POLYGON,
    private_key="0x...",
    rpq_api_key="your_rpq_key",
    user_email="you@example.com",
    routing_strategy=RoutingStrategy.BEST_PRICE  # Default
) as client:
    # Start trading with automatic platform selection!
    pass
```

### Configuration Options

| Parameter          | Type              | Required | Description                                      |
| ------------------ | ----------------- | -------- | ------------------------------------------------ |
| `network`          | `Network`         | ✅       | Blockchain network (e.g., `Network.POLYGON`)     |
| `private_key`      | `str`             | ✅       | Wallet private key (with `0x` prefix)            |
| `rpq_api_key`      | `str`             | ✅       | API key for Market Maker RPQ Service             |
| `user_email`       | `str`             | ❌       | Email for Cross-Chain Access (recommended)       |
| `rpc_url`          | `str`             | ❌       | Custom RPC endpoint (uses default if omitted)    |
| `routing_strategy` | `RoutingStrategy` | ❌       | Default routing strategy (default: `BEST_PRICE`) |

### Using Context Managers (Recommended)

Always use the `async with` pattern for automatic cleanup:

```python
# ✅ Good - Automatic cleanup
async with TradingClient(...) as client:
    result = await client.trade(...)

# ❌ Bad - Manual cleanup needed
client = TradingClient(...)
result = await client.trade(...)
await client.close()  # Don't forget this!
```

---

## Understanding Smart Routing

The Trading SDK's **Router** is the brain that decides which platform to use:

### How It Works

```
User Trade Request
        ↓
    [Router]
        ↓
   ┌────┴────┐
   ↓         ↓
Market    Cross-Chain
Maker     Access
   ↓         ↓
   └────┬────┘
        ↓
  Best Platform Selected
        ↓
  Trade Executed
```

### Routing Process

1. **Get Quotes** - Fetches quotes from both platforms in parallel
2. **Check Availability** - Validates which platforms are available
3. **Apply Strategy** - Uses your routing strategy to select platform
4. **Execute Trade** - Runs trade on selected platform
5. **Fallback (if needed)** - Automatically tries alternative if primary fails

### Smart Decisions

The Router considers:

- ✅ **Price** - Which platform offers better rate
- ✅ **Availability** - Is platform accessible (market hours, liquidity)
- ✅ **User Strategy** - Your preference (best price, specific platform, etc.)
- ✅ **Error Recovery** - Automatic fallback on failure

---

## Routing Strategies

Choose from 5 routing strategies to control how the SDK selects platforms:

### BEST_PRICE (Recommended)

**Best for**: Most users who want optimal pricing

```python
async with TradingClient(
    network=Network.POLYGON,
    private_key="0x...",
    rpq_api_key="your_key",
    user_email="you@example.com",
    routing_strategy=RoutingStrategy.BEST_PRICE
) as client:
    result = await client.trade(...)
```

**How it works:**

1. Gets quotes from both platforms
2. Compares prices (considers buy vs sell direction)
3. Selects platform with best price
4. Falls back to alternative if primary fails

**Example scenario:**

```
Market Maker quote: 1 RWA = 100 USDC
Cross-Chain Access quote: 1 RWA = 98 USDC

For BUY: Selects Cross-Chain Access (cheaper at 98 USDC) ✅
For SELL: Selects Market Maker (better return at 100 USDC) ✅
```

### Platform-First Strategies

Try a preferred platform first, with automatic fallback:

#### CROSS_CHAIN_ACCESS_FIRST

**Best for**: Stock trading during market hours with fallback

```python
routing_strategy=RoutingStrategy.CROSS_CHAIN_ACCESS_FIRST
```

**Flow:**

1. Try Cross-Chain Access first
2. If unavailable (market closed, no liquidity), use Market Maker
3. If both fail, raise error

**Use case:** "I prefer stock market pricing, but use P2P if market is closed"

#### MARKET_MAKER_FIRST

**Best for**: 24/7 trading with P2P preference

```python
routing_strategy=RoutingStrategy.MARKET_MAKER_FIRST
```

**Flow:**

1. Try Market Maker first
2. If unavailable (no offers), use Cross-Chain Access
3. If both fail, raise error

**Use case:** "I prefer decentralized P2P, but use centralized if no offers"

### Platform-Only Strategies

Force using a specific platform with no fallback:

#### CROSS_CHAIN_ACCESS_ONLY

**Best for**: Stock market only, fail if unavailable

```python
routing_strategy=RoutingStrategy.CROSS_CHAIN_ACCESS_ONLY
```

**Flow:**

1. Only use Cross-Chain Access
2. Fail if unavailable (market hours, no liquidity)
3. No fallback

**Use case:** "I only want stock market prices, fail otherwise"

#### MARKET_MAKER_ONLY

**Best for**: P2P only, fail if unavailable

```python
routing_strategy=RoutingStrategy.MARKET_MAKER_ONLY
```

**Flow:**

1. Only use Market Maker
2. Fail if unavailable (no offers)
3. No fallback

**Use case:** "I only want decentralized P2P, fail otherwise"

### Strategy Comparison Table

| Strategy                   | Tries Both? | Fallback? | Best For                      |
| -------------------------- | ----------- | --------- | ----------------------------- |
| `BEST_PRICE`               | ✅ Yes      | ✅ Yes    | Optimal pricing (recommended) |
| `CROSS_CHAIN_ACCESS_FIRST` | ❌ No       | ✅ Yes    | Stock market preference       |
| `MARKET_MAKER_FIRST`       | ❌ No       | ✅ Yes    | P2P preference                |
| `CROSS_CHAIN_ACCESS_ONLY`  | ❌ No       | ❌ No     | Stock market only             |
| `MARKET_MAKER_ONLY`        | ❌ No       | ❌ No     | P2P only                      |

---

## Getting Quotes

Compare quotes from both platforms before trading:

```python
from decimal import Decimal

async with TradingClient(...) as client:
    # Get quotes from all platforms
    quotes = await client.get_quotes(
        from_token="0xUSDC...",
        to_token="0xRWA...",
        from_amount=Decimal("100"),
        to_token_symbol="AAPL"  # Required for Cross-Chain Access
    )

    # Compare quotes
    print("📊 Quote Comparison:")
    print("-" * 40)

    if quotes["market_maker"]:
        print(f"Market Maker:   ${quotes['market_maker'].rate}")
        print(f"  You'll get: {quotes['market_maker'].buy_amount} tokens")
    else:
        print(f"Market Maker:   ❌ Not available")

    if quotes["cross_chain_access"]:
        print(f"Cross-Chain Access: ${quotes['cross_chain_access'].rate}")
        print(f"  You'll get: {quotes['cross_chain_access'].buy_amount} tokens")
    else:
        print(f"Cross-Chain Access: ❌ Not available")

    # Determine best price
    if quotes["market_maker"] and quotes["cross_chain_access"]:
        mm_rate = quotes["market_maker"].rate
        cc_rate = quotes["cross_chain_access"].rate

        if mm_rate < cc_rate:
            print(f"\n🏆 Best price: Market Maker (saves ${cc_rate - mm_rate} per token)")
        else:
            print(f"\n🏆 Best price: Cross-Chain Access (saves ${mm_rate - cc_rate} per token)")
```

### What You Get

The `get_quotes()` method returns a dictionary:

```python
{
    "market_maker": Quote or None,
    "cross_chain_access": Quote or None
}
```

Each `Quote` contains:

- `sell_token_address`: Token being sold
- `sell_amount`: Amount being sold
- `buy_token_address`: Token being bought
- `buy_amount`: Amount being bought
- `rate`: Exchange rate
- `source`: Platform name
- `timestamp`: Quote timestamp

> 💡 **Tip**: Use `get_quotes()` to show users price comparison before executing trades!

---

## Trading with Smart Routing

Execute trades with automatic platform selection:

### Basic Trade

```python
from decimal import Decimal

async with TradingClient(
    network=Network.POLYGON,
    private_key="0x...",
    rpq_api_key="your_key",
    user_email="you@example.com"
) as client:

    # Buy RWA tokens with USDC (automatic routing)
    result = await client.trade(
        from_token="0xUSDC...",
        to_token="0xRWA...",
        from_amount=Decimal("100"),
        to_token_symbol="AAPL",
        user_email="you@example.com"
    )

    print(f"✅ Trade successful!")
    print(f"   Platform: {result.source}")
    print(f"   TX Hash: {result.tx_hash}")
    print(f"   Spent: {result.sell_amount} USDC")
    print(f"   Received: {result.buy_amount} AAPL")
    print(f"   Rate: ${result.rate}")
```

### What Happens Behind the Scenes

```
1. SDK gets quotes from both platforms in parallel
   ├─ Market Maker: Query RPQ API
   └─ Cross-Chain Access: Check market hours, get quote

2. Router selects optimal platform
   ├─ Checks availability
   ├─ Compares prices (if BEST_PRICE)
   └─ Applies routing strategy

3. SDK executes trade on selected platform
   ├─ Approves tokens
   ├─ Submits transaction
   └─ Waits for confirmation

4. If primary fails, tries fallback (if strategy allows)
   ├─ Logs primary error
   ├─ Selects alternative platform
   └─ Attempts trade again

5. Returns TradeResult or raises exception
```

### Override Routing Strategy

You can override the default strategy per trade:

```python
# Client has BEST_PRICE as default
async with TradingClient(
    routing_strategy=RoutingStrategy.BEST_PRICE,
    ...
) as client:

    # Override to use only Market Maker for this trade
    result = await client.trade(
        from_token="0xUSDC...",
        to_token="0xRWA...",
        from_amount=Decimal("100"),
        user_email="you@example.com",
        routing_strategy=RoutingStrategy.MARKET_MAKER_ONLY  # Override!
    )
```

### Two Ways to Specify Amount

Just like individual SDKs, you can specify either the amount to sell OR buy:

**Option 1: Specify Amount to Sell**

```python
result = await client.trade(
    from_token="0xUSDC...",
    to_token="0xRWA...",
    from_amount=Decimal("100"),  # Spend 100 USDC
    to_token_symbol="AAPL",
    user_email="you@example.com"
)
```

**Option 2: Specify Amount to Buy**

```python
result = await client.trade(
    from_token="0xUSDC...",
    to_token="0xRWA...",
    to_amount=Decimal("10"),  # Receive 10 RWA tokens
    to_token_symbol="AAPL",
    user_email="you@example.com"
)
```

> ⚠️ **Important**: Provide **either** `from_amount` **OR** `to_amount`, not both!

---

## Platform Comparison

Understanding the differences helps you choose the right strategy:

### Feature Comparison

| Feature          | Market Maker             | Cross-Chain Access         | Trading SDK                    |
| ---------------- | ------------------------ | -------------------------- | ------------------------------ |
| **Execution**    | P2P on-chain             | Centralized API + on-chain | Smart routing to both          |
| **Availability** | 24/7 (if offers exist)   | Market hours only          | Best of both                   |
| **KYC Required** | ❌ No                    | ✅ Yes                     | ✅ For Cross-Chain Access only |
| **Price Source** | Community offers         | Stock market               | Compares both                  |
| **Liquidity**    | Depends on offers        | High (stock market)        | Combined                       |
| **Speed**        | Fast (on-chain only)     | Fast (API + on-chain)      | Depends on selected            |
| **Fees**         | Gas + optional affiliate | Gas + trading fees         | Depends on selected            |

### When Each Platform Excels

**Market Maker is better for:**

- ✅ 24/7 trading needs
- ✅ Avoiding KYC
- ✅ Lower fees (sometimes)
- ✅ Decentralization preference

**Cross-Chain Access is better for:**

- ✅ Stock market pricing
- ✅ High liquidity
- ✅ Consistent pricing during market hours
- ✅ Regulatory compliance

**Trading SDK is better for:**

- ✅ **Automatic best price**
- ✅ **Maximum uptime** (fallback)
- ✅ **Simplified development**
- ✅ **Combined liquidity**

---

## Error Handling

The Trading SDK provides clear error messages:

### Common Exceptions

```python
from swarm.trading_sdk import TradingClient, RoutingStrategy
from swarm.trading_sdk.exceptions import (
    TradingException,
    NoLiquidityException,
    AllPlatformsFailedException,
)

async with TradingClient(...) as client:
    try:
        result = await client.trade(
            from_token="0xUSDC...",
            to_token="0xRWA...",
            from_amount=Decimal("100"),
            to_token_symbol="AAPL",
            user_email="you@example.com"
        )
        print(f"✅ Trade successful on {result.source}!")

    except NoLiquidityException as e:
        print(f"❌ No platforms available: {e}")
        print("💡 Try:")
        print("   - Wait for market hours (Cross-Chain Access)")
        print("   - Check for Market Maker offers")
        print("   - Try a different token pair")

    except AllPlatformsFailedException as e:
        print(f"❌ All platforms failed: {e}")
        print("💡 Both primary and fallback failed")
        print("   Check the error details above")

    except ValueError as e:
        print(f"❌ Invalid parameters: {e}")
        print("💡 Provide either from_amount OR to_amount, not both")

    except TradingException as e:
        print(f"❌ Trading error: {e}")
        print("💡 Check logs for details")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("💡 Contact support if this persists")
```

### Error Reference

| Exception                     | When It Happens        | How to Handle                    |
| ----------------------------- | ---------------------- | -------------------------------- |
| `NoLiquidityException`        | No platforms available | Wait for market hours or offers  |
| `AllPlatformsFailedException` | Both platforms failed  | Check error details, retry later |
| `ValueError`                  | Invalid parameters     | Fix parameter combination        |
| `TradingException`            | Generic trading error  | Check logs, contact support      |

Platform-specific errors are also possible:

- **Market Maker errors**: `NoOffersAvailableException`, `OfferNotFoundError`, etc.
- **Cross-Chain Access errors**: `MarketClosedException`, `InsufficientFundsException`, etc.

These are caught and handled by the routing logic, triggering fallbacks when appropriate.

---

## Complete Example

Here's a comprehensive example showing best practices:

```python
import asyncio
import logging
from decimal import Decimal
from dotenv import load_dotenv
import os

from swarm.trading_sdk import TradingClient, RoutingStrategy
from swarm.shared.models import Network
from swarm.trading_sdk.exceptions import (
    NoLiquidityException,
    AllPlatformsFailedException,
    TradingException,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()


async def main():
    """
    Complete example: Smart trading with automatic platform selection
    """

    # Configuration
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")
    RPQ_API_KEY = os.getenv("RPQ_API_KEY")
    USER_EMAIL = os.getenv("USER_EMAIL")
    USDC_ADDRESS = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"  # Polygon
    RWA_ADDRESS = "0x..."  # Replace with actual RWA token

    if not all([PRIVATE_KEY, RPQ_API_KEY, USER_EMAIL]):
        print("❌ Missing required environment variables")
        return

    # Initialize Trading SDK with smart routing
    async with TradingClient(
        network=Network.POLYGON,
        private_key=PRIVATE_KEY,
        rpq_api_key=RPQ_API_KEY,
        user_email=USER_EMAIL,
        routing_strategy=RoutingStrategy.BEST_PRICE
    ) as client:

        print(f"✅ Connected to Trading SDK")
        print(f"   Network: {Network.POLYGON.name}")
        print(f"   Strategy: BEST_PRICE (automatic optimization)")
        print()

        try:
            # Step 1: Get quotes from all platforms
            print("📊 Step 1: Get Quotes from All Platforms")
            quotes = await client.get_quotes(
                from_token=USDC_ADDRESS,
                to_token=RWA_ADDRESS,
                from_amount=Decimal("100"),
                to_token_symbol="AAPL"
            )

            print("\nQuote Comparison:")
            print("-" * 50)

            # Display quotes
            platforms_available = 0
            best_rate = None
            best_platform = None

            for platform, quote in quotes.items():
                if quote:
                    platforms_available += 1
                    print(f"{platform.replace('_', ' ').title()}:")
                    print(f"  Rate: ${quote.rate}")
                    print(f"  You'll receive: {quote.buy_amount} tokens")

                    if best_rate is None or quote.rate < best_rate:
                        best_rate = quote.rate
                        best_platform = platform
                else:
                    print(f"{platform.replace('_', ' ').title()}: ❌ Not available")

            if best_platform:
                print(f"\n🏆 Best price: {best_platform.replace('_', ' ').title()} (${best_rate})")
            print()

            # Step 2: Execute trade with smart routing
            print("🔄 Step 2: Execute Trade with Smart Routing")
            print("⚠️  Trade execution commented out for safety")

            # Uncomment to execute real trade:
            """
            result = await client.trade(
                from_token=USDC_ADDRESS,
                to_token=RWA_ADDRESS,
                from_amount=Decimal("100"),
                to_token_symbol="AAPL",
                user_email=USER_EMAIL
            )

            print(f"\n✅ Trade Successful!")
            print(f"   Platform: {result.source}")
            print(f"   TX Hash: {result.tx_hash}")
            print(f"   Spent: {result.sell_amount} USDC")
            print(f"   Received: {result.buy_amount} AAPL")
            print(f"   Rate: ${result.rate}")
            print(f"   Network: {result.network.name}")
            """

        except NoLiquidityException as e:
            print(f"\n❌ No Liquidity Available")
            print(f"   Error: {e}")
            print("\n💡 Suggestions:")
            print("   - Check if market hours apply (Cross-Chain Access)")
            print("   - Verify Market Maker offers exist")
            print("   - Try a different amount or token pair")

        except AllPlatformsFailedException as e:
            print(f"\n❌ All Platforms Failed")
            print(f"   Error: {e}")
            print("\n💡 Both primary and fallback attempts failed")
            print("   Review the error details and try again later")

        except ValueError as e:
            print(f"\n❌ Invalid Parameters")
            print(f"   Error: {e}")
            print("\n💡 Ensure you provide either from_amount OR to_amount")

        except TradingException as e:
            print(f"\n❌ Trading Error")
            print(f"   Error: {e}")
            print("\n💡 Check logs for more details")

        except Exception as e:
            print(f"\n❌ Unexpected Error")
            print(f"   Error: {e}")
            print("\n💡 Contact support if this persists")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## When to Use Which SDK

Choose the right SDK for your needs:

### Use Trading SDK When:

✅ You want **automatic best price** selection  
✅ You need **fallback protection**  
✅ You prefer **simplified API** over fine control  
✅ You want to **maximize liquidity** access  
✅ You're building a **user-facing trading app**

**Perfect for**: Trading UIs, arbitrage bots, portfolio managers

### Use Market Maker SDK When:

✅ You want to **create liquidity offers**  
✅ You need **24/7 guaranteed availability**  
✅ You prefer **decentralized-only** trading  
✅ You want to **earn as market maker**  
✅ You need **direct contract interaction**

**Perfect for**: Market makers, liquidity providers, DeFi protocols

### Use Cross-Chain Access SDK When:

✅ You need **stock market pricing** only  
✅ You want **high liquidity** during market hours  
✅ You're building **stock trading apps**  
✅ You need **regulatory compliance** (KYC)  
✅ You want **consistent pricing**

**Perfect for**: Stock trading platforms, regulated services

### Decision Tree

```
Do you need to CREATE offers?
├─ YES → Market Maker SDK
└─ NO → Continue

Do you only trade stocks during market hours?
├─ YES → Cross-Chain Access SDK
└─ NO → Continue

Do you want automatic best price?
├─ YES → Trading SDK ✅ (Recommended!)
└─ NO → Market Maker SDK or Cross-Chain Access SDK
```

---

## API Reference

For detailed technical documentation of all methods, parameters, and return types, see:

📚 **[Trading SDK API Reference](./trading_sdk_references.md)**

The API reference includes:

- Complete method signatures
- Routing strategy details
- Parameter descriptions
- Return type details
- Exception specifications
- Advanced usage examples

---

## Need Help?

### Resources

- 📖 **API Reference**: [trading_sdk_references.md](./trading_sdk_references.md)
- 📚 **Market Maker SDK Docs**: [market_maker_sdk_doc.md](./market_maker_sdk_doc.md)
- 📚 **Cross-Chain Access SDK Docs**: [cross_chain_access_sdk_doc.md](./cross_chain_access_sdk_doc.md)
- 💬 **Support**: Contact us through the platform
- 🐛 **Issues**: Report bugs on GitHub

### Common Questions

**Q: Does Trading SDK charge extra fees?**  
A: No! You only pay the fees of whichever platform is selected. No additional SDK fees.

**Q: Can I use Trading SDK without KYC?**  
A: Yes! It will automatically use Market Maker if Cross-Chain Access is unavailable. However, you won't get stock market pricing.

**Q: What happens if both platforms fail?**  
A: The SDK raises `AllPlatformsFailedException` with details about both failures.

**Q: Can I force using a specific platform?**  
A: Yes! Use `MARKET_MAKER_ONLY` or `CROSS_CHAIN_ACCESS_ONLY` routing strategies.

**Q: How accurate is the price comparison?**  
A: Very accurate! Quotes are fetched in real-time from both platforms before selection.

**Q: Does fallback cost extra gas?**  
A: Only if the primary trade is actually submitted on-chain but reverts. Quote failures don't cost gas.

**Q: Can I see which platform was used?**  
A: Yes! Check `result.source` in the `TradeResult` - it will be either `"market_maker"` or `"cross_chain_access"`.

---

## Quick Reference

### Import Statements

```python
from swarm.trading_sdk import TradingClient, RoutingStrategy
from swarm.shared.models import Network
from swarm.trading_sdk.exceptions import (
    NoLiquidityException,
    AllPlatformsFailedException,
    TradingException,
)
from decimal import Decimal
```

### Initialize Client

```python
async with TradingClient(
    network=Network.POLYGON,
    private_key="0x...",
    rpq_api_key="your_key",
    user_email="you@example.com",
    routing_strategy=RoutingStrategy.BEST_PRICE
) as client:
    # Your code here
    pass
```

### Get Quotes

```python
quotes = await client.get_quotes(
    from_token="0xUSDC...",
    to_token="0xRWA...",
    from_amount=Decimal("100"),
    to_token_symbol="AAPL"
)
```

### Execute Trade

```python
result = await client.trade(
    from_token="0xUSDC...",
    to_token="0xRWA...",
    from_amount=Decimal("100"),
    to_token_symbol="AAPL",
    user_email="you@example.com"
)
```

### Routing Strategies

```python
RoutingStrategy.BEST_PRICE              # Automatic (recommended)
RoutingStrategy.CROSS_CHAIN_ACCESS_FIRST # Prefer Cross-Chain Access
RoutingStrategy.MARKET_MAKER_FIRST      # Prefer Market Maker
RoutingStrategy.CROSS_CHAIN_ACCESS_ONLY # Cross-Chain Access only
RoutingStrategy.MARKET_MAKER_ONLY       # Market Maker only
```

---

**Happy Trading! 🚀**

_Last Updated: November 20, 2025_

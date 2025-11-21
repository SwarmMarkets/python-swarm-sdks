# Market Maker SDK User Guide

Welcome to the **Market Maker SDK**! This guide will help you start trading Real World Assets (RWAs) through decentralized, peer-to-peer offers on-chain. Trade 24/7 with no market hours restrictions using smart contracts.

## Table of Contents

1. [What is Market Maker?](#what-is-market-maker)
2. [Prerequisites](#prerequisites)
3. [Supported Networks](#supported-networks)
4. [Installation](#installation)
5. [Initializing the SDK](#initializing-the-sdk)
6. [Understanding Offers](#understanding-offers)
7. [Getting Offers and Quotes](#getting-offers-and-quotes)
   - [Browse Available Offers](#browse-available-offers)
   - [Get Best Offers](#get-best-offers)
   - [Get Quotes](#get-quotes)
8. [Trading (Taking Offers)](#trading-taking-offers)
   - [Taking Fixed-Price Offers](#taking-fixed-price-offers)
   - [Taking Dynamic-Price Offers](#taking-dynamic-price-offers)
9. [Creating Your Own Offers](#creating-your-own-offers)
10. [Canceling Offers](#canceling-offers)
11. [Error Handling](#error-handling)
12. [Complete Example](#complete-example)
13. [API Reference](#api-reference)

---

## What is Market Maker?

Market Maker is a **decentralized Over-The-Counter (OTC) trading protocol** that allows you to:

- ✅ **Trade 24/7** - No market hours restrictions
- ✅ **Peer-to-peer** - Direct trades via smart contracts
- ✅ **On-chain execution** - Fully decentralized and transparent
- ✅ **Become a liquidity provider** - Create your own offers
- ✅ **Fixed or dynamic pricing** - Use static prices or live price feeds

Unlike Cross-Chain Access (centralized stock trading), Market Maker operates entirely through blockchain smart contracts.

---

## Prerequisites

Before you can use the Market Maker SDK:

### 1. Required Items

You'll need:

- **Python 3.8+** installed on your system
- A **wallet with a private key**
- **Tokens to trade** (e.g., USDC, RWA tokens)
- **Gas tokens** (MATIC, ETH, etc.) for transaction fees
- **RPQ API Key** - Required for accessing offer data

### 2. Get Your RPQ API Key

The RPQ (Request for Quote) Service provides market data for Market Maker offers:

1. Contact support or visit the platform to request an API key
2. Set your API key in environment variables: `RPQ_API_KEY=your_key_here`

> ⚠️ **Important**: The RPQ API Key is required for getting offers, best offers, and quotes. Without it, you can only execute trades if you already know the offer ID.

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

The Market Maker SDK works on multiple blockchain networks:

### Available Networks

| Network  | Chain ID | Gas Token | Contract Available |
| -------- | -------- | --------- | ------------------ |
| Polygon  | 137      | MATIC     | ✅                 |
| Ethereum | 1        | ETH       | ✅                 |
| Arbitrum | 42161    | ETH       | ✅                 |
| Base     | 8453     | ETH       | ✅                 |
| Optimism | 10       | ETH       | ✅                 |

### Important Notes

- **No KYC Required**: Unlike Cross-Chain Access, Market Maker is permissionless
- **24/7 Trading**: Trade anytime, any day
- **Gas Fees**: You'll need native tokens for gas (MATIC, ETH, etc.)
- **Contract Addresses**: Automatically loaded from remote config

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

Setting up the Market Maker SDK is simple:

### Basic Setup

```python
from swarm.market_maker_sdk import MarketMakerClient
from swarm.shared.models import Network

# Initialize the client
async with MarketMakerClient(
    network=Network.POLYGON,           # Choose your network
    private_key="0x...",               # Your wallet private key
    rpq_api_key="your_rpq_key",        # RPQ Service API key
    user_email="you@example.com"       # Optional: for authentication
) as client:
    # Start trading!
    pass
```

### Configuration Options

| Parameter     | Type      | Required | Description                                   |
| ------------- | --------- | -------- | --------------------------------------------- |
| `network`     | `Network` | ✅       | Blockchain network (e.g., `Network.POLYGON`)  |
| `private_key` | `str`     | ✅       | Wallet private key (with `0x` prefix)         |
| `rpq_api_key` | `str`     | ✅       | API key for RPQ Service                       |
| `user_email`  | `str`     | ❌       | Email for Swarm authentication (optional)     |
| `rpc_url`     | `str`     | ❌       | Custom RPC endpoint (uses default if omitted) |

### Using Context Managers (Recommended)

Always use the `async with` pattern for automatic cleanup:

```python
# ✅ Good - Automatic cleanup
async with MarketMakerClient(...) as client:
    result = await client.trade(...)

# ❌ Bad - Manual cleanup needed
client = MarketMakerClient(...)
await client.authenticate()
result = await client.trade(...)
await client.close()  # Don't forget this!
```

---

## Understanding Offers

Before trading, it's important to understand how Market Maker offers work:

### Offer Terminology

- **Deposit Asset**: What the **maker deposited** (what **takers receive**)
- **Withdrawal Asset**: What the **maker wants** (what **takers pay**)
- **Maker**: The person who created the offer
- **Taker**: The person who accepts (takes) the offer

### Example: Buying RWA Tokens

```
Maker's Offer:
  - Deposit: 10 RWA tokens
  - Withdrawal: 1000 USDC
  - Rate: 100 USDC per RWA

When you TAKE this offer:
  - You PAY: 1000 USDC (withdrawal asset)
  - You RECEIVE: 10 RWA (deposit asset)
```

### Offer Types

**Partial Offers**:

- Can be taken in parts
- Multiple takers can fill
- Useful for large amounts

**Block Offers**:

- Must be taken all at once
- One taker only
- Useful for specific amounts

### Pricing Types

**Fixed Pricing**:

- Price set when offer created
- Won't change during trade
- Simple and predictable

**Dynamic Pricing**:

- Uses live price feeds
- Updates in real-time
- Includes slippage protection

---

## Getting Offers and Quotes

Before trading, you'll want to explore available offers:

### Browse Available Offers

Get a list of all available offers for a token pair:

```python
async with MarketMakerClient(...) as client:
    # Get all offers where you buy RWA by selling USDC
    offers = await client.rpq_client.get_offers(
        buy_asset_address="0xRWA...",   # Token you want to receive
        sell_asset_address="0xUSDC...", # Token you want to pay with
        page=0,
        limit=10
    )

    print(f"Found {len(offers)} offers")

    for offer in offers:
        print(f"Offer ID: {offer.id}")
        print(f"  Deposit: {offer.amount_in} {offer.deposit_asset.symbol}")
        print(f"  Withdraw: {offer.amount_out} {offer.withdrawal_asset.symbol}")
        print(f"  Available: {offer.available_amount}")
        print(f"  Type: {offer.offer_type.value}")
        print(f"  Status: {offer.offer_status.value}")
        print()
```

> 💡 **Tip**: Use pagination with `page` and `limit` parameters for large result sets.

### Get Best Offers

Find the optimal combination of offers to reach your target amount:

```python
async with MarketMakerClient(...) as client:
    # Find best offers to spend 100 USDC
    best_offers = await client.rpq_client.get_best_offers(
        buy_asset_address="0xRWA...",   # What you want to receive
        sell_asset_address="0xUSDC...", # What you want to pay
        target_sell_amount="100"        # How much USDC to spend
    )

    print(f"To spend {best_offers.result.target_amount}:")
    print(f"  Will pay: {best_offers.result.total_withdrawal_amount_paid}")
    print(f"  Using {len(best_offers.result.selected_offers)} offer(s)")

    for offer in best_offers.result.selected_offers:
        print(f"\n  Offer {offer.id}:")
        print(f"    Amount: {offer.withdrawal_amount_paid}")
        print(f"    Price: {offer.price_per_unit}")
        print(f"    Type: {offer.pricing_type.value}")
```

**Two Ways to Specify Amount**:

```python
# Option 1: Specify how much to SELL
best_offers = await client.rpq_client.get_best_offers(
    buy_asset_address="0xRWA...",
    sell_asset_address="0xUSDC...",
    target_sell_amount="100"  # Spend 100 USDC
)

# Option 2: Specify how much to BUY
best_offers = await client.rpq_client.get_best_offers(
    buy_asset_address="0xRWA...",
    sell_asset_address="0xUSDC...",
    target_buy_amount="10"  # Receive 10 RWA tokens
)
```

> ⚠️ **Important**: Provide **either** `target_sell_amount` **OR** `target_buy_amount`, not both!

### Get Quotes

Get a quick price quote without offer details:

```python
async with MarketMakerClient(...) as client:
    # Get quote for spending 50 USDC
    quote = await client.get_quote(
        from_token="0xUSDC...",
        to_token="0xRWA...",
        from_amount=Decimal("50")
    )

    print(f"💰 Quote for 50 USDC:")
    print(f"   You'll receive: {quote.buy_amount} RWA")
    print(f"   Rate: {quote.rate}")
    print(f"   Source: {quote.source}")
```

---

## Trading (Taking Offers)

Once you've found good offers, you can take them to execute trades:

### Taking Fixed-Price Offers

The `trade()` method automatically handles everything:

```python
from decimal import Decimal

async with MarketMakerClient(...) as client:
    # Buy RWA tokens by spending USDC
    result = await client.trade(
        from_token="0xUSDC...",  # What you're paying
        to_token="0xRWA...",     # What you're receiving
        from_amount=Decimal("100"),
        affiliate=None  # Optional affiliate address
    )

    print(f"✅ Trade successful!")
    print(f"   TX Hash: {result.tx_hash}")
    print(f"   Offer ID: {result.order_id}")
    print(f"   Paid: {result.sell_amount} USDC")
    print(f"   Received: {result.buy_amount} RWA")
    print(f"   Rate: {result.rate}")
```

### What Happens When You Trade?

The SDK automatically:

1. 🔍 **Finds best offers** - Queries RPQ Service
2. ✅ **Approves tokens** - Allows contract to spend your tokens
3. 💰 **Checks balance** - Verifies you have enough tokens
4. 📊 **Handles pricing** - Works with both fixed and dynamic offers
5. 🔗 **Executes on-chain** - Submits transaction to blockchain
6. ⏳ **Waits for confirmation** - Returns after transaction is mined

### Taking Dynamic-Price Offers

Dynamic offers are handled automatically by the `trade()` method. The SDK:

- Uses `depositToWithdrawalRate` for slippage protection
- Protects against price changes during transaction
- Automatically calls the correct smart contract function

```python
# Same syntax - SDK handles fixed vs dynamic automatically
result = await client.trade(
    from_token="0xUSDC...",
    to_token="0xRWA...",
    from_amount=Decimal("50")
)
# Works with both fixed AND dynamic offers!
```

### Two Ways to Specify Amount

Just like quotes, you can specify either the amount to sell OR the amount to buy:

**Option 1: Specify Amount to Sell**

```python
result = await client.trade(
    from_token="0xUSDC...",
    to_token="0xRWA...",
    from_amount=Decimal("100")  # Spend 100 USDC
)
```

**Option 2: Specify Amount to Buy**

```python
result = await client.trade(
    from_token="0xUSDC...",
    to_token="0xRWA...",
    to_amount=Decimal("10")  # Receive 10 RWA tokens
)
```

> ⚠️ **Important**: Provide **either** `from_amount` **OR** `to_amount`, not both!

---

## Creating Your Own Offers

Want to become a liquidity provider? Create your own offers!

### Making an Offer

```python
from decimal import Decimal

async with MarketMakerClient(...) as client:
    # Offer to sell 10 RWA for 1000 USDC
    result = await client.make_offer(
        sell_token="0xRWA...",           # Token you're offering
        sell_amount=Decimal("10"),       # Amount you're selling
        buy_token="0xUSDC...",           # Token you want
        buy_amount=Decimal("1000"),      # Amount you want to receive
        is_dynamic=False,                # Fixed price offer
        expires_at=None                  # No expiration
    )

    print(f"✅ Offer created!")
    print(f"   TX Hash: {result.tx_hash}")
    print(f"   Offer ID: {result.order_id}")
    print(f"   Selling: {result.sell_amount} RWA")
    print(f"   For: {result.buy_amount} USDC")
    print(f"   Rate: {result.rate}")
```

### Creating Dynamic Offers

Dynamic offers use price feeds to adjust pricing in real-time:

```python
# Get available price feeds
feeds = await client.rpq_client.get_price_feeds()
print(f"Available price feeds: {len(feeds.price_feeds)}")

# Create dynamic offer
result = await client.make_offer(
    sell_token="0xRWA...",
    sell_amount=Decimal("10"),
    buy_token="0xUSDC...",
    buy_amount=Decimal("1000"),
    is_dynamic=True,  # Use price feeds!
    expires_at=None
)
```

### Setting Expiration

You can set an expiration timestamp for your offer:

```python
from datetime import datetime, timedelta

# Expire in 7 days
expires_at = int((datetime.now() + timedelta(days=7)).timestamp())

result = await client.make_offer(
    sell_token="0xRWA...",
    sell_amount=Decimal("10"),
    buy_token="0xUSDC...",
    buy_amount=Decimal("1000"),
    expires_at=expires_at  # Unix timestamp
)
```

### What Happens When You Make an Offer?

The SDK automatically:

1. ✅ **Approves tokens** - Allows contract to hold your tokens
2. 🔗 **Creates offer on-chain** - Deposits tokens into smart contract
3. ⏳ **Waits for confirmation** - Returns after transaction is mined
4. 📋 **Returns offer ID** - You can track or cancel later

> 💡 **Tip**: Your tokens are locked in the contract until the offer is taken or you cancel it.

---

## Canceling Offers

Changed your mind? Cancel your own offers anytime:

```python
async with MarketMakerClient(...) as client:
    # Cancel an offer you created
    tx_hash = await client.cancel_offer(offer_id="12345")

    print(f"✅ Offer cancelled!")
    print(f"   TX Hash: {tx_hash}")
```

### Important Notes

- ✅ Only the **offer creator** can cancel
- ✅ Your tokens are **returned immediately**
- ❌ You **cannot cancel** if partially taken (partial offers)
- ❌ You **pay gas fees** for cancellation

---

## Error Handling

The SDK provides clear error messages for troubleshooting:

### Common Exceptions

```python
from swarm.market_maker_sdk.rpq_service.exceptions import (
    NoOffersAvailableException,
    QuoteUnavailableException,
    RPQServiceException,
)
from swarm.market_maker_sdk.market_maker_web3.exceptions import (
    OfferNotFoundError,
    OfferInactiveError,
    InsufficientOfferBalanceError,
    OfferExpiredError,
    UnauthorizedError,
    MarketMakerWeb3Exception,
)

async with MarketMakerClient(...) as client:
    try:
        result = await client.trade(
            from_token="0xUSDC...",
            to_token="0xRWA...",
            from_amount=Decimal("100")
        )
        print(f"✅ Trade successful!")

    except NoOffersAvailableException as e:
        print(f"❌ No offers available: {e}")
        # Try a different token pair or amount

    except OfferNotFoundError as e:
        print(f"❌ Offer doesn't exist: {e}")
        # Offer was likely already taken

    except OfferInactiveError as e:
        print(f"❌ Offer is inactive: {e}")
        # Offer was cancelled or fully taken

    except InsufficientOfferBalanceError as e:
        print(f"❌ Maker has insufficient balance: {e}")
        # Try a different offer

    except OfferExpiredError as e:
        print(f"❌ Offer has expired: {e}")
        # Find a newer offer

    except UnauthorizedError as e:
        print(f"❌ Not authorized: {e}")
        # You're not the offer creator

    except MarketMakerWeb3Exception as e:
        print(f"❌ Blockchain error: {e}")
        # Check gas, balance, approvals

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        # Contact support if persists
```

### Error Reference

| Exception                       | When It Happens              | How to Handle                     |
| ------------------------------- | ---------------------------- | --------------------------------- |
| `NoOffersAvailableException`    | No offers for token pair     | Try different pair or create one  |
| `QuoteUnavailableException`     | Cannot calculate quote       | Check token addresses             |
| `OfferNotFoundError`            | Offer doesn't exist on-chain | Offer was taken or invalid        |
| `OfferInactiveError`            | Offer is not active          | Find a different offer            |
| `InsufficientOfferBalanceError` | Maker lacks tokens           | Try smaller amount or other offer |
| `OfferExpiredError`             | Offer past expiration        | Find newer offers                 |
| `UnauthorizedError`             | Not the offer creator        | Only cancel your own offers       |
| `RPQServiceException`           | RPQ API error                | Check API key, network connection |
| `MarketMakerWeb3Exception`      | Smart contract error         | Check gas, balance, approvals     |
| `Web3Exception`                 | Blockchain connection issue  | Check RPC endpoint, network       |

---

## Complete Example

Here's a comprehensive example showing best practices:

```python
import asyncio
import logging
from decimal import Decimal
from dotenv import load_dotenv
import os

from swarm.market_maker_sdk import MarketMakerClient
from swarm.shared.models import Network
from swarm.market_maker_sdk.rpq_service.exceptions import (
    NoOffersAvailableException,
    QuoteUnavailableException,
)
from swarm.market_maker_sdk.market_maker_web3.exceptions import (
    MarketMakerWeb3Exception,
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
    Complete example: Trade RWA tokens via Market Maker
    """

    # Configuration
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")
    RPQ_API_KEY = os.getenv("RPQ_API_KEY")
    USDC_ADDRESS = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"  # Polygon
    RWA_ADDRESS = "0x..."  # Replace with actual RWA token

    if not PRIVATE_KEY or not RPQ_API_KEY:
        print("❌ Missing required environment variables")
        return

    # Initialize client
    async with MarketMakerClient(
        network=Network.POLYGON,
        private_key=PRIVATE_KEY,
        rpq_api_key=RPQ_API_KEY,
    ) as client:

        print(f"✅ Connected to Market Maker")
        print(f"   Network: {Network.POLYGON.name}")
        print(f"   Wallet: {client.web3_client.account.address}")
        print()

        try:
            # Step 1: Browse available offers
            print("📋 Step 1: Browse Available Offers")
            offers = await client.rpq_client.get_offers(
                buy_asset_address=RWA_ADDRESS,
                sell_asset_address=USDC_ADDRESS,
                limit=5
            )
            print(f"Found {len(offers)} offers")
            print()

            # Step 2: Get best offers
            print("🎯 Step 2: Get Best Offers")
            best_offers = await client.rpq_client.get_best_offers(
                buy_asset_address=RWA_ADDRESS,
                sell_asset_address=USDC_ADDRESS,
                target_sell_amount="100"  # Spend 100 USDC
            )
            print(f"Best combination uses {len(best_offers.result.selected_offers)} offer(s)")
            print()

            # Step 3: Get a quote
            print("💰 Step 3: Get Quote")
            quote = await client.get_quote(
                from_token=USDC_ADDRESS,
                to_token=RWA_ADDRESS,
                from_amount=Decimal("100")
            )
            print(f"Rate: {quote.rate}")
            print(f"You'll receive: {quote.buy_amount} RWA tokens")
            print()

            # Step 4: Execute trade
            print("🔄 Step 4: Execute Trade")
            print("⚠️  Trade execution commented out for safety")
            # Uncomment below to execute real trade:
            """
            result = await client.trade(
                from_token=USDC_ADDRESS,
                to_token=RWA_ADDRESS,
                from_amount=Decimal("100")
            )

            print(f"✅ Trade successful!")
            print(f"   TX Hash: {result.tx_hash}")
            print(f"   Offer ID: {result.order_id}")
            print(f"   Paid: {result.sell_amount} USDC")
            print(f"   Received: {result.buy_amount} RWA")
            """

        except NoOffersAvailableException as e:
            print(f"❌ No offers available: {e}")
            print("💡 Try creating your own offer!")

        except QuoteUnavailableException as e:
            print(f"❌ Quote unavailable: {e}")
            print("💡 Check token addresses")

        except MarketMakerWeb3Exception as e:
            print(f"❌ Blockchain error: {e}")
            print("💡 Check balance, gas, and approvals")

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print("💡 Contact support if this persists")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## API Reference

For detailed technical documentation of all methods, parameters, and return types, see:

📚 **[Market Maker SDK API Reference](./market_maker_sdk_references.md)**

The API reference includes:

- Complete method signatures
- Parameter descriptions
- Return type details
- Exception specifications
- Advanced usage examples

---

## Need Help?

### Resources

- 📖 **API Reference**: [market_maker_sdk_references.md](./market_maker_sdk_references.md)
- 🔧 **Migration Guide**: See `rpq_service/MIGRATION_GUIDE.md` for API changes
- 💬 **Support**: Contact us through the platform
- 🐛 **Issues**: Report bugs on GitHub

### Common Questions

**Q: What's the difference between Market Maker and Cross-Chain Access?**  
A:

- **Market Maker**: Decentralized P2P trading, 24/7, no KYC, on-chain only
- **Cross-Chain Access**: Centralized stock trading, market hours only, KYC required

**Q: Can I trade any token pair?**  
A: Only pairs with existing offers. Check `get_offers()` or create your own offer!

**Q: What fees are charged?**  
A:

- Blockchain gas fees (varies by network)
- Optional affiliate fees (if you specify an affiliate address)
- No SDK fees

**Q: Is my private key safe?**  
A: Your private key is used only locally to sign transactions. It's never sent to our servers. Always keep it secure!

**Q: How do I get an RPQ API key?**  
A: Contact support or visit the platform to request access.

**Q: Can offers be partially filled?**  
A: Yes, if it's a `PartialOffer`. `BlockOffer` must be filled completely.

---

## Quick Reference

### Import Statements

```python
from swarm.market_maker_sdk import MarketMakerClient
from swarm.shared.models import Network
from swarm.market_maker_sdk.rpq_service.exceptions import (
    NoOffersAvailableException,
    QuoteUnavailableException,
)
from swarm.market_maker_sdk.market_maker_web3.exceptions import (
    MarketMakerWeb3Exception,
)
from decimal import Decimal
```

### Initialize Client

```python
async with MarketMakerClient(
    network=Network.POLYGON,
    private_key="0x...",
    rpq_api_key="your_key",
) as client:
    # Your code here
    pass
```

### Get Quote

```python
quote = await client.get_quote(
    from_token="0xUSDC...",
    to_token="0xRWA...",
    from_amount=Decimal("100")
)
```

### Execute Trade

```python
result = await client.trade(
    from_token="0xUSDC...",
    to_token="0xRWA...",
    from_amount=Decimal("100")
)
```

### Create Offer

```python
result = await client.make_offer(
    sell_token="0xRWA...",
    sell_amount=Decimal("10"),
    buy_token="0xUSDC...",
    buy_amount=Decimal("1000")
)
```

---

**Happy Trading! 🚀**

_Last Updated: November 20, 2025_

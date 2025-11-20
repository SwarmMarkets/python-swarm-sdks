# Cross-Chain Access SDK User Guide

Welcome to the **Cross-Chain Access SDK**! This guide will help you start trading Real World Assets (RWAs) like stocks through our decentralized platform. Trade Apple, Tesla, and other stocks 24/7 using cryptocurrency.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Trading Hours](#trading-hours)
3. [Supported Networks](#supported-networks)
4. [Installation](#installation)
5. [Initializing the SDK](#initializing-the-sdk)
6. [Trading Assets](#trading-assets)
   - [Buying Assets](#buying-assets)
   - [Selling Assets](#selling-assets)
   - [Cross-Chain Trading](#cross-chain-trading)
7. [Manually Getting Quotes](#manually-getting-quotes)
8. [Manually Checking Market Hours](#manually-checking-market-hours)
9. [Error Handling](#error-handling)
10. [Built-in Retry Logic](#built-in-retry-logic)
11. [Email Notifications](#email-notifications)
12. [Complete Example](#complete-example)
13. [API Reference](#api-reference)

---

## Prerequisites

Before you can use the Cross-Chain Access SDK, you **must** complete the KYC (Know Your Customer) process:

### 1. Register Your Wallet

Visit our platform at **[https://dotc.eth.limo/](https://dotc.eth.limo/)** and complete the following steps:

1. **Connect your wallet** to the platform
2. **Complete KYC verification** - This is required by regulations for stock trading
3. **Wait for approval** - Usually takes 1-2 business days
4. **Your wallet is now authorized** to trade stocks via the SDK

> ⚠️ **Important**: Without KYC approval, your trades will be rejected. Make sure to complete this step first!

### 2. Required Setup

You'll need:

- **Python 3.8+** installed on your system
- A **wallet with a private key** (the same wallet used for KYC)
- **USDC tokens** on one of our supported networks
- **Gas tokens** (MATIC, ETH, etc.) for transaction fees

---

## Trading Hours

The US stock market operates during specific hours. The Cross-Chain Access SDK automatically checks these hours for you:

### Market Schedule

- **Opening Time**: 14:30 UTC (9:30 AM EST)
- **Closing Time**: 21:00 UTC (4:00 PM EST)
- **Trading Days**: Monday - Friday (weekdays only)
- **Closed**: Weekends and US market holidays

### Automatic Validation

Don't worry about checking hours manually! The SDK automatically:

✅ Validates market hours before executing trades  
✅ Provides helpful messages like "Market opens in 5h 30m"  
✅ Throws `MarketClosedException` if you try trading when closed

**Example output when market is closed:**

```
Market is closed. Opens in 12h 45m
```

---

## Supported Networks

The Cross-Chain Access SDK works on multiple blockchain networks. All trading is done with **USDC stablecoin**.

### Available Networks

| Network  | Chain ID | Gas Token |
| -------- | -------- | --------- |
| Polygon  | 137      | MATIC     |
| Ethereum | 1        | ETH       |
| BSC      | 56       | BNB       |
| Base     | 8453     | ETH       |

### Important Notes

- **USDC Only**: All trades must be in USDC. We automatically detect the correct USDC address for your network.
- **Cross-Chain**: You can receive assets on a different chain than where you send USDC (see [Cross-Chain Trading](#cross-chain-trading))
- **Gas Fees**: Make sure you have enough gas tokens (MATIC, ETH, etc.) for transactions

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

Setting up the SDK is simple. Here's how to get started:

### Basic Setup

```python
from cross_chain_access_sdk.sdk import CrossChainAccessClient

# Initialize the client
async with CrossChainAccessClient(
    network="polygon",                 # Choose your network: "polygon", "ethereum", "bsc", "base"
    private_key="0x...",               # Your KYC-verified wallet
    user_email="you@example.com"       # For trade notifications
) as client:
    # Start trading!
    pass
```

### Configuration Options

| Parameter     | Type   | Required | Description                                                  |
| ------------- | ------ | -------- | ------------------------------------------------------------ |
| `network`     | `str`  | ✅       | Network name: "polygon", "ethereum", "bsc", or "base"        |
| `private_key` | `str`  | ✅       | Private key (must be KYC-verified at https://dotc.eth.limo/) |
| `user_email`  | `str`  | ❌       | Email for trade confirmations                                |
| `rpc_url`     | `str`  | ❌       | Custom RPC endpoint (optional)                               |
| `is_dev`      | `bool` | ❌       | Use development environment (default: `False`)               |

### Using Context Managers (Recommended)

Always use the `async with` pattern. This ensures proper cleanup:

```python
# ✅ Good - Automatic cleanup
async with CrossChainAccessClient(...) as client:
    result = await client.buy(...)

# ❌ Bad - Manual cleanup needed
client = CrossChainAccessClient(...)
result = await client.buy(...)
await client.close()  # Don't forget this!
```

---

## Trading Assets

The SDK makes trading stocks simple. Buy or sell with just a few lines of code!

### Buying Assets

Purchase stock tokens using USDC:

```python
from decimal import Decimal

async with CrossChainAccessClient(
    network="polygon",
    private_key="0x...",
    user_email="you@example.com"
) as client:
    # Buy 10 shares of Apple
    result = await client.buy(
        rwa_token_address="0x1234...",     # Apple token address
        rwa_symbol="AAPL",                 # Stock symbol
        rwa_amount=10,                     # Buy 10 shares (can use int/float)
        user_email="you@example.com"       # Get email confirmation
    )

    print(f"✅ Success! Bought {result.buy_amount} AAPL")
    print(f"💰 Spent: ${result.sell_amount} USDC")
    print(f"🔗 Transaction: {result.tx_hash}")
    print(f"📋 Order ID: {result.order_id}")
```

#### Two Ways to Specify Amount

You can specify either the amount of shares OR the USDC to spend:

**Option 1: Specify Shares**

```python
# Buy exactly 10 shares of AAPL
result = await client.buy(
    rwa_token_address="0x1234...",
    rwa_symbol="AAPL",
    rwa_amount=10,                         # Can use int, float, or Decimal
    user_email="you@example.com"
)
```

**Option 2: Specify USDC**

```python
# Spend exactly $1000 USDC
result = await client.buy(
    rwa_token_address="0x1234...",
    rwa_symbol="AAPL",
    usdc_amount=1000,                      # Can use int, float, or Decimal
    user_email="you@example.com"
)
# You'll get as many shares as $1000 can buy at current price
```

> 💡 **Tip**: You can use regular numbers (10, 1000.5) or Decimal("10") - the SDK automatically handles conversion for precision!

#### What Happens When You Buy?

The SDK automatically handles everything:

1. ✅ **Checks market hours** - Ensures market is open
2. ✅ **Validates your account** - Checks if trading is allowed
3. 📈 **Gets real-time price** - Fetches current market quote
4. 🧮 **Calculates amounts** - Includes 1% slippage protection
5. 💰 **Checks balance** - Verifies you have enough USDC
6. 🔗 **Transfers USDC** - Sends USDC to escrow on-chain
7. 📋 **Places order** - Submits order to Cross-Chain Access
8. 📧 **Sends email** - Confirms trade (if email provided)

### Selling Assets

Sell your stock tokens back to USDC:

```python
async with CrossChainAccessClient(
    network="polygon",
    private_key="0x...",
    user_email="you@example.com"
) as client:
    # Sell 5 shares of Apple
    result = await client.sell(
        rwa_token_address="0x1234...",     # Apple token address
        rwa_symbol="AAPL",                 # Stock symbol
        rwa_amount=5,                      # Sell 5 shares (can use int/float)
        user_email="you@example.com"       # Get email confirmation
    )

    print(f"✅ Success! Sold {result.sell_amount} AAPL")
    print(f"💰 Received: ${result.buy_amount} USDC")
    print(f"🔗 Transaction: {result.tx_hash}")
```

#### Two Ways to Specify Amount

Just like buying, you can specify shares OR target USDC:

**Option 1: Specify Shares**

```python
# Sell exactly 5 shares
result = await client.sell(
    rwa_token_address="0x1234...",
    rwa_symbol="AAPL",
    rwa_amount=5,                          # Can use int, float, or Decimal
    user_email="you@example.com"
)
```

**Option 2: Target USDC**

```python
# Sell enough shares to get $500 USDC
result = await client.sell(
    rwa_token_address="0x1234...",
    rwa_symbol="AAPL",
    usdc_amount=500,                       # Can use int, float, or Decimal
    user_email="you@example.com"
)
```

> 💡 **Tip**: The SDK automatically converts regular numbers to Decimal for financial precision!

#### What Happens When You Sell?

The process is similar to buying:

1. ✅ **Checks market hours** - Ensures market is open
2. ✅ **Validates your account** - Checks if trading is allowed
3. 📈 **Gets real-time price** - Fetches current market quote
4. 🧮 **Calculates amounts** - Includes 1% slippage protection
5. 🏦 **Checks balance** - Verifies you have enough shares
6. 🔗 **Transfers shares** - Sends tokens to escrow on-chain
7. 📋 **Places order** - Submits order to Cross-Chain Access
8. 📧 **Sends email** - Confirms trade (if email provided)

### Cross-Chain Trading

Want to send USDC from Polygon but receive shares on Base? We support that!

#### How It Works

Use the `target_chain_id` parameter when you need cross-chain functionality:

```python
async with CrossChainAccessClient(
    network="polygon",                # Send USDC from Polygon
    private_key="0x...",
    user_email="you@example.com"
) as client:
    result = await client.buy(
        rwa_token_address="0x1234...",
        rwa_symbol="AAPL",
        rwa_amount=10,                    # Simple numeric value
        user_email="you@example.com",
        target_chain_id=8453              # Receive on Base!
    )
```

---

## Manually Getting Quotes

If you want to display current prices to users before they trade, you can manually fetch quotes:

```python
async with CrossChainAccessClient(...) as client:
    quote = await client.get_quote("AAPL")

    print(f"💵 Current AAPL Price: ${quote.rate}")
    print(f" Quote Time: {quote.timestamp}")
```

### Building a Price Display

```python
async with CrossChainAccessClient(...) as client:
    # Get quotes for multiple symbols
    symbols = ["AAPL", "TSLA", "GOOGL"]

    for symbol in symbols:
        quote = await client.get_quote(symbol)
        print(f"{symbol}: ${quote.rate:.2f}")

# Output:
# AAPL: $175.50
# TSLA: $242.30
# GOOGL: $138.75
```

> 💡 **Note**: You don't need to fetch quotes manually before trading - the `buy()` and `sell()` methods automatically get real-time prices for you!

---

## Manually Checking Market Hours

The SDK automatically validates market hours for every trade, but if you want to check manually:

```python
async with CrossChainAccessClient(...) as client:
    is_available, message = await client.check_trading_availability()

    if is_available:
        print(f"✅ {message}")
        # Example: "Trading is available"
    else:
        print(f"❌ {message}")
        # Example: "Market is closed. Opens in 8h 30m"
```

### What Does It Check?

This method validates:

- ✅ Market hours (14:30-21:00 UTC, weekdays)
- ✅ Your account status (not blocked)
- ✅ Trading permissions (trading allowed)
- ✅ Transfer permissions (not restricted)
- ✅ Market status (currently open)

> 💡 **Note**: You don't need to call this before trading - the `buy()` and `sell()` methods automatically check everything for you!

---

## Error Handling

The SDK provides clear error messages to help you handle issues gracefully.

### Common Exceptions

```python
from cross_chain_access_sdk.cross_chain_access.exceptions import (
    MarketClosedException,
    AccountBlockedException,
    InsufficientFundsException,
    QuoteUnavailableException,
    InvalidSymbolException,
)

async with CrossChainAccessClient(...) as client:
        try:
            result = await client.buy(
                rwa_token_address="0x1234...",
                rwa_symbol="AAPL",
                rwa_amount=10,
                user_email="you@example.com"
            )
            print(f"✅ Trade successful!")    except MarketClosedException as e:
        print(f"❌ Market is closed: {e}")
        # Show user when market opens

    except InsufficientFundsException as e:
        print(f"❌ Not enough funds: {e}")
        # Prompt user to add more USDC

    except AccountBlockedException as e:
        print(f"❌ Account restricted: {e}")
        # Direct user to support

    except InvalidSymbolException as e:
        print(f"❌ Invalid symbol: {e}")
        # Show user available symbols

    except QuoteUnavailableException as e:
        print(f"❌ Can't get price: {e}")
        # Retry or try later

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        # Log and report to support
```

### Error Reference

| Exception                    | When It Happens                        | How to Handle                 |
| ---------------------------- | -------------------------------------- | ----------------------------- |
| `MarketClosedException`      | Trading outside market hours           | Wait until market opens       |
| `AccountBlockedException`    | Account is restricted                  | Contact support               |
| `InsufficientFundsException` | Not enough USDC or shares              | Add funds or reduce amount    |
| `QuoteUnavailableException`  | Can't fetch current price              | Retry after a moment          |
| `InvalidSymbolException`     | Stock symbol doesn't exist             | Check symbol spelling         |
| `ValueError`                 | Invalid parameters (e.g., both amounts | Fix parameter combination     |
| `AuthenticationError`        | Wallet not KYC-verified                | Complete KYC at dotc.eth.limo |

---

## Built-in Retry Logic

The SDK automatically retries failed API requests, so you don't have to!

### How Retries Work

- **Number of Retries**: 3 attempts
- **Backoff Strategy**: Exponential (waits longer between each retry)
- **Retry Delays**: 1s, 2s, 4s
- **Automatic**: No configuration needed

### What Gets Retried?

✅ Network timeouts  
✅ Temporary API errors (5xx errors)  
✅ Rate limiting (429 errors)

❌ Invalid parameters (4xx errors) - No retry, fails immediately  
❌ Authentication failures - No retry, fails immediately

### Example Behavior

```python
# If API is temporarily down:
result = await client.buy(...)
# Attempt 1: Failed (network timeout)
# Waiting 1 second...
# Attempt 2: Failed (still down)
# Waiting 2 seconds...
# Attempt 3: Success! ✅
```

You don't need to implement retry logic yourself - it's all handled automatically!

---

## Email Notifications

Get instant email confirmations for your trades!

### How to Enable

Simply provide your email address:

```python
result = await client.buy(
    rwa_token_address="0x1234...",
    rwa_symbol="AAPL",
    rwa_amount=10,
    user_email="you@example.com"  # ← Add your email here!
)
```

### What You'll Receive

When you provide an email, you'll get:

📧 **Order Confirmation Email** containing:

- ✅ Trade details (symbol, amount, price)
- ✅ Transaction hash (blockchain proof)
- ✅ Order ID (for tracking)
- ✅ Timestamp (when trade executed)
- ✅ Network information (which blockchain)

### Email Example

```
🎉 Your AAPL Trade is Complete!

You bought 10 shares of AAPL for $1,755.00 USDC

Order ID: abc-123-def
Transaction: 0x1234...5678
Network: Polygon
Time: Nov 13, 2025 15:30 UTC

View on blockchain: [Link]
```

> 💡 **Privacy**: Your email is only used for trade notifications. We don't send marketing emails.

---

## Complete Example

Here's a full example showing best practices:

```python
import asyncio
from cross_chain_access_sdk.sdk import CrossChainAccessClient
from cross_chain_access_sdk.cross_chain_access.exceptions import (
    MarketClosedException,
    InsufficientFundsException,
    CrossChainAccessException
)


async def main():
    """
    Complete example: Buy AAPL stock with error handling
    """

    # Initialize client
    async with CrossChainAccessClient(
        network="polygon",
        private_key="0x...",  # Your KYC-verified wallet
        user_email="you@example.com"
    ) as client:

        try:
            # Optional: Get current price to show user
            quote = await client.get_quote("AAPL")
            print(f"💰 Current AAPL Price: ${quote.rate}")

            # Calculate estimated cost
            shares = 10
            estimated_cost = shares * quote.rate
            print(f"📊 Estimated cost for {shares} shares: ${estimated_cost}")

            # In a real app, you'd confirm with the user here
            # confirm = input("Proceed? (y/n): ")
            # if confirm.lower() != 'y':
            #     return

            # Execute buy order (market hours are automatically checked)
            print("\n🔄 Executing buy order...")
            result = await client.buy(
                rwa_token_address="0x1234...",  # AAPL token address
                rwa_symbol="AAPL",
                rwa_amount=shares,
                user_email="you@example.com"
            )

            # Show success
            print("\n✅ Trade Successful!")
            print(f"📦 Bought: {result.buy_amount} AAPL")
            print(f"💵 Spent: ${result.sell_amount} USDC")
            print(f"📈 Price: ${result.rate} per share")
            print(f"🔗 TX Hash: {result.tx_hash}")
            print(f"📋 Order ID: {result.order_id}")
            print(f"\n📧 Check your email for confirmation!")

        except MarketClosedException as e:
            print(f"❌ Market is closed: {e}")
            print("💡 Try again during market hours (14:30-21:00 UTC)")

        except InsufficientFundsException as e:
            print(f"❌ Insufficient funds: {e}")
            print("💡 Add more USDC to your wallet")

        except CrossChainAccessException as e:
            print(f"❌ Trading error: {e}")
            print("💡 Please try again or contact support")

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print("💡 Please contact support if this persists")


if __name__ == "__main__":
    asyncio.run(main())
```

### Example Output

```
💰 Current AAPL Price: $175.50
📊 Estimated cost for 10 shares: $1755.00

🔄 Executing buy order...

✅ Trade Successful!
📦 Bought: 10.000000000 AAPL
💵 Spent: $1755.00 USDC
📈 Price: $175.50 per share
🔗 TX Hash: 0xabc123...def789
📋 Order ID: order_12345

📧 Check your email for confirmation!
```

---

## API Reference

For detailed technical documentation of all methods, parameters, and return types, see:

📚 **[Cross-Chain Access SDK API Reference](./cross_chain_access_sdk_api.md)**

The API reference includes:

- Complete method signatures
- Parameter descriptions
- Return type details
- Exception specifications
- Advanced usage examples

---

## Need Help?

### Resources

- 📖 **API Reference**: [cross_chain_access_sdk_api.md](./cross_chain_access_sdk_api.md)
- 🌐 **Platform**: [https://dotc.eth.limo/](https://dotc.eth.limo/)
- 💬 **Support**: Contact us through the platform
- 🐛 **Issues**: Report bugs on GitHub

### Common Questions

**Q: Why is my trade failing?**  
A: Most common reasons:

1. Market is closed (check hours)
2. Wallet not KYC-verified (complete KYC)
3. Insufficient USDC balance
4. Invalid stock symbol

**Q: Can I trade on weekends?**  
A: No, US stock market is closed on weekends. Trading hours are Monday-Friday, 14:30-21:00 UTC.

**Q: What fees are charged?**  
A: You pay:

- Blockchain gas fees (varies by network)
- Trading fees (included in the price)
- No additional SDK fees

**Q: Is my private key safe?**  
A: Your private key is used only locally to sign transactions. It's never sent to our servers. Always keep it secure!

---

## Quick Reference

### Import Statements

```python
from cross_chain_access_sdk.sdk import CrossChainAccessClient
from cross_chain_access_sdk.cross_chain_access.exceptions import (
    MarketClosedException,
    AccountBlockedException,
    InsufficientFundsException,
)
# No need to import Decimal - SDK auto-converts numbers!
```

### Basic Buy

```python
async with CrossChainAccessClient(
    network="polygon",  # or "ethereum", "bsc", "base"
    private_key="0x...",
    user_email="you@example.com"
) as client:
    result = await client.buy(
        rwa_token_address="0x...",
        rwa_symbol="AAPL",
        rwa_amount=10,  # Simple numeric value
        user_email="you@example.com"
    )
```

### Basic Sell

```python
async with CrossChainAccessClient(
    network="polygon",  # or "ethereum", "bsc", "base"
    private_key="0x...",
    user_email="you@example.com"
) as client:
    result = await client.sell(
        rwa_token_address="0x...",
        rwa_symbol="AAPL",
        rwa_amount=5,  # Simple numeric value
        user_email="you@example.com"
    )
```

---

**Happy Trading! 🚀**

_Last Updated: November 13, 2025_

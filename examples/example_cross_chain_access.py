"""Example: Cross-Chain Access SDK - Stock market RWA trading.

This example demonstrates how to use the Cross-Chain Access SDK for trading
Real World Assets through the stock market API.

Features shown:
- Check market hours and trading availability
- Get real-time quotes
- Check account status and funds
- Execute buy/sell trades
"""

import asyncio
import logging
import os
from decimal import Decimal
from dotenv import load_dotenv

from cross_chain_access_sdk import CrossChainAccessClient
from _shared.models import Network

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Load environment variables from .env file
load_dotenv()


async def main():
    # Configuration
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")
    USER_EMAIL = os.getenv("USER_EMAIL")
    
    # Token addresses (Polygon example)
    RWA_TOKEN_ADDRESS = "0x267fc8b95345916c9740cbc007ed65c71b052395"  # Replace with actual RWA token address
    RWA_SYMBOL = "NVDA"  # Trading symbol
    
    if not PRIVATE_KEY or not USER_EMAIL:
        print("❌ Please set PRIVATE_KEY and USER_EMAIL environment variables")
        return
    
    print("=" * 60)
    print("Cross-Chain Access SDK Example - Stock Market RWA Trading")
    print("=" * 60)
    print()
    
    # Initialize Cross-Chain Access client
    # Environment (dev/prod) is set via SWARM_COLLECTION_MODE env variable
    async with CrossChainAccessClient(
        network=Network.POLYGON,
        private_key=PRIVATE_KEY,
        user_email=USER_EMAIL,
    ) as client:
        
        print(f"✅ Connected to Cross-Chain Access on {Network.POLYGON.name}")
        print(f"   Wallet: {client.web3_helper.account.address}")
        print()
        
        # # Example 1: Check market hours
        # print("🕐 Example 1: Check Market Hours")
        # print("-" * 60)
        # is_open, status_message = MarketHours.get_market_status()
        # print(f"Status: {status_message}")
        # print(f"Market is {'OPEN ✅' if is_open else 'CLOSED ❌'}")
        # print()
        
        # # Example 2: Check trading availability
        # print("🔍 Example 2: Check Trading Availability")
        # print("-" * 60)
        # try:
        #     is_available, message = await client.check_trading_availability()
        #     print(f"Trading: {'AVAILABLE ✅' if is_available else 'UNAVAILABLE ❌'}")
        #     print(f"Message: {message}")
        #     print()
        # except Exception as e:
        #     print(f"❌ Error checking availability: {e}")
        #     print()
        
        # # Example 3: Get account status
        # print("👤 Example 3: Get Account Status")
        # print("-" * 60)
        # try:
        #     status = await client.cross_chain_access_api.get_account_status()
        #     print(f"Account Status: {status.account_status}")
        #     print(f"  Account Blocked: {status.account_blocked}")
        #     print(f"  Trading Blocked: {status.trading_blocked}")
        #     print(f"  Transfers Blocked: {status.transfers_blocked}")
        #     print(f"  Market Open: {status.market_open}")
        #     print(f"  Trading Allowed: {status.is_trading_allowed()}")
        #     print()
        # except Exception as e:
        #     print(f"❌ Error getting account status: {e}")
        #     print()
        
        # # Example 4: Get account funds
        # print("💵 Example 4: Get Account Funds")
        # print("-" * 60)
        # try:
        #     funds = await client.cross_chain_access_api.get_account_funds()
        #     print(f"Cash: ${funds.cash}")
        #     print(f"Buying Power: ${funds.buying_power}")
        #     print(f"Day Trading Buying Power: ${funds.day_trading_buying_power}")
        #     print(f"Effective Buying Power: ${funds.effective_buying_power}")
        #     print()
        # except Exception as e:
        #     print(f"❌ Error getting funds: {e}")
        #     print()
        
        # # Example 5: Get real-time quote
        # print("💰 Example 5: Get Real-Time Quote")
        # print("-" * 60)
        # try:
        #     quote = await client.get_quote(RWA_SYMBOL)
        #     print(f"Quote for {RWA_SYMBOL}:")
        #     print(f"  Bid: ${quote.rate} (to sell)")
        #     print(f"  Ask: ${quote.rate} (to buy)")
        #     print(f"  Source: {quote.source}")
        #     print()
        # except Exception as e:
        #     print(f"❌ Error getting quote: {e}")
        #     print()
        
        # Example 6: Buy RWA tokens (commented out for safety)
        print("🛒 Example 6: Buy RWA Tokens")
        print("-" * 60)
        # print("⚠️  Trade execution commented out for safety")
        # print("    Uncomment the code below to execute a real trade")
        print()
        try:
            result = await client.buy(
                rwa_token_address=RWA_TOKEN_ADDRESS,
                rwa_symbol=RWA_SYMBOL,
                usdc_amount=Decimal("1"),  # Buy 1 tokens
                user_email=USER_EMAIL,
            )
            
            print(f"✅ Buy order successful!")
            print(f"   TX Hash: {result.tx_hash}")
            print(f"   Order ID: {result.order_id}")
            print(f"   Bought: {result.buy_amount} {RWA_SYMBOL}")
            print(f"   Spent: {result.sell_amount} USDC")
            print(f"   Price: ${result.rate}")
            print()
        except Exception as e:
            print(f"❌ Buy order failed: {e}")
        
        # Example 7: Sell RWA tokens (commented out for safety)
        print("💸 Example 7: Sell RWA Tokens")
        print("-" * 60)
        print("⚠️  Trade execution commented out for safety")
        print("    Uncomment the code below to execute a real trade")
        print()
        """
        try:
            result = await client.sell(
                rwa_token_address=RWA_TOKEN_ADDRESS,
                rwa_symbol=RWA_SYMBOL,
                rwa_amount=Decimal("10"),  # Sell 10 tokens
                user_email=USER_EMAIL,
            )
            
            print(f"✅ Sell order successful!")
            print(f"   TX Hash: {result.tx_hash}")
            print(f"   Order ID: {result.order_id}")
            print(f"   Sold: {result.sell_amount} {RWA_SYMBOL}")
            print(f"   Received: {result.buy_amount} USDC")
            print(f"   Price: ${result.rate}")
            print()
        except Exception as e:
            print(f"❌ Sell order failed: {e}")
        """
    
    print("=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

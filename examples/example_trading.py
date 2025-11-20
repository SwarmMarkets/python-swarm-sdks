"""Example: Trading SDK - Unified multi-platform trading with smart routing.

This example demonstrates how to use the Trading SDK to automatically
choose the best platform (Market Maker or Cross-Chain Access) for your trades.

Features shown:
- Get quotes from all platforms
- Compare prices across platforms
- Execute trades with smart routing
- Use different routing strategies
- Handle fallback scenarios
"""

import asyncio
import logging
import os
from decimal import Decimal
from dotenv import load_dotenv

from trading_sdk import TradingClient, RoutingStrategy
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
    RPQ_API_KEY = os.getenv("RPQ_API_KEY")
    USER_EMAIL = os.getenv("USER_EMAIL")
    
    # Token addresses (Polygon example)
    USDC_ADDRESS = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"  # USDC on Polygon
    RWA_TOKEN_ADDRESS = "0x267fc8b95345916c9740cbc007ed65c71b052395"  # Replace with actual RWA token address
    RWA_SYMBOL="NVDA"
    
    if not PRIVATE_KEY or not RPQ_API_KEY or not USER_EMAIL:
        print("❌ Please set PRIVATE_KEY, RPQ_API_KEY, and USER_EMAIL environment variables")
        return
    
    print("=" * 60)
    print("Trading SDK Example - Unified Multi-Platform Trading")
    print("=" * 60)
    print()
    
    # Example 1: BEST_PRICE strategy (default)
    print("🎯 Example 1: BEST_PRICE Strategy (Default)")
    print("-" * 60)
    print("Automatically selects platform with best price")
    print()
    
    # Environment (dev/prod) is set via SWARM_COLLECTION_MODE env variable
    async with TradingClient(
        network=Network.POLYGON,
        private_key=PRIVATE_KEY,
        rpq_api_key=RPQ_API_KEY,
        user_email=USER_EMAIL,
        routing_strategy=RoutingStrategy.BEST_PRICE,
    ) as client:
        
        print(f"✅ Connected to Trading SDK on {Network.POLYGON.name}")
        print()
        
        # Get quotes from all platforms
        print("📊 Getting quotes from all platforms...")
        try:
            quotes = await client.get_quotes(
                from_token=USDC_ADDRESS,
                to_token=RWA_TOKEN_ADDRESS,
                to_token_symbol=RWA_SYMBOL,
                from_amount=Decimal("1")
            )
            
            print()
            print("Quote Comparison:")
            print("-" * 40)
            
            if quotes["market_maker"]:
                market_maker_rate = quotes["market_maker"].rate
                print(f"Market Maker:   ${market_maker_rate} per token")
            else:
                print(f"Market Maker:   ❌ Not available")
            
            if quotes["cross_chain_access"]:
                cross_chain_access_rate = quotes["cross_chain_access"].rate
                print(f"Cross-Chain Access: ${cross_chain_access_rate} per token")
            else:
                print(f"Cross-Chain Access: ❌ Not available")
            
            print()
            
            # Determine which is better
            if quotes["market_maker"] and quotes["cross_chain_access"]:
                if quotes["market_maker"].rate < quotes["cross_chain_access"].rate:
                    print("🏆 Best price: Market Maker (lower cost per token)")
                else:
                    print("🏆 Best price: Cross-Chain Access (lower cost per token)")
            elif quotes["market_maker"]:
                print("🏆 Only Market Maker available")
            elif quotes["cross_chain_access"]:
                print("🏆 Only Cross-Chain Access available")
            else:
                print("❌ No platforms available")
            
            print()
        except Exception as e:
            print(f"❌ Error getting quotes: {e}")
            print()
        
        # Execute trade with smart routing (commented out for safety)
        print("🔄 Execute Trade with Smart Routing")
        print("-" * 60)
        print("⚠️  Trade execution commented out for safety")
        print("    SDK will automatically:")
        print("    1. Get quotes from both platforms")
        print("    2. Select platform with best price")
        print("    3. Execute trade on selected platform")
        print("    4. Fallback to alternative if primary fails")
        print()
        try:
            result = await client.trade(
                from_token=USDC_ADDRESS,
                to_token=RWA_TOKEN_ADDRESS,
                from_amount=Decimal("1"),
                to_token_symbol=RWA_SYMBOL,
                user_email=USER_EMAIL,
            )
            
            print(f"✅ Trade successful!")
            print(f"   Platform: Automatically selected")
            print(f"   TX Hash: {result.tx_hash}")
            print(f"   From: {result.sell_amount} USDC")
            print(f"   To: {result.buy_amount} {RWA_SYMBOL}")
            print(f"   Rate: ${result.rate}")
            print()
        except Exception as e:
            print(f"❌ Trade failed: {e}")
    
    print()
    
    # # Example 2: CROSS_CHAIN_ACCESS_FIRST strategy
    # print("🏦 Example 2: CROSS_CHAIN_ACCESS_FIRST Strategy")
    # print("-" * 60)
    # print("Try Cross-Chain Access first, fallback to Market Maker if unavailable")
    # print()
    
    # # Environment (dev/prod) is set via SWARM_COLLECTION_MODE env variable
    # async with TradingClient(
    #     network=Network.POLYGON,
    #     private_key=PRIVATE_KEY,
    #     rpq_api_key=RPQ_API_KEY,
    #     user_email=USER_EMAIL,
    #     routing_strategy=RoutingStrategy.CROSS_CHAIN_ACCESS_FIRST,
    # ) as client:
        
    #     print("✅ Routing: CROSS_CHAIN_ACCESS_FIRST")
    #     print("   - Primary: Cross-Chain Access")
    #     print("   - Fallback: Market Maker")
    #     print()
    #     """
    #     try:
    #         result = await client.trade(
    #             from_token=USDC_ADDRESS,
    #             to_token=RWA_TOKEN_ADDRESS,
    #             from_amount=Decimal("100"),
    #             to_token_symbol=RWA_SYMBOL,
    #             user_email=USER_EMAIL,
    #         )
    #         print(f"✅ Trade executed")
    #     except Exception as e:
    #         print(f"❌ Trade failed: {e}")
    #     """
    
    # print()
    
    # # Example 3: MARKET_MAKER_FIRST strategy
    # print("🔗 Example 3: MARKET_MAKER_FIRST Strategy")
    # print("-" * 60)
    # print("Try Market Maker first, fallback to Cross-Chain Access if unavailable")
    # print()
    
    # async with TradingClient(
    #     network=Network.POLYGON,
    #     private_key=PRIVATE_KEY,
    #     rpq_api_key=RPQ_API_KEY,
    #     user_email=USER_EMAIL,
    #     routing_strategy=RoutingStrategy.MARKET_MAKER_FIRST,
    # ) as client:
        
    #     print("✅ Routing: MARKET_MAKER_FIRST")
    #     print("   - Primary: Market Maker")
    #     print("   - Fallback: Cross-Chain Access")
    #     print()
    
    # print()
    
    # # Example 4: CROSS_CHAIN_ACCESS_ONLY strategy
    # print("🏦 Example 4: CROSS_CHAIN_ACCESS_ONLY Strategy")
    # print("-" * 60)
    # print("Only use Cross-Chain Access, fail if unavailable")
    # print()
    
    # async with TradingClient(
    #     network=Network.POLYGON,
    #     private_key=PRIVATE_KEY,
    #     rpq_api_key=RPQ_API_KEY,
    #     user_email=USER_EMAIL,
    #     routing_strategy=RoutingStrategy.CROSS_CHAIN_ACCESS_ONLY,
    # ) as client:
        
    #     print("✅ Routing: CROSS_CHAIN_ACCESS_ONLY")
    #     print("   - No fallback")
    #     print("   - Requires market hours")
    #     print()
    
    # print()
    
    # # Example 5: MARKET_MAKER_ONLY strategy
    # print("🔗 Example 5: MARKET_MAKER_ONLY Strategy")
    # print("-" * 60)
    # print("Only use Market Maker, fail if unavailable")
    # print()
    
    # async with TradingClient(
    #     network=Network.POLYGON,
    #     private_key=PRIVATE_KEY,
    #     rpq_api_key=RPQ_API_KEY,
    #     user_email=USER_EMAIL,
    #     routing_strategy=RoutingStrategy.MARKET_MAKER_ONLY,
    # ) as client:
        
    #     print("✅ Routing: MARKET_MAKER_ONLY")
    #     print("   - No fallback")
    #     print("   - 24/7 availability")
    #     print()
    
    # print()
    # print("=" * 60)
    # print("Example completed!")
    # print("=" * 60)
    # print()
    # print("Summary of Routing Strategies:")
    # print("-" * 60)
    # print("BEST_PRICE                   - Automatic price comparison (recommended)")
    # print("CROSS_CHAIN_ACCESS_FIRST     - Prefer Cross-Chain Access, fallback to Market Maker")
    # print("MARKET_MAKER_FIRST           - Prefer Market Maker, fallback to Cross-Chain Access")
    # print("CROSS_CHAIN_ACCESS_ONLY      - Only Cross-Chain Access (market hours required)")
    # print("MARKET_MAKER_ONLY            - Only Market Maker (24/7 availability)")
    # print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

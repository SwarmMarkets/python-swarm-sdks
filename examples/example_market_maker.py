"""Example: Market Maker SDK - Decentralized OTC trading.

This example demonstrates how to use the Market Maker SDK for peer-to-peer
RWA trading through smart contracts and the RPQ API.

Features shown:
- Get available offers
- Get best offers for a token pair
- Get quotes
- Execute trades
- Make your own offers
- Cancel offers
"""

import asyncio
import logging
import os
from decimal import Decimal
from dotenv import load_dotenv

from market_maker_sdk import MarketMakerClient
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
    USER_EMAIL = os.getenv("USER_EMAIL", "user@example.com")
    
    # Token addresses (Polygon example)
    USDC_ADDRESS = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"  # USDC on Polygon
    RWA_TOKEN_ADDRESS = "0x267fc8b95345916c9740cbc007ed65c71b052395"  # Replace with actual RWA token address
    
    if not PRIVATE_KEY or not RPQ_API_KEY:
        print("❌ Please set PRIVATE_KEY and RPQ_API_KEY environment variables")
        return
    
    print("=" * 60)
    print("Market Maker SDK Example - Decentralized OTC Trading")
    print("=" * 60)
    print()
    
    # Initialize Market Maker client
    # Environment (dev/prod) is set via SWARM_COLLECTION_MODE env variable
    async with MarketMakerClient(
        network=Network.POLYGON,
        private_key=PRIVATE_KEY,
        rpq_api_key=RPQ_API_KEY,
        user_email=USER_EMAIL,
    ) as client:
        
        print(f"✅ Connected to Market Maker on {Network.POLYGON.name}")
        print(f"   Wallet: {client.web3_client.account.address}")
        print()
        
        # Example 1: Get all available offers
        print("📋 Example 1: Get Available Offers")
        print("-" * 60)
        try:
            offers = await client.rpq_client.get_offers(
                buy_asset_address=RWA_TOKEN_ADDRESS,
                sell_asset_address=USDC_ADDRESS,
                limit=5,
            )
            
            print(f"Found {len(offers)} offers:")
            for i, offer in enumerate(offers, 1):
                print(f"  {i}. Offer ID: {offer.id}")
                print(f"     Deposit: {offer.amount_in} {offer.deposit_asset.symbol}")
                print(f"     Receive: {offer.amount_out} {offer.withdrawal_asset.symbol}")
                print(f"     Type: {offer.offer_type.value}")
                print(f"     Status: {offer.offer_status.value}")
                print(f"     Available: {offer.available_amount}")
                print()
        except Exception as e:
            print(f"❌ Error getting offers: {e}")
        print()
        
        # Example 2: Get best offers
        print("🎯 Example 2: Get Best Offers")
        print("-" * 60)
        try:
            best_offers = await client.rpq_client.get_best_offers(
                buy_asset_address=RWA_TOKEN_ADDRESS,
                sell_asset_address=USDC_ADDRESS,
                target_sell_amount="1",  # Want to sell 100 USDC
            )
            
            print(f"Best offers to buy RWA with 1 USDC:")
            print(f"  Success: {best_offers.result.success}")
            print(f"  Target amount: {best_offers.result.target_amount}")
            print(f"  Total taken: {best_offers.result.total_withdrawal_amount_paid}")
            print(f"  Mode: {best_offers.result.mode}")
            print(f"  Selected offers: {len(best_offers.result.selected_offers)}")
            
            for i, offer in enumerate(best_offers.result.selected_offers, 1):
                print(f"\n  Offer {i}:")
                print(f"    ID: {offer.id}")
                print(f"    Taken amount: {offer.withdrawal_amount_paid}")
                print(f"    Price per unit: {offer.price_per_unit}")
                print(f"    Type: {offer.offer_type.value}")
            print()
        except Exception as e:
            print(f"❌ Error getting best offers: {e}")
        print()
        
        # Example 3: Get a quote
        print("💰 Example 3: Get Quote")
        print("-" * 60)
        try:
            quote = await client.get_quote(
                from_token=USDC_ADDRESS,
                to_token=RWA_TOKEN_ADDRESS,
                from_amount=Decimal("1"),  # Spend 1 USDC
            )
            
            print(f"Quote for 1 USDC:")
            print(f"  You will receive: {quote.buy_amount} RWA tokens")
            print(f"  Rate: {quote.rate}")
            print(f"  Source: {quote.source}")
            print()
        except Exception as e:
            print(f"❌ Error getting quote: {e}")
        print()
        
        # Example 4: Execute a trade (commented out for safety)
        print("🔄 Example 4: Execute Trade")
        print("-" * 60)
        # print("⚠️  Trade execution commented out for safety")
        # print("    Uncomment the code below to execute a real trade")
        print()
        try:
            result = await client.trade(
                from_token=USDC_ADDRESS,
                to_token=RWA_TOKEN_ADDRESS,
                from_amount=Decimal("0.1"),  # Spend 0.1 USDC
            )
            
            print(f"✅ Trade successful!")
            print(f"   TX Hash: {result.tx_hash}")
            print(f"   Order ID: {result.order_id}")
            print(f"   Sold: {result.sell_amount} USDC")
            print(f"   Bought: {result.buy_amount} RWA")
            print()
        except Exception as e:
            print(f"❌ Trade failed: {e}")
        
        # Example 5: Make your own offer (commented out for safety)
        print("📝 Example 5: Make Your Own Offer")
        print("-" * 60)
        print("⚠️  Offer creation commented out for safety")
        print("    Uncomment the code below to create a real offer")
        print()
        """
        try:
            result = await client.make_offer(
                sell_token=RWA_TOKEN_ADDRESS,
                sell_amount=Decimal("10"),
                buy_token=USDC_ADDRESS,
                buy_amount=Decimal("1000"),
                is_dynamic=False,
            )
            
            print(f"✅ Offer created!")
            print(f"   TX Hash: {result.tx_hash}")
            print(f"   Offer ID: {result.order_id}")
            print(f"   Selling: {result.sell_amount} RWA")
            print(f"   For: {result.buy_amount} USDC")
            print(f"   Rate: {result.rate}")
            print()
        except Exception as e:
            print(f"❌ Offer creation failed: {e}")
        """
        
        # Example 6: Get price feeds for dynamic offers
        print("📊 Example 6: Get Price Feeds")
        print("-" * 60)
        try:
            feeds = await client.rpq_client.get_price_feeds()
            
            print(f"Found {len(feeds.price_feeds)} price feeds:")
            # Show first 5 feeds
            for i, (contract_addr, feed_addr) in enumerate(list(feeds.price_feeds.items())[:5], 1):
                print(f"  {i}. Contract: {contract_addr[:10]}...")
                print(f"     Feed: {feed_addr[:10]}...")
            print()
        except Exception as e:
            print(f"❌ Error getting price feeds: {e}")
        print()
    
    print("=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

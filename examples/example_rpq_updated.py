"""Example demonstrating the updated RPQ Service API client.

This example shows how to use the RPQ client with the new API structure.
"""

import asyncio
from swarm.market_maker_sdk.rpq_service import (
    RPQClient,
)


async def main():
    """Demonstrate RPQ Service API usage."""
    
    # Initialize client (API key required for some endpoints)
    # For testing, you can use network="polygon", "base", or "ethereum"
    api_key = "your-api-key-here"  # Replace with actual API key
    client = RPQClient(network="polygon", api_key=api_key)
    
    # Example token addresses on Polygon
    WETH_ADDRESS = "0x7ceB23fd6bc0add59E62ac25578270cFf1b9f619"  # WETH
    USDC_ADDRESS = "0x3c499c542cef5E3811e1192ce70d8cC03d5c3359"  # USDC
    
    try:
        # 1. Get price feeds (no API key required)
        print("\n=== Getting Price Feeds ===")
        client_no_key = RPQClient(network="polygon")
        price_feeds = await client_no_key.get_price_feeds()
        print(f"Found {len(price_feeds.price_feeds)} price feeds")
        
        # Show first few feeds
        for i, (contract, feed) in enumerate(list(price_feeds.price_feeds.items())[:3]):
            print(f"  {contract[:10]}... -> {feed[:10]}...")
        
        # 2. Get best offers for a target amount
        print("\n=== Getting Best Offers ===")
        best_offers = await client_no_key.get_best_offers(
            buy_asset_address=WETH_ADDRESS,
            sell_asset_address=USDC_ADDRESS,
            target_sell_amount="100",  # Want to sell 100 USDC
        )
        
        print(f"Success: {best_offers.result.success}")
        print(f"Target amount: {best_offers.result.target_amount}")
        print(f"Total taken: {best_offers.result.total_withdrawal_amount_paid}")
        print(f"Mode: {best_offers.result.mode}")
        print(f"Selected offers: {len(best_offers.result.selected_offers)}")
        
        for offer in best_offers.result.selected_offers:
            print(f"  Offer {offer.id[:10]}...")
            print(f"    Taken: {offer.withdrawal_amount_paid}")
            print(f"    Type: {offer.offer_type.value}")
            print(f"    Price: {offer.price_per_unit}")
        
        # 3. Get a quote (requires API key)
        print("\n=== Getting Quote ===")
        
        quote = await client.get_quote(
            buy_asset_address=WETH_ADDRESS,
            sell_asset_address=USDC_ADDRESS,
            target_sell_amount="100",
        )
        print(f"Sell amount: {quote.sell_amount}")
        print(f"Buy amount: {quote.buy_amount}")
        print(f"Rate: {quote.rate}")
        
        # 4. Get all offers with filters (requires API key)
        print("\n=== Getting All Offers ===")
        offers = await client.get_offers(
            buy_asset_address=WETH_ADDRESS,
            sell_asset_address=USDC_ADDRESS,
            limit=5,
        )
        
        print(f"Found {len(offers)} offers")
        for offer in offers[:2]:  # Show first 2
            print(f"\nOffer {offer.id[:10]}...")
            print(f"  Maker: {offer.maker[:10]}...")
            print(f"  Type: {offer.offer_type.value}")
            print(f"  Status: {offer.offer_status.value}")
            print(f"  Amount In: {offer.amount_in}")
            print(f"  Amount Out: {offer.amount_out}")
            print(f"  Available: {offer.available_amount}")
            print(f"  Deposit Asset: {offer.deposit_asset.symbol}")
            print(f"  Withdrawal Asset: {offer.withdrawal_asset.symbol}")
            print(f"  Pricing: {offer.offer_price.pricing_type.value}")
        
    except Exception as e:
        print(f"\nError: {e}")
    
    finally:
        await client.close()
        await client_no_key.close()


if __name__ == "__main__":
    asyncio.run(main())

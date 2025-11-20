"""Example: Error handling patterns across all SDKs.

This example demonstrates proper error handling for common scenarios
when using the Swarm Trading SDKs.
"""

import asyncio
import os
from decimal import Decimal
from dotenv import load_dotenv

from trading_sdk import TradingClient, RoutingStrategy
from trading_sdk.exceptions import NoLiquidityException, AllPlatformsFailedException
from cross_chain_access_sdk import CrossChainAccessClient
from cross_chain_access_sdk.cross_chain_access.exceptions import (
    MarketClosedException,
    AccountBlockedException,
    InsufficientFundsException,
)
from market_maker_sdk import MarketMakerClient
from market_maker_sdk.rpq_service.exceptions import NoOffersAvailableException
from _shared.models import Network
from _shared.web3.exceptions import (
    InsufficientBalanceException,
    TransactionFailedException,
)

# Load environment variables from .env file
load_dotenv()


async def example_cross_chain_access_errors():
    """Example: Handling Cross-Chain Access-specific errors."""
    print("=" * 60)
    print("Cross-Chain Access SDK - Error Handling")
    print("=" * 60)
    print()
    
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")
    USER_EMAIL = os.getenv("USER_EMAIL")
    
    if not PRIVATE_KEY or not USER_EMAIL:
        print("❌ Skipping - missing credentials")
        return
    
    # Environment (dev/prod) is set via SWARM_COLLECTION_MODE env variable
    async with CrossChainAccessClient(
        network=Network.POLYGON,
        private_key=PRIVATE_KEY,
        user_email=USER_EMAIL,
    ) as client:
        
        # Error 1: Market Closed
        print("📍 Error 1: Market Closed")
        print("-" * 60)
        try:
            result = await client.buy(
                rwa_token_address="0x...",
                rwa_symbol="AAPL",
                rwa_amount=Decimal("10"),
                user_email=USER_EMAIL,
            )
        except MarketClosedException as e:
            print(f"✅ Caught MarketClosedException: {e}")
            print("   Solution: Trade during market hours (14:30-21:00 UTC)")
        except Exception as e:
            print(f"⚠️  Other error: {e}")
        print()
        
        # Error 2: Account Blocked
        print("📍 Error 2: Account Blocked")
        print("-" * 60)
        try:
            status = await client.cross_chain_access_api.get_account_status()
            if status.account_blocked:
                raise AccountBlockedException("Account is blocked")
            print("✅ Account not blocked")
        except AccountBlockedException as e:
            print(f"✅ Caught AccountBlockedException: {e}")
            print("   Solution: Contact support to unblock account")
        print()
        
        # Error 3: Insufficient Funds
        print("📍 Error 3: Insufficient Funds")
        print("-" * 60)
        try:
            result = await client.buy(
                rwa_token_address="0x...",
                rwa_symbol="AAPL",
                usdc_amount=Decimal("1000000"),  # Very large amount
                user_email=USER_EMAIL,
            )
        except InsufficientFundsException as e:
            print(f"✅ Caught InsufficientFundsException: {e}")
            print("   Solution: Reduce trade amount or add more funds")
        except Exception as e:
            print(f"⚠️  Other error: {type(e).__name__}: {e}")
        print()


async def example_market_maker_errors():
    """Example: Handling Market Maker-specific errors."""
    print("=" * 60)
    print("Market Maker SDK - Error Handling")
    print("=" * 60)
    print()
    
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")
    RPQ_API_KEY = os.getenv("RPQ_API_KEY")
    
    if not PRIVATE_KEY or not RPQ_API_KEY:
        print("❌ Skipping - missing credentials")
        return
    
    # Environment (dev/prod) is set via SWARM_COLLECTION_MODE env variable
    async with MarketMakerClient(
        network=Network.POLYGON,
        private_key=PRIVATE_KEY,
        rpq_api_key=RPQ_API_KEY,
    ) as client:
        
        # Error 1: No Offers Available
        print("📍 Error 1: No Offers Available")
        print("-" * 60)
        try:
            offers = await client.rpq_client.get_offers(
                deposit_token="0xInvalidToken",
                withdraw_token="0xAnotherInvalid",
            )
        except NoOffersAvailableException as e:
            print(f"✅ Caught NoOffersAvailableException: {e}")
            print("   Solution: Try different token pair or create your own offer")
        except Exception as e:
            print(f"⚠️  Other error: {type(e).__name__}: {e}")
        print()
        
        # Error 2: Insufficient Balance
        print("📍 Error 2: Insufficient Token Balance")
        print("-" * 60)
        try:
            # This would fail if you don't have enough tokens
            result = await client.trade(
                from_token="0x...",
                to_token="0x...",
                from_amount=Decimal("1000000"),  # Very large amount
            )
        except InsufficientBalanceException as e:
            print(f"✅ Caught InsufficientBalanceException: {e}")
            print("   Solution: Reduce trade amount or acquire more tokens")
        except Exception as e:
            print(f"⚠️  Other error: {type(e).__name__}: {e}")
        print()


async def example_trading_sdk_errors():
    """Example: Handling Trading SDK errors with fallback."""
    print("=" * 60)
    print("Trading SDK - Error Handling with Fallback")
    print("=" * 60)
    print()
    
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")
    RPQ_API_KEY = os.getenv("RPQ_API_KEY")
    USER_EMAIL = os.getenv("USER_EMAIL")
    
    if not PRIVATE_KEY or not RPQ_API_KEY or not USER_EMAIL:
        print("❌ Skipping - missing credentials")
        return
    
    # Error 1: No Liquidity on Any Platform
    print("📍 Error 1: No Liquidity Exception")
    print("-" * 60)
    
    # Environment (dev/prod) is set via SWARM_COLLECTION_MODE env variable
    async with TradingClient(
        network=Network.POLYGON,
        private_key=PRIVATE_KEY,
        rpq_api_key=RPQ_API_KEY,
        user_email=USER_EMAIL,
        routing_strategy=RoutingStrategy.BEST_PRICE,
    ) as client:
        
        try:
            result = await client.trade(
                from_token="0xInvalidToken",
                to_token="0xAnotherInvalid",
                from_amount=Decimal("100"),
                user_email=USER_EMAIL,
            )
        except NoLiquidityException as e:
            print(f"✅ Caught NoLiquidityException: {e}")
            print("   Solution: Check token addresses or try later")
        except Exception as e:
            print(f"⚠️  Other error: {type(e).__name__}: {e}")
        print()
    
    # Error 2: All Platforms Failed
    print("📍 Error 2: All Platforms Failed")
    print("-" * 60)
    print("This happens when primary platform fails and fallback also fails")
    print()
    """
    try:
        result = await client.trade(...)
    except AllPlatformsFailedException as e:
        print(f"✅ Caught AllPlatformsFailedException: {e}")
        print("   Solution: Check network connectivity or try later")
    """
    
    # Error 3: Successful Fallback
    print("📍 Error 3: Successful Fallback Scenario")
    print("-" * 60)
    print("When primary platform fails, SDK automatically tries fallback:")
    print()
    print("Scenario: Market closed on Cross-Chain Access")
    print("  1. Try Cross-Chain Access → MarketClosedException")
    print("  2. Automatic fallback to Market Maker")
    print("  3. ✅ Trade succeeds on Market Maker")
    print()
    print("This happens automatically with BEST_PRICE, CROSS_CHAIN_ACCESS_FIRST, or MARKET_MAKER_FIRST")
    print()


async def example_web3_errors():
    """Example: Handling Web3/blockchain errors."""
    print("=" * 60)
    print("Web3 - Blockchain Error Handling")
    print("=" * 60)
    print()
    
    # Error types:
    print("Common Web3 errors and solutions:")
    print("-" * 60)
    print()
    
    print("1. InsufficientBalanceException")
    print("   - Cause: Not enough tokens in wallet")
    print("   - Solution: Acquire more tokens or reduce amount")
    print()
    
    print("2. TransactionFailedException")
    print("   - Cause: Transaction reverted on-chain")
    print("   - Solution: Check gas, allowances, or contract state")
    print()
    
    print("3. InsufficientAllowanceException")
    print("   - Cause: Contract not approved to spend tokens")
    print("   - Solution: SDK auto-approves, but check approval status")
    print()
    
    print("4. NetworkNotSupportedException")
    print("   - Cause: Trying to use unsupported network")
    print("   - Solution: Use supported networks (Ethereum, Polygon, etc.)")
    print()


async def main():
    """Run all error handling examples."""
    
    print()
    print("🔧 Swarm Trading SDKs - Error Handling Guide")
    print("=" * 60)
    print()
    
    await example_cross_chain_access_errors()
    print()
    
    await example_market_maker_errors()
    print()
    
    await example_trading_sdk_errors()
    print()
    
    await example_web3_errors()
    print()
    
    print("=" * 60)
    print("Error Handling Guide Complete!")
    print("=" * 60)
    print()
    print("Best Practices:")
    print("-" * 60)
    print("1. Always use try-except blocks for trades")
    print("2. Catch specific exceptions before generic ones")
    print("3. Use Trading SDK for automatic fallback handling")
    print("4. Check market hours before Cross-Chain Access trades")
    print("5. Validate balances before large trades")
    print("6. Use context managers (async with) for cleanup")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

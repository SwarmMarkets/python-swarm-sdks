"""Market Maker smart contract ABIs and addresses.

Contract addresses are now fetched from remote configuration.
Use get_market_maker_manager_address() to retrieve addresses dynamically.
"""


# Market Maker Manager contract ABI (simplified - only methods we need)
MARKET_MAKER_MANAGER_ABI = [
    # Take fixed offer
    {
        "inputs": [
            {"internalType": "uint256", "name": "offerId", "type": "uint256"},
            {"internalType": "uint256", "name": "withdrawalAmountPaid", "type": "uint256"},
            {"internalType": "address", "name": "affiliate", "type": "address"},
        ],
        "name": "takeOfferFixed",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    # Take dynamic offer
    {
        "inputs": [
            {"internalType": "uint256", "name": "offerId", "type": "uint256"},
            {"internalType": "uint256", "name": "withdrawalAmountPaid", "type": "uint256"},
            {"internalType": "uint256", "name": "maximumDepositToWithdrawalRate", "type": "uint256"},
            {"internalType": "address", "name": "affiliate", "type": "address"},
        ],
        "name": "takeOfferDynamic",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    # Make offer
    {
        "inputs": [
            {"internalType": "address", "name": "depositToken", "type": "address"},
            {"internalType": "uint256", "name": "depositAmount", "type": "uint256"},
            {"internalType": "address", "name": "withdrawToken", "type": "address"},
            {"internalType": "uint256", "name": "withdrawAmount", "type": "uint256"},
            {"internalType": "bool", "name": "isDynamic", "type": "bool"},
            {"internalType": "uint256", "name": "expiresAt", "type": "uint256"},
        ],
        "name": "makeOffer",
        "outputs": [{"internalType": "uint256", "name": "offerId", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    # Cancel offer
    {
        "inputs": [
            {"internalType": "uint256", "name": "offerId", "type": "uint256"},
        ],
        "name": "cancelOffer",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    # Get offer details
    {
        "inputs": [
            {"internalType": "uint256", "name": "offerId", "type": "uint256"},
        ],
        "name": "getOffer",
        "outputs": [
            {"internalType": "address", "name": "maker", "type": "address"},
            {"internalType": "address", "name": "depositToken", "type": "address"},
            {"internalType": "uint256", "name": "depositAmount", "type": "uint256"},
            {"internalType": "address", "name": "withdrawToken", "type": "address"},
            {"internalType": "uint256", "name": "withdrawAmount", "type": "uint256"},
            {"internalType": "bool", "name": "isActive", "type": "bool"},
            {"internalType": "bool", "name": "isDynamic", "type": "bool"},
            {"internalType": "uint256", "name": "expiresAt", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


async def get_market_maker_manager_address(chain_id: int) -> str:
    """Get Market Maker Manager contract address for a specific chain.
    
    Fetches from remote configuration with fallback to legacy addresses.
    
    Args:
        chain_id: Blockchain network ID
    
    Returns:
        Market Maker Manager contract address
    
    Raises:
        ValueError: If address not found for chain
    """
    from swarm.shared.remote_config import get_config_fetcher
    # Determine if dev mode based on environment
    import os
    is_dev = os.getenv("SWARM_COLLECTION_MODE", "prod").lower() == "dev"
    fetcher = await get_config_fetcher(is_dev=is_dev)
    return fetcher.get_market_maker_manager_address(chain_id)

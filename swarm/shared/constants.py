"""Shared constants for Swarm Collection.

This module contains static addresses and configuration that do NOT vary by environment.
For environment-dependent values (dev/prod), see shared/config.py instead.
"""

from .models import Network

# USDC token addresses for different networks (static, not environment-dependent)
USDC_ADDRESSES = {
    Network.ETHEREUM: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    Network.POLYGON: "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
    Network.BASE: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    Network.BSC: "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d"
}

# Common token decimals (static)
TOKEN_DECIMALS = {
    "USDC": 6,
    "USDT": 6,
    "DAI": 18,
    "WETH": 18,
    "WMATIC": 18,
}

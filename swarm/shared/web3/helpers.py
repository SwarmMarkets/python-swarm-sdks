"""Web3 helper for blockchain transactions."""

import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from web3 import Web3

try:
    from web3.middleware import geth_poa_middleware
except ImportError:
    # For newer versions of web3.py
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware

from eth_account import Account
from eth_account.signers.local import LocalAccount

from ..models import Network
from .constants import (
    ERC20_ABI,
    RPC_ENDPOINTS,
    POA_NETWORKS,
    GAS_BUFFER_MULTIPLIER,
    DEFAULT_GAS_LIMIT,
    TX_TIMEOUT,
)
from .exceptions import (
    InsufficientBalanceException,
    TransactionFailedException,
    NetworkNotSupportedException,
)

logger = logging.getLogger(__name__)


class Web3Helper:
    """
    Helper for Web3 blockchain interactions.
    
    Provides methods for:
    - ERC20 token operations (transfer, approve, balance, allowance)
    - Gas estimation
    - Transaction signing and submission
    - Native token balance checks
    """

    def __init__(self, private_key: str, network: Network, rpc_url: Optional[str] = None):
        """
        Initialize Web3 helper.

        Args:
            private_key: Private key for signing transactions
            network: Blockchain network
            rpc_url: Optional custom RPC URL (uses default if not provided)
            
        Raises:
            NetworkNotSupportedException: If network is not supported
        """
        self.network = network
        self.chain_id = network.value
        
        # Initialize Web3 with RPC
        if rpc_url is None:
            rpc_url = RPC_ENDPOINTS.get(network)
            if not rpc_url:
                raise NetworkNotSupportedException(network.name)
        
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Add PoA middleware for certain chains
        if network in POA_NETWORKS:
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Initialize account
        self.account: LocalAccount = Account.from_key(private_key)
        self.address = self.account.address
        
        logger.info(f"Initialized Web3 for {network.name} (chain_id: {self.chain_id})")
        logger.info(f"Wallet address: {self.address}")
        logger.info(f"RPC: {rpc_url}")

    def get_balance(self, token_address: str) -> Decimal:
        """
        Get ERC20 token balance.

        Args:
            token_address: Token contract address

        Returns:
            Token balance in normalized decimal units
        """
        token_address = Web3.to_checksum_address(token_address)
        contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
        
        # Get balance in smallest units
        balance_wei = contract.functions.balanceOf(self.address).call()
        
        # Get decimals
        decimals = self._get_token_decimals(token_address)
        
        # Convert to normalized decimal
        balance = Decimal(balance_wei) / Decimal(10 ** decimals)
        
        return balance

    def get_allowance(self, token_address: str, spender: str) -> Decimal:
        """
        Get token allowance for a spender.

        Args:
            token_address: Token contract address
            spender: Spender address

        Returns:
            Allowance in normalized decimal units
        """
        token_address = Web3.to_checksum_address(token_address)
        spender = Web3.to_checksum_address(spender)
        contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
        
        # Get allowance in smallest units
        allowance_wei = contract.functions.allowance(self.address, spender).call()
        
        # Get decimals
        decimals = self._get_token_decimals(token_address)
        
        # Convert to normalized decimal
        allowance = Decimal(allowance_wei) / Decimal(10 ** decimals)
        
        return allowance

    def approve_token(
        self,
        token_address: str,
        spender: str,
        amount: Decimal,
        wait_for_receipt: bool = True,
    ) -> str:
        """
        Approve token spending.

        Args:
            token_address: Token contract address
            spender: Spender address
            amount: Amount to approve (normalized)
            wait_for_receipt: Wait for transaction confirmation

        Returns:
            Transaction hash

        Raises:
            TransactionFailedException: When transaction fails
        """
        token_address = Web3.to_checksum_address(token_address)
        spender = Web3.to_checksum_address(spender)
        
        contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
        decimals = self._get_token_decimals(token_address)
        
        # Convert to smallest units
        amount_wei = int(amount * Decimal(10 ** decimals))
        
        logger.info(f"Approving {amount} tokens for {spender}")
        
        # Build transaction
        nonce = self.w3.eth.get_transaction_count(self.address)
        
        transaction = contract.functions.approve(
            spender, amount_wei
        ).build_transaction({
            "from": self.address,
            "gas": 100000,  # Standard approve gas
            "gasPrice": self.w3.eth.gas_price,
            "nonce": nonce,
            "chainId": self.chain_id,
        })
        
        # Sign and send
        return self._sign_and_send_transaction(transaction, wait_for_receipt)

    def transfer_token(
        self,
        to_address: str,
        token_address: str,
        amount: Decimal,
        wait_for_receipt: bool = True,
    ) -> str:
        """
        Transfer ERC20 tokens.

        Args:
            to_address: Recipient address
            token_address: Token contract address
            amount: Amount to transfer (normalized)
            wait_for_receipt: Wait for transaction confirmation

        Returns:
            Transaction hash

        Raises:
            InsufficientBalanceException: When balance is insufficient
            TransactionFailedException: When transaction fails
        """
        token_address = Web3.to_checksum_address(token_address)
        to_address = Web3.to_checksum_address(to_address)
        
        # Check balance
        balance = self.get_balance(token_address)
        if balance < amount:
            raise InsufficientBalanceException(
                required=float(amount),
                available=float(balance),
                token=token_address,
            )
        
        contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
        decimals = self._get_token_decimals(token_address)
        
        # Convert to smallest units
        amount_wei = int(amount * Decimal(10 ** decimals))
        
        logger.info(f"Transferring {amount} tokens to {to_address}")
        logger.info(f"Amount in smallest units: {amount_wei}")
        
        # Estimate gas
        gas_info = self.estimate_gas(to_address, token_address, amount)
        
        # Build transaction
        nonce = self.w3.eth.get_transaction_count(self.address)
        
        transaction = contract.functions.transfer(
            to_address, amount_wei
        ).build_transaction({
            "from": self.address,
            "gas": gas_info["gas_limit"],
            "gasPrice": gas_info["gas_price"],
            "nonce": nonce,
            "chainId": self.chain_id,
        })
        
        # Sign and send
        return self._sign_and_send_transaction(transaction, wait_for_receipt)

    def estimate_gas(
        self,
        to_address: str,
        token_address: str,
        amount: Decimal,
    ) -> Dict[str, Any]:
        """
        Estimate gas for token transfer.

        Args:
            to_address: Recipient address
            token_address: Token contract address
            amount: Amount to transfer (normalized)

        Returns:
            Dict with gas_limit, gas_price, and gas_cost
        """
        token_address = Web3.to_checksum_address(token_address)
        to_address = Web3.to_checksum_address(to_address)
        contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
        
        decimals = self._get_token_decimals(token_address)
        amount_wei = int(amount * Decimal(10 ** decimals))
        
        # Estimate gas
        try:
            gas_limit = contract.functions.transfer(
                to_address, amount_wei
            ).estimate_gas({"from": self.address})
            
            # Add buffer
            gas_limit = int(gas_limit * GAS_BUFFER_MULTIPLIER)
        except Exception as e:
            logger.warning(f"Gas estimation failed: {e}, using default")
            gas_limit = DEFAULT_GAS_LIMIT
        
        # Get gas price
        gas_price = self.w3.eth.gas_price
        
        # Calculate cost in native token
        gas_cost = Decimal(gas_limit * gas_price) / Decimal(10 ** 18)
        
        return {
            "gas_limit": gas_limit,
            "gas_price": gas_price,
            "gas_cost": gas_cost,
        }

    def get_native_balance(self) -> Decimal:
        """
        Get native token balance (ETH, MATIC, etc.).

        Returns:
            Native token balance
        """
        balance_wei = self.w3.eth.get_balance(self.address)
        balance = Decimal(balance_wei) / Decimal(10 ** 18)
        return balance

    def is_connected(self) -> bool:
        """Check if Web3 is connected to RPC."""
        return self.w3.is_connected()

    def _get_token_decimals(self, token_address: str) -> int:
        """
        Get token decimals.

        Args:
            token_address: Token contract address

        Returns:
            Number of decimals (default 18 if call fails)
        """
        try:
            contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
            return contract.functions.decimals().call()
        except Exception as e:
            logger.warning(f"Failed to get decimals for {token_address}: {e}, using default 18")
            return 18

    def _sign_and_send_transaction(
        self,
        transaction: Dict[str, Any],
        wait_for_receipt: bool = True,
    ) -> str:
        """
        Sign and send a transaction.

        Args:
            transaction: Transaction dict
            wait_for_receipt: Wait for confirmation

        Returns:
            Transaction hash

        Raises:
            TransactionFailedException: When transaction fails
        """
        try:
            # Sign transaction
            signed_txn = self.account.sign_transaction(transaction)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            logger.info(f"Transaction sent: {tx_hash_hex}")
            
            # Wait for receipt if requested
            if wait_for_receipt:
                logger.info("Waiting for transaction confirmation...")
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=TX_TIMEOUT)
                
                if receipt["status"] == 0:
                    raise TransactionFailedException(
                        tx_hash=tx_hash_hex,
                        reason="Transaction reverted"
                    )
                
                logger.info(f"Transaction confirmed in block {receipt['blockNumber']}")
            
            return tx_hash_hex
            
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            if isinstance(e, TransactionFailedException):
                raise
            raise TransactionFailedException(reason=str(e))

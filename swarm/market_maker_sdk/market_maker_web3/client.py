"""Market Maker Web3 client for smart contract interactions."""

import asyncio
from typing import Optional, Dict, Any
from decimal import Decimal
from eth_account.signers.local import LocalAccount
import logging

from web3 import Web3
from web3.exceptions import ContractLogicError

from swarm.shared.web3 import Web3Helper, Web3Exception, TransactionFailedException
from swarm.shared.models import Network
from swarm.shared.constants import TOKEN_DECIMALS
from .constants import MARKET_MAKER_MANAGER_ABI, get_market_maker_manager_address
from .exceptions import (
    MarketMakerWeb3Exception,
    OfferNotFoundError,
    OfferInactiveError,
    InsufficientOfferBalanceError,
    OfferExpiredError,
    UnauthorizedError,
)

logger = logging.getLogger(__name__)


class MarketMakerWeb3Client:
    """Client for interacting with Market Maker smart contracts.
    
    Provides methods to:
    - Take fixed and dynamic offers
    - Make new offers
    - Cancel existing offers
    - Approve tokens for trading
    
    Attributes:
        network: Network for this client instance
        web3_helper: Web3Helper for blockchain operations
        contract: Market Maker Manager contract instance
        account: User's wallet account
    
    Example:
        >>> client = MarketMakerWeb3Client(
        ...     network=Network.POLYGON,
        ...     private_key="0x..."
        ... )
        >>> tx_hash = await client.take_offer_fixed(
        ...     offer_id="12345",
        ...     amount=Decimal("10")
        ... )
    """
    
    def __init__(
        self,
        network: Network,
        private_key: str,
        rpc_url: Optional[str] = None,
    ):
        """Initialize Market Maker Web3 client.
        
        Args:
            network: Network to interact with
            private_key: Private key for signing transactions
            rpc_url: Optional custom RPC URL (uses default if not provided)
        """
        self.network = network
        self.web3_helper = Web3Helper(
            network=network,
            private_key=private_key,
            rpc_url=rpc_url,
        )
        
        # Contract address will be loaded lazily on first use
        self.contract = None
        self.account = self.web3_helper.account
        
        logger.info(
            f"Initialized Market Maker Web3 client for network {network.name} "
            f"with account {self.account.address}"
        )
    
    async def _ensure_contract_loaded(self):
        """Ensure Market Maker Manager contract is loaded.
        
        This loads the contract address dynamically from remote config.
        """
        if self.contract is not None:
            return
        
        # Get Market Maker Manager contract address from remote config
        contract_address = await get_market_maker_manager_address(self.network.value)
        
        if not contract_address or contract_address == "0x0000000000000000000000000000000000000000":
            raise MarketMakerWeb3Exception(
                f"Market Maker Manager contract not deployed on network {self.network.name}"
            )
        
        # Initialize contract
        self.contract = self.web3_helper.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=MARKET_MAKER_MANAGER_ABI,
        )
        
        logger.info(f"Market Maker Manager contract loaded: {contract_address}")
    
    async def take_offer_fixed(
        self,
        offer_id: str,
        withdrawal_token: str,
        withdrawal_amount_paid: Decimal,
        affiliate: Optional[str] = None,
    ) -> str:
        """Take a fixed-price offer.
        
        When taking an offer:
        - Taker PAYS the withdrawal asset (what maker wants to receive)
        - Taker RECEIVES the deposit asset (what maker deposited)
        
        This will:
        1. Approve Market Maker contract to spend withdrawal tokens
        2. Call takeOfferFixed on-chain
        3. Return transaction hash
        
        Args:
            offer_id: Unique offer identifier
            withdrawal_token: Token address to pay (maker's withdrawalAsset)
            withdrawal_amount_paid: Amount to pay in smallest units (from RPQ API amountIn)
            affiliate: Optional affiliate address for fee sharing (use None for zero address)
        
        Returns:
            Transaction hash (0x...)
        
        Raises:
            OfferNotFoundError: If offer doesn't exist
            OfferInactiveError: If offer is not active
            InsufficientOfferBalanceError: If maker has insufficient balance
            Web3Exception: If blockchain operation fails
        
        Example:
            >>> # Taker pays 100 USDC (withdrawalAsset) to receive RWA (depositAsset)
            >>> tx_hash = await client.take_offer_fixed(
            ...     offer_id="12345",
            ...     withdrawal_token="0xUSDC...",
            ...     withdrawal_amount_paid=Decimal("100500000"),  # 100.5 USDC in smallest units
            ...     affiliate=None
            ... )
        """
        try:
            # Ensure contract is loaded
            await self._ensure_contract_loaded()
            
            logger.info(
                f"Taking fixed offer {offer_id} with {withdrawal_amount_paid} tokens"
            )
            
            # Amount is already in smallest units from RPQ API (amountIn)
            amount_wei = int(withdrawal_amount_paid)
            
            # Convert offer_id to int (handle both hex and decimal strings)
            if isinstance(offer_id, str):
                if offer_id.startswith('0x'):
                    offer_id_int = int(offer_id, 16)  # Convert from hex
                else:
                    offer_id_int = int(offer_id)  # Convert from decimal string
            else:
                offer_id_int = int(offer_id)
            
            # Use zero address if no affiliate provided
            affiliate_address = affiliate if affiliate else "0x0000000000000000000000000000000000000000"
            affiliate_address = Web3.to_checksum_address(affiliate_address)
            
            # Step 1: Approve Market Maker contract to spend withdrawal tokens
            # Convert back to normalized units for approval
            token_decimals = TOKEN_DECIMALS.get(
                self.network.value, {}
            ).get(withdrawal_token.lower(), 18)
            normalized_amount = withdrawal_amount_paid / Decimal(10 ** token_decimals)
            
            await self._approve_token_if_needed(
                token_address=withdrawal_token,
                spender=self.contract.address,
                amount=normalized_amount,
            )
            
            # Step 2: Take offer on-chain
            # function takeOfferFixed(uint256 offerId, uint256 withdrawalAmountPaid, address affiliate)
            tx_hash = await self._execute_contract_function(
                "takeOfferFixed",
                offer_id_int,
                amount_wei,
                affiliate_address,
            )
            
            logger.info(f"Successfully took fixed offer {offer_id}: {tx_hash}")
            
            return tx_hash
            
        except ContractLogicError as e:
            self._handle_contract_error(e, "take fixed offer")
        except Web3Exception:
            raise
        except Exception as e:
            raise MarketMakerWeb3Exception(f"Failed to take fixed offer: {e}") from e
    
    async def take_offer_dynamic(
        self,
        offer_id: str,
        withdrawal_token: str,
        withdrawal_amount_paid: Decimal,
        maximum_deposit_to_withdrawal_rate: Decimal,
        affiliate: Optional[str] = None,
    ) -> str:
        """Take a dynamic-price offer.
        
        Dynamic offers use real-time price feeds to determine exchange rates.
        
        When taking an offer:
        - Taker PAYS the withdrawal asset (what maker wants to receive)
        - Taker RECEIVES the deposit asset (what maker deposited)
        
        This will:
        1. Approve Market Maker contract to spend withdrawal tokens
        2. Call takeOfferDynamic on-chain with slippage protection
        3. Return transaction hash
        
        Args:
            offer_id: Unique offer identifier
            withdrawal_token: Token address to pay (maker's withdrawalAsset)
            withdrawal_amount_paid: Amount to pay in smallest units (from RPQ API amountIn)
            maximum_deposit_to_withdrawal_rate: Max on-chain rate to accept (in withdrawal token decimals).
                Copy from API's depositToWithdrawalRate. Set to 0 to use current rate without cap.
            affiliate: Optional affiliate address for fee sharing (use None for zero address)
        
        Returns:
            Transaction hash (0x...)
        
        Raises:
            OfferNotFoundError: If offer doesn't exist
            OfferInactiveError: If offer is not active
            Web3Exception: If blockchain operation fails
        
        Example:
            >>> # Taker pays 50.25 USDC (withdrawalAsset) to receive RWA (depositAsset)
            >>> # Use depositToWithdrawalRate from API response for slippage protection
            >>> tx_hash = await client.take_offer_dynamic(
            ...     offer_id="67890",
            ...     withdrawal_token="0xUSDC...",
            ...     withdrawal_amount_paid=Decimal("50250000"),  # 50.25 USDC in smallest units
            ...     maximum_deposit_to_withdrawal_rate=Decimal("1050000"),  # From API
            ...     affiliate=None
            ... )
        """
        try:
            # Ensure contract is loaded
            await self._ensure_contract_loaded()
            
            logger.info(
                f"Taking dynamic offer {offer_id} with {withdrawal_amount_paid} tokens "
                f"(max rate: {maximum_deposit_to_withdrawal_rate})"
            )
            
            # Amount is already in smallest units from RPQ API (amountIn)
            amount_wei = int(withdrawal_amount_paid)
            
            # Convert rate to int (already in withdrawal token decimals from API)
            max_rate_wei = int(maximum_deposit_to_withdrawal_rate)
            
            # Convert offer_id to int (handle both hex and decimal strings)
            if isinstance(offer_id, str):
                if offer_id.startswith('0x'):
                    offer_id_int = int(offer_id, 16)  # Convert from hex
                else:
                    offer_id_int = int(offer_id)  # Convert from decimal string
            else:
                offer_id_int = int(offer_id)
            
            # Use zero address if no affiliate provided
            affiliate_address = affiliate if affiliate else "0x0000000000000000000000000000000000000000"
            affiliate_address = Web3.to_checksum_address(affiliate_address)
            
            # Step 1: Approve Market Maker contract to spend withdrawal tokens
            # Convert back to normalized units for approval
            token_decimals = TOKEN_DECIMALS.get(
                self.network.value, {}
            ).get(withdrawal_token.lower(), 18)
            normalized_amount = withdrawal_amount_paid / Decimal(10 ** token_decimals)
            
            await self._approve_token_if_needed(
                token_address=withdrawal_token,
                spender=self.contract.address,
                amount=normalized_amount,
            )
            
            # Step 2: Take offer on-chain
            # function takeOfferDynamic(uint256 offerId, uint256 withdrawalAmountPaid, uint256 maximumDepositToWithdrawalRate, address affiliate)
            tx_hash = await self._execute_contract_function(
                "takeOfferDynamic",
                offer_id_int,
                amount_wei,
                max_rate_wei,
                affiliate_address,
            )
            
            logger.info(f"Successfully took dynamic offer {offer_id}: {tx_hash}")
            
            return tx_hash
            
        except ContractLogicError as e:
            self._handle_contract_error(e, "take dynamic offer")
        except Web3Exception:
            raise
        except Exception as e:
            raise MarketMakerWeb3Exception(f"Failed to take dynamic offer: {e}") from e
    
    async def make_offer(
        self,
        deposit_token: str,
        deposit_amount: Decimal,
        withdraw_token: str,
        withdraw_amount: Decimal,
        is_dynamic: bool = False,
        expires_at: Optional[int] = None,
    ) -> tuple[str, str]:
        """Create a new Market Maker offer.
        
        This will:
        1. Approve Market Maker contract to spend deposit tokens
        2. Call makeOffer on-chain
        3. Return transaction hash and offer ID
        
        Args:
            deposit_token: Token to deposit
            deposit_amount: Amount to deposit (normalized)
            withdraw_token: Token to withdraw
            withdraw_amount: Amount to withdraw (normalized)
            is_dynamic: Whether to create dynamic offer
            expires_at: Optional expiration timestamp (0 = no expiry)
        
        Returns:
            Tuple of (transaction_hash, offer_id)
        
        Raises:
            Web3Exception: If blockchain operation fails
        
        Example:
            >>> tx_hash, offer_id = await client.make_offer(
            ...     deposit_token="0xRWA...",
            ...     deposit_amount=Decimal("10"),
            ...     withdraw_token="0xUSDC...",
            ...     withdraw_amount=Decimal("1000"),
            ...     is_dynamic=False
            ... )
        """
        try:
            logger.info(
                f"Creating {'dynamic' if is_dynamic else 'fixed'} offer: "
                f"{deposit_amount} -> {withdraw_amount}"
            )
            
            # Convert amounts to smallest units
            deposit_decimals = TOKEN_DECIMALS.get(
                self.network.value, {}
            ).get(deposit_token.lower(), 18)
            withdraw_decimals = TOKEN_DECIMALS.get(
                self.network.value, {}
            ).get(withdraw_token.lower(), 18)
            
            deposit_wei = int(deposit_amount * Decimal(10 ** deposit_decimals))
            withdraw_wei = int(withdraw_amount * Decimal(10 ** withdraw_decimals))
            
            # Step 1: Approve Market Maker contract to spend deposit tokens
            await self._approve_token_if_needed(
                token_address=deposit_token,
                spender=self.contract.address,
                amount=deposit_amount,
            )
            
            # Step 2: Make offer on-chain
            expires_timestamp = expires_at or 0
            
            tx_hash = await self._execute_contract_function(
                "makeOffer",
                Web3.to_checksum_address(deposit_token),
                deposit_wei,
                Web3.to_checksum_address(withdraw_token),
                withdraw_wei,
                is_dynamic,
                expires_timestamp,
            )
            
            # Extract offer ID from transaction receipt
            receipt = self.web3_helper.w3.eth.get_transaction_receipt(tx_hash)
            
            # Parse logs to get offer ID (simplified - assumes first log contains it)
            # In production, you'd parse the specific event
            offer_id = "0"  # Placeholder - need to parse from logs
            
            logger.info(
                f"Successfully created offer {offer_id}: {tx_hash}"
            )
            
            return tx_hash, offer_id
            
        except ContractLogicError as e:
            self._handle_contract_error(e, "make offer")
        except Web3Exception:
            raise
        except Exception as e:
            raise MarketMakerWeb3Exception(f"Failed to make offer: {e}") from e
    
    async def cancel_offer(self, offer_id: str) -> str:
        """Cancel an existing offer.
        
        Only the offer maker can cancel their own offers.
        
        Args:
            offer_id: Offer ID to cancel
        
        Returns:
            Transaction hash (0x...)
        
        Raises:
            OfferNotFoundError: If offer doesn't exist
            UnauthorizedError: If caller is not the maker
            Web3Exception: If blockchain operation fails
        
        Example:
            >>> tx_hash = await client.cancel_offer(offer_id="12345")
        """
        try:
            logger.info(f"Cancelling offer {offer_id}")
            
            # Convert offer_id to int (handle both hex and decimal strings)
            if isinstance(offer_id, str):
                if offer_id.startswith('0x'):
                    offer_id_int = int(offer_id, 16)  # Convert from hex
                else:
                    offer_id_int = int(offer_id)  # Convert from decimal string
            else:
                offer_id_int = int(offer_id)
            
            tx_hash = await self._execute_contract_function(
                "cancelOffer",
                offer_id_int,
            )
            
            logger.info(f"Successfully cancelled offer {offer_id}: {tx_hash}")
            
            return tx_hash
            
        except ContractLogicError as e:
            self._handle_contract_error(e, "cancel offer")
        except Web3Exception:
            raise
        except Exception as e:
            raise MarketMakerWeb3Exception(f"Failed to cancel offer: {e}") from e
    
    async def get_offer_details(self, offer_id: str) -> Dict[str, Any]:
        """Get on-chain details for an offer.
        
        Args:
            offer_id: Offer ID to query
        
        Returns:
            Dictionary with offer details
        
        Raises:
            OfferNotFoundError: If offer doesn't exist
        
        Example:
            >>> details = await client.get_offer_details("12345")
            >>> print(f"Maker: {details['maker']}")
        """
        try:
            # Convert offer_id to int (handle both hex and decimal strings)
            if isinstance(offer_id, str):
                if offer_id.startswith('0x'):
                    offer_id_int = int(offer_id, 16)  # Convert from hex
                else:
                    offer_id_int = int(offer_id)  # Convert from decimal string
            else:
                offer_id_int = int(offer_id)
            
            result = self.contract.functions.getOffer(offer_id_int).call()
            
            return {
                "maker": result[0],
                "deposit_token": result[1],
                "deposit_amount": result[2],
                "withdraw_token": result[3],
                "withdraw_amount": result[4],
                "is_active": result[5],
                "is_dynamic": result[6],
                "expires_at": result[7],
            }
            
        except Exception as e:
            if "execution reverted" in str(e).lower():
                raise OfferNotFoundError(f"Offer {offer_id} not found") from e
            raise MarketMakerWeb3Exception(f"Failed to get offer details: {e}") from e
    
    async def _approve_token_if_needed(
        self,
        token_address: str,
        spender: str,
        amount: Decimal,
    ) -> Optional[str]:
        """Approve token spending if allowance is insufficient.
        
        Args:
            token_address: Token to approve
            spender: Address to approve (Market Maker contract)
            amount: Amount needed (normalized)
        
        Returns:
            Transaction hash if approval was needed, None otherwise
        """
        # Check current allowance
        current_allowance = self.web3_helper.get_allowance(
            token_address=token_address,
            spender=spender,
        )
        
        if current_allowance >= amount:
            logger.debug(
                f"Sufficient allowance: {current_allowance} >= {amount}"
            )
            return None
        
        # Need to approve
        logger.info(
            f"Approving {spender} to spend {amount} of {token_address}"
        )
        
        tx_hash = self.web3_helper.approve_token(
            token_address=token_address,
            spender=spender,
            amount=amount,
        )
        
        return tx_hash
    
    async def _execute_contract_function(
        self,
        function_name: str,
        *args,
        **kwargs
    ) -> str:
        """Execute a contract function.
        
        Args:
            function_name: Name of contract function
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        
        Returns:
            Transaction hash
        
        Raises:
            TransactionFailedException: If transaction fails
        """
        try:
            # Get function
            contract_function = getattr(self.contract.functions, function_name)
            
            # Call function with args and kwargs
            # If args are provided, use them; otherwise use kwargs
            if args:
                function_call = contract_function(*args)
            else:
                function_call = contract_function(**kwargs)
            
            # Build transaction
            tx = function_call.build_transaction({
                "from": self.account.address,
                "nonce": self.web3_helper.w3.eth.get_transaction_count(
                    self.account.address
                ),
                "gas": 0,  # Will be estimated
                "gasPrice": self.web3_helper.w3.eth.gas_price,
            })
            
            # Estimate gas
            estimated_gas = self.web3_helper.w3.eth.estimate_gas(tx)
            tx["gas"] = int(estimated_gas * 1.2)  # 20% buffer
            
            # Sign and send
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.web3_helper.w3.eth.send_raw_transaction(
                signed_tx.raw_transaction
            )
            print(f"tx_hash {tx_hash}")
            
            # Wait for confirmation
            receipt = self.web3_helper.w3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=300
            )
            
            if receipt["status"] != 1:
                raise TransactionFailedException(
                    f"Transaction failed: {tx_hash.hex()}"
                )
            
            return tx_hash.hex()
            
        except Exception as e:
            raise TransactionFailedException(
                f"Failed to execute {function_name}: {e}"
            ) from e
    
    def _handle_contract_error(self, error: ContractLogicError, operation: str):
        """Parse and raise specific exception for contract errors.
        
        Args:
            error: Contract error
            operation: Operation that failed
        
        Raises:
            Specific Market Maker exception based on error message
        """
        error_msg = str(error).lower()
        
        if "offer not found" in error_msg or "invalid offer" in error_msg:
            raise OfferNotFoundError(f"Offer not found during {operation}") from error
        
        if "offer inactive" in error_msg or "not active" in error_msg:
            raise OfferInactiveError(f"Offer is inactive for {operation}") from error
        
        if "insufficient balance" in error_msg:
            raise InsufficientOfferBalanceError(
                f"Insufficient balance for {operation}"
            ) from error
        
        if "expired" in error_msg:
            raise OfferExpiredError(f"Offer expired for {operation}") from error
        
        if "unauthorized" in error_msg or "not maker" in error_msg:
            raise UnauthorizedError(f"Unauthorized for {operation}") from error
        
        # Generic error
        raise MarketMakerWeb3Exception(f"Contract error during {operation}: {error}") from error

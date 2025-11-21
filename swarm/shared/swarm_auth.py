"""Swarm authentication module - consolidates wallet-based authentication."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass

from eth_account.messages import encode_defunct
from eth_account.signers.local import LocalAccount

from .base_client import BaseAPIClient, APIException
from .config import get_swarm_auth_url

logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================

class SigningTimeoutError(Exception):
    """Raised when message signing takes too long."""
    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class NonceResponse:
    """Response from nonce request."""
    message: str


@dataclass
class LoginResponse:
    """Response from login request."""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    refresh_expires_in: int


@dataclass
class UserAttributes:
    """User account attributes."""
    id: int
    email: str
    role: str
    nft_role: str
    smt_claims: int
    affiliate_id: str
    affiliate_locked: bool
    affiliate: int
    affiliate_updated_at: Optional[str]
    affiliate_campaign: str


@dataclass
class RegisterResponse:
    """Response from register request."""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    refresh_expires_in: int
    address: str
    user: UserAttributes


@dataclass
class AuthTokens:
    """Authentication tokens with expiration."""
    access_token: str
    refresh_token: str
    expires_at: datetime
    refresh_expires_at: datetime
    address: str
    
    def is_expired(self) -> bool:
        """Check if access token is expired."""
        return datetime.utcnow() >= self.expires_at
    
    def is_refresh_expired(self) -> bool:
        """Check if refresh token is expired."""
        return datetime.utcnow() >= self.refresh_expires_at


# ============================================================================
# Token Storage
# ============================================================================

class TokenStorageInterface:
    """Interface for token storage implementations."""
    
    def save(self, address: str, tokens: AuthTokens):
        """Save tokens for an address."""
        raise NotImplementedError

    def load(self, address: str) -> Optional[AuthTokens]:
        """Load tokens for an address."""
        raise NotImplementedError

    def clear(self, address: str):
        """Clear tokens for an address."""
        raise NotImplementedError


class InMemoryStorage(TokenStorageInterface):
    """Simple in-memory token storage (not persistent)."""

    def __init__(self):
        self._store: Dict[str, AuthTokens] = {}

    def save(self, address: str, tokens: AuthTokens):
        """Save tokens in memory."""
        self._store[address.lower()] = tokens

    def load(self, address: str) -> Optional[AuthTokens]:
        """Load tokens from memory."""
        return self._store.get(address.lower())

    def clear(self, address: str):
        """Clear tokens from memory."""
        self._store.pop(address.lower(), None)


# ============================================================================
# Authentication Client
# ============================================================================

class SwarmAuth(BaseAPIClient):
    """
    Swarm authentication client using wallet signatures.
    
    Provides wallet-based authentication for Swarm services:
    1. Checks if wallet is registered
    2. Requests nonce message
    3. Signs message with private key
    4. Logs in or registers based on existence
    5. Returns authentication tokens
    
    Both Cross-Chain Access and Market Maker SDKs use this for authentication.
    Environment (dev/prod) is controlled via SWARM_COLLECTION_MODE env variable.
    """

    def __init__(self, storage: Optional[TokenStorageInterface] = None):
        """
        Initialize Swarm auth client.

        Args:
            storage: Token storage interface (default: InMemoryStorage)
        """
        super().__init__(base_url=get_swarm_auth_url(), auth_token=None)
        self.storage = storage or InMemoryStorage()

    async def check_existence(self, address: str) -> bool:
        """
        Check if wallet address is registered.

        Args:
            address: Wallet address

        Returns:
            True if address exists, False otherwise
        """
        address = address.lower()
        endpoint = f"/addresses/{address}"
        
        try:
            logger.debug(f"Checking existence: GET {self.base_url}{endpoint}")
            await self._make_request("GET", endpoint)
            return True
        except APIException as e:
            # 404 means address doesn't exist
            if e.status_code == 404 or "404" in str(e.message) or "Not Found" in str(e.message):
                return False
            raise

    async def get_nonce(self, address: str, terms: Optional[str] = None) -> NonceResponse:
        """
        Request nonce message for signing.

        Args:
            address: Wallet address
            terms: Optional terms hash (used for registration)

        Returns:
            NonceResponse with message to sign
        """
        endpoint = "/nonce"
        payload = {
            "data": {
                "type": "auth_nonce_request",
                "attributes": {
                    "address": address
                }
            }
        }
        
        if terms:
            payload["data"]["attributes"]["terms_hash"] = terms

        logger.debug(f"Requesting nonce: POST {self.base_url}{endpoint}")
        response = await self._make_request("POST", endpoint, data=payload)
        
        attrs = response.get("data", {}).get("attributes", {})
        message = attrs.get("message", "")
        
        return NonceResponse(message=message)

    async def login(self, address: str, signed_message: str) -> LoginResponse:
        """
        Login with signed message.

        Args:
            address: Wallet address
            signed_message: Signed nonce message

        Returns:
            LoginResponse with tokens
        """
        endpoint = "/login"
        payload = {
            "data": {
                "type": "login_request",
                "attributes": {
                    "auth_pair": {
                        "address": address,
                        "signed_message": signed_message
                    }
                }
            }
        }
        
        logger.debug(f"Logging in: POST {self.base_url}{endpoint}")
        response = await self._make_request("POST", endpoint, data=payload)
        
        attrs = response.get("data", {}).get("attributes", {})
        
        return LoginResponse(
            access_token=attrs.get("access_token"),
            refresh_token=attrs.get("refresh_token"),
            token_type=attrs.get("token_type"),
            expires_in=int(attrs.get("expires_in", 0)),
            refresh_expires_in=int(attrs.get("refresh_expires_in", 0)),
        )

    async def register(
        self,
        address: str,
        signed_message: str,
        safe_addresses: Optional[Dict[str, List[str]]] = None
    ) -> RegisterResponse:
        """
        Register new user with signed message.

        Args:
            address: Wallet address
            signed_message: Signed nonce message
            safe_addresses: Optional Gnosis Safe addresses by network

        Returns:
            RegisterResponse with tokens and user info
        """
        endpoint = "/register"
        payload = {
            "data": {
                "type": "register",
                "attributes": {
                    "auth_pair": {
                        "address": address,
                        "signed_message": signed_message
                    }
                }
            }
        }
        
        if safe_addresses:
            payload["data"]["attributes"]["safe_addresses"] = safe_addresses

        logger.debug(f"Registering: POST {self.base_url}{endpoint}")
        response = await self._make_request("POST", endpoint, data=payload)
        
        attrs = response.get("data", {}).get("attributes", {})
        user_attrs = attrs.get("user", {}).get("attributes", {})

        user = UserAttributes(
            id=int(user_attrs.get("id", 0)),
            email=user_attrs.get("email", ""),
            role=user_attrs.get("role", "user"),
            nft_role=user_attrs.get("nft_role", ""),
            smt_claims=int(user_attrs.get("smt_claims", 0)),
            affiliate_id=user_attrs.get("affiliate_id", ""),
            affiliate_locked=bool(user_attrs.get("affiliate_locked", False)),
            affiliate=int(user_attrs.get("affiliate", 0)),
            affiliate_updated_at=user_attrs.get("affiliate_updated_at"),
            affiliate_campaign=user_attrs.get("affiliate_campaign", ""),
        )

        return RegisterResponse(
            access_token=attrs.get("access_token"),
            refresh_token=attrs.get("refresh_token"),
            token_type=attrs.get("token_type"),
            expires_in=int(attrs.get("expires_in", 0)),
            refresh_expires_in=int(attrs.get("refresh_expires_in", 0)),
            address=attrs.get("address", ""),
            user=user,
        )

    async def verify(
        self,
        signer: LocalAccount,
        safe_addresses: Optional[Dict[str, List[str]]] = None,
        signing_timeout: float = 60.0,
    ) -> AuthTokens:
        """
        Complete authentication flow: check existence, sign message, login/register.
        
        This is the main method to use for authentication.

        Args:
            signer: LocalAccount from eth_account
            safe_addresses: Optional Gnosis Safe addresses
            signing_timeout: Timeout for message signing (seconds)

        Returns:
            AuthTokens with access and refresh tokens

        Raises:
            SigningTimeoutError: If signing takes too long
            AuthenticationError: If authentication fails

        Example:
            >>> from eth_account import Account
            >>> account = Account.from_key("0x...")
            >>> auth = SwarmAuth()
            >>> tokens = await auth.verify(account)
            >>> print(f"Token expires at: {tokens.expires_at}")
        """
        address = signer.address
        logger.info(f"Authenticating wallet: {address}")

        # Step 1: Check if wallet is registered
        exists = await self.check_existence(address)
        logger.info(f"Wallet exists: {exists}")

        # Step 2: Get nonce message
        if exists:
            nonce = await self.get_nonce(address)
        else:
            nonce = await self.get_nonce(address, terms="Terms and Conditions")

        # Step 3: Sign message
        try:
            signature = await self._sign_message_async(signer, nonce.message, signing_timeout)
        except asyncio.TimeoutError:
            raise SigningTimeoutError(f"Signing took longer than {signing_timeout} seconds")

        # Step 4: Login or register
        if exists:
            resp = await self.login(address, signature)
            expires_at = datetime.utcnow() + timedelta(seconds=resp.expires_in)
            refresh_expires_at = datetime.utcnow() + timedelta(seconds=resp.refresh_expires_in)
            
            tokens = AuthTokens(
                access_token=resp.access_token,
                refresh_token=resp.refresh_token,
                expires_at=expires_at,
                refresh_expires_at=refresh_expires_at,
                address=address,
            )
        else:
            resp = await self.register(address, signature, safe_addresses)
            expires_at = datetime.utcnow() + timedelta(seconds=resp.expires_in)
            refresh_expires_at = datetime.utcnow() + timedelta(seconds=resp.refresh_expires_in)
            
            tokens = AuthTokens(
                access_token=resp.access_token,
                refresh_token=resp.refresh_token,
                expires_at=expires_at,
                refresh_expires_at=refresh_expires_at,
                address=resp.address or address,
            )

        # Step 5: Store tokens
        self.storage.save(address, tokens)
        logger.info(f"Authentication successful. Token expires at: {tokens.expires_at}")

        return tokens

    def load_tokens(self, address: str) -> Optional[AuthTokens]:
        """
        Load stored tokens for an address.

        Args:
            address: Wallet address

        Returns:
            AuthTokens if found, None otherwise
        """
        return self.storage.load(address)

    def clear_tokens(self, address: str):
        """
        Clear stored tokens for an address.

        Args:
            address: Wallet address
        """
        self.storage.clear(address)

    async def _sign_message_async(
        self,
        signer: LocalAccount,
        message: str,
        timeout: float
    ) -> str:
        """
        Sign message asynchronously with timeout.

        Args:
            signer: LocalAccount to sign with
            message: Message to sign
            timeout: Timeout in seconds

        Returns:
            Signed message (hex with 0x prefix)
        """
        loop = asyncio.get_event_loop()
        
        def sign_sync():
            signature = signer.sign_message(encode_defunct(text=message)).signature.hex()
            # Ensure signature starts with 0x (required by backend)
            if not signature.startswith('0x'):
                signature = '0x' + signature
            return signature
        
        return await asyncio.wait_for(
            loop.run_in_executor(None, sign_sync),
            timeout=timeout
        )

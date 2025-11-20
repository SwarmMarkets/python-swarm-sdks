"""Web3 exceptions for Swarm Collection."""


class Web3Exception(Exception):
    """Base exception for Web3 operations."""
    pass


class InsufficientBalanceException(Web3Exception):
    """Raised when wallet has insufficient token balance."""
    
    def __init__(self, required: float, available: float, token: str):
        self.required = required
        self.available = available
        self.token = token
        self.message = f"Insufficient {token} balance: required {required}, available {available}"
        super().__init__(self.message)


class TransactionFailedException(Web3Exception):
    """Raised when blockchain transaction fails."""
    
    def __init__(self, tx_hash: str = "", reason: str = "Transaction failed"):
        self.tx_hash = tx_hash
        self.message = f"{reason}" + (f" (tx: {tx_hash})" if tx_hash else "")
        super().__init__(self.message)


class InsufficientAllowanceException(Web3Exception):
    """Raised when token allowance is insufficient."""
    
    def __init__(self, required: float, current: float, token: str, spender: str):
        self.required = required
        self.current = current
        self.token = token
        self.spender = spender
        self.message = (
            f"Insufficient allowance for {token}: "
            f"required {required}, current {current} "
            f"(spender: {spender[:10]}...)"
        )
        super().__init__(self.message)


class NetworkNotSupportedException(Web3Exception):
    """Raised when network is not supported."""
    
    def __init__(self, network: str):
        self.network = network
        self.message = f"Network not supported: {network}"
        super().__init__(self.message)

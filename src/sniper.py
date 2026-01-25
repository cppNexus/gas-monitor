"""
Isolated sniper module for automated transactions.
WARNING: Use with caution and only in dry-run mode!
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

from src.config import config
from src.alerting import ConfirmationManager

logger = logging.getLogger(__name__)

# Импорты для web3
try:
    from web3 import AsyncWeb3
    from web3.providers import AsyncHTTPProvider
    from eth_account import Account
    from eth_account.signers.local import LocalAccount
    
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logger.warning("Web3 is not available, the sniper will not work")

@dataclass
class SniperConfig:
    """Sniper configuration"""
    dry_run: bool = True
    max_gas_multiplier: float = 1.2
    require_confirmation: bool = True
    confirmation_ttl: int = 30
    min_profit_gwei: float = 5.0


class TransactionSniper:
    """
    Sniper for automatic transactions at low gas prices.

    WARNING:
    - Always use dry-run mode for testing
    - Never store private keys in the code
    - Use a separate wallet with minimal funds
    """
    
    def __init__(self, network: str):
        self.network = network
        self.config = SniperConfig(
            dry_run=config.sniper.dry_run,
            require_confirmation=config.sniper.require_confirmation
        )
        
        # Web3 клиент
        self.web3: Optional[AsyncWeb3] = None
        
        # Аккаунт
        self.account: Optional[LocalAccount] = None
        
        # Менеджер подтверждений
        self.confirmation_manager = ConfirmationManager(
            ttl_seconds=self.config.confirmation_ttl
        )
        
        # Статистика
        self.stats = {
            "transactions_sent": 0,
            "transactions_failed": 0,
            "last_transaction_time": None,
            "total_gas_saved_gwei": 0.0
        }
    
    async def init(self):
        """Sniper initialization"""
        if not WEB3_AVAILABLE:
            logger.error("Web3 is not installed, sniper cannot be initialized")
            return
        
        try:
            # Инициализация Web3
            network_config = config.networks.get(self.network)
            if not network_config or not network_config.rpc_urls:
                raise ValueError(f"No RPC for network {self.network}")
            
            rpc_url = network_config.rpc_urls[0]
            self.web3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))
            
            # Проверка соединения
            is_connected = await self.web3.is_connected()
            if not is_connected:
                raise ConnectionError(f"Failed to connect to {self.network}")
            
            logger.info(f"Sniper initialized for network {self.network}")
            logger.info(f"Mode: {'DRY-RUN' if self.config.dry_run else 'REAL'}")
            
        except Exception as e:
            logger.error(f"Sniper initialization error: {e}")
            raise
    
    async def cleanup(self):
        """Resource cleaning"""
        await self.confirmation_manager.cleanup()
    
    async def check_opportunity(self, 
                               current_gas_price: float,
                               target_gas_price: float) -> Tuple[bool, float]:
        """
        Checking the feasibility of a transaction.

        Returns (is_feasible, savings_in_Gwei)
        """
        if current_gas_price > target_gas_price:
            return False, 0.0
        
        # Рассчитываем экономию
        savings = target_gas_price - current_gas_price
        
        # Проверяем минимальную прибыль
        if savings < self.config.min_profit_gwei:
            return False, savings
        
        return True, savings
    
    async def get_stats(self) -> Dict:
        """Getting sniper statistics"""
        return {
            **self.stats,
            "network": self.network,
            "dry_run": self.config.dry_run,
            "account_set": self.account is not None,
            "web3_available": WEB3_AVAILABLE
        }


# Глобальный инстанс снайпера (опционально)
_sniper_instance: Optional[TransactionSniper] = None

async def get_sniper(network: str = "ethereum") -> TransactionSniper:
    """Obtaining a global sniper instance"""
    global _sniper_instance
    
    if _sniper_instance is None or _sniper_instance.network != network:
        _sniper_instance = TransactionSniper(network)
        await _sniper_instance.init()
    
    return _sniper_instance

async def cleanup_sniper():
    """Clearing the global sniper instance"""
    global _sniper_instance
    
    if _sniper_instance:
        await _sniper_instance.cleanup()
        _sniper_instance = None
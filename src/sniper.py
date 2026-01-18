"""
Изолированный модуль снайпера для автоматических транзакций.
ВНИМАНИЕ: Использовать с осторожностью, только с dry-run режимом!
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
    logger.warning("Web3 не доступен, снайпер работать не будет")


@dataclass
class SniperConfig:
    """Конфигурация снайпера"""
    dry_run: bool = True
    max_gas_multiplier: float = 1.2
    require_confirmation: bool = True
    confirmation_ttl: int = 30
    min_profit_gwei: float = 5.0


class TransactionSniper:
    """
    Снайпер для автоматических транзакций при низких ценах газа.
    
    ВНИМАНИЕ:
    - Всегда используйте dry-run режим для тестирования
    - Никогда не храните приватные ключи в коде
    - Используйте отдельный кошелек с минимальными средствами
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
        """Инициализация снайпера"""
        if not WEB3_AVAILABLE:
            logger.error("Web3 не установлен, снайпер не может быть инициализирован")
            return
        
        try:
            # Инициализация Web3
            network_config = config.networks.get(self.network)
            if not network_config or not network_config.rpc_urls:
                raise ValueError(f"Нет RPC для сети {self.network}")
            
            rpc_url = network_config.rpc_urls[0]
            self.web3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))
            
            # Проверка соединения
            is_connected = await self.web3.is_connected()
            if not is_connected:
                raise ConnectionError(f"Не удалось подключиться к {self.network}")
            
            logger.info(f"Снайпер инициализирован для сети {self.network}")
            logger.info(f"Режим: {'DRY-RUN' if self.config.dry_run else 'REAL'}")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации снайпера: {e}")
            raise
    
    async def cleanup(self):
        """Очистка ресурсов"""
        await self.confirmation_manager.cleanup()
    
    async def check_opportunity(self, 
                               current_gas_price: float,
                               target_gas_price: float) -> Tuple[bool, float]:
        """
        Проверка возможности для транзакции.
        
        Возвращает (есть_возможность, экономия_в_Gwei)
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
        """Получение статистики снайпера"""
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
    """Получение глобального инстанса снайпера"""
    global _sniper_instance
    
    if _sniper_instance is None or _sniper_instance.network != network:
        _sniper_instance = TransactionSniper(network)
        await _sniper_instance.init()
    
    return _sniper_instance

async def cleanup_sniper():
    """Очистка глобального инстанса снайпера"""
    global _sniper_instance
    
    if _sniper_instance:
        await _sniper_instance.cleanup()
        _sniper_instance = None
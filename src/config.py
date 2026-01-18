"""
Главный конфигурационный файл Gas Monitor.
Все настройки в одном месте с приоритетом: переменные окружения → значения по умолчанию.
Протестировано и готово к продакшену.
"""

import os
import sys
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def get_env_bool(key: str, default: bool = False) -> bool:
    """Получение булевой переменной из окружения"""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 't', 'y')

def get_env_int(key: str, default: int) -> int:
    """Получение целочисленной переменной из окружения"""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default

def get_env_float(key: str, default: float) -> float:
    """Получение дробной переменной из окружения"""
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default

def get_env_list(key: str, default: List[str]) -> List[str]:
    """Получение списка из переменной окружения"""
    value = os.getenv(key, '')
    if not value:
        return default
    return [item.strip() for item in value.split(',') if item.strip()]

# ============================================================================
# КЛАССЫ КОНФИГУРАЦИИ
# ============================================================================

@dataclass
class NetworkConfig:
    """Конфигурация сети"""
    name: str
    chain_id: int
    native_token: str
    is_l2: bool
    supports_eip1559: bool
    block_time: int
    explorer_url: str
    
    # RPC endpoints
    rpc_urls: List[str] = field(default_factory=list)
    
    # Пороги газа в Gwei
    gas_thresholds: Dict[str, float] = field(default_factory=dict)
    
    # Отключить fast алерты для L2
    disable_fast_alerts: bool = False

@dataclass
class TelegramConfig:
    """Конфигурация Telegram бота"""
    bot_token: str
    chat_id: str
    parse_mode: str = "HTML"
    enable_photo_upload: bool = True
    message_timeout: int = 10
    
    def is_configured(self) -> bool:
        """Проверка, настроен ли Telegram"""
        return bool(self.bot_token and self.chat_id)

@dataclass
class SniperConfig:
    """Конфигурация снайпера"""
    enabled: bool = False
    dry_run: bool = True
    require_confirmation: bool = True
    confirmation_ttl: int = 30
    max_gas_multiplier: float = 1.2
    min_profit_gwei: float = 5.0
    private_key: Optional[str] = None
    
    def is_safe(self) -> bool:
        """Проверка безопасности конфигурации снайпера"""
        if not self.enabled:
            return True
        return self.dry_run and not self.private_key

@dataclass
class LoggingConfig:
    """Конфигурация логирования"""
    level: str
    file_path: str
    max_size_mb: int
    backup_count: int
    console_output: bool
    
    @property
    def max_bytes(self) -> int:
        return self.max_size_mb * 1024 * 1024

# ============================================================================
# ГЛАВНЫЙ КЛАСС КОНФИГУРАЦИИ
# ============================================================================

class Config:
    """Главный класс конфигурации приложения"""
    
    def __init__(self):
        # Валидация Python версии
        self._validate_python_version()
        
        # Секции конфигурации
        self.networks = self._configure_networks()
        self.telegram = self._configure_telegram()
        self.sniper = self._configure_sniper()
        self.logging = self._configure_logging()
        self.monitoring = self._configure_monitoring()
        self.charts = self._configure_charts()
        self.l2_settings = self._configure_l2_settings()
        
        # Загрузка RPC endpoints
        self._load_rpc_endpoints()
        
        # Валидация
        self._validate_config()
        
        # Shortcuts для обратной совместимости
        self.telegram_bot_token = self.telegram.bot_token
        self.telegram_chat_id = self.telegram.chat_id
        self.telegram_parse_mode = self.telegram.parse_mode
        self.log_level = self.logging.level
        self.log_file = self.logging.file_path
        self.max_chart_files = self.charts["max_chart_files"]
    
    def _validate_python_version(self):
        """Проверка версии Python"""
        if sys.version_info < (3, 9):
            print("❌ Требуется Python 3.9 или выше")
            sys.exit(1)
    
    def _validate_config(self):
        """Валидация всей конфигурации"""
        errors = []
        
        # Проверка Telegram
        if not self.telegram.is_configured():
            errors.append("Telegram bot не настроен. Укажите TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID")
        
        # Проверка RPC endpoints
        for network_name, cfg in self.networks.items():
            if not cfg.rpc_urls:
                errors.append(f"Нет RPC endpoints для сети {network_name}")
        
        # Проверка снайпера
        if not self.sniper.is_safe():
            errors.append("Снайпер настроен небезопасно! Всегда используйте dry_run=true")
        
        if errors:
            print("❌ Ошибки конфигурации:")
            for error in errors:
                print(f"  - {error}")
            print("\n📝 Исправьте ошибки и перезапустите приложение")
            sys.exit(1)
    
    def _configure_networks(self) -> Dict[str, NetworkConfig]:
        """Конфигурация всех поддерживаемых сетей"""
        networks = {}
        
        # Ethereum Mainnet
        networks["ethereum"] = NetworkConfig(
            name="Ethereum",
            chain_id=1,
            native_token="ETH",
            is_l2=False,
            supports_eip1559=True,
            block_time=12,
            explorer_url="https://etherscan.io",
            gas_thresholds={
                "ultra_low": 15,
                "low": 20,
                "medium": 35,
                "high": 50,
                "ultra_high": 100
            }
        )
        
        # Arbitrum One
        networks["arbitrum"] = NetworkConfig(
            name="Arbitrum One",
            chain_id=42161,
            native_token="ETH",
            is_l2=True,
            supports_eip1559=True,
            block_time=0,
            explorer_url="https://arbiscan.io",
            gas_thresholds={
                "low": 0.1,
                "medium": 0.3,
                "high": 1.0
            },
            disable_fast_alerts=True
        )
        
        # Optimism
        networks["optimism"] = NetworkConfig(
            name="Optimism",
            chain_id=10,
            native_token="ETH",
            is_l2=True,
            supports_eip1559=True,
            block_time=2,
            explorer_url="https://optimistic.etherscan.io",
            gas_thresholds={
                "low": 0.1,
                "medium": 0.3,
                "high": 1.0
            },
            disable_fast_alerts=True
        )
        
        # Base
        networks["base"] = NetworkConfig(
            name="Base",
            chain_id=8453,
            native_token="ETH",
            is_l2=True,
            supports_eip1559=True,
            block_time=2,
            explorer_url="https://basescan.org",
            gas_thresholds={
                "low": 0.1,
                "medium": 0.3,
                "high": 1.0
            },
            disable_fast_alerts=True
        )
        
        # Polygon PoS
        networks["polygon"] = NetworkConfig(
            name="Polygon PoS",
            chain_id=137,
            native_token="MATIC",
            is_l2=False,
            supports_eip1559=True,
            block_time=2,
            explorer_url="https://polygonscan.com",
            gas_thresholds={
                "low": 30,
                "medium": 60,
                "high": 100
            }
        )
        
        return networks
    
    def _load_rpc_endpoints(self):
        """Загрузка RPC endpoints из переменных окружения"""
        # Маппинг сетей на переменные окружения
        env_mapping = {
            "ethereum": ["ETHEREUM", "ETH"],
            "arbitrum": ["ARBITRUM", "ARB"],
            "optimism": ["OPTIMISM", "OP"],
            "base": ["BASE"],
            "polygon": ["POLYGON", "MATIC"]
        }
        
        for network_name, cfg in self.networks.items():
            rpc_urls = []
            
            # Пробуем найти переменные окружения
            for prefix in env_mapping.get(network_name, [network_name.upper()]):
                # Ищем RPC, RPC_1, RPC_2, RPC_3 и т.д.
                for suffix in ["_RPC", "_RPC_1", "_RPC_2", "_RPC_3"]:
                    env_var = f"{prefix}{suffix}"
                    value = os.getenv(env_var)
                    if value and value not in rpc_urls:  # Избегаем дубликатов
                        rpc_urls.append(value)
                
                # Также проверяем без суффикса
                value = os.getenv(f"{prefix}_RPC")
                if value and value not in rpc_urls:
                    rpc_urls.append(value)
            
            # Если не нашли, используем публичные RPC
            if not rpc_urls:
                rpc_urls = self._get_public_rpc_endpoints(network_name)
            
            cfg.rpc_urls = rpc_urls
    
    def _get_public_rpc_endpoints(self, network: str) -> List[str]:
        """Получение публичных RPC endpoints"""
        public_rpcs = {
            "ethereum": [
                "https://rpc.ankr.com/eth",
                "https://eth.llamarpc.com",
                "https://eth-mainnet.public.blastapi.io",
                "https://ethereum.publicnode.com"
            ],
            "arbitrum": [
                "https://rpc.ankr.com/arbitrum",
                "https://arbitrum.llamarpc.com",
                "https://arbitrum.publicnode.com",
                "https://arb1.arbitrum.io/rpc"
            ],
            "optimism": [
                "https://rpc.ankr.com/optimism",
                "https://optimism.llamarpc.com",
                "https://optimism.publicnode.com",
                "https://mainnet.optimism.io"
            ],
            "base": [
                "https://rpc.ankr.com/base",
                "https://base.llamarpc.com",
                "https://base.publicnode.com",
                "https://mainnet.base.org"
            ],
            "polygon": [
                "https://rpc.ankr.com/polygon",
                "https://polygon.llamarpc.com",
                "https://polygon-bor.publicnode.com"
            ]
        }
        
        return public_rpcs.get(network, [])
    
    def _configure_telegram(self) -> TelegramConfig:
        """Конфигурация Telegram"""
        return TelegramConfig(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
            parse_mode=os.getenv("TELEGRAM_PARSE_MODE", "HTML"),
            enable_photo_upload=get_env_bool("TELEGRAM_ENABLE_PHOTOS", True),
            message_timeout=get_env_int("TELEGRAM_TIMEOUT", 10)
        )
    
    def _configure_sniper(self) -> SniperConfig:
        """Конфигурация снайпера"""
        return SniperConfig(
            enabled=get_env_bool("ENABLE_SNIPER", False),
            dry_run=get_env_bool("SNIPER_DRY_RUN", True),
            require_confirmation=get_env_bool("SNIPER_REQUIRE_CONFIRMATION", True),
            confirmation_ttl=get_env_int("SNIPER_CONFIRMATION_TTL", 30),
            max_gas_multiplier=get_env_float("SNIPER_MAX_GAS_MULTIPLIER", 1.2),
            min_profit_gwei=get_env_float("SNIPER_MIN_PROFIT_GWEI", 5.0),
            private_key=os.getenv("SNIPER_PRIVATE_KEY")
        )
    
    def _configure_logging(self) -> LoggingConfig:
        """Конфигурация логирования"""
        return LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO").upper(),
            file_path=os.getenv("LOG_FILE", "logs/gas_monitor.log"),
            max_size_mb=get_env_int("LOG_MAX_SIZE_MB", 10),
            backup_count=get_env_int("LOG_BACKUP_COUNT", 5),
            console_output=get_env_bool("LOG_CONSOLE", True)
        )
    
    def _configure_monitoring(self) -> Dict[str, Any]:
        """Конфигурация параметров мониторинга"""
        return {
            "check_interval": get_env_int("CHECK_INTERVAL", 12),
            "alert_cooldown": get_env_int("ALERT_COOLDOWN", 300),
            "fee_history_blocks": get_env_int("FEE_HISTORY_BLOCKS", 16),
            "percentiles": [10, 25, 50, 75, 90],
            "max_history_hours": get_env_int("MAX_HISTORY_HOURS", 24),
            "smoothing_window": get_env_int("SMOOTHING_WINDOW", 5),
            "save_history_interval": get_env_int("SAVE_HISTORY_INTERVAL", 300),
            "enable_network_stats": get_env_bool("ENABLE_NETWORK_STATS", True)
        }
    
    def _configure_charts(self) -> Dict[str, Any]:
        """Конфигурация генерации графиков"""
        return {
            "enabled": get_env_bool("ENABLE_CHARTS", True),
            "update_interval": get_env_int("CHART_UPDATE_INTERVAL", 3600),
            "max_chart_files": get_env_int("MAX_CHART_FILES", 5),
            "chart_width": get_env_int("CHART_WIDTH", 14),
            "chart_height": get_env_int("CHART_HEIGHT", 8),
            "chart_dpi": get_env_int("CHART_DPI", 150),
            "chart_format": os.getenv("CHART_FORMAT", "png"),
            "chart_directory": os.getenv("CHART_DIRECTORY", "charts")
        }
    
    def _configure_l2_settings(self) -> Dict[str, Any]:
        """Конфигурация специфичных для L2 настроек"""
        return {
            "include_l1_fee": {
                "arbitrum": get_env_bool("ARBITRUM_INCLUDE_L1_FEE", False),
                "optimism": get_env_bool("OPTIMISM_INCLUDE_L1_FEE", False),
                "base": get_env_bool("BASE_INCLUDE_L1_FEE", False)
            },
            "l1_fee_cache_ttl": get_env_int("L1_FEE_CACHE_TTL", 30),
            "l1_gas_price_fallback": get_env_float("L1_GAS_PRICE_FALLBACK", 20.0),
            "l2_gas_price_fallback": get_env_float("L2_GAS_PRICE_FALLBACK", 0.02)
        }
    
    def print_summary(self):
        """Вывод сводки конфигурации"""
        print("=" * 70)
        print("GAS MONITOR - КОНФИГУРАЦИЯ")
        print("=" * 70)
        
        print(f"Сети ({len(self.networks)}): {', '.join(self.networks.keys())}")
        
        telegram_status = "Настроен" if self.telegram.is_configured() else "❌ Не настроен"
        print(f"Telegram: {telegram_status}")
        
        print(f"Интервал проверки: {self.monitoring['check_interval']} сек")
        print(f"Задержка алертов: {self.monitoring['alert_cooldown']} сек")
        
        charts_status = "Включены" if self.charts["enabled"] else "Выключены"
        print(f"📊 Графики: {charts_status}")
        
        if self.sniper.enabled:
            mode = "сухой режим" if self.sniper.dry_run else "РЕАЛЬНЫЙ РЕЖИМ"
            print(f"Снайпер: Включен ({mode})")
        else:
            print(f"Снайпер: Выключен")
        
        l2_networks = [n for n in self.networks if self.networks[n].is_l2]
        if l2_networks:
            l2_with_fee = [n for n in l2_networks 
                          if self.l2_settings["include_l1_fee"].get(n, False)]
            print(f"L2 с L1 комиссией: {', '.join(l2_with_fee) if l2_with_fee else 'нет'}")
        
        print("=" * 70)
        
        print("\n🔗 RPC Endpoints:")
        for network_name in self.networks:
            cfg = self.networks[network_name]
            print(f"  {cfg.name}:")
            for i, url in enumerate(cfg.rpc_urls[:2], 1):
                print(f"    {i}. {url}")
            if len(cfg.rpc_urls) > 2:
                print(f"    ... и еще {len(cfg.rpc_urls) - 2}")
        
        print("=" * 70)

# ============================================================================
# ГЛОБАЛЬНЫЙ ИНСТАНС КОНФИГУРАЦИИ
# ============================================================================

try:
    config = Config()
    print("Конфигурация успешно загружена")
except Exception as e:
    print(f"Ошибка загрузки конфигурации: {e}")
    sys.exit(1)

# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    # Выводим сводку конфигурации
    config.print_summary()
    
    # Создаем необходимые директории
    os.makedirs('logs', exist_ok=True)
    os.makedirs('charts', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    print("\nКонфигурация готова. Запустите: python main.py")
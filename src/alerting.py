"""
Модуль для отправки алертов через Telegram.
Управляет форматом сообщений и подтверждениями.
"""

import asyncio
import time
import hashlib
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import logging

import aiohttp

from src.config import config

logger = logging.getLogger(__name__)

@dataclass
class Alert:
    """Данные алерта"""
    network: str
    alert_type: str
    value: float
    threshold: float
    base_fee: float
    percentile: str
    block_number: int
    timestamp: float
    
    @property
    def priority_fee(self) -> float:
        """Приоритетная комиссия"""
        return self.value - self.base_fee
    
    @property
    def alert_name(self) -> str:
        """Название алерта"""
        return self.alert_type.replace("_", " ").title()

class AlertManager:
    """Менеджер алертов"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.message_formatter = MessageFormatter()
        
    async def init_session(self):
        """Инициализация HTTP сессии"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
    
    async def cleanup(self):
        """Очистка ресурсов"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def send_alert(self, **kwargs) -> bool:
        """Отправка алерта"""
        try:
            # Создаем объект алерта
            alert = Alert(**kwargs, timestamp=time.time())
            
            # Форматируем сообщение
            message = self.message_formatter.format_alert(alert)
            
            # Отправляем в Telegram
            success = await self._send_telegram_message(message)
            
            if success:
                logger.info(f"Алерт отправлен: {alert.network} {alert.alert_type}")
            else:
                logger.warning(f"Не удалось отправить алерт: {alert.network}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка отправки алерта: {e}")
            return False
    
    async def _send_telegram_message(self, message: str) -> bool:
        """Отправка сообщения в Telegram"""
        if not config.telegram_bot_token or not config.telegram_chat_id:
            logger.error("Не настроен Telegram бот")
            return False
        
        await self.init_session()
        
        try:
            url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
            
            payload = {
                "chat_id": config.telegram_chat_id,
                "text": message,
                "parse_mode": config.telegram_parse_mode,
                "disable_web_page_preview": True
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Telegram API error: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
            return False

class MessageFormatter:
    """Форматирование сообщений для Telegram"""
    
    # Emoji для разных типов алертов
    EMOJI_MAP = {
        "ultra_low": "🚀",
        "low": "✅",
        "medium": "⚠️",
        "high": "🔥",
        "ultra_high": "💥"
    }
    
    # Рекомендации
    RECOMMENDATIONS = {
        "ultra_low": "Отличное время для транзакций!",
        "low": "Хорошее время для транзакций",
        "medium": "Умеренная комиссия, можно подождать",
        "high": "Высокая комиссия, избегайте если возможно",
        "ultra_high": "Очень высокая комиссия, подождите"
    }
    
    def format_alert(self, alert: Alert) -> str:
        """Форматирование алерта"""
        emoji = self.EMOJI_MAP.get(alert.alert_type, "⛽")
        recommendation = self.RECOMMENDATIONS.get(alert.alert_type, "")
        
        # Получаем конфигурацию сети
        network_config = config.networks.get(alert.network)
        network_name = network_config.name if network_config else alert.network
        
        # Форматируем сообщение
        message = (
            f"{emoji} <b>GAS ALERT: {network_name}</b>\n"
            f"Type: {alert.alert_name}\n"
            f"Current: {alert.value:.2f} Gwei\n"
            f"Base: {alert.base_fee:.2f} Gwei\n"
            f"Priority: {alert.priority_fee:.2f} Gwei\n"
            f"Threshold: {alert.threshold} Gwei\n"
            f"Percentile: {alert.percentile}\n"
            f"Block: #{alert.block_number}\n"
            f"Time: {datetime.now().strftime('%H:%M:%S')}\n"
        )
        
        # Добавляем рекомендацию
        if recommendation:
            message += f"\n💡 <i>{recommendation}</i>"
        
        # Добавляем ссылку на explorer
        if network_config and network_config.explorer_url:
            explorer_name = network_config.explorer_url.split('//')[1].split('.')[0].title()
            message += f"\n🔗 {explorer_name}: {network_config.explorer_url}/block/{alert.block_number}"
        
        return message

class ConfirmationManager:
    """Менеджер подтверждений для снайпера"""
    
    def __init__(self, ttl_seconds: int = 30):
        self.ttl = ttl_seconds
        self.pending_confirmations: Dict[str, Dict] = {}
        self.locks: Dict[str, asyncio.Lock] = {}
    
    async def create_confirmation(self, tx_data: Dict, network: str) -> Tuple[str, float]:
        """Создание запроса на подтверждение"""
        # Генерируем уникальный ID
        tx_id = hashlib.sha256(
            f"{network}{tx_data}{time.time()}".encode()
        ).hexdigest()[:16]
        
        full_id = f"{network}_{tx_id}"
        
        # Сохраняем запрос
        self.pending_confirmations[full_id] = {
            "id": full_id,
            "network": network,
            "tx_data": tx_data,
            "created_at": time.time(),
            "expires_at": time.time() + self.ttl
        }
        
        # Создаем lock
        self.locks[full_id] = asyncio.Lock()
        
        # Запускаем таймер истечения
        asyncio.create_task(self._expire_confirmation(full_id))
        
        return full_id, self.ttl
    
    async def confirm(self, confirmation_id: str) -> Optional[Dict]:
        """Подтверждение запроса"""
        if confirmation_id not in self.locks:
            return None
        
        async with self.locks[confirmation_id]:
            if confirmation_id not in self.pending_confirmations:
                return None
            
            request = self.pending_confirmations[confirmation_id]
            
            # Проверяем не истек ли
            if time.time() > request["expires_at"]:
                del self.pending_confirmations[confirmation_id]
                del self.locks[confirmation_id]
                return None
            
            # Удаляем запрос
            del self.pending_confirmations[confirmation_id]
            del self.locks[confirmation_id]
            
            return request
    
    async def _expire_confirmation(self, confirmation_id: str):
        """Фоновая задача для истечения запроса"""
        await asyncio.sleep(self.ttl)
        
        if confirmation_id in self.pending_confirmations:
            async with self.locks.get(confirmation_id, asyncio.Lock()):
                if confirmation_id in self.pending_confirmations:
                    del self.pending_confirmations[confirmation_id]
                    del self.locks[confirmation_id]
                    logger.debug(f"Confirmation expired: {confirmation_id}")
    
    async def cleanup(self):
        """Очистка истекших запросов"""
        now = time.time()
        expired = []
        
        for conf_id, request in self.pending_confirmations.items():
            if now > request["expires_at"]:
                expired.append(conf_id)
        
        for conf_id in expired:
            async with self.locks.get(conf_id, asyncio.Lock()):
                if conf_id in self.pending_confirmations:
                    del self.pending_confirmations[conf_id]
                if conf_id in self.locks:
                    del self.locks[conf_id]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired confirmations")
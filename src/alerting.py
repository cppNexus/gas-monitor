"""
A module for sending alerts via Telegram.
Manages message formats and confirmations.
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
    """Alert data"""
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
        """Priority Commission"""
        return self.value - self.base_fee
    
    @property
    def alert_name(self) -> str:
        """Alert name"""
        return self.alert_type.replace("_", " ").title()

class AlertManager:
    """Alert Manager"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.message_formatter = MessageFormatter()
        
    async def init_session(self):
        """Initializing an HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
    
    async def cleanup(self):
        """Resource cleaning"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def send_alert(self, **kwargs) -> bool:
        """Sending an alert"""
        try:
            if not config.telegram.enabled:
                logger.info("Alerts disabled; skipping send")
                return True

            # Создаем объект алерта
            alert = Alert(**kwargs, timestamp=time.time())
            
            # Форматируем сообщение
            message = self.message_formatter.format_alert(alert)
            
            # Отправляем в Telegram
            success = await self._send_telegram_message(message)
            
            if success:
                logger.info(f"Alert sent: {alert.network} {alert.alert_type}")
            else:
                logger.warning(f"Failed to send alert: {alert.network}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return False

    async def send_consolidated_alerts(self, alerts_data: list) -> bool:
        """Sending multiple alerts in a single message"""
        try:
            if not alerts_data:
                return True

            if not config.telegram.enabled:
                logger.info("Alerts disabled; skipping send")
                return True

            alerts = [Alert(**data, timestamp=time.time()) for data in alerts_data]
            message = self.message_formatter.format_alerts(alerts)
            if not message:
                return False

            success = await self._send_telegram_message(message)
            if success:
                logger.info("Consolidated alert sent")
            else:
                logger.warning("Failed to send consolidated alert")

            return success
        except Exception as e:
            logger.error(f"Error sending consolidated alerts: {e}")
            return False
    
    async def _send_telegram_message(self, message: str) -> bool:
        """Sending a message in Telegram"""
        if not config.telegram.enabled:
            return False
        if not config.telegram_bot_token or not config.telegram_chat_id:
            logger.error("The Telegram bot is not configured.")
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
            logger.error(f"Error sending to Telegram: {e}")
            return False

class MessageFormatter:
    """Formatting messages for Telegram"""
    
    # Emoji для разных типов алертов
    EMOJI_MAP = {
        "ultra_low": "💥",
        "low": "✅",
        "medium": "⚠️",
        "high": "🔥",
        "ultra_high": "🚀"
    }
    
    # Рекомендации
    RECOMMENDATIONS = {
        "ultra_low": "Great time for transactions!",
        "low": "Good time for transactions",
        "medium": "Moderate fees, you can wait",
        "high": "High fees, avoid if possible",
        "ultra_high": "Very high fees, please wait"
    }
    
    def format_alert(self, alert: Alert) -> str:
        """Alert formatting"""
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
            message += f"\n<i>{recommendation}</i>"
        
        # Добавляем ссылку на explorer
        if network_config and network_config.explorer_url:
            explorer_name = network_config.explorer_url.split('//')[1].split('.')[0].title()
            message += f"\n🔗 {explorer_name}: {network_config.explorer_url}/block/{alert.block_number}"
        
        return message

    def format_alerts(self, alerts: list) -> str:
        """Formatting a consolidated alert message"""
        if not alerts:
            return ""

        network_names = {config.networks.get(a.network).name if config.networks.get(a.network) else a.network for a in alerts}
        network_label = network_names.pop() if len(network_names) == 1 else "Multiple Networks"

        block_numbers = {a.block_number for a in alerts}
        block_number = block_numbers.pop() if len(block_numbers) == 1 else None
        block_line = f"Block: #{block_number}\n" if block_number is not None else ""

        header = (
            f"⛽ <b>GAS ALERTS: {network_label}</b>\n"
            f"{block_line}"
            f"Time: {datetime.now().strftime('%H:%M:%S')}\n"
        )

        lines = []
        for alert in alerts:
            emoji = self.EMOJI_MAP.get(alert.alert_type, "⛽")
            recommendation = self.RECOMMENDATIONS.get(alert.alert_type, "")
            line = (
                f"{emoji} <b>{alert.alert_name}</b>: "
                f"{alert.value:.2f} Gwei "
                f"(threshold {alert.threshold}, base {alert.base_fee:.2f}, "
                f"priority {alert.priority_fee:.2f}, {alert.percentile})"
            )
            lines.append(line)
            if recommendation:
                lines.append(f"<i>{recommendation}</i>")

        message = header + "\n" + "\n".join(lines)

        network_config = config.networks.get(alerts[0].network)
        if network_config and network_config.explorer_url and block_number is not None:
            explorer_name = network_config.explorer_url.split('//')[1].split('.')[0].title()
            message += f"\n\n🔗 {explorer_name}: {network_config.explorer_url}/block/{block_number}"

        return message

class ConfirmationManager:
    """Confirmation Manager for Sniper"""
    
    def __init__(self, ttl_seconds: int = 30):
        self.ttl = ttl_seconds
        self.pending_confirmations: Dict[str, Dict] = {}
        self.locks: Dict[str, asyncio.Lock] = {}
    
    async def create_confirmation(self, tx_data: Dict, network: str) -> Tuple[str, float]:
        """Creating a confirmation request"""
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
        """Confirm request"""
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
        """Background task for request expiration"""
        await asyncio.sleep(self.ttl)
        
        if confirmation_id in self.pending_confirmations:
            async with self.locks.get(confirmation_id, asyncio.Lock()):
                if confirmation_id in self.pending_confirmations:
                    del self.pending_confirmations[confirmation_id]
                    del self.locks[confirmation_id]
                    logger.debug(f"Confirmation expired: {confirmation_id}")
    
    async def cleanup(self):
        """Clearing expired requests"""
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

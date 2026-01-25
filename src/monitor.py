"""
The main gas monitoring module.
Collects data from all networks and manages alerts.
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

import aiohttp
from statistics import median

from src.config import config
from src.alerting import AlertManager
from src.l2_calculator import get_l2_calculator
from src.charts import ChartGenerator
from src.models import GasData

logger = logging.getLogger(__name__)

class GasMonitor:
    """Main monitoring class"""
    
    def __init__(self, 
                 alert_manager: AlertManager,
                 chart_generator: ChartGenerator):
        self.alert_manager = alert_manager
        self.l2_calculator = None  # Initialized asynchronously
        self.chart_generator = chart_generator
        
        # Data history
        self.history: Dict[str, List[GasData]] = {}
        self.last_alert_times: Dict[str, float] = {}
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Control flags
        self.is_running = False
        self.iteration = 0
        
        # Initializing history
        for network in config.networks:
            self.history[network] = []
    
    async def init_session(self):
        """Initializing an HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(limit=20)
            )
            logger.debug("HTTP session initialized")
        
        # Инициализируем L2 калькулятор
        if not self.l2_calculator:
            self.l2_calculator = await get_l2_calculator()
            logger.debug("L2 calculator initialized")
    
    async def stop(self):
        """Stop monitoring"""
        self.is_running = False
        
        if self.session:
            await self.session.close()
            self.session = None
            logger.debug("HTTP session closed")
    
    async def _rpc_call(self, 
                       rpc_url: str, 
                       method: str, 
                       params: list,
                       network: str = "unknown") -> Optional[Any]:
        """Asynchronous RPC call with retries"""
        if not self.session:
            await self.init_session()
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        for attempt in range(3):
            try:
                async with self.session.post(rpc_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "error" in data:
                            logger.error(f"RPC error ({network}): {data['error']}")
                            continue
                        return data.get("result")
                    else:
                        logger.warning(f"HTTP {response.status} ({network}), attempt {attempt+1}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Network error ({network}), attempt {attempt+1}: {type(e).__name__}")
            
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _hex_to_gwei(self, hex_value: str) -> float:
        """Convert hex to Gwei"""
        try:
            return int(hex_value, 16) / 1e9
        except (ValueError, TypeError):
            return 0.0
    
    async def _get_gas_data_for_network(self, network_name: str) -> Optional[GasData]:
        """Obtaining gas data for a specific network"""
        """Getting gaze data for a specific network"""
        network_config = config.networks[network_name]
        
        # We try all RPC endpoints
        for rpc_url in network_config.rpc_urls:
            if not rpc_url:
                continue
            
            # We obtain data via eth_feeHistory
            result = await self._rpc_call(
                rpc_url,
                "eth_feeHistory",
                ["0x10", "latest", [10, 25, 50, 75, 90]],  # 16 блоков, 5 процентилей
                network_name
            )
            
            if not result:
                continue
            
            try:
                # Базовые данные
                base_fees = [self._hex_to_gwei(b) for b in result["baseFeePerGas"]]
                current_base = median(base_fees[-5:])  # Медиана последних 5 блоков
                
                # Приоритетные комиссии
                priority_fees = {}
                total_fees = {}
                
                # Берем последний блок для reward
                last_rewards = result["reward"][-1]
                
                # Маппинг процентилей
                percentiles = ["p10", "p25", "p50", "p75", "p90"]
                
                for i, percentile in enumerate(percentiles):
                    if i < len(last_rewards):
                        priority = self._hex_to_gwei(last_rewards[i])
                        priority_fees[percentile] = priority
                        total_fees[percentile] = current_base + priority
                
                # Получаем номер блока
                block_number = int(result["oldestBlock"], 16) + len(result["reward"])
                
                # Создаем объект данных
                gas_data = GasData(
                    network=network_name,
                    timestamp=time.time(),
                    block_number=block_number,
                    base_fee=current_base,
                    priority_fees=priority_fees,
                    total_fees=total_fees
                )
                
                return gas_data
                
            except (KeyError, IndexError, ValueError) as e:
                logger.error(f"Parsing error ({network_name}): {e}")
                continue
        
        return None
    
    def _update_history(self, gas_data: GasData):
        """Updating data history"""
        network = gas_data.network
        self.history[network].append(gas_data)
        
        # Удаляем старые данные
        cutoff_time = time.time() - (config.monitoring["max_history_hours"] * 3600)
        self.history[network] = [
            d for d in self.history[network] 
            if d.timestamp > cutoff_time
        ]
        
        # Ограничиваем размер истории
        max_history = config.monitoring["max_history_hours"] * 3600 // config.monitoring["check_interval"]
        if len(self.history[network]) > max_history:
            self.history[network] = self.history[network][-max_history:]
    
    async def _process_network(self, network_name: str) -> Optional[GasData]:
        """Processing one network"""
        try:
            # Получаем данные
            gas_data = await self._get_gas_data_for_network(network_name)
            if not gas_data:
                logger.warning(f"Failed to retrieve data for {network_name}")
                return None
            
            # Обновляем историю
            self._update_history(gas_data)
            
            # Логируем
            self._log_gas_data(gas_data)
            
            # Проверяем алерты
            await self._check_alerts(gas_data)
            
            return gas_data
            
        except Exception as e:
            logger.error(f"Network processing error {network_name}: {e}")
            return None
    
    def _log_gas_data(self, gas_data: GasData):
        """Logging gas data"""
        network_config = config.networks[gas_data.network]
        
        # Форматируем строку
        log_line = (
            f"{network_config.name:12} | "
            f"Base: {gas_data.base_fee:6.2f} | "
            f"Safe: {gas_data.get_fee_for_percentile('p25') or 0:6.2f} | "
            f"Fast: {gas_data.get_fee_for_percentile('p75') or 0:6.2f} Gwei"
        )
        
        logger.info(log_line)
    
    async def _check_alerts(self, gas_data: GasData):
        """Checking triggers for alerts"""
        network_config = config.networks[gas_data.network]
        thresholds = network_config.gas_thresholds
        
        # Маппинг процентилей на типы алертов
        percentile_mapping = {
            "p10": "ultra_low",
            "p25": "low",
            "p50": "medium",
            "p75": "high",
            "p90": "ultra_high"
        }
        
        now = time.time()
        
        for percentile, alert_type in percentile_mapping.items():
            # Пропускаем если для этого типа нет порога
            if alert_type not in thresholds:
                continue
            
            # Для L2 сетей пропускаем fast алерты если отключены
            if network_config.disable_fast_alerts and alert_type in ["high", "ultra_high"]:
                continue
            
            # Получаем значение
            value = gas_data.get_fee_for_percentile(percentile)
            if value is None:
                continue
            
            threshold = thresholds[alert_type]
            
            # Проверяем условие (ниже порога)
            if value <= threshold:
                key = f"{gas_data.network}_{alert_type}"
                
                # Проверяем cooldown
                if now - self.last_alert_times.get(key, 0) > config.monitoring["alert_cooldown"]:
                    # Отправляем алерт
                    await self.alert_manager.send_alert(
                        network=gas_data.network,
                        alert_type=alert_type,
                        value=value,
                        threshold=threshold,
                        base_fee=gas_data.base_fee,
                        percentile=percentile,
                        block_number=gas_data.block_number
                    )
                    
                    # Обновляем время последнего алерта
                    self.last_alert_times[key] = now
    
    async def _generate_charts(self):
        """Generating graphs"""
        if not config.charts["enabled"]:
            return
        
        try:
            for network_name in config.networks:
                if self.history[network_name]:
                    await self.chart_generator.generate_network_chart(
                        network_name,
                        self.history[network_name]
                    )
        except Exception as e:
            logger.error(f"Error generating graphs: {e}")
    
    async def _save_history(self):
        """Saving history to a file"""
        try:
            # Конвертируем историю в JSON-сериализуемый формат
            serializable = {}
            for network, data_list in self.history.items():
                serializable[network] = [d.to_dict() for d in data_list]
            
            with open("data/history_backup.json", "w") as f:
                json.dump(serializable, f, indent=2, default=str)
            
            logger.debug("History saved")
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    async def run(self):
        """Basic monitoring cycle"""
        self.is_running = True
        self.iteration = 0
        
        # Инициализация сессии
        await self.init_session()
        
        logger.info("Monitoring has been launched")
        
        # Время последней генерации графиков
        last_chart_time = 0
        last_save_time = 0
        
        try:
            while self.is_running:
                self.iteration += 1
                iteration_start = time.time()
                
                logger.info(f"\n{'='*60}")
                logger.info(f"Iteration {self.iteration} - {datetime.now().strftime('%H:%M:%S')}")
                
                # Обрабатываем все сети параллельно
                tasks = [
                    self._process_network(network_name)
                    for network_name in config.networks
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Подсчет успешных
                successful = sum(1 for r in results if r is not None and not isinstance(r, Exception))
                logger.info(f"Successfully: {successful}/{len(results)} networks")
                
                # Генерация графиков раз в заданный интервал
                now = time.time()
                if config.charts["enabled"] and now - last_chart_time > config.charts["update_interval"]:
                    logger.info("Generating graphs...")
                    await self._generate_charts()
                    last_chart_time = now
                
                # Сохранение истории раз в 5 минут
                if now - last_save_time > config.monitoring["save_history_interval"]:
                    await self._save_history()
                    last_save_time = now
                
                # Ожидание до следующей итерации
                elapsed = time.time() - iteration_start
                sleep_time = max(1, config.monitoring["check_interval"] - elapsed)
                
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                else:
                    logger.warning(f"The iteration took {elapsed:.2f}sec, more than CHECK_INTERVAL")
                    
        except asyncio.CancelledError:
            logger.info("Monitoring canceled")
        except Exception as e:
            logger.error(f"Error in the main loop: {e}")
            raise
        finally:
            # Сохраняем историю при завершении
            await self._save_history()
            logger.info("Мониторинг остановлен")